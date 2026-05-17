import pytest
from grammar import Production
from yalp_reader import _parse_productions, YAParError


def test_produccion_multilinea():
    texto = """
expr:
    expr PLUS term
  | term
;
"""
    prods = _parse_productions(texto)
    assert Production("expr", ("expr", "PLUS", "term")) in prods
    assert Production("expr", ("term",)) in prods
    assert len(prods) == 2


def test_produccion_una_linea():
    prods = _parse_productions("factor: NUMBER | ID ;")
    assert Production("factor", ("NUMBER",)) in prods
    assert Production("factor", ("ID",)) in prods
    assert len(prods) == 2


def test_produccion_alternativa_unica():
    prods = _parse_productions("prod: TOKEN_1 ;")
    assert prods == [Production("prod", ("TOKEN_1",))]


def test_error_sin_colon():
    with pytest.raises(YAParError) as exc:
        _parse_productions("production1\n    TOKEN_1\n;")
    assert str(exc.value) == "Error YAPar: producción sin ':'."


def test_error_sin_semicolon():
    with pytest.raises(YAParError) as exc:
        _parse_productions("production1:\n    TOKEN_1\n")
    assert str(exc.value) == "Error YAPar: producción sin ';'."


def test_error_alternativa_vacia_simple():
    with pytest.raises(YAParError) as exc:
        _parse_productions("expr: ;")
    assert str(exc.value) == "Error YAPar: producción vacía."


def test_error_alternativa_vacia_en_medio():
    with pytest.raises(YAParError) as exc:
        _parse_productions("expr: PLUS | ;")
    assert str(exc.value) == "Error YAPar: producción vacía."


def test_multiples_producciones():
    texto = "a: X ; b: Y ;"
    prods = _parse_productions(texto)
    assert len(prods) == 2
    assert Production("a", ("X",)) in prods
    assert Production("b", ("Y",)) in prods
