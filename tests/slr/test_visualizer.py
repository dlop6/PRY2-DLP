import pytest

from lr0Visualizer import buildLr0DotSource, generateLr0Diagram, isGraphvizAvailable
from slrGenerator import augmentGrammar, buildGotoTable, buildLr0States


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
