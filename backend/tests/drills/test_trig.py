import sympy as sp

from app.drills.expr_utils import parse_user_expr
from app.drills.trig import ALL_FUNCS, TrigValuesDrill, format_pi_angle


def test_common_angles_are_correct_and_exact_form_accepted():
    drill = TrigValuesDrill()
    for seed in range(30):
        problem = drill.generate(0.2, rng_seed=seed)
        num, den, func_name = problem.seed["frac_num"], problem.seed["frac_den"], problem.seed["func"]
        theta = sp.Rational(num, den) * sp.pi
        true_val = sp.simplify(ALL_FUNCS[func_name](theta))
        # the drill's own answer should match an independently recomputed value
        assert sp.simplify(parse_user_expr(problem.answer) - true_val) == 0
        assert drill.check(problem, problem.answer).correct


def test_prompt_uses_latex_pi_notation_not_degrees():
    drill = TrigValuesDrill()
    problem = drill.generate(0.2, rng_seed=1)
    assert "$$" in problem.prompt  # LaTeX-wrapped for KaTeX rendering
    assert "deg" not in problem.prompt.lower()
    assert "pi" in problem.prompt or problem.seed["frac_num"] == 0


def test_format_pi_angle():
    assert format_pi_angle(0, 1) == "0"
    assert format_pi_angle(1, 2) == "pi/2"
    assert format_pi_angle(3, 4) == "3pi/4"
    assert format_pi_angle(1, 1) == "pi"
    assert format_pi_angle(2, 1) == "2pi"


def test_decimal_answer_accepted_for_exact_form_answer():
    """A user typing a decimal approximation should be accepted even when
    the canonical answer is stored as an exact symbolic form."""
    drill = TrigValuesDrill()
    problem = drill.generate(0.2, rng_seed=1)
    true_val = float(sp.N(parse_user_expr(problem.answer)))
    assert drill.check(problem, f"{true_val:.4f}").correct


def test_high_difficulty_arbitrary_angles_correct():
    drill = TrigValuesDrill()
    for seed in range(20):
        problem = drill.generate(0.9, rng_seed=seed)
        num, den, func_name = problem.seed["frac_num"], problem.seed["frac_den"], problem.seed["func"]
        theta = sp.Rational(num, den) * sp.pi
        true_val = float(sp.N(ALL_FUNCS[func_name](theta)))
        assert abs(float(problem.answer) - true_val) < 0.02
        assert drill.check(problem, problem.answer).correct


def test_wrong_answer_rejected():
    drill = TrigValuesDrill()
    problem = drill.generate(0.2, rng_seed=1)
    assert not drill.check(problem, "9999").correct
