"""
Calculus drills: derivatives (basic + partial), integrals (definite + line).

Only DerivativesDrill is fully implemented here as the reference pattern
for anything sympy-backed. Integrals follows the same shape (see stub).

Key idea: because sympy can both GENERATE a random expression and
symbolically CHECK whether a submitted answer is equivalent to the true
derivative (even if written differently, e.g. "2*x+5" vs "5+2*x"), we get
free-form answer entry instead of multiple choice.
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem

x, y = sp.symbols("x y")


def _random_polynomial(rng: random.Random, max_degree: int, coeff_range: int = 9) -> sp.Expr:
    """Build a random single-variable polynomial in x with degree <= max_degree."""
    expr = sp.Integer(0)
    for deg in range(max_degree, -1, -1):
        coeff = rng.randint(-coeff_range, coeff_range)
        if coeff != 0:
            expr += coeff * x**deg
    if expr == 0:
        expr = sp.Integer(rng.randint(1, coeff_range))
    return expr


def _degree_for_difficulty(difficulty: float) -> int:
    # 0.0 -> degree 1 (linear), 1.0 -> degree 4
    return 1 + min(3, int(difficulty * 4))


class DerivativesDrill(Drill):
    """
    difficulty 0.0-0.5: single-variable polynomials, d/dx
    difficulty 0.5-1.0: two-variable polynomials, partial derivative d/dx or d/dy
    """

    id = "derivatives"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        max_degree = _degree_for_difficulty(difficulty)

        if difficulty < 0.5:
            expr = _random_polynomial(rng, max_degree)
            derivative = sp.diff(expr, x)
            prompt = f"d/dx [ {sp.sstr(expr)} ] = ?"
            var_name = "x"
        else:
            # two-variable expression, partial derivative w.r.t. a randomly chosen var
            expr_x = _random_polynomial(rng, max_degree)
            expr_y_part = rng.randint(-9, 9) * y ** rng.randint(1, max_degree)
            expr = expr_x + expr_y_part
            wrt = rng.choice([x, y])
            derivative = sp.diff(expr, wrt)
            var_name = str(wrt)
            prompt = f"∂/∂{var_name} [ {sp.sstr(expr)} ] = ?"

        answer_str = sp.sstr(sp.expand(derivative))

        hints = [
            f"Differentiate term by term with respect to {var_name}.",
            "Recall the power rule: d/dx[x^n] = n*x^(n-1). Constants and other-variable "
            "terms not containing the variable you're differentiating w.r.t. drop to 0.",
            f"The answer is {answer_str}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=prompt,
            answer=answer_str,
            difficulty=difficulty,
            seed={"expr": str(expr), "wrt": var_name},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        """
        Symbolic equivalence check -- accepts any algebraically equivalent
        form of the answer, not just an exact string match.
        """
        norm_answer = problem.answer.strip()
        try:
            submitted_expr = sp.sympify(submitted, locals={"x": x, "y": y})
            answer_expr = sp.sympify(norm_answer, locals={"x": x, "y": y})
            correct = sp.simplify(submitted_expr - answer_expr) == 0
        except Exception:  # broad on purpose -- garbage input fails in many different ways
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=str(submitted).strip(),
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )


class IntegralsDrill(Drill):
    """
    Definite integrals of single-variable polynomials: integral of expr dx from a to b.

    NOTE: line integrals (integral over a parametrized curve of a vector
    field) are NOT implemented here -- they need a meaningfully different
    problem shape (a curve + a vector field, not just an expr + bounds).
    Left as a future extension; see docs/DRILL_AUTHORING.md.
    """

    id = "integrals"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        max_degree = _degree_for_difficulty(difficulty)
        expr = _random_polynomial(rng, max_degree)

        # Keep bounds small and integer so the arithmetic stays clean-ish.
        bound_range = 2 + int(difficulty * 4)
        a = rng.randint(-bound_range, bound_range)
        b = rng.randint(-bound_range, bound_range)
        if a == b:
            b += 1
        if a > b:
            a, b = b, a

        definite_value = sp.integrate(expr, (x, a, b))
        answer_str = sp.sstr(sp.simplify(definite_value))

        antiderivative = sp.integrate(expr, x)
        hints = [
            f"First find the antiderivative of {sp.sstr(expr)} with respect to x.",
            f"The antiderivative is {sp.sstr(antiderivative)} + C. "
            f"Evaluate it at x={b} and x={a}, then subtract.",
            f"The answer is {answer_str}.",
        ]

        return Problem(
            drill_id=self.id,
            prompt=f"Evaluate: integral from {a} to {b} of ( {sp.sstr(expr)} ) dx",
            answer=answer_str,
            difficulty=difficulty,
            seed={"expr": str(expr), "a": a, "b": b},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_answer = problem.answer.strip()
        try:
            submitted_expr = sp.sympify(submitted)
            answer_expr = sp.sympify(norm_answer)
            correct = sp.simplify(submitted_expr - answer_expr) == 0
        except Exception:  # broad on purpose -- garbage input fails in many different ways
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=str(submitted).strip(),
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )
