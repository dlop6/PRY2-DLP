import pytest
from grammarModel import Production
from yalpReader import _parseProductions, YAParError


def test_produccion_multilinea():
    texto = """
expr:
    expr PLUS term
  | term
;
"""
    prods = _parseProductions(texto)
    assert Production("expr", ("expr", "PLUS", "term")) in prods
    assert Production("expr", ("term",)) in prods
    assert len(prods) == 2


def test_produccion_una_linea():
    prods = _parseProductions("factor: NUMBER | ID ;")
    assert Production("factor", ("NUMBER",)) in prods
    assert Production("factor", ("ID",)) in prods
    assert len(prods) == 2


def test_produccion_alternativa_unica():
    prods = _parseProductions("prod: TOKEN_1 ;")
    assert prods == [Production("prod", ("TOKEN_1",))]


def test_error_sin_colon():
    with pytest.raises(YAParError) as exc:
        _parseProductions("production1\n    TOKEN_1\n;")
    assert str(exc.value) == "Error YAPar: producción sin ':'."


def test_error_sin_semicolon():
    with pytest.raises(YAParError) as exc:
        _parseProductions("production1:\n    TOKEN_1\n")
    assert str(exc.value) == "Error YAPar: producción sin ';'."


def test_alternativa_vacia_genera_epsilon():
    """BUG 6: alternativa vacía es una producción epsilon, no un error."""
    prods = _parseProductions("expr: ;")
    assert Production("expr", ()) in prods


def test_alternativa_vacia_en_medio_genera_epsilon():
    """BUG 6: alternativa vacía en el medio produce tanto la producción normal como epsilon."""
    prods = _parseProductions("expr: PLUS | ;")
    assert Production("expr", ("PLUS",)) in prods
    assert Production("expr", ()) in prods


def test_producciones_duplicadas_se_deduplicen():
    """BUG 9: producciones idénticas no se repiten en la lista."""
    prods = _parseProductions("expr: PLUS | PLUS ;")
    assert len(prods) == 1
    assert Production("expr", ("PLUS",)) in prods


def test_multiples_producciones():
    texto = "a: X ; b: Y ;"
    prods = _parseProductions(texto)
    assert len(prods) == 2
    assert Production("a", ("X",)) in prods
    assert Production("b", ("Y",)) in prods
