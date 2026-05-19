"""El parser aplica shift correctamente al avanzar en la entrada."""

from lexerAdapter import makeToken
from parserRuntime import parseTokens


def test_shift_leads_to_accept(simple_table, capsys):
    tokens = [makeToken("A", "a")]
    result = parseTokens(tokens, simple_table)
    assert result is True
    out = capsys.readouterr().out
    assert "Parsing exitoso" in out


def test_shift_consumes_all_tokens(expr_table, capsys):
    tokens = [makeToken("NUMBER", "5", 1, 1)]
    result = parseTokens(tokens, expr_table)
    assert result is True


def test_shift_multiple_tokens(expr_table, capsys):
    tokens = [
        makeToken("NUMBER", "1", 1, 1),
        makeToken("PLUS", "+", 1, 3),
        makeToken("NUMBER", "2", 1, 5),
    ]
    result = parseTokens(tokens, expr_table)
    assert result is True
