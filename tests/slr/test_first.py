from grammarModel import Grammar, Production
from slrGenerator import EPSILON, _firstOfSequence, augmentGrammar, computeFirst, formatFirst


def test_first_terminals(expr_grammar):
    first = computeFirst(expr_grammar)
    assert first["NUMBER"] == {"NUMBER"}
    assert first["PLUS"] == {"PLUS"}


def test_first_simple_nonterminal(expr_grammar):
    first = computeFirst(expr_grammar)
    assert "NUMBER" in first["factor"]
    assert "LPAREN" in first["factor"]
    assert "ID" in first["factor"]


def test_first_expr_includes_terminals(expr_grammar):
    first = computeFirst(expr_grammar)
    assert "NUMBER" in first["expr"]
    assert "LPAREN" in first["expr"]


def test_first_epsilon_production(epsilon_grammar):
    first = computeFirst(epsilon_grammar)
    assert EPSILON in first["A"]
    assert "a" in first["A"]


def test_first_chain_with_epsilon(epsilon_grammar):
    first = computeFirst(epsilon_grammar)
    assert "b" in first["S"]
    assert "a" in first["S"]


def test_format_first_readable(expr_grammar):
    first = computeFirst(expr_grammar)
    text = formatFirst(first, "factor")
    assert "NUMBER" in text
    assert text.startswith("FIRST(factor)")


def test_first_augmented_grammar(expr_grammar):
    aug = augmentGrammar(expr_grammar)
    first = computeFirst(aug)
    assert "expr" in first["expr'"] or "NUMBER" in first["expr'"]


def test_first_of_sequence_unknown_symbol_is_terminal():
    """BUG 3: símbolo ausente del dict first se trata como terminal (no deriva epsilon)."""
    result = _firstOfSequence(("UNKNOWN",), {})
    assert result == {"UNKNOWN"}
    assert EPSILON not in result


def test_first_of_sequence_unknown_symbol_stops_propagation():
    """BUG 3: símbolo desconocido no propaga epsilon al siguiente símbolo."""
    result = _firstOfSequence(("UNKNOWN", "Y"), {"Y": {"y"}})
    assert "UNKNOWN" in result
    assert "y" not in result
    assert EPSILON not in result
