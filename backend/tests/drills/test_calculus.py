import sympy as sp

from app.drills.calculus import DerivativesDrill, x, y
from app.drills.expr_utils import parse_user_expr


def test_single_variable_derivative_is_correct():
    drill = DerivativesDrill()
    for seed in range(20):
        problem = drill.generate(0.2, rng_seed=seed)  # single-variable tier
        expr = sp.sympify(problem.seed["expr"])
        true_derivative = sp.diff(expr, x)
        assert sp.simplify(parse_user_expr(problem.answer, {'x': x, 'y': y}) - true_derivative) == 0


def test_partial_derivative_is_correct():
    drill = DerivativesDrill()
    for seed in range(20):
        problem = drill.generate(0.8, rng_seed=seed)  # two-variable / partial tier
        expr = sp.sympify(problem.seed["expr"])
        wrt = x if problem.seed["wrt"] == "x" else y
        true_derivative = sp.diff(expr, wrt)
        assert sp.simplify(parse_user_expr(problem.answer, {'x': x, 'y': y}) - true_derivative) == 0


def test_checker_accepts_algebraically_equivalent_forms():
    """
    The whole point of using sympy for checking: '2*x + 5' and '5 + 2*x'
    and 'x*2 + 5' should ALL be marked correct, not just an exact string match.
    """
    drill = DerivativesDrill()
    problem = drill.generate(0.2, rng_seed=7)
    answer_expr = parse_user_expr(problem.answer, {'x': x, 'y': y})

    # Same value, differently ordered/formatted -- must still be marked correct.
    reordered = sp.sstr(sp.expand(answer_expr), order="rev-lex")
    assert drill.check(problem, reordered).correct
    assert drill.check(problem, str(answer_expr)).correct


def test_answer_display_uses_implicit_multiplication_but_explicit_still_accepted():
    """Prompts/answers show '6x' style, but a user typing '6*x' must still work."""
    drill = DerivativesDrill()
    problem = drill.generate(0.2, rng_seed=2)
    answer_expr = parse_user_expr(problem.answer, {'x': x, 'y': y})
    explicit_form = sp.sstr(answer_expr)  # sympy's default always includes '*'
    assert drill.check(problem, explicit_form).correct
    assert drill.check(problem, problem.answer).correct  # the displayed form itself


def test_checker_rejects_wrong_answer():
    drill = DerivativesDrill()
    problem = drill.generate(0.2, rng_seed=7)
    answer_expr = parse_user_expr(problem.answer, {'x': x, 'y': y})
    wrong = str(answer_expr + 1)
    assert not drill.check(problem, wrong).correct


def test_checker_rejects_garbage_input_without_crashing():
    drill = DerivativesDrill()
    problem = drill.generate(0.2, rng_seed=7)
    result = drill.check(problem, "not a math expression @@@")
    assert result.correct is False
