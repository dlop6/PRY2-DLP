import pytest
from lexerAdapter import makeToken, filterIgnoredTokens
from parserRuntime import parseTokens


def test_filter_removes_ignored():
    tokens = [
        makeToken("NUMBER", "1"),
        makeToken("WS", " "),
        makeToken("PLUS", "+"),
        makeToken("WS", "\t"),
        makeToken("NUMBER", "2"),
    ]
    result = filterIgnoredTokens(tokens, {"WS"})
    assert [t["type"] for t in result] == ["NUMBER", "PLUS", "NUMBER"]


def test_filter_empty_ignore_set():
    tokens = [makeToken("A", "a"), makeToken("B", "b")]
    assert filterIgnoredTokens(tokens, set()) == tokens


def test_filter_all_tokens_ignored():
    tokens = [makeToken("WS", " "), makeToken("WS", "\n")]
    assert filterIgnoredTokens(tokens, {"WS"}) == []


def test_filter_preserves_lexical_errors():
    tokens = [
        makeToken("NUMBER", "1"),
        {"type": "LEXICAL_ERROR", "lexeme": "@", "line": 1, "column": 8, "message": "símbolo no reconocido"},
    ]
    result = filterIgnoredTokens(tokens, {"WS"})
    assert len(result) == 2
    assert result[1]["type"] == "LEXICAL_ERROR"


def test_parse_tokens_none_ignore_same_as_empty_set(simple_table):
    """BUG 16: ignoreTokens=None e ignoreTokens=set() producen el mismo resultado."""
    tokens = [makeToken("A", "a")]
    result_none = parseTokens(tokens, simple_table, ignoreTokens=None)
    result_empty = parseTokens(tokens, simple_table, ignoreTokens=set())
    assert result_none == result_empty is True
