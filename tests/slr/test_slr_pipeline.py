from grammarModel import Grammar, Production
from slrGenerator import (
    ParserTable,
    augmentGrammar,
    buildSlrParserTable,
    buildLr0States,
    buildSLRData,
    formatState,
)


def test_build_slr_parser_table_returns_parser_table(unambiguous_grammar):
    table = buildSlrParserTable(unambiguous_grammar)
    assert isinstance(table, ParserTable)
    assert table.productions[0].left.endswith("'")


def test_augment_grammar_inserts_prime_production(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    assert aug.productions[0].left == "program'"
    assert aug.productions[0].right == ("program",)
    assert aug.startSymbol == "program'"
    assert len(aug.productions) == len(simple_program_grammar.productions) + 1


def test_augmented_production_is_index_zero(unambiguous_grammar):
    table = buildSlrParserTable(unambiguous_grammar)
    assert table.productions[0].left == "S'"
    assert table.productions[0].right == ("S",)


def test_readable_state_output(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    text = formatState(states[0])
    assert text.startswith("I0:")
    assert "·" in text


def test_augment_grammar_no_collision_with_apostrophe_nonterminal():
    """BUG 1: si existe un non-terminal 's\'' el símbolo aumentado debe ser 's\'\''."""
    grammar = Grammar(
        tokens={"X"},
        ignoreTokens=set(),
        productions=[
            Production("s", ("X",)),
            Production("s'", ("s",)),
        ],
        startSymbol="s",
    )
    aug = augmentGrammar(grammar)
    assert aug.startSymbol == "s''"
    assert aug.productions[0].left == "s''"
    assert aug.productions[0].right == ("s",)


def test_build_slr_data_returns_all_components(unambiguous_grammar):
    """BUG 8: buildSLRData devuelve aug, states, gotoTable, allTrans, table en una sola llamada."""
    aug, states, gotoTable, allTrans, table = buildSLRData(unambiguous_grammar)
    assert aug.startSymbol.endswith("'")
    assert len(states) > 0
    assert isinstance(table, ParserTable)
    assert table.productions[0].left == aug.startSymbol


def test_build_slr_data_consistent_with_build_slr_parser_table(expr_grammar):
    """BUG 8: la tabla de buildSLRData debe ser idéntica a la de buildSlrParserTable."""
    _, _, _, _, table_via_data = buildSLRData(expr_grammar)
    table_direct = buildSlrParserTable(expr_grammar)
    assert table_via_data.action == table_direct.action
    assert table_via_data.goto == table_direct.goto
    assert table_via_data.productions == table_direct.productions
