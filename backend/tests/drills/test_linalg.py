import sympy as sp

from app.drills.linalg import RREFDrill


def test_rref_matches_sympy_independently():
    drill = RREFDrill()
    for seed in range(15):
        problem = drill.generate(0.3, rng_seed=seed)
        rows = problem.seed["rows"]
        true_rref, _ = sp.Matrix(rows).rref()
        submitted_matrix = sp.Matrix(sp.sympify(problem.answer))
        assert submitted_matrix == true_rref
        assert drill.check(problem, problem.answer).correct


def test_matrix_size_scales_with_difficulty():
    drill = RREFDrill()
    easy = drill.generate(0.0, rng_seed=1)
    hard = drill.generate(1.0, rng_seed=1)
    assert len(easy.seed["rows"]) == 2
    assert len(hard.seed["rows"]) == 4


def test_checker_accepts_equivalent_fraction_formatting():
    drill = RREFDrill()
    problem = drill.generate(0.3, rng_seed=2)
    # re-serialize through sympy to a different (but equal) textual form
    matrix = sp.Matrix(sp.sympify(problem.answer))
    resubmitted = str(matrix.tolist())
    assert drill.check(problem, resubmitted).correct


def test_checker_rejects_wrong_matrix():
    drill = RREFDrill()
    problem = drill.generate(0.3, rng_seed=2)
    matrix = sp.Matrix(sp.sympify(problem.answer))
    wrong = (matrix + sp.eye(matrix.shape[0])).tolist()
    assert not drill.check(problem, str(wrong)).correct


def test_checker_rejects_garbage_without_crashing():
    drill = RREFDrill()
    problem = drill.generate(0.3, rng_seed=2)
    assert not drill.check(problem, "not a matrix").correct
