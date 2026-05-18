from slr_generator import augment_grammar, build_lr0_states, format_state


def test_lr0_has_initial_state(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    assert len(states) >= 1
    assert states[0].id == 0


def test_initial_state_contains_augmented_item(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    items_text = format_state(states[0])
    assert "program'" in items_text
    assert "program" in items_text


def test_states_numbered_sequentially(unambiguous_grammar):
    aug = augment_grammar(unambiguous_grammar)
    states = build_lr0_states(aug)
    ids = [s.id for s in states]
    assert ids == list(range(len(states)))


def test_no_duplicate_item_sets(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    item_sets = [s.items for s in states]
    assert len(item_sets) == len(set(item_sets))
