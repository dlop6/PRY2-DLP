from grammar import Production
from slr_generator import Item, augment_grammar, closure


def test_closure_adds_nonterminal_productions(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    start = Item(aug.productions[0].left, aug.productions[0].right, 0)
    result = closure({start}, aug)
    assert start in result
    assert any(item.left == "program" for item in result)
    assert any(item.left == "stmt_list" for item in result)


def test_closure_idempotent(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    start = Item(aug.productions[0].left, aug.productions[0].right, 0)
    once = closure({start}, aug)
    twice = closure(set(once), aug)
    assert once == twice


def test_closure_stops_at_terminal_dot(simple_program_grammar):
    aug = augment_grammar(simple_program_grammar)
    item = Item("stmt", ("ID", "ASSIGN", "expr", "SEMI"), 0)
    result = closure({item}, aug)
    assert all(i.left != "ID" for i in result if i.left == "ID")
