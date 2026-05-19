"""Caso 4: entrada con error léxico."""

from pathlib import Path

import pytest

from grammarModel import Grammar, Production
from lexerAdapter import makeLexicalError, makeToken, tokenizeSimple
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


def test_lexical_error_returns_false(expr_table, expr_grammar):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeLexicalError("@", 1, 9),
        makeToken("NUMBER", "2", 1, 11),
    ]
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is False


def test_lexical_error_message_printed(expr_table, expr_grammar, capsys):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeLexicalError("@", 1, 9),
    ]
    parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    out = capsys.readouterr().out
    assert "Error léxico en línea 1, columna 9." in out
    assert "Símbolo: '@'" in out


def test_example_lexical_error_file(expr_table, expr_grammar, capsys):
    tokens = tokenizeSimple(str(EXAMPLES / "input_lexical_error.txt"), expr_grammar.tokens)
    result = parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    assert result is False
    out = capsys.readouterr().out
    assert "Error léxico" in out
    assert "@" in out


def test_lexical_error_before_syntax_check(expr_table, expr_grammar, capsys):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeLexicalError("$$", 1, 3, message="símbolo ilegal"),
    ]
    parseTokens(tokens, expr_table, expr_grammar.ignoreTokens)
    out = capsys.readouterr().out
    assert "símbolo ilegal" in out
    assert "Error sintáctico" not in out
