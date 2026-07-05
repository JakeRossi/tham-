from app.drills.arithmetic import AdditionDrill, SubtractionDrill


def test_addition_is_correct_across_difficulties():
    drill = AdditionDrill()
    for difficulty in (0.0, 0.25, 0.5, 0.75, 1.0):
        for seed in range(20):
            problem = drill.generate(difficulty, rng_seed=seed)
            a, b = problem.seed["a"], problem.seed["b"]
            assert problem.answer == str(a + b)

            result = drill.check(problem, problem.answer)
            assert result.correct

            wrong = drill.check(problem, str(a + b + 1))
            assert not wrong.correct


def test_addition_digit_count_scales_with_difficulty():
    drill = AdditionDrill()
    easy = drill.generate(0.0, rng_seed=1)
    hard = drill.generate(1.0, rng_seed=1)
    assert int(easy.answer) < 100          # ~1-digit + 1-digit
    assert int(hard.answer) > 1000         # 4-digit + 4-digit territory


def test_addition_check_handles_whitespace_and_commas():
    drill = AdditionDrill()
    problem = drill.generate(0.5, rng_seed=42)
    correct_val = int(problem.answer)
    assert drill.check(problem, f"  {correct_val:,}  ").correct


def test_subtraction_never_goes_negative_and_is_correct():
    drill = SubtractionDrill()
    for seed in range(20):
        problem = drill.generate(0.5, rng_seed=seed)
        a, b = problem.seed["a"], problem.seed["b"]
        assert a >= b
        assert problem.answer == str(a - b)
        assert drill.check(problem, problem.answer).correct
