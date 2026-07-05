"""
Trig values drill: evaluate sin/cos/tan (and reciprocals at higher
difficulty) at common or arbitrary angles.

difficulty < 0.5: common angles (0, 30, 45, 60, 90, ...) in degrees,
                  sin/cos/tan only, exact answers (e.g. "sqrt(2)/2" or "1/2").
difficulty >= 0.5: arbitrary angles, all six functions, decimal answers
                   accepted within epsilon.
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem

COMMON_ANGLES_DEG = [0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330, 360]
BASIC_FUNCS = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan}
ALL_FUNCS = {**BASIC_FUNCS, "csc": lambda t: 1 / sp.sin(t), "sec": lambda t: 1 / sp.cos(t), "cot": sp.cot}


class TrigValuesDrill(Drill):
    id = "trig-values"
    EPSILON = 0.01

    @staticmethod
    def _safe_eval(func, theta) -> sp.Expr | None:
        """Returns the simplified value, or None if it's undefined/complex/infinite
        (e.g. tan(90deg), csc(180deg))."""
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
            angle_deg = rng.choice(COMMON_ANGLES_DEG)
            func_name = rng.choice(list(BASIC_FUNCS))
        else:
            angle_deg = rng.randint(0, 359)
            func_name = rng.choice(list(ALL_FUNCS))

        func = ALL_FUNCS[func_name]
        theta = sp.rad(angle_deg)

        exact_val = self._safe_eval(func, theta)
        attempts = 0
        while exact_val is None and attempts < 20:
            # e.g. tan(90deg), csc(180deg) undefined -- retry with a new angle
            angle_deg = rng.choice(COMMON_ANGLES_DEG) if difficulty < 0.5 else rng.randint(0, 359)
            theta = sp.rad(angle_deg)
            exact_val = self._safe_eval(func, theta)
            attempts += 1
        if exact_val is None:
            # last-resort safe fallback, guaranteed defined for every function in ALL_FUNCS
            angle_deg = 30
            theta = sp.rad(angle_deg)
            exact_val = self._safe_eval(func, theta)

        if difficulty < 0.5:
            # exact symbolic form, e.g. "sqrt(3)/2"
            answer = sp.sstr(exact_val)
        else:
            answer = f"{float(exact_val):.2f}"

        hints = [
            f"Recall the unit circle position for {angle_deg} degrees.",
            f"{func_name}({angle_deg} deg) relates to a reference angle within the first quadrant.",
            f"The answer is {answer}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"{func_name}({angle_deg} deg) = ?",
            answer=answer,
            difficulty=difficulty,
            seed={"angle_deg": angle_deg, "func": func_name},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_submitted = submitted.strip()
        norm_answer = problem.answer.strip()

        # Try numeric comparison first (handles both exact-symbolic and decimal answers,
        # and lets a user type "0.71" even when the canonical answer is "sqrt(2)/2").
        try:
            submitted_val = float(sp.N(sp.sympify(norm_submitted)))
            answer_val = float(sp.N(sp.sympify(norm_answer)))
            correct = abs(submitted_val - answer_val) <= self.EPSILON
        except (sp.SympifyError, TypeError, ValueError):
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=norm_submitted,
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )
