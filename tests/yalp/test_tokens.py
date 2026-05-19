import pytest
from yalpReader import _parseTokens, YAParError


def test_token_unico():
    assert _parseTokens("%token TOKEN_1\n") == {"TOKEN_1"}


def test_multiples_tokens_en_linea():
    result = _parseTokens("%token TOKEN_2 TOKEN_3 TOKEN_4\n")
    assert result == {"TOKEN_2", "TOKEN_3", "TOKEN_4"}


def test_multiples_lineas_token():
    result = _parseTokens("%token A\n%token B\n%token C\n")
    assert result == {"A", "B", "C"}


def test_token_ws_valido():
    assert "WS" in _parseTokens("%token WS\n")


def test_error_token_vacio():
    with pytest.raises(YAParError) as exc:
        _parseTokens("%token\n%%\n")
    assert str(exc.value) == "Error YAPar: declaración %token sin tokens."


def test_error_token_minuscula():
    with pytest.raises(YAParError) as exc:
        _parseTokens("%token token_1\n")
    assert str(exc.value) == "Error YAPar: token inválido 'token_1'. Los tokens deben estar en mayúscula."


def test_error_token_duplicado():
    with pytest.raises(YAParError) as exc:
        _parseTokens("%token ID\n%token ID\n")
    assert str(exc.value) == "Error YAPar: token duplicado 'ID'."


def test_ignora_lineas_no_token():
    result = _parseTokens("IGNORE WS\n%token WS\n")
    assert result == {"WS"}
