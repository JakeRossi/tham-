import sympy as sp

from app.drills.algebra import AlgebraicManipulationDrill, x


def test_combine_like_terms_is_correct():
    drill = AlgebraicManipulationDrill()
    for seed in range(20):
        problem = drill.generate(0.2, rng_seed=seed)
        answer_expr = sp.sympify(problem.answer, locals={"x": x})
        # answer should be a fully simplified (expanded) form
        assert sp.expand(answer_expr) == answer_expr
        assert drill.check(problem, problem.answer).correct


def test_expand_binomials_is_correct():
    drill = AlgebraicManipulationDrill()
    for seed in range(20):
        problem = drill.generate(0.8, rng_seed=seed)
        answer_expr = sp.sympify(problem.answer, locals={"x": x})
        assert sp.expand(answer_expr) == answer_expr
        assert drill.check(problem, problem.answer).correct


def test_checker_accepts_reordered_equivalent_form():
    drill = AlgebraicManipulationDrill()
    problem = drill.generate(0.8, rng_seed=3)
    answer_expr = sp.sympify(problem.answer, locals={"x": x})
    reordered = sp.sstr(answer_expr, order="rev-lex")
    assert drill.check(problem, reordered).correct


def test_checker_rejects_wrong_answer():
    drill = AlgebraicManipulationDrill()
    problem = drill.generate(0.8, rng_seed=3)
    answer_expr = sp.sympify(problem.answer, locals={"x": x})
    assert not drill.check(problem, str(answer_expr + 1)).correct
