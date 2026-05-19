"""Caso 3: entrada con error sintáctico."""

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


def test_syntax_error_returns_false(expr_table, expr_grammar):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeToken("PLUS", "+", 1, 3),
        makeToken("PLUS", "+", 1, 5),
    ]
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is False


def test_syntax_error_message_printed(expr_table, expr_grammar, capsys):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeToken("PLUS", "+", 1, 3),
        makeToken("PLUS", "+", 1, 5),
    ]
    parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    out = capsys.readouterr().out
    assert "Error sintáctico" in out
    assert "PLUS" in out


def test_example_syntax_error_file(expr_table, expr_grammar, capsys):
    tokens = tokenizeSimple(str(EXAMPLES / "medium" / "input_error.txt"), expr_grammar.tokens)
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is False
    out = capsys.readouterr().out
    assert "Error sintáctico" in out


def test_syntax_error_shows_expected(expr_table, expr_grammar, capsys):
    tokens = [makeToken("PLUS", "+", 1, 1)]
    parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    out = capsys.readouterr().out
    assert "Tokens esperados" in out


def test_empty_input_syntax_error(expr_table, expr_grammar, capsys):
    result = parseTokens([], expr_table, expr_grammar.ignoreTokens)
    assert result is False
    out = capsys.readouterr().out
    assert "Error sintáctico" in out
