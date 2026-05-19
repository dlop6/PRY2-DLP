from lexerAdapter import makeToken
from parserRuntime import parseTokens


def test_syntax_error_returns_false(expr_table):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeToken("PLUS", "+", 1, 3),
        makeToken("PLUS", "+", 1, 5),
    ]
    assert parseTokens(tokens, expr_table) is False


def test_syntax_error_message(expr_table, capsys):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeToken("PLUS", "+", 1, 3),
        makeToken("PLUS", "+", 1, 5),
    ]
    parseTokens(tokens, expr_table)
    out = capsys.readouterr().out
    assert "Error sintáctico" in out
    assert "PLUS" in out


def test_syntax_error_shows_expected_tokens(expr_table, capsys):
    tokens = [makeToken("PLUS", "+", 1, 1)]
    parseTokens(tokens, expr_table)
    out = capsys.readouterr().out
    assert "Tokens esperados" in out


def test_syntax_error_shows_line_and_column(expr_table, capsys):
    tokens = [makeToken("PLUS", "+", 3, 7)]
    parseTokens(tokens, expr_table)
    out = capsys.readouterr().out
    assert "línea 3" in out
    assert "columna 7" in out
