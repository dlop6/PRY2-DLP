import pytest

from lr0_visualizer import build_lr0_dot_source, generate_lr0_diagram
from slr_generator import augment_grammar, build_goto_table, build_lr0_states


def test_dot_source_contains_states(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    goto_table = build_goto_table(aug, states)
    dot = build_lr0_dot_source(states, goto_table)
    assert "I0" in dot
    assert "->" in dot or "->" in dot.replace("\\n", "")


def test_dot_source_has_edges(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    goto_table = build_goto_table(aug, states)
    dot = build_lr0_dot_source(states, goto_table)
    assert "program" in dot or len(goto_table) == 0


def test_generate_lr0_diagram_file(tmp_path, unambiguous_grammar):
    aug = augment_grammar(unambiguous_grammar)
    states = build_lr0_states(aug)
    goto_table = build_goto_table(aug, states)
    output = tmp_path / "lr0.png"
    result = generate_lr0_diagram(states, goto_table, str(output))
    assert result.path.exists()
    assert result.engine in ("graphviz", "matplotlib")


def test_matplotlib_fallback_when_no_dot(tmp_path, unambiguous_grammar, monkeypatch):
    monkeypatch.setattr("lr0_visualizer.is_graphviz_available", lambda: False)
    pytest.importorskip("matplotlib")
    pytest.importorskip("networkx")

    aug = augment_grammar(unambiguous_grammar)
    states = build_lr0_states(aug)
    goto_table = build_goto_table(aug, states)
    result = generate_lr0_diagram(states, goto_table, str(tmp_path / "lr0.png"))
    assert result.engine == "matplotlib"
    assert result.path.exists()
