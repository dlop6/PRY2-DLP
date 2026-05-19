"""Fixtures compartidos para tests del runtime del parser."""

import pytest
from grammarModel import Grammar, Production
from slrGenerator import buildSlrParserTable, ParserTable
from lexerAdapter import makeToken, makeLexicalError


@pytest.fixture
def simple_grammar() -> Grammar:
    """Gramática mínima: s -> A"""
    return Grammar(
        tokens={"A"},
        ignoreTokens=set(),
        productions=[Production("s", ("A",))],
        startSymbol="s",
    )


@pytest.fixture
def simple_table(simple_grammar) -> ParserTable:
    return buildSlrParserTable(simple_grammar)


@pytest.fixture
def expr_grammar() -> Grammar:
    """Gramática aritmética no ambigua: expr -> expr PLUS term | term; term -> NUMBER"""
    return Grammar(
        tokens={"PLUS", "NUMBER"},
        ignoreTokens=set(),
        productions=[
            Production("expr", ("expr", "PLUS", "term")),
            Production("expr", ("term",)),
            Production("term", ("NUMBER",)),
        ],
        startSymbol="expr",
    )


@pytest.fixture
def expr_table(expr_grammar) -> ParserTable:
    return buildSlrParserTable(expr_grammar)


@pytest.fixture
def expr_grammar_with_ignore() -> Grammar:
    return Grammar(
        tokens={"PLUS", "NUMBER", "WS"},
        ignoreTokens={"WS"},
        productions=[
            Production("expr", ("expr", "PLUS", "term")),
            Production("expr", ("term",)),
            Production("term", ("NUMBER",)),
        ],
        startSymbol="expr",
    )


@pytest.fixture
def expr_table_with_ignore(expr_grammar_with_ignore) -> ParserTable:
    return buildSlrParserTable(expr_grammar_with_ignore)
