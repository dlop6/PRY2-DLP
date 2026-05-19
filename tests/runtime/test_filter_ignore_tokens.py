from lexerAdapter import makeToken, filterIgnoredTokens


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
