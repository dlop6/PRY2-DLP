import pytest

from slrGenerator import (
    SLRConflictError,
    Shift,
    augmentGrammar,
    buildActionTable,
    buildLr0States,
    buildSlrParserTable,
    computeFirst,
    computeFollow,
)


def test_ambiguous_expr_has_conflicts(ambiguous_expr_grammar):
    aug = augmentGrammar(ambiguous_expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    with pytest.raises(SLRConflictError) as excInfo:
        buildActionTable(aug, states, follow)
    assert excInfo.value.conflicts
    kinds = {c.kind for c in excInfo.value.conflicts}
    assert "shift/reduce" in kinds or "reduce/reduce" in kinds


def test_conflict_message_format(ambiguous_expr_grammar):
    aug = augmentGrammar(ambiguous_expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    with pytest.raises(SLRConflictError) as excInfo:
        buildActionTable(aug, states, follow)
    message = str(excInfo.value)
    assert "Conflicto" in message
    assert "Acción existente:" in message
    assert "Nueva acción:" in message


def test_build_slr_parser_table_raises_on_conflict(ambiguous_expr_grammar):
    with pytest.raises(SLRConflictError):
        buildSlrParserTable(ambiguous_expr_grammar)


def test_slr_grammar_builds_without_conflict(expr_grammar):
    table = buildSlrParserTable(expr_grammar)
    assert table.productions
    assert table.action
    assert table.goto


def test_dangling_else_has_shift_reduce_conflict(slr_dangling_else_grammar):
    with pytest.raises(SLRConflictError) as excInfo:
        buildSlrParserTable(slr_dangling_else_grammar)
    sr = [c for c in excInfo.value.conflicts if c.kind == "shift/reduce"]
    assert sr
    c = sr[0]
    assert c.token == "ASSIGN"


def test_shift_reduce_conflict_details(ambiguous_expr_grammar):
    aug = augmentGrammar(ambiguous_expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    states = buildLr0States(aug)
    with pytest.raises(SLRConflictError) as excInfo:
        buildActionTable(aug, states, follow)
    sr = [c for c in excInfo.value.conflicts if c.kind == "shift/reduce"]
    if sr:
        c = sr[0]
        assert isinstance(c.existing, Shift) or isinstance(c.new, Shift)
