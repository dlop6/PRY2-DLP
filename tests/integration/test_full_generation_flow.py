"""Flujo completo: .yalp -> Grammar -> ParserTable -> theparser.py"""

from pathlib import Path

import pytest

from codeGenerator import generateParserFile
from grammarModel import Production
from slrGenerator import SLRConflictError, buildSlrParserTable
from yalpReader import YAParError, parseYalp

FIXTURES = Path("tests/yalp/fixtures")
EXAMPLES = Path("examples")


def test_full_generation_valid_grammar(tmp_path):
    """Caso 1: parser válido generado correctamente."""
    grammar = parseYalp(EXAMPLES / "parser.yalp")
    table = buildSlrParserTable(grammar)
    out = tmp_path / "theparser.py"
    generateParserFile(grammar, table, str(out))
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "def parse(" in content
    assert "TOKENS" in content
    assert "ACTION" in content
    assert "GOTO" in content


def test_full_generation_example_parser(tmp_path):
    grammar = parseYalp(EXAMPLES / "parser.yalp")
    assert "NUMBER" in grammar.tokens
    assert "PLUS" in grammar.tokens
    assert "WS" in grammar.ignoreTokens
    table = buildSlrParserTable(grammar)
    out = tmp_path / "theparser.py"
    generateParserFile(grammar, table, str(out))
    assert out.exists()


def test_full_generation_invalid_yalp_raises():
    with pytest.raises(YAParError):
        parseYalp(FIXTURES / "error_missing_separator.yalp")


def test_full_generation_slr_conflict_raises():
    from grammarModel import Grammar

    grammar = Grammar(
        tokens={"PLUS", "ID"},
        ignoreTokens=set(),
        productions=[
            Production("expr", ("expr", "PLUS", "expr")),
            Production("expr", ("ID",)),
        ],
        startSymbol="expr",
    )
    with pytest.raises(SLRConflictError):
        buildSlrParserTable(grammar)


def test_full_generation_start_symbol_correct():
    grammar = parseYalp(EXAMPLES / "parser.yalp")
    assert grammar.startSymbol == "expr"


def test_full_generation_productions_count():
    grammar = parseYalp(EXAMPLES / "parser.yalp")
    assert len(grammar.productions) == 6
