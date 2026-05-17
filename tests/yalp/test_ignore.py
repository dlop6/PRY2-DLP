import pytest
from yalp_reader import _parse_ignore, YAParError


def test_ignore_simple():
    assert _parse_ignore("IGNORE WS\n", {"WS"}) == {"WS"}


def test_ignore_multiples():
    result = _parse_ignore("IGNORE WS COMMENT\n", {"WS", "COMMENT"})
    assert result == {"WS", "COMMENT"}


def test_sin_ignore_retorna_vacio():
    assert _parse_ignore("%token TOKEN_1\n", {"TOKEN_1"}) == set()


def test_error_ignore_sin_tokens():
    with pytest.raises(YAParError) as exc:
        _parse_ignore("IGNORE\n", {"WS"})
    assert str(exc.value) == "Error YAPar: declaración IGNORE sin tokens."


def test_error_token_no_declarado():
    with pytest.raises(YAParError) as exc:
        _parse_ignore("IGNORE SPACE\n", {"WS"})
    assert str(exc.value) == "Error YAPar: token ignorado no declarado 'SPACE'."
