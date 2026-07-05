"""
Trig values drill: evaluate sin/cos/tan (and reciprocals at higher
difficulty) at angles expressed in RADIANS using pi notation
(e.g. "pi/2", "3pi/4"), not degrees.

difficulty < 0.5: common unit-circle angles (multiples of pi/6, pi/4,
                  etc.), sin/cos/tan only, exact answers
                  (e.g. "sqrt(2)/2" or "1/2").
difficulty >= 0.5: arbitrary pi-fraction angles, all six functions,
                  decimal answers accepted within epsilon.
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem
from app.drills.expr_utils import parse_user_expr

# Common unit-circle angles as fractions of pi (numerator, denominator).
COMMON_ANGLE_FRACTIONS = [
    (0, 1), (1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4), (5, 6),
    (1, 1), (7, 6), (5, 4), (4, 3), (3, 2), (5, 3), (7, 4), (11, 6), (2, 1),
]

BASIC_FUNCS = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan}
ALL_FUNCS = {**BASIC_FUNCS, "csc": lambda t: 1 / sp.sin(t), "sec": lambda t: 1 / sp.cos(t), "cot": sp.cot}


def format_pi_angle(num: int, den: int) -> str:
    """(1, 2) -> 'pi/2', (3, 4) -> '3pi/4', (0, 1) -> '0', (1, 1) -> 'pi'."""
    if num == 0:
        return "0"
    sign = "-" if num < 0 else ""
    num = abs(num)
    pi_part = "pi" if num == 1 else f"{num}pi"
    return f"{sign}{pi_part}" if den == 1 else f"{sign}{pi_part}/{den}"


class TrigValuesDrill(Drill):
    id = "trig-values"
    EPSILON = 0.01

    @staticmethod
    def _safe_eval(func, theta) -> sp.Expr | None:
        """Returns the simplified value, or None if it's undefined/complex/infinite
        (e.g. tan(pi/2), csc(pi))."""
        try:
            val = sp.simplify(func(theta))
        except ZeroDivisionError:
            return None
        if val.has(sp.zoo, sp.oo, -sp.oo, sp.nan) or val.is_real is False:
            return None
        return val

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)

        if difficulty < 0.5:
            num, den = rng.choice(COMMON_ANGLE_FRACTIONS)
            func_name = rng.choice(list(BASIC_FUNCS))
        else:
            den = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
            num = rng.randint(0, 2 * den)
            func_name = rng.choice(list(ALL_FUNCS))

        func = ALL_FUNCS[func_name]
        theta = sp.Rational(num, den) * sp.pi
        exact_val = self._safe_eval(func, theta)

        attempts = 0
        while exact_val is None and attempts < 20:
            # e.g. tan(pi/2), csc(pi) undefined -- retry with a new angle
            if difficulty < 0.5:
                num, den = rng.choice(COMMON_ANGLE_FRACTIONS)
            else:
                den = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
                num = rng.randint(0, 2 * den)
            theta = sp.Rational(num, den) * sp.pi
            exact_val = self._safe_eval(func, theta)
            attempts += 1
        if exact_val is None:
            # last-resort safe fallback, guaranteed defined for every function in ALL_FUNCS
            num, den = 1, 6
            theta = sp.Rational(num, den) * sp.pi
            exact_val = self._safe_eval(func, theta)

        angle_str = format_pi_angle(num, den)

        if difficulty < 0.5:
            answer = sp.sstr(exact_val)  # exact symbolic form, e.g. "sqrt(3)/2"
        else:
            answer = f"{float(exact_val):.2f}"

        hints = [
            f"Recall the unit circle position for {angle_str} radians.",
            f"{func_name}({angle_str}) relates to a reference angle within the first quadrant.",
            f"The answer is {answer}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"{func_name}({angle_str}) = ?",
            answer=answer,
            difficulty=difficulty,
            seed={"frac_num": num, "frac_den": den, "func": func_name},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_submitted = submitted.strip()
        norm_answer = problem.answer.strip()

        # Numeric comparison handles both exact-symbolic and decimal answers,
        # and lets a user type "0.71" even when the canonical answer is "sqrt(2)/2".
        try:
            submitted_val = float(sp.N(parse_user_expr(norm_submitted)))
            answer_val = float(sp.N(parse_user_expr(norm_answer)))
            correct = abs(submitted_val - answer_val) <= self.EPSILON
        except Exception:
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=norm_submitted,
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )
