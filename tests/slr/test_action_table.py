import pytest

from slr_generator import (
    Accept,
    END_MARKER,
    Shift,
    Reduce,
    augment_grammar,
    build_action_table,
    build_lr0_states,
    compute_first,
    compute_follow,
    format_action_entry,
)


def test_action_shift_on_terminal(unambiguous_grammar):
    aug = augment_grammar(unambiguous_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    action = build_action_table(aug, states, follow)
    assert any(isinstance(v, Shift) for v in action.values())


def test_action_accept_on_end(unambiguous_grammar):
    aug = augment_grammar(unambiguous_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    action = build_action_table(aug, states, follow)
    accept_keys = [k for k, v in action.items() if isinstance(v, Accept)]
    assert accept_keys
    assert accept_keys[0][1] == END_MARKER


def test_action_reduce_entries(expr_grammar):
    aug = augment_grammar(expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    action = build_action_table(aug, states, follow)
    assert any(isinstance(v, Reduce) for v in action.values())


def test_format_action_entry(unambiguous_grammar):
    aug = augment_grammar(unambiguous_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    action = build_action_table(aug, states, follow)
    key, val = next(iter(action.items()))
    text = format_action_entry(key[0], key[1], val, aug.productions)
    assert text.startswith(f"ACTION[{key[0]}, {key[1]}]")
