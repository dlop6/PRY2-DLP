import pytest

from grammarModel import Grammar, Production
from lr0Visualizer import buildLr0DotSource, generateLr0Diagram, isGraphvizAvailable
from slrGenerator import augmentGrammar, buildGotoTable, buildLr0States, buildSLRData


def test_dot_source_contains_states(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    dot = buildLr0DotSource(states, gotoTable)
    assert "I0" in dot
    assert "->" in dot or "->" in dot.replace("\\n", "")


def test_dot_source_has_edges(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    dot = buildLr0DotSource(states, gotoTable)
    assert "program" in dot or len(gotoTable) == 0


def test_generate_lr0_diagram_file(tmp_path, unambiguous_grammar):
    aug = augmentGrammar(unambiguous_grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    output = tmp_path / "lr0.png"
    result = generateLr0Diagram(states, gotoTable, str(output))
    assert result.path.exists()
    assert result.engine in ("graphviz", "matplotlib")


def test_matplotlib_fallback_when_no_dot(tmp_path, unambiguous_grammar, monkeypatch):
    monkeypatch.setattr("lr0Visualizer.isGraphvizAvailable", lambda: False)
    pytest.importorskip("matplotlib")
    pytest.importorskip("networkx")

    aug = augmentGrammar(unambiguous_grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    result = generateLr0Diagram(states, gotoTable, str(tmp_path / "lr0.png"))
    assert result.engine == "matplotlib"
    assert result.path.exists()


def test_accept_state_only_marks_augmented_production(tmp_path):
    """BUG 2: non-terminal con apóstrofe que NO es el aumentado no se marca como accept."""
    # b' aparece en el lado derecho de a -> b', por eso habrá un estado con b' -> X ·
    # la heurística endswith("'") lo marcaría falsamente como accept
    grammar = Grammar(
        tokens={"X"},
        ignoreTokens=set(),
        productions=[
            Production("a", ("b'",)),
            Production("b'", ("X",)),
        ],
        startSymbol="a",
    )
    from lr0Visualizer import _acceptStateIds
    from slrGenerator import Item

    aug, states, gotoTable, allTrans, _ = buildSLRData(grammar)
    assert aug.startSymbol == "a'"

    # localizar IDs de los estados relevantes
    real_accept_id = None
    false_accept_id = None
    for state in states:
        for item in state.items:
            if item.left == "a'" and item.dot == len(item.right):
                real_accept_id = state.id
            if item.left == "b'" and item.dot == len(item.right):
                false_accept_id = state.id

    assert real_accept_id is not None
    assert false_accept_id is not None

    # con el fix: _acceptStateIds recibe augStart explícito
    accept_ids = _acceptStateIds(states, aug.startSymbol)
    assert real_accept_id in accept_ids
    assert false_accept_id not in accept_ids
