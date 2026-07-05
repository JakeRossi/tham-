import sympy as sp

from app.drills.calculus import IntegralsDrill, x
from app.drills.expr_utils import parse_user_expr


def test_definite_integral_is_correct():
    drill = IntegralsDrill()
    for seed in range(20):
        problem = drill.generate(0.4, rng_seed=seed)
        expr = sp.sympify(problem.seed["expr"])
        a, b = problem.seed["a"], problem.seed["b"]
        true_value = sp.integrate(expr, (x, a, b))
        assert sp.simplify(parse_user_expr(problem.answer) - true_value) == 0
        assert drill.check(problem, problem.answer).correct


def test_bounds_are_always_ordered_low_to_high():
    drill = IntegralsDrill()
    for seed in range(20):
        problem = drill.generate(0.6, rng_seed=seed)
        assert problem.seed["a"] < problem.seed["b"]


def test_checker_accepts_equivalent_fraction_form():
    drill = IntegralsDrill()
    problem = drill.generate(0.4, rng_seed=5)
    answer_expr = parse_user_expr(problem.answer)
    # e.g. if answer is a Rational, "same value written as a decimal-free fraction" should match
    equivalent = sp.nsimplify(answer_expr)
    assert drill.check(problem, str(equivalent)).correct


def test_checker_rejects_wrong_answer():
    drill = IntegralsDrill()
    problem = drill.generate(0.4, rng_seed=5)
    answer_expr = parse_user_expr(problem.answer)
    assert not drill.check(problem, str(answer_expr + 1)).correct
