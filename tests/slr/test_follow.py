from slr_generator import END_MARKER, augment_grammar, compute_first, compute_follow, format_follow


def test_follow_start_has_end_marker(expr_grammar):
    aug = augment_grammar(expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    assert END_MARKER in follow["expr'"]


def test_follow_expr_after_plus(expr_grammar):
    aug = augment_grammar(expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    assert "PLUS" in follow["term"]
    assert END_MARKER in follow["expr"]


def test_follow_factor_rparen(expr_grammar):
    aug = augment_grammar(expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    assert "RPAREN" in follow["expr"]


def test_format_follow_readable(expr_grammar):
    aug = augment_grammar(expr_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    text = format_follow(follow, "expr")
    assert "RPAREN" in text or END_MARKER in text
    assert text.startswith("FOLLOW(expr)")


def test_follow_slr_grammar(slr_dangling_else_grammar):
    aug = augment_grammar(slr_dangling_else_grammar)
    first = compute_first(aug)
    follow = compute_follow(aug, first)
    assert END_MARKER in follow["L"]
    assert "ASSIGN" in follow["R"]
