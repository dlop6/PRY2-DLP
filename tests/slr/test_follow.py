from slrGenerator import END_MARKER, augmentGrammar, computeFirst, computeFollow, formatFollow


def test_follow_start_has_end_marker(expr_grammar):
    aug = augmentGrammar(expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    assert END_MARKER in follow["expr'"]


def test_follow_expr_after_plus(expr_grammar):
    aug = augmentGrammar(expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    assert "PLUS" in follow["term"]
    assert END_MARKER in follow["expr"]


def test_follow_factor_rparen(expr_grammar):
    aug = augmentGrammar(expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    assert "RPAREN" in follow["expr"]


def test_format_follow_readable(expr_grammar):
    aug = augmentGrammar(expr_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    text = formatFollow(follow, "expr")
    assert "RPAREN" in text or END_MARKER in text
    assert text.startswith("FOLLOW(expr)")


def test_follow_slr_grammar(slr_dangling_else_grammar):
    aug = augmentGrammar(slr_dangling_else_grammar)
    first = computeFirst(aug)
    follow = computeFollow(aug, first)
    assert END_MARKER in follow["L"]
    assert "ASSIGN" in follow["R"]
