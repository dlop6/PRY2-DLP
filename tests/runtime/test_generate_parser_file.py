import importlib.util
from pathlib import Path

import pytest

from codeGenerator import generateParserFile
from grammarModel import Grammar, Production
from slrGenerator import buildSlrParserTable


@pytest.fixture
def simple_grammar():
    return Grammar(
        tokens={"A"},
        ignoreTokens=set(),
        productions=[Production("s", ("A",))],
        startSymbol="s",
    )


@pytest.fixture
def generated_parser(simple_grammar, tmp_path):
    table = buildSlrParserTable(simple_grammar)
    out = tmp_path / "theparser.py"
    generateParserFile(simple_grammar, table, str(out))
    return out


def test_file_is_created(generated_parser):
    assert generated_parser.exists()


def test_file_contains_tokens(generated_parser):
    content = generated_parser.read_text(encoding="utf-8")
    assert "TOKENS" in content
    assert '"A"' in content


def test_file_contains_productions(generated_parser):
    content = generated_parser.read_text(encoding="utf-8")
    assert "PRODUCTIONS" in content
    assert '"s"' in content


def test_file_contains_action_and_goto(generated_parser):
    content = generated_parser.read_text(encoding="utf-8")
    assert "ACTION" in content
    assert "GOTO" in content


def test_file_contains_parse_function(generated_parser):
    content = generated_parser.read_text(encoding="utf-8")
    assert "def parse(" in content


def test_file_no_regex_import(generated_parser):
    content = generated_parser.read_text(encoding="utf-8")
    assert "import re" not in content


def test_generated_parser_accepts_valid_input(generated_parser, capsys):
    spec = importlib.util.spec_from_file_location("theparser_test", generated_parser)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tokens = [{"type": "A", "lexeme": "a", "line": 1, "column": 1}]
    result = mod.parse(tokens)
    out = capsys.readouterr().out
    assert result is True
    assert "Parsing exitoso" in out


def test_generated_parser_rejects_invalid_input(generated_parser, capsys):
    spec = importlib.util.spec_from_file_location("theparser_test2", generated_parser)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tokens = [
        {"type": "A", "lexeme": "a", "line": 1, "column": 1},
        {"type": "A", "lexeme": "a", "line": 1, "column": 3},
    ]
    result = mod.parse(tokens)
    assert result is False
