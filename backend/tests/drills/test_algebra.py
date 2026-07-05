import sympy as sp

from app.drills.algebra import AlgebraicManipulationDrill, x
from app.drills.expr_utils import parse_user_expr


def test_combine_like_terms_is_correct():
    drill = AlgebraicManipulationDrill()
    for seed in range(20):
        problem = drill.generate(0.2, rng_seed=seed)
        answer_expr = parse_user_expr(problem.answer, {"x": x})
        # answer should be a fully simplified (expanded) form
        assert sp.expand(answer_expr) == answer_expr
        assert drill.check(problem, problem.answer).correct


def test_expand_binomials_is_correct():
    drill = AlgebraicManipulationDrill()
    for seed in range(20):
        problem = drill.generate(0.8, rng_seed=seed)
        answer_expr = parse_user_expr(problem.answer, {"x": x})
        assert sp.expand(answer_expr) == answer_expr
        assert drill.check(problem, problem.answer).correct


def test_checker_accepts_reordered_equivalent_form():
    drill = AlgebraicManipulationDrill()
    problem = drill.generate(0.8, rng_seed=3)
    answer_expr = parse_user_expr(problem.answer, {"x": x})
    reordered = sp.sstr(answer_expr, order="rev-lex")
    assert drill.check(problem, reordered).correct


def test_checker_accepts_explicit_asterisk_even_though_display_is_implicit():
    """The core ask: prompt/answer show '6x', but a user typing '6*x' must
    still be marked correct."""
    drill = AlgebraicManipulationDrill()
    problem = drill.generate(0.2, rng_seed=1)
    answer_expr = parse_user_expr(problem.answer, {"x": x})
    explicit_form = sp.sstr(answer_expr)  # sympy's default form always has '*'
    assert drill.check(problem, explicit_form).correct


def test_checker_rejects_wrong_answer():
    drill = AlgebraicManipulationDrill()
    problem = drill.generate(0.8, rng_seed=3)
    answer_expr = parse_user_expr(problem.answer, {"x": x})
    assert not drill.check(problem, str(answer_expr + 1)).correct
