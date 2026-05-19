"""El parser aplica reduce correctamente."""

from lexerAdapter import makeToken
from parserRuntime import parseTokens


def test_reduce_single_production(simple_table, capsys):
    tokens = [makeToken("A", "a")]
    result = parseTokens(tokens, simple_table)
    assert result is True
    out = capsys.readouterr().out
    assert "Parsing exitoso" in out


def test_reduce_chain(expr_table, capsys):
    tokens = [makeToken("NUMBER", "42")]
    result = parseTokens(tokens, expr_table)
    assert result is True


def test_reduce_with_multiple_symbols(expr_table, capsys):
    tokens = [
        makeToken("NUMBER", "1"),
        makeToken("PLUS", "+"),
        makeToken("NUMBER", "2"),
    ]
    result = parseTokens(tokens, expr_table)
    assert result is True
