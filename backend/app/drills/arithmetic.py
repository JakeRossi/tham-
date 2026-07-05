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


def _mul_digits_for_difficulty(difficulty: float) -> int:
    """Multiplication grows fast -- cap digit count lower than addition's."""
    # 0.0 -> 1 digit x 1 digit, 1.0 -> 3 digit x 3 digit
    return 1 + min(2, int(difficulty * 3))


class MultiplicationDrill(Drill):
    id = "multiplication"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        digits = _mul_digits_for_difficulty(difficulty)
        low, high = 10 ** (digits - 1), (10 ** digits) - 1
        if digits == 1:
            low = 0

        a = rng.randint(low, high)
        b = rng.randint(low, high)
        answer = a * b

        hints = [
            f"Break {b} into place values and multiply {a} by each part.",
            f"{a} x {b} = {a} x {b - b % 10} + {a} x {b % 10}." if b >= 10
            else f"Think of it as {a} added to itself {b} times.",
            f"The answer is {answer}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"{a} x {b} = ?",
            answer=str(answer),
            difficulty=difficulty,
            seed={"a": a, "b": b, "op": "mul"},
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


class DivisionDrill(Drill):
    """
    difficulty < 0.5: divides evenly, answer is a plain integer.
    difficulty >= 0.5: may have a remainder, answer format is "Q R r"
                       (e.g. "12 R 3"), case-insensitive, spaces optional.
    """

    id = "division"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        digits = _mul_digits_for_difficulty(difficulty)
        divisor = rng.randint(2, (10 ** min(digits, 2)) - 1)
        quotient = rng.randint(10 ** (digits - 1) if digits > 1 else 1, (10 ** digits) - 1)

        allow_remainder = difficulty >= 0.5
        remainder = rng.randint(0, divisor - 1) if allow_remainder else 0
        dividend = divisor * quotient + remainder

        if remainder == 0:
            answer = str(quotient)
            hints = [
                f"How many times does {divisor} go into {dividend}?",
                f"{divisor} x {quotient} = {dividend}.",
                f"The answer is {quotient}.",
            ]
        else:
            answer = f"{quotient} R {remainder}"
            hints = [
                f"{divisor} does not divide {dividend} evenly -- find the closest multiple below it.",
                f"{divisor} x {quotient} = {divisor * quotient}, leaving a remainder.",
                f"The answer is {quotient} R {remainder}.",
            ]

        return Problem(
            drill_id=self.id,
            prompt=f"{dividend} / {divisor} = ?" + ("" if remainder == 0 else " (write as Q R r)"),
            answer=answer,
            difficulty=difficulty,
            seed={"dividend": dividend, "divisor": divisor, "op": "div"},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        def normalize(s: str) -> str:
            return s.strip().upper().replace(" ", "")

        norm_submitted = normalize(submitted)
        norm_answer = normalize(problem.answer)
        correct = norm_submitted == norm_answer
        return CheckResult(
            correct=correct,
            normalized_submitted=norm_submitted,
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {problem.answer}.",
        )


class SquaresDrill(Drill):
    """0.0 -> bases 1-10, 1.0 -> bases up to 999."""

    id = "squares"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        max_base = 10 + int(difficulty * 989)  # 10 at 0.0, ~999 at 1.0
        n = rng.randint(1, max_base)
        answer = n * n

        hints = [
            f"{n}^2 means {n} multiplied by itself.",
            f"{n} x {n} = ?",
            f"The answer is {answer}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"{n}^2 = ?",
            answer=str(answer),
            difficulty=difficulty,
            seed={"n": n, "op": "square"},
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


class SqrtsDrill(Drill):
    """
    difficulty < 0.6: perfect squares only, exact integer answer.
    difficulty >= 0.6: arbitrary integers, irrational root, answer accepted
                       within +/- 0.01 of the true value (submit as decimal).
    """

    id = "sqrts"
    EPSILON = 0.01

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        max_base = 10 + int(difficulty * 40)  # perfect-square base range scales too

        if difficulty < 0.6:
            n = rng.randint(1, max_base)
            radicand = n * n
            answer = str(n)
            hints = [
                f"What number times itself equals {radicand}?",
                f"Try checking {max(1, n - 1)} and {n + 1} squared as bounds.",
                f"The answer is {n}.",
            ]
        else:
            radicand = rng.randint(2, 200)
            true_val = radicand ** 0.5
            answer = f"{true_val:.2f}"
            hints = [
                f"{radicand} is not a perfect square -- estimate between the nearest perfect squares.",
                f"sqrt({radicand}) is between {int(radicand ** 0.5)} and {int(radicand ** 0.5) + 1}.",
                f"The answer is approximately {answer}.",
            ]

        return Problem(
            drill_id=self.id,
            prompt=f"sqrt({radicand}) = ?",
            answer=answer,
            difficulty=difficulty,
            seed={"radicand": radicand, "op": "sqrt"},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_submitted = submitted.strip()
        norm_answer = problem.answer.strip()
        try:
            correct = abs(float(norm_submitted) - float(norm_answer)) <= self.EPSILON
        except ValueError:
            correct = False
        return CheckResult(
            correct=correct,
            normalized_submitted=norm_submitted,
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )


class CubesDrill(Drill):
    """0.0 -> bases 1-10, 1.0 -> bases up to 50 (cubing grows fast)."""

    id = "cubes"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        max_base = 10 + int(difficulty * 40)
        n = rng.randint(1, max_base)
        answer = n ** 3

        hints = [
            f"{n}^3 means {n} multiplied by itself three times.",
            f"{n} x {n} = {n * n}, then multiply that by {n} again.",
            f"The answer is {answer}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"{n}^3 = ?",
            answer=str(answer),
            difficulty=difficulty,
            seed={"n": n, "op": "cube"},
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


class CbrtsDrill(Drill):
    """
    difficulty < 0.6: perfect cubes only, exact integer answer.
    difficulty >= 0.6: arbitrary integers, irrational root, answer accepted
                       within +/- 0.01 of the true value.
    """

    id = "cbrts"
    EPSILON = 0.01

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        max_base = 10 + int(difficulty * 15)

        if difficulty < 0.6:
            n = rng.randint(1, max_base)
            radicand = n ** 3
            answer = str(n)
            hints = [
                f"What number cubed equals {radicand}?",
                f"Try checking {max(1, n - 1)} and {n + 1} cubed as bounds.",
                f"The answer is {n}.",
            ]
        else:
            radicand = rng.randint(2, 500)
            true_val = radicand ** (1 / 3)
            answer = f"{true_val:.2f}"
            hints = [
                f"{radicand} is not a perfect cube -- estimate between the nearest perfect cubes.",
                f"cbrt({radicand}) is between {int(radicand ** (1/3))} and {int(radicand ** (1/3)) + 1}.",
                f"The answer is approximately {answer}.",
            ]

        return Problem(
            drill_id=self.id,
            prompt=f"cbrt({radicand}) = ?",
            answer=answer,
            difficulty=difficulty,
            seed={"radicand": radicand, "op": "cbrt"},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_submitted = submitted.strip()
        norm_answer = problem.answer.strip()
        try:
            correct = abs(float(norm_submitted) - float(norm_answer)) <= self.EPSILON
        except ValueError:
            correct = False
        return CheckResult(
            correct=correct,
            normalized_submitted=norm_submitted,
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )
