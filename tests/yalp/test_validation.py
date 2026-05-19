import pytest
from grammarModel import Production
from yalpReader import _validateNames, _validateSymbols, YAParError


def test_nombre_valido_minuscula():
    _validateNames([Production("expr", ("X",))])  # no lanza


def test_nombre_valido_con_numero():
    _validateNames([Production("production1", ("X",))])  # no lanza


def test_error_nombre_inicia_mayuscula():
    with pytest.raises(YAParError) as exc:
        _validateNames([Production("Expr", ("X",))])
    assert str(exc.value) == (
        "Error YAPar: nombre de producción inválido 'Expr'. "
        "Los no terminales deben iniciar en minúscula."
    )


def test_error_nombre_todo_mayuscula():
    with pytest.raises(YAParError) as exc:
        _validateNames([Production("TOKEN", ("X",))])
    assert str(exc.value) == (
        "Error YAPar: nombre de producción inválido 'TOKEN'. "
        "Los no terminales deben escribirse como identificadores en minúscula."
    )


def test_simbolos_validos():
    prods = [
        Production("expr", ("expr", "PLUS", "term")),
        Production("term", ("NUMBER",)),
    ]
    _validateSymbols(prods, {"PLUS", "NUMBER"})  # no lanza


def test_error_token_no_declarado():
    prods = [Production("expr", ("PLUS",))]
    with pytest.raises(YAParError) as exc:
        _validateSymbols(prods, set())
    assert str(exc.value) == "Error YAPar: token usado pero no declarado 'PLUS'."


def test_error_no_terminal_no_definido():
    prods = [Production("expr", ("term",))]
    with pytest.raises(YAParError) as exc:
        _validateSymbols(prods, set())
    assert str(exc.value) == "Error YAPar: no terminal usado pero no definido 'term'."


def test_no_terminal_referenciado_en_misma_lista():
    prods = [
        Production("expr", ("term",)),
        Production("term", ("NUM",)),
    ]
    _validateSymbols(prods, {"NUM"})  # no lanza
