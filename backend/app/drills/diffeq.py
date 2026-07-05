"""
ODE/PDE drill.

Scope for now: separable first-order ODEs of the form dy/dx = k*y, solved
with an initial condition y(0) = y0 so the answer is a CONCRETE function
(no arbitrary constant to grade against) -- e.g. y = 3*exp(2*x) rather than
y = C*exp(2*x). This sidesteps the hard problem of grading answers that
differ only in how the constant of integration is expressed.

PDEs are NOT implemented -- grading general PDE solutions is a much harder
problem (boundary conditions, multiple valid solution forms) and deserves
its own design pass. See docs/DRILL_AUTHORING.md.
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem

x = sp.symbols("x")
y = sp.Function("y")


def _k_range_for_difficulty(difficulty: float) -> int:
    # 0.0 -> k in [1,3], 1.0 -> k in [1,9]
    return 3 + int(difficulty * 6)


class OdePdeDrill(Drill):
    """
    Generates: dy/dx = k*y, y(0) = y0
    Solution:  y = y0 * exp(k*x)

    NOTE: id kept as "ode-pde" to match content/builtin-drills/ode-pde.json,
    even though only the ODE half is implemented.
    """

    id = "ode-pde"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        k_max = _k_range_for_difficulty(difficulty)
        k = rng.choice([i for i in range(-k_max, k_max + 1) if i != 0])
        y0 = rng.randint(1, 5)

        solution = y0 * sp.exp(k * x)
        answer_str = sp.sstr(solution)

        hints = [
            "This is a separable ODE: move all y terms to one side, all x terms to the other.",
            f"Integrating both sides gives ln|y| = {k}x + C, so y = A*exp({k}x) for some constant A. "
            f"Use y(0) = {y0} to solve for A.",
            f"The answer is {answer_str}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"Solve: dy/dx = {k}*y, with y(0) = {y0}. Find y(x).",
            answer=answer_str,
            difficulty=difficulty,
            seed={"k": k, "y0": y0},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        """
        Numeric sampling check rather than pure symbolic simplify: exponential
        expressions are more prone to sympy simplify() not recognizing
        equivalence than polynomials are, so evaluate both sides at several
        x values and compare within a small tolerance.
        """
        norm_answer = problem.answer.strip()
        try:
            submitted_expr = sp.sympify(submitted, locals={"x": x})
            answer_expr = sp.sympify(norm_answer, locals={"x": x})
            if not (hasattr(submitted_expr, "subs") and hasattr(answer_expr, "subs")):
                raise TypeError("sympify did not produce a substitutable expression")
            sample_points = [-1, 0, 0.5, 1, 2]
            correct = all(
                abs(float(submitted_expr.subs(x, pt)) - float(answer_expr.subs(x, pt))) < 1e-6
                for pt in sample_points
            )
        except Exception:
            # Broad catch is intentional: garbage input can fail in many different
            # ways depending on how sympify happens to parse it (SympifyError,
            # TypeError, ValueError, AttributeError, complex results, etc.) --
            # all of them should just mean "not correct," never a 500.
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=str(submitted).strip(),
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )
