from slr_generator import (
    ParserTable,
    augment_grammar,
    build_slr_parser_table,
    format_state,
)


def test_build_slr_parser_table_returns_parser_table(unambiguous_grammar):
    table = build_slr_parser_table(unambiguous_grammar)
    assert isinstance(table, ParserTable)
    assert table.productions[0].left.endswith("'")


def test_augment_grammar_inserts_prime_production(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    assert aug.productions[0].left == "program'"
    assert aug.productions[0].right == ("program",)
    assert aug.start_symbol == "program'"
    assert len(aug.productions) == len(simple_program_grammar.productions) + 1


def test_augmented_production_is_index_zero(unambiguous_grammar):
    table = build_slr_parser_table(unambiguous_grammar)
    assert table.productions[0].left == "S'"
    assert table.productions[0].right == ("S",)


def test_readable_state_output(simple_program_grammar):
    from slr_generator import build_lr0_states

    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    text = format_state(states[0])
    assert text.startswith("I0:")
    assert "·" in text
