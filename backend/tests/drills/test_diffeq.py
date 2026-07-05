import sympy as sp

from app.drills.diffeq import OdePdeDrill, x
from app.drills.expr_utils import parse_user_expr


def test_solution_satisfies_the_ode_and_initial_condition():
    drill = OdePdeDrill()
    for seed in range(20):
        problem = drill.generate(0.4, rng_seed=seed)
        k, y0 = problem.seed["k"], problem.seed["y0"]
        y_expr = parse_user_expr(problem.answer, {'x': x})

        # dy/dx should equal k*y
        dy_dx = sp.diff(y_expr, x)
        assert sp.simplify(dy_dx - k * y_expr) == 0

        # initial condition y(0) == y0
        assert sp.simplify(y_expr.subs(x, 0) - y0) == 0

        assert drill.check(problem, problem.answer).correct


def test_checker_accepts_reordered_exponential_form():
    drill = OdePdeDrill()
    problem = drill.generate(0.4, rng_seed=1)
    y0, k = problem.seed["y0"], problem.seed["k"]
    reordered = f"{sp.exp(k * x)}*{y0}"
    assert drill.check(problem, reordered).correct


def test_checker_rejects_wrong_answer():
    drill = OdePdeDrill()
    problem = drill.generate(0.4, rng_seed=1)
    assert not drill.check(problem, "x**2").correct


def test_checker_rejects_garbage_without_crashing():
    drill = OdePdeDrill()
    problem = drill.generate(0.4, rng_seed=1)
    assert not drill.check(problem, "not math").correct
