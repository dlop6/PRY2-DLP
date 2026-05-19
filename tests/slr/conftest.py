import pytest

from grammarModel import Grammar, Production


@pytest.fixture
def simple_program_grammar() -> Grammar:
    """Gramática mínima tipo program / stmt_list."""
    return Grammar(
        tokens={"SEMI", "ID", "ASSIGN", "PLUS", "NUMBER"},
        ignoreTokens=set(),
        productions=[
            Production("program", ("stmt_list",)),
            Production("stmt_list", ("stmt_list", "stmt")),
            Production("stmt_list", ("stmt",)),
            Production("stmt", ("ID", "ASSIGN", "expr", "SEMI")),
            Production("expr", ("expr", "PLUS", "term")),
            Production("expr", ("term",)),
            Production("term", ("NUMBER",)),
        ],
        startSymbol="program",
    )


@pytest.fixture
def expr_grammar() -> Grammar:
    return Grammar(
        tokens={"PLUS", "TIMES", "LPAREN", "RPAREN", "NUMBER", "ID"},
        ignoreTokens=set(),
        productions=[
            Production("expr", ("expr", "PLUS", "term")),
            Production("expr", ("term",)),
            Production("term", ("term", "TIMES", "factor")),
            Production("term", ("factor",)),
            Production("factor", ("LPAREN", "expr", "RPAREN")),
            Production("factor", ("NUMBER",)),
            Production("factor", ("ID",)),
        ],
        startSymbol="expr",
    )


@pytest.fixture
def ambiguous_expr_grammar() -> Grammar:
    """E -> E + E | id — no es SLR (conflictos shift/reduce)."""
    return Grammar(
        tokens={"PLUS", "ID"},
        ignoreTokens=set(),
        productions=[
            Production("E", ("E", "PLUS", "E")),
            Production("E", ("ID",)),
        ],
        startSymbol="E",
    )


@pytest.fixture
def slr_aho_ullman_grammar() -> Grammar:
    """Gramática clásica Aho-Ullman (S -> L = R | R, etc.) — no es SLR."""
    return Grammar(
        tokens={"ASSIGN", "STAR", "ID"},
        ignoreTokens=set(),
        productions=[
            Production("S", ("L", "ASSIGN", "R")),
            Production("S", ("R",)),
            Production("L", ("STAR", "R")),
            Production("L", ("ID",)),
            Production("R", ("L",)),
        ],
        startSymbol="S",
    )


@pytest.fixture
def epsilon_grammar() -> Grammar:
    return Grammar(
        tokens={"a", "b"},
        ignoreTokens=set(),
        productions=[
            Production("S", ("A", "B")),
            Production("A", ()),
            Production("A", ("a",)),
            Production("B", ("b",)),
        ],
        startSymbol="S",
    )


@pytest.fixture
def unambiguous_grammar() -> Grammar:
    return Grammar(
        tokens={"a"},
        ignoreTokens=set(),
        productions=[Production("S", ("a",))],
        startSymbol="S",
    )
