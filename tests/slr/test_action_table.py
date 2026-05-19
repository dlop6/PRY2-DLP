import pytest

from slrGenerator import (
    Accept,
    END_MARKER,
    Shift,
    Reduce,
    augmentGrammar,
    buildActionTable,
    buildLr0States,
    computeFirst,
    computeFollow,
    formatActionEntry,
)


def test_action_shift_on_terminal(unambiguous_grammar):
    aug = augmentGrammar(unambiguous_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    action = buildActionTable(aug, states, follow)
    assert any(isinstance(v, Shift) for v in action.values())


def test_action_accept_on_end(unambiguous_grammar):
    aug = augmentGrammar(unambiguous_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    action = buildActionTable(aug, states, follow)
    acceptKeys = [k for k, v in action.items() if isinstance(v, Accept)]
    assert acceptKeys
    assert acceptKeys[0][1] == END_MARKER


def test_action_reduce_entries(expr_grammar):
    aug = augmentGrammar(expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    action = buildActionTable(aug, states, follow)
    assert any(isinstance(v, Reduce) for v in action.values())


def test_format_action_entry(unambiguous_grammar):
    aug = augmentGrammar(unambiguous_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    action = buildActionTable(aug, states, follow)
    key, val = next(iter(action.items()))
    text = formatActionEntry(key[0], key[1], val, aug.productions)
    assert text.startswith(f"ACTION[{key[0]}, {key[1]}]")
