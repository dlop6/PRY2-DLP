from lexerAdapter import makeToken
from parserRuntime import parseTokens


def test_accept_returns_true(simple_table):
    tokens = [makeToken("A", "a")]
    assert parseTokens(tokens, simple_table) is True


def test_accept_prints_message(simple_table, capsys):
    tokens = [makeToken("A", "a")]
    parseTokens(tokens, simple_table)
    out = capsys.readouterr().out
    assert "Parsing exitoso: entrada aceptada." in out


def test_accept_expr(expr_table, capsys):
    tokens = [
        makeToken("NUMBER", "3"),
        makeToken("PLUS", "+"),
        makeToken("NUMBER", "4"),
    ]
    result = parseTokens(tokens, expr_table)
    out = capsys.readouterr().out
    assert result is True
    assert "Parsing exitoso: entrada aceptada." in out
