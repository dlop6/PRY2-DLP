import pytest
from grammarModel import Production, Grammar


def test_production_instanciable():
    p = Production("expr", ("PLUS", "term"))
    assert p.left == "expr"
    assert p.right == ("PLUS", "term")


def test_production_es_frozen():
    p = Production("expr", ("PLUS",))
    with pytest.raises(Exception):
        p.left = "otro"


def test_production_igualdad_por_valor():
    p1 = Production("expr", ("PLUS", "term"))
    p2 = Production("expr", ("PLUS", "term"))
    assert p1 == p2


def test_production_desigualdad():
    p1 = Production("expr", ("PLUS",))
    p2 = Production("expr", ("MINUS",))
    assert p1 != p2


def test_grammar_instanciable():
    g = Grammar(
        tokens={"TOKEN_1", "TOKEN_2"},
        ignoreTokens={"TOKEN_2"},
        productions=[Production("prod", ("TOKEN_1",))],
        startSymbol="prod",
    )
    assert "TOKEN_1" in g.tokens
    assert "TOKEN_2" in g.ignoreTokens
    assert g.startSymbol == "prod"
    assert len(g.productions) == 1


def test_grammar_campos_mutables():
    g = Grammar(tokens=set(), ignoreTokens=set(), productions=[], startSymbol="")
    g.tokens.add("X")
    assert "X" in g.tokens
