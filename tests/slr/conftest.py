import pytest

from grammar import Grammar, Production


@pytest.fixture
def simple_program_grammar() -> Grammar:
    """Gramática mínima tipo program / stmt_list."""
    return Grammar(
        tokens={"SEMI", "ID", "ASSIGN", "PLUS", "NUMBER"},
        ignore_tokens=set(),
        productions=[
            Production("program", ("stmt_list",)),
            Production("stmt_list", ("stmt_list", "stmt")),
            Production("stmt_list", ("stmt",)),
            Production("stmt", ("ID", "ASSIGN", "expr", "SEMI")),
            Production("expr", ("expr", "PLUS", "term")),
            Production("expr", ("term",)),
            Production("term", ("NUMBER",)),
        ],
        start_symbol="program",
    )


@pytest.fixture
def expr_grammar() -> Grammar:
    return Grammar(
        tokens={"PLUS", "TIMES", "LPAREN", "RPAREN", "NUMBER", "ID"},
        ignore_tokens=set(),
        productions=[
            Production("expr", ("expr", "PLUS", "term")),
            Production("expr", ("term",)),
            Production("term", ("term", "TIMES", "factor")),
            Production("term", ("factor",)),
            Production("factor", ("LPAREN", "expr", "RPAREN")),
            Production("factor", ("NUMBER",)),
            Production("factor", ("ID",)),
        ],
        start_symbol="expr",
    )


@pytest.fixture
def ambiguous_expr_grammar() -> Grammar:
    """E -> E + E | id — no es SLR (conflictos shift/reduce)."""
    return Grammar(
        tokens={"PLUS", "ID"},
        ignore_tokens=set(),
        productions=[
            Production("E", ("E", "PLUS", "E")),
            Production("E", ("ID",)),
        ],
        start_symbol="E",
    )


@pytest.fixture
def slr_dangling_else_grammar() -> Grammar:
    """Gramática SLR clásica (S -> L = R | R, etc.)."""
    return Grammar(
        tokens={"ASSIGN", "STAR", "ID"},
        ignore_tokens=set(),
        productions=[
            Production("S", ("L", "ASSIGN", "R")),
            Production("S", ("R",)),
            Production("L", ("STAR", "R")),
            Production("L", ("ID",)),
            Production("R", ("L",)),
        ],
        start_symbol="S",
    )


@pytest.fixture
def epsilon_grammar() -> Grammar:
    return Grammar(
        tokens={"a", "b"},
        ignore_tokens=set(),
        productions=[
            Production("S", ("A", "B")),
            Production("A", ()),
            Production("A", ("a",)),
            Production("B", ("b",)),
        ],
        start_symbol="S",
    )


@pytest.fixture
def unambiguous_grammar() -> Grammar:
    return Grammar(
        tokens={"a"},
        ignore_tokens=set(),
        productions=[Production("S", ("a",))],
        start_symbol="S",
    )
