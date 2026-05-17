import pytest
from yalp_reader import _parse_tokens, YAParError


def test_token_unico():
    assert _parse_tokens("%token TOKEN_1\n") == {"TOKEN_1"}


def test_multiples_tokens_en_linea():
    result = _parse_tokens("%token TOKEN_2 TOKEN_3 TOKEN_4\n")
    assert result == {"TOKEN_2", "TOKEN_3", "TOKEN_4"}


def test_multiples_lineas_token():
    result = _parse_tokens("%token A\n%token B\n%token C\n")
    assert result == {"A", "B", "C"}


def test_token_ws_valido():
    assert "WS" in _parse_tokens("%token WS\n")


def test_error_token_vacio():
    with pytest.raises(YAParError) as exc:
        _parse_tokens("%token\n%%\n")
    assert str(exc.value) == "Error YAPar: declaración %token sin tokens."


def test_error_token_minuscula():
    with pytest.raises(YAParError) as exc:
        _parse_tokens("%token token_1\n")
    assert str(exc.value) == "Error YAPar: token inválido 'token_1'. Los tokens deben estar en mayúscula."


def test_error_token_duplicado():
    with pytest.raises(YAParError) as exc:
        _parse_tokens("%token ID\n%token ID\n")
    assert str(exc.value) == "Error YAPar: token duplicado 'ID'."


def test_ignora_lineas_no_token():
    result = _parse_tokens("IGNORE WS\n%token WS\n")
    assert result == {"WS"}
