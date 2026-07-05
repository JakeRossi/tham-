from app.drills.arithmetic import (
    CbrtsDrill,
    CubesDrill,
    DivisionDrill,
    MultiplicationDrill,
    SqrtsDrill,
    SquaresDrill,
)


def test_multiplication_is_correct():
    drill = MultiplicationDrill()
    for seed in range(20):
        problem = drill.generate(0.5, rng_seed=seed)
        a, b = problem.seed["a"], problem.seed["b"]
        assert problem.answer == str(a * b)
        assert drill.check(problem, problem.answer).correct
        assert not drill.check(problem, str(a * b + 1)).correct


def test_division_exact_at_low_difficulty():
    drill = DivisionDrill()
    for seed in range(20):
        problem = drill.generate(0.1, rng_seed=seed)
        dividend, divisor = problem.seed["dividend"], problem.seed["divisor"]
        assert dividend % divisor == 0
        assert int(problem.answer) == dividend // divisor
        assert drill.check(problem, problem.answer).correct


def test_division_with_remainder_at_high_difficulty():
    drill = DivisionDrill()
    saw_remainder = False
    for seed in range(30):
        problem = drill.generate(0.9, rng_seed=seed)
        dividend, divisor = problem.seed["dividend"], problem.seed["divisor"]
        true_q, true_r = divmod(dividend, divisor)
        if true_r != 0:
            saw_remainder = True
            assert problem.answer == f"{true_q} R {true_r}"
            # format flexibility: lowercase, no spaces
            assert drill.check(problem, f"{true_q}r{true_r}").correct
        assert drill.check(problem, problem.answer).correct
    assert saw_remainder, "expected at least one remainder case across 30 seeds at high difficulty"


def test_squares_is_correct():
    drill = SquaresDrill()
    for seed in range(20):
        problem = drill.generate(0.5, rng_seed=seed)
        n = problem.seed["n"]
        assert problem.answer == str(n * n)
        assert drill.check(problem, problem.answer).correct


def test_sqrts_perfect_squares_exact():
    drill = SqrtsDrill()
    for seed in range(20):
        problem = drill.generate(0.1, rng_seed=seed)
        radicand = problem.seed["radicand"]
        assert int(problem.answer) ** 2 == radicand
        assert drill.check(problem, problem.answer).correct


def test_sqrts_irrational_within_epsilon():
    drill = SqrtsDrill()
    for seed in range(20):
        problem = drill.generate(0.9, rng_seed=seed)
        radicand = problem.seed["radicand"]
        true_val = radicand ** 0.5
        assert abs(float(problem.answer) - true_val) < 0.02
        assert drill.check(problem, f"{true_val:.2f}").correct
        assert not drill.check(problem, f"{true_val + 1:.2f}").correct


def test_cubes_is_correct():
    drill = CubesDrill()
    for seed in range(20):
        problem = drill.generate(0.5, rng_seed=seed)
        n = problem.seed["n"]
        assert problem.answer == str(n ** 3)
        assert drill.check(problem, problem.answer).correct


def test_cbrts_perfect_cubes_exact():
    drill = CbrtsDrill()
    for seed in range(20):
        problem = drill.generate(0.1, rng_seed=seed)
        radicand = problem.seed["radicand"]
        assert int(problem.answer) ** 3 == radicand
        assert drill.check(problem, problem.answer).correct


def test_cbrts_irrational_within_epsilon():
    drill = CbrtsDrill()
    for seed in range(20):
        problem = drill.generate(0.9, rng_seed=seed)
        radicand = problem.seed["radicand"]
        true_val = radicand ** (1 / 3)
        assert drill.check(problem, f"{true_val:.2f}").correct
