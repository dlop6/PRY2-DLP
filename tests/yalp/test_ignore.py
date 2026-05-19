import pytest
from yalpReader import _parseIgnore, YAParError


def test_ignore_simple():
    assert _parseIgnore("IGNORE WS\n", {"WS"}) == {"WS"}


def test_ignore_multiples():
    result = _parseIgnore("IGNORE WS COMMENT\n", {"WS", "COMMENT"})
    assert result == {"WS", "COMMENT"}


def test_sin_ignore_retorna_vacio():
    assert _parseIgnore("%token TOKEN_1\n", {"TOKEN_1"}) == set()


def test_error_ignore_sin_tokens():
    with pytest.raises(YAParError) as exc:
        _parseIgnore("IGNORE\n", {"WS"})
    assert str(exc.value) == "Error YAPar: declaración IGNORE sin tokens."


def test_error_token_no_declarado():
    with pytest.raises(YAParError) as exc:
        _parseIgnore("IGNORE SPACE\n", {"WS"})
    assert str(exc.value) == "Error YAPar: token ignorado no declarado 'SPACE'."
