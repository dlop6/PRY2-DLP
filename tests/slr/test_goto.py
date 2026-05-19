from slrGenerator import Item, augmentGrammar, closure, goto


def test_goto_moves_dot_over_symbol(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    start = Item(aug.productions[0].left, aug.productions[0].right, 0)
    i0 = closure({start}, aug)
    target = goto(set(i0), "program", aug)
    assert any(
        item.left == "program'" and item.dot == 1
        for item in target
    )


def test_goto_empty_when_no_matching_dot(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    start = Item(aug.productions[0].left, aug.productions[0].right, 0)
    i0 = closure({start}, aug)
    assert goto(set(i0), "PLUS", aug) == frozenset()


def test_goto_on_terminal(simple_program_grammar):
    aug = augmentGrammar(simple_program_grammar)
    item = Item("term", ("NUMBER",), 0)
    target = goto({item}, "NUMBER", aug)
    assert Item("term", ("NUMBER",), 1) in target
