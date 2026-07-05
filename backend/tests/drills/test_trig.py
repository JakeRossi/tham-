import sympy as sp

from app.drills.trig import ALL_FUNCS, TrigValuesDrill


def test_common_angles_are_correct_and_exact_form_accepted():
    drill = TrigValuesDrill()
    for seed in range(30):
        problem = drill.generate(0.2, rng_seed=seed)
        angle_deg, func_name = problem.seed["angle_deg"], problem.seed["func"]
        true_val = sp.simplify(ALL_FUNCS[func_name](sp.rad(angle_deg)))
        # the drill's own answer should match an independently recomputed value
        assert sp.simplify(sp.sympify(problem.answer) - true_val) == 0
        assert drill.check(problem, problem.answer).correct


def test_decimal_answer_accepted_for_exact_form_answer():
    """A user typing a decimal approximation should be accepted even when
    the canonical answer is stored as an exact symbolic form."""
    drill = TrigValuesDrill()
    problem = drill.generate(0.2, rng_seed=1)
    true_val = float(sp.N(sp.sympify(problem.answer)))
    assert drill.check(problem, f"{true_val:.4f}").correct


def test_high_difficulty_arbitrary_angles_correct():
    drill = TrigValuesDrill()
    for seed in range(20):
        problem = drill.generate(0.9, rng_seed=seed)
        angle_deg, func_name = problem.seed["angle_deg"], problem.seed["func"]
        true_val = float(sp.N(ALL_FUNCS[func_name](sp.rad(angle_deg))))
        assert abs(float(problem.answer) - true_val) < 0.02
        assert drill.check(problem, problem.answer).correct


def test_wrong_answer_rejected():
    drill = TrigValuesDrill()
    problem = drill.generate(0.2, rng_seed=1)
    assert not drill.check(problem, "9999").correct
