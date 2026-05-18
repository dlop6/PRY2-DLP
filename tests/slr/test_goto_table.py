from slr_generator import augment_grammar, build_goto_table, build_lr0_states, format_goto_entry


def test_goto_nonterminal_only(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    goto_table = build_goto_table(aug, states)
    for (_, symbol), _ in goto_table.items():
        assert symbol in {p.left for p in aug.productions}


def test_goto_from_initial_state(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    goto_table = build_goto_table(aug, states)
    assert (0, "program") in goto_table


def test_format_goto_entry(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    states = build_lr0_states(aug)
    goto_table = build_goto_table(aug, states)
    key, target = next(iter(goto_table.items()))
    text = format_goto_entry(key[0], key[1], target)
    assert text == f"GOTO[{key[0]}, {key[1]}] = {target}"
