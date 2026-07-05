"""
Arithmetic drills: addition, subtraction, multiplication, division,
squares, square roots, cubes, cube roots.

Only Addition is fully implemented here as the reference pattern.
The others follow the exact same shape -- see the stubs at the bottom
with TODOs for what to fill in.
"""

from __future__ import annotations

import random

from app.drills.base import CheckResult, Drill, Problem


def _digits_for_difficulty(difficulty: float) -> int:
    """Map 0.0-1.0 difficulty to an integer digit-count (1-4 digits)."""
    # 0.0 -> 1 digit, 0.33 -> 2 digits, 0.66 -> 3 digits, 1.0 -> 4 digits
    return 1 + min(3, int(difficulty * 4))


class AdditionDrill(Drill):
    id = "addition"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        digits = _digits_for_difficulty(difficulty)
        low, high = 10 ** (digits - 1), (10 ** digits) - 1
        if digits == 1:
            low = 0  # allow single-digit 0-9 at the easiest tier

        a = rng.randint(low, high)
        b = rng.randint(low, high)
        answer = a + b

        # Hints get progressively more revealing.
        hints = [
            f"Try adding the ones place first: {a % 10} + {b % 10}.",
            f"Break it into place values: {a} = {a - a % 10} + {a % 10}, "
            f"{b} = {b - b % 10} + {b % 10}.",
            f"The answer is {answer}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"{a} + {b} = ?",
            answer=str(answer),
            difficulty=difficulty,
            seed={"a": a, "b": b, "op": "add"},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_submitted = submitted.strip().replace(",", "")
        norm_answer = problem.answer.strip()
        try:
            correct = int(norm_submitted) == int(norm_answer)
        except ValueError:
            correct = False
        return CheckResult(
            correct=correct,
            normalized_submitted=norm_submitted,
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )


class SubtractionDrill(Drill):
    id = "subtraction"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        digits = _digits_for_difficulty(difficulty)
        low, high = 10 ** (digits - 1), (10 ** digits) - 1
        if digits == 1:
            low = 0

        a = rng.randint(low, high)
        b = rng.randint(low, high)
        # Keep it non-negative for now (simplest version); flip if needed.
        if b > a:
            a, b = b, a
        answer = a - b

        hints = [
            f"Line up the digits of {a} and {b} by place value.",
            "Borrow from the next place value if the top digit is smaller.",
            f"The answer is {answer}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"{a} - {b} = ?",
            answer=str(answer),
            difficulty=difficulty,
            seed={"a": a, "b": b, "op": "sub"},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_submitted = submitted.strip().replace(",", "")
        norm_answer = problem.answer.strip()
        try:
            correct = int(norm_submitted) == int(norm_answer)
        except ValueError:
            correct = False
        return CheckResult(
            correct=correct,
            normalized_submitted=norm_submitted,
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )


# --- TODO: implement following the same pattern as AdditionDrill above ---
#
# class MultiplicationDrill(Drill):
#     id = "multiplication"
#     ...
#
# class DivisionDrill(Drill):
#     id = "division"
#     # decide: integer division only, or allow remainders/decimals by difficulty tier
#     ...
#
# class SquaresDrill(Drill):
#     id = "squares"
#     ...
#
# class SqrtsDrill(Drill):
#     id = "sqrts"
#     # decide: perfect squares only at low difficulty, irrational (decimal-rounded) at high
#     ...
#
# class CubesDrill(Drill):
#     id = "cubes"
#     ...
#
# class CbrtsDrill(Drill):
#     id = "cbrts"
#     ...
