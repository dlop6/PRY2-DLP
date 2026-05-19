from slrGenerator import (
    ParserTable,
    augmentGrammar,
    buildSlrParserTable,
    buildLr0States,
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
