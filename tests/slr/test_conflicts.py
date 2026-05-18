import pytest

from slr_generator import (
    SLRConflictError,
    Shift,
    augment_grammar,
    build_action_table,
    build_lr0_states,
    build_slr_parser_table,
    compute_first,
    compute_follow,
)


def test_ambiguous_expr_has_conflicts(ambiguous_expr_grammar):
    aug = augment_grammar(ambiguous_expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    with pytest.raises(SLRConflictError) as exc_info:
        build_action_table(aug, states, follow)
    assert exc_info.value.conflicts
    kinds = {c.kind for c in exc_info.value.conflicts}
    assert "shift/reduce" in kinds or "reduce/reduce" in kinds


def test_conflict_message_format(ambiguous_expr_grammar):
    aug = augment_grammar(ambiguous_expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    with pytest.raises(SLRConflictError) as exc_info:
        build_action_table(aug, states, follow)
    message = str(exc_info.value)
    assert "Conflicto" in message
    assert "Acción existente:" in message
    assert "Nueva acción:" in message


def test_build_slr_parser_table_raises_on_conflict(ambiguous_expr_grammar):
    with pytest.raises(SLRConflictError):
        build_slr_parser_table(ambiguous_expr_grammar)


def test_slr_grammar_builds_without_conflict(expr_grammar):
    table = build_slr_parser_table(expr_grammar)
    assert table.productions
    assert table.action
    assert table.goto


def test_dangling_else_has_shift_reduce_conflict(slr_dangling_else_grammar):
    with pytest.raises(SLRConflictError) as exc_info:
        build_slr_parser_table(slr_dangling_else_grammar)
    sr = [c for c in exc_info.value.conflicts if c.kind == "shift/reduce"]
    assert sr
    c = sr[0]
    assert c.token == "ASSIGN"


def test_shift_reduce_conflict_details(ambiguous_expr_grammar):
    aug = augment_grammar(ambiguous_expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    states = build_lr0_states(aug)
    with pytest.raises(SLRConflictError) as exc_info:
        build_action_table(aug, states, follow)
    sr = [c for c in exc_info.value.conflicts if c.kind == "shift/reduce"]
    if sr:
        c = sr[0]
        assert isinstance(c.existing, Shift) or isinstance(c.new, Shift)
