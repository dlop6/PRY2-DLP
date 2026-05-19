"""Caso 2: entrada válida aceptada."""

from pathlib import Path

import pytest

from grammarModel import Grammar, Production
from lexerAdapter import makeToken, tokenizeSimple
from parserRuntime import parseTokens
from slrGenerator import buildSlrParserTable

EXAMPLES = Path("examples")


@pytest.fixture
def expr_grammar():
    return Grammar(
        tokens={"PLUS", "TIMES", "NUMBER", "LPAREN", "RPAREN", "WS"},
        ignoreTokens={"WS"},
        productions=[
            Production("expr", ("expr", "PLUS", "term")),
            Production("expr", ("term",)),
            Production("term", ("term", "TIMES", "factor")),
            Production("term", ("factor",)),
            Production("factor", ("LPAREN", "expr", "RPAREN")),
            Production("factor", ("NUMBER",)),
        ],
        startSymbol="expr",
    )


@pytest.fixture
def expr_table(expr_grammar):
    return buildSlrParserTable(expr_grammar)


def test_single_number_accepted(expr_table, expr_grammar, capsys):
    tokens = [makeToken("NUMBER", "5", 1, 1)]
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is True
    assert "Parsing exitoso: entrada aceptada." in capsys.readouterr().out


def test_addition_accepted(expr_table, expr_grammar, capsys):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeToken("PLUS", "+", 1, 3),
        makeToken("NUMBER", "2", 1, 5),
    ]
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is True


def test_example_input_valid_file(expr_table, expr_grammar, capsys):
    tokens = tokenizeSimple(str(EXAMPLES / "input_valid.txt"), expr_grammar.tokens)
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is True


def test_whitespace_ignored(expr_table, expr_grammar, capsys):
    tokens = [
        makeToken("NUMBER", "1"),
        makeToken("WS", " "),
        makeToken("PLUS", "+"),
        makeToken("WS", " "),
        makeToken("NUMBER", "2"),
    ]
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is True


def test_nested_parens_accepted(expr_table, expr_grammar, capsys):
    tokens = [
        makeToken("LPAREN", "("),
        makeToken("NUMBER", "3"),
        makeToken("RPAREN", ")"),
    ]
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is True
