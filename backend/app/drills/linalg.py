"""
Reduced Row Echelon Form drill.

sympy.Matrix.rref() gives both the problem generation (build a random
matrix) and the answer key (its RREF) for free -- see docs/DRILL_AUTHORING.md.

Answer format: the user submits the full matrix as nested-list syntax,
e.g. "[[1,0,2],[0,1,-1]]". Checked via symbolic equality with the true
RREF (element-wise, after simplification, so equivalent fractions match).
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem


def _size_for_difficulty(difficulty: float) -> int:
    # 0.0 -> 2x2, 1.0 -> 4x4
    return 2 + min(2, int(difficulty * 3))


class RREFDrill(Drill):
    id = "rref"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        n = _size_for_difficulty(difficulty)

        # Build a random integer matrix. Retry if it's already in a trivial
        # form (all zero, or already identity) so problems aren't degenerate.
        for _ in range(20):
            rows = [[rng.randint(-9, 9) for _ in range(n)] for _ in range(n)]
            matrix = sp.Matrix(rows)
            rref_matrix, _ = matrix.rref()
            if rref_matrix != sp.eye(n) and any(any(v != 0 for v in row) for row in rows):
                break

        answer_str = str(rref_matrix.tolist())
        matrix_latex = sp.latex(matrix, mat_str="bmatrix", mat_delim="")
        rref_latex = sp.latex(rref_matrix, mat_str="bmatrix", mat_delim="")

        hints = [
            "Use row operations to get a leading 1 in the first row, first column.",
            "Use that leading 1 to eliminate all other entries in its column, "
            "then move to the next row/column and repeat.",
            f"The RREF is $$ {rref_latex} $$",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"Find the RREF of: $$ {matrix_latex} $$",
            answer=answer_str,
            difficulty=difficulty,
            seed={"rows": rows},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_answer = problem.answer.strip()
        try:
            submitted_matrix = sp.Matrix(sp.sympify(submitted))
            answer_matrix = sp.Matrix(sp.sympify(norm_answer))
            correct = (
                submitted_matrix.shape == answer_matrix.shape
                and sp.simplify(submitted_matrix - answer_matrix).is_zero_matrix
            )
        except (sp.SympifyError, TypeError, ValueError, AttributeError):
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=str(submitted).strip(),
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the RREF was {norm_answer}.",
        )
