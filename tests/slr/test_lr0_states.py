from slrGenerator import augmentGrammar, buildLr0States, formatState


def test_lr0_has_initial_state(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    assert len(states) >= 1
    assert states[0].id == 0


def test_initial_state_contains_augmented_item(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    itemsText = formatState(states[0])
    assert "program'" in itemsText
    assert "program" in itemsText


def test_states_numbered_sequentially(unambiguous_grammar):
    aug = augmentGrammar(unambiguous_grammar)
    states = buildLr0States(aug)
    ids = [s.id for s in states]
    assert ids == list(range(len(states)))


def test_no_duplicate_item_sets(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    itemSets = [s.items for s in states]
    assert len(itemSets) == len(set(itemSets))
