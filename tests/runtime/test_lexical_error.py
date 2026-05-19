from lexerAdapter import makeLexicalError, makeToken
from parserRuntime import parseTokens


def test_lexical_error_returns_false(expr_table):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeLexicalError("@", 1, 3),
    ]
    assert parseTokens(tokens, expr_table) is False


def test_lexical_error_message(expr_table, capsys):
    tokens = [makeLexicalError("@", 2, 4)]
    parseTokens(tokens, expr_table)
    out = capsys.readouterr().out
    assert "Error léxico en línea 2, columna 4." in out
    assert "Símbolo: '@'" in out
    assert "Detalle: símbolo no reconocido." in out


def test_lexical_error_stops_at_first_error(expr_table, capsys):
    tokens = [
        makeLexicalError("@", 1, 1),
        makeLexicalError("#", 1, 3),
    ]
    parseTokens(tokens, expr_table)
    out = capsys.readouterr().out
    assert out.count("Error léxico") == 1


def test_lexical_error_with_custom_message(expr_table, capsys):
    tokens = [makeLexicalError("$$", 1, 1, message="token ilegal")]
    parseTokens(tokens, expr_table)
    out = capsys.readouterr().out
    assert "token ilegal" in out
