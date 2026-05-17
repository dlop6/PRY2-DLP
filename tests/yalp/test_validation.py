import pytest
from grammar import Production
from yalp_reader import _validate_names, _validate_symbols, YAParError


# --- _validate_names ---

def test_nombre_valido_minuscula():
    _validate_names([Production("expr", ("X",))])  # no lanza


def test_nombre_valido_con_numero():
    _validate_names([Production("production1", ("X",))])  # no lanza


def test_error_nombre_inicia_mayuscula():
    with pytest.raises(YAParError) as exc:
        _validate_names([Production("Expr", ("X",))])
    assert str(exc.value) == (
        "Error YAPar: nombre de producción inválido 'Expr'. "
        "Los no terminales deben iniciar en minúscula."
    )


def test_error_nombre_todo_mayuscula():
    with pytest.raises(YAParError) as exc:
        _validate_names([Production("TOKEN", ("X",))])
    assert str(exc.value) == (
        "Error YAPar: nombre de producción inválido 'TOKEN'. "
        "Los no terminales deben escribirse como identificadores en minúscula."
    )


# --- _validate_symbols ---

def test_simbolos_validos():
    prods = [
        Production("expr", ("expr", "PLUS", "term")),
        Production("term", ("NUMBER",)),
    ]
    _validate_symbols(prods, {"PLUS", "NUMBER"})  # no lanza


def test_error_token_no_declarado():
    prods = [Production("expr", ("PLUS",))]
    with pytest.raises(YAParError) as exc:
        _validate_symbols(prods, set())
    assert str(exc.value) == "Error YAPar: token usado pero no declarado 'PLUS'."


def test_error_no_terminal_no_definido():
    prods = [Production("expr", ("term",))]
    with pytest.raises(YAParError) as exc:
        _validate_symbols(prods, set())
    assert str(exc.value) == "Error YAPar: no terminal usado pero no definido 'term'."


def test_no_terminal_referenciado_en_misma_lista():
    prods = [
        Production("expr", ("term",)),
        Production("term", ("NUM",)),
    ]
    _validate_symbols(prods, {"NUM"})  # no lanza
