import pytest
from pathlib import Path
from grammar import Production
from yalp_reader import parse_yalp, YAParError

FIXTURES = Path("tests/yalp/fixtures")


# --- casos válidos ---

def test_valid_basic_yalp():
    g = parse_yalp(FIXTURES / "valid_basic.yalp")
    assert g.start_symbol == "production1"
    assert g.tokens == {"TOKEN_1", "TOKEN_2", "TOKEN_3", "TOKEN_4", "WS"}
    assert g.ignore_tokens == {"WS"}
    assert len(g.productions) == 6


def test_valid_basic_producciones_correctas():
    g = parse_yalp(FIXTURES / "valid_basic.yalp")
    assert Production("production1", ("production1", "TOKEN_2", "production2")) in g.productions
    assert Production("production1", ("production2",)) in g.productions
    assert Production("production3", ("TOKEN_1",)) in g.productions


def test_valid_with_ignore():
    g = parse_yalp(FIXTURES / "valid_with_ignore.yalp")
    assert "WS" in g.ignore_tokens
    assert "WS" in g.tokens
    assert g.start_symbol == "expr"
    assert len(g.productions) == 2


# --- errores de comentarios ---

def test_error_unclosed_comment():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_unclosed_comment.yalp")
    assert str(exc.value) == "Error YAPar: comentario sin cerrar."


# --- errores de separador ---

def test_error_missing_separator():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_missing_separator.yalp")
    assert str(exc.value) == "Error YAPar: falta separador %% entre tokens y producciones."


def test_error_multiple_separator():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_multiple_separator.yalp")
    assert str(exc.value) == "Error YAPar: se encontró más de un separador %%."


# --- errores de tokens ---

def test_error_empty_token():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_empty_token.yalp")
    assert str(exc.value) == "Error YAPar: declaración %token sin tokens."


def test_error_duplicate_token():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_duplicate_token.yalp")
    assert str(exc.value) == "Error YAPar: token duplicado 'ID'."


def test_error_lowercase_token():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_lowercase_token.yalp")
    assert str(exc.value) == "Error YAPar: token inválido 'token_1'. Los tokens deben estar en mayúscula."


# --- errores de IGNORE ---

def test_error_ignore_undeclared_token():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_ignore_undeclared_token.yalp")
    assert str(exc.value) == "Error YAPar: token ignorado no declarado 'SPACE'."


# --- errores de producciones ---

def test_error_missing_semicolon():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_missing_semicolon.yalp")
    assert str(exc.value) == "Error YAPar: producción sin ';'."


def test_error_missing_colon():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_missing_colon.yalp")
    assert str(exc.value) == "Error YAPar: producción sin ':'."


# --- errores de validación de símbolos ---

def test_error_undeclared_token_in_production():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_undeclared_token_in_production.yalp")
    assert str(exc.value) == "Error YAPar: token usado pero no declarado 'PLUS'."


def test_error_undefined_nonterminal():
    with pytest.raises(YAParError) as exc:
        parse_yalp(FIXTURES / "error_undefined_nonterminal.yalp")
    assert str(exc.value) == "Error YAPar: no terminal usado pero no definido 'term'."
