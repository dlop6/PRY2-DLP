from slrGenerator import augmentGrammar, buildGotoTable, buildLr0States, formatGotoEntry


def test_goto_nonterminal_only(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    for (_, symbol), _ in gotoTable.items():
        assert symbol in {p.left for p in aug.productions}


def test_goto_from_initial_state(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    assert (0, "program") in gotoTable


def test_format_goto_entry(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    states = buildLr0States(aug)
    gotoTable = buildGotoTable(aug, states)
    key, target = next(iter(gotoTable.items()))
    text = formatGotoEntry(key[0], key[1], target)
    assert text == f"GOTO[{key[0]}, {key[1]}] = {target}"
