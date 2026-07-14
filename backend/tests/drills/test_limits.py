import sympy as sp

from app.drills.expr_utils import parse_user_expr
from app.drills.limits import LimitsDrill, MAX_LEVEL, level_for_difficulty

x = sp.symbols("x")


def test_every_level_produces_a_correct_finite_limit():
    drill = LimitsDrill()
    for level in range(1, MAX_LEVEL + 1):
        difficulty = (level - 1) / (MAX_LEVEL - 1)
        for seed in range(20):
            problem = drill.generate(difficulty, rng_seed=seed)
            expr = parse_user_expr(problem.seed["expr"], {"x": x})
            approach = sp.sympify(problem.seed["approach"])
            recomputed = sp.limit(expr, x, approach)
            assert sp.simplify(recomputed - parse_user_expr(problem.answer)) == 0, (
                f"level {level} seed {seed}: {problem.prompt} -> {problem.answer}"
            )
            assert drill.check(problem, problem.answer).correct


def test_level_for_difficulty_spans_full_range():
    assert level_for_difficulty(0.0) == 1
    assert level_for_difficulty(1.0) == MAX_LEVEL


def test_level_progression_is_monotonic():
    prev = 0
    for d in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        level = level_for_difficulty(d)
        assert level >= prev
        prev = level


def test_level_1_always_has_real_x_dependence():
    """Regression test: level 1 used to sometimes degenerate to a trivial
    constant limit when the random term count happened to be 1."""
    drill = LimitsDrill()
    for seed in range(30):
        problem = drill.generate(0.0, rng_seed=seed)
        expr = parse_user_expr(problem.seed["expr"], {"x": x})
        assert expr.has(x), f"seed {seed}: {expr} has no x-dependence"


def test_level_5_does_not_trivially_precollapse_to_a_constant():
    """Regression test: same-degree monomial ratios auto-simplify to a
    bare constant before display, making the problem pointless."""
    drill = LimitsDrill()
    for seed in range(30):
        problem = drill.generate((5 - 1) / (MAX_LEVEL - 1), rng_seed=seed)
        expr = parse_user_expr(problem.seed["expr"], {"x": x})
        assert expr.has(x), f"seed {seed}: {expr} has no x-dependence (trivially pre-collapsed)"


def test_checker_accepts_algebraically_equivalent_forms():
    drill = LimitsDrill()
    problem = drill.generate(0.7, rng_seed=3)
    answer_expr = parse_user_expr(problem.answer)
    reordered = sp.sstr(answer_expr, order="rev-lex")
    assert drill.check(problem, reordered).correct


def test_checker_rejects_wrong_answer():
    drill = LimitsDrill()
    problem = drill.generate(0.3, rng_seed=1)
    answer_expr = parse_user_expr(problem.answer)
    assert not drill.check(problem, str(answer_expr + 1)).correct


def test_checker_rejects_garbage_without_crashing():
    drill = LimitsDrill()
    problem = drill.generate(0.3, rng_seed=1)
    assert not drill.check(problem, "not math @@@").correct


def test_higher_levels_use_richer_function_variety():
    """Levels 7-9 should draw on multiple function families (trig, exp,
    log), not just polynomials."""
    drill = LimitsDrill()
    saw_trig = saw_exp = saw_log = False
    for seed in range(30):
        problem = drill.generate(1.0, rng_seed=seed)  # level 9
        expr = parse_user_expr(problem.seed["expr"], {"x": x})
        if expr.has(sp.sin) or expr.has(sp.cos):
            saw_trig = True
        if expr.has(sp.exp):
            saw_exp = True
        if expr.has(sp.log):
            saw_log = True
    assert saw_trig and saw_exp and saw_log
