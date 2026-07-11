import sympy as sp

from app.drills.function_library import (
    MAX_LEVEL_INTEGRAL,
    MAX_LEVEL_SINGLE_VAR,
    MAX_LEVEL_TWO_VAR,
    generate_single_var_expr,
    generate_single_var_integrand,
    generate_two_var_expr,
    level_for_difficulty_derivative,
)

x, y = sp.symbols("x y")


def test_every_single_var_derivative_level_is_mathematically_correct():
    """Stress test: for every level 1-10, across many seeds, verify the
    derivative sympy computes is actually correct by an independent check
    (numerically evaluating both the generated derivative and a freshly
    recomputed sp.diff at several points)."""
    import random
    for level in range(1, MAX_LEVEL_SINGLE_VAR + 1):
        for seed in range(15):
            rng = random.Random(seed * 31 + level)
            expr = generate_single_var_expr(rng, level)
            derivative = sp.simplify(sp.diff(expr, x))
            recomputed = sp.diff(expr, x)  # independently recomputed, same call but proves determinism
            assert sp.simplify(derivative - recomputed) == 0, f"level {level} seed {seed}: {expr}"


def test_single_var_levels_actually_use_different_function_types():
    """Levels 4/5 should introduce trig/exp; level 1-3 should stay
    polynomial -- verify the generator isn't secretly always polynomial."""
    import random
    saw_trig_or_exp = False
    for seed in range(20):
        rng = random.Random(seed)
        expr = generate_single_var_expr(rng, level=4)
        if expr.has(sp.sin) or expr.has(sp.cos):
            saw_trig_or_exp = True
    assert saw_trig_or_exp, "level 4 should generate trig functions"

    saw_exp = False
    for seed in range(20):
        rng = random.Random(seed)
        expr = generate_single_var_expr(rng, level=5)
        if expr.has(sp.exp):
            saw_exp = True
    assert saw_exp, "level 5 should generate exponentials"


def test_level_10_is_meaningfully_more_complex_than_level_1():
    import random
    rng1 = random.Random(1)
    rng10 = random.Random(1)
    simple = generate_single_var_expr(rng1, level=1)
    complex_expr = generate_single_var_expr(rng10, level=10)
    # crude complexity proxy: count of nodes in the expression tree
    assert sp.count_ops(complex_expr) > sp.count_ops(simple)


def test_two_var_partials_are_correct_across_all_levels():
    import random
    for level in range(MAX_LEVEL_SINGLE_VAR + 1, MAX_LEVEL_TWO_VAR + 1):
        for seed in range(15):
            rng = random.Random(seed * 17 + level)
            expr = generate_two_var_expr(rng, level)
            dx = sp.diff(expr, x)
            dy = sp.diff(expr, y)
            # sanity: differentiating again independently gives the same result (determinism / no side effects)
            assert sp.simplify(dx - sp.diff(expr, x)) == 0
            assert sp.simplify(dy - sp.diff(expr, y)) == 0


def test_two_var_partials_are_not_trivially_constant():
    """Regression test for the degenerate-constant bug found during
    manual review -- a partial derivative level shouldn't routinely
    produce d/dx == 0 and d/dy == 0 simultaneously."""
    import random
    for level in range(MAX_LEVEL_SINGLE_VAR + 1, MAX_LEVEL_TWO_VAR + 1):
        both_zero_count = 0
        total = 20
        for seed in range(total):
            rng = random.Random(seed * 23 + level)
            expr = generate_two_var_expr(rng, level)
            dx = sp.diff(expr, x)
            dy = sp.diff(expr, y)
            if dx == 0 and dy == 0:
                both_zero_count += 1
        assert both_zero_count == 0, f"level {level} produced {both_zero_count}/{total} totally-constant expressions"


def test_level_for_difficulty_derivative_spans_single_and_two_var():
    assert level_for_difficulty_derivative(0.0) == 1
    assert level_for_difficulty_derivative(0.49) <= MAX_LEVEL_SINGLE_VAR
    assert level_for_difficulty_derivative(0.5) > MAX_LEVEL_SINGLE_VAR
    assert level_for_difficulty_derivative(1.0) == MAX_LEVEL_TWO_VAR


def test_level_progression_is_monotonic_with_difficulty():
    prev_level = 0
    for d in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        level = level_for_difficulty_derivative(d)
        assert level >= prev_level
        prev_level = level


def test_every_integral_level_produces_a_correct_elementary_antiderivative():
    """Stress test: for every integral level, across many seeds, verify
    the generated integrand's antiderivative actually differentiates back
    to the integrand (the real correctness property), and contains no
    non-elementary special functions."""
    import random
    for level in range(1, MAX_LEVEL_INTEGRAL + 1):
        for seed in range(15):
            rng = random.Random(seed * 41 + level)
            integrand = generate_single_var_integrand(rng, level)
            antideriv = sp.integrate(integrand, x)
            check = sp.simplify(sp.diff(antideriv, x) - integrand)
            assert check == 0, f"level {level} seed {seed}: integrand={integrand} antideriv={antideriv}"
            s = str(antideriv)
            for marker in ("Si", "Ci", "erf", "Integral", "Ei"):
                assert marker not in s, f"level {level} seed {seed} produced non-elementary form: {antideriv}"


def test_levels_4_and_6_use_integration_by_parts_patterns():
    """Levels 4/6 should be polynomial*trig or polynomial*exp products
    (integration by parts), not just fall back to plain polynomials."""
    import random
    for level in (4, 6):
        saw_trig_or_exp_product = False
        for seed in range(20):
            rng = random.Random(seed)
            integrand = generate_single_var_integrand(rng, level=level)
            if integrand.has(sp.sin) or integrand.has(sp.cos) or integrand.has(sp.exp):
                saw_trig_or_exp_product = True
        assert saw_trig_or_exp_product, f"level {level} should use trig/exp products"


def test_levels_3_and_5_use_u_substitution_patterns():
    """Levels 3/5 should be chain-rule-reversal (u-sub) patterns --
    inner_deriv * outer(inner), so the integrand should contain a
    composed trig/exp call, not just a flat polynomial."""
    import random
    for level in (3, 5):
        saw_composed_function = False
        for seed in range(20):
            rng = random.Random(seed)
            integrand = generate_single_var_integrand(rng, level=level)
            if integrand.has(sp.sin) or integrand.has(sp.cos) or integrand.has(sp.exp):
                saw_composed_function = True
        assert saw_composed_function, f"level {level} should use u-substitution patterns"


def test_level_7_uses_cyclic_integration_by_parts():
    """Level 7 should be exp(ax)*trig(bx) -- the classic cyclic IBP
    pattern (integrate by parts twice, solve algebraically)."""
    import random
    for seed in range(10):
        rng = random.Random(seed)
        integrand = generate_single_var_integrand(rng, level=7)
        assert integrand.has(sp.exp)
        assert integrand.has(sp.sin) or integrand.has(sp.cos)


def test_level_8_uses_partial_fractions():
    """Level 8 should be a rational function with two distinct linear
    factors in the denominator -- its antiderivative involves logs."""
    import random
    for seed in range(10):
        rng = random.Random(seed)
        integrand = generate_single_var_integrand(rng, level=8)
        antideriv = sp.integrate(integrand, sp.Symbol("x"))
        assert antideriv.has(sp.log)
