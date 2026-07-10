"""
Calculus drills: derivatives (single-variable through 2-variable partials,
with real functional variety) and definite integrals.

Content generation is delegated to app/drills/function_library.py, which
maps the continuous difficulty (already combo/accuracy-accelerated by
engine/mastery.py) onto a discrete content level and builds an expression
appropriate to that level -- see that module's docstring for the full
level scheme.

Key idea: because sympy can both GENERATE a random expression and
symbolically CHECK whether a submitted answer is equivalent to the true
derivative (even if written differently, e.g. "2*x+5" vs "5+2*x"), we get
free-form answer entry instead of multiple choice.

Prompts are rendered as LaTeX (wrapped in $$...$$) so the frontend can
show proper mathematical notation instead of ASCII "d/dx [ ... ]" text --
see frontend/standalone/index.html's renderMathOrText(). Canonical answers
(used for grading, not display) still use expr_utils.pretty_str/
parse_user_expr so "6x" and "6*x" are accepted identically.
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem
from app.drills.expr_utils import parse_user_expr, pretty_str
from app.drills.function_library import (
    MAX_LEVEL_SINGLE_VAR,
    generate_single_var_expr,
    generate_single_var_integrand,
    generate_two_var_expr,
    level_for_difficulty,
    level_for_difficulty_derivative,
)

x, y = sp.symbols("x y")


class DerivativesDrill(Drill):
    """
    difficulty 0.0-0.5: single-variable, levels 1-10 (power rule through
    combined product/quotient/chain rule -- see function_library.py).
    difficulty 0.5-1.0: two-variable partials, levels 11-16.
    """

    id = "derivatives"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        level = level_for_difficulty_derivative(difficulty)

        if level <= MAX_LEVEL_SINGLE_VAR:
            expr = generate_single_var_expr(rng, level)
            derivative = sp.diff(expr, x)
            var_name = "x"
            prompt = f"$$\\frac{{d}}{{dx}}\\left[ {sp.latex(expr)} \\right]$$"
        else:
            expr = generate_two_var_expr(rng, level)
            wrt = rng.choice([x, y])
            derivative = sp.diff(expr, wrt)
            var_name = str(wrt)
            prompt = f"$$\\frac{{\\partial}}{{\\partial {var_name}}}\\left[ {sp.latex(expr)} \\right]$$"

        target = sp.simplify(sp.expand(derivative))
        answer_str = pretty_str(target)

        hints = [
            f"Differentiate term by term with respect to {var_name}. If terms are multiplied "
            "or divided, you'll need the product or quotient rule; if one function is nested "
            "inside another, use the chain rule.",
            "Recall: power rule d/dx[x^n]=n*x^(n-1), product rule (fg)'=f'g+fg', "
            "quotient rule (f/g)'=(f'g-fg')/g^2, chain rule d/dx[f(g(x))]=f'(g(x))*g'(x).",
            f"The answer is $$ {sp.latex(target)} $$",
        ]

        return Problem(
            drill_id=self.id,
            prompt=prompt,
            answer=answer_str,
            difficulty=difficulty,
            seed={"expr": str(expr), "wrt": var_name, "level": level},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        """
        Symbolic equivalence check -- accepts any algebraically equivalent
        form of the answer (including implicit multiplication like '6x'),
        not just an exact string match.
        """
        norm_answer = problem.answer.strip()
        try:
            submitted_expr = parse_user_expr(submitted, {"x": x, "y": y})
            answer_expr = parse_user_expr(norm_answer, {"x": x, "y": y})
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
    Definite integrals, levels 1-9 (power rule through a guaranteed-
    integrable u-substitution pattern -- see function_library.py). Levels
    are capped lower than derivatives' 10 because not every product/
    quotient combination has an elementary antiderivative; generation
    verifies integrability defensively (see generate_single_var_integrand).

    NOTE: line integrals and triple integrals are NOT implemented --
    they need meaningfully different problem shapes. Left as a future
    extension; see docs/DRILL_AUTHORING.md.
    """

    id = "integrals"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)
        level = level_for_difficulty(difficulty, max_level=9)
        expr = generate_single_var_integrand(rng, level)

        # Keep bounds small and integer so the arithmetic stays clean-ish.
        bound_range = 2 + int(difficulty * 4)
        a = rng.randint(-bound_range, bound_range)
        b = rng.randint(-bound_range, bound_range)
        if a == b:
            b += 1
        if a > b:
            a, b = b, a

        definite_value = sp.integrate(expr, (x, a, b))
        target = sp.simplify(definite_value)
        answer_str = pretty_str(target)

        antiderivative = sp.integrate(expr, x)
        prompt = f"$$\\int_{{{a}}}^{{{b}}} {sp.latex(expr)} \\, dx$$"
        hints = [
            "First find the antiderivative of the integrand with respect to x. Watch for "
            "products (integration by parts) or a chain-rule pattern (u-substitution).",
            f"The antiderivative is $$ {sp.latex(antiderivative)} + C $$ "
            f"Evaluate it at x={b} and x={a}, then subtract.",
            f"The answer is $$ {sp.latex(target)} $$",
        ]

        return Problem(
            drill_id=self.id,
            prompt=prompt,
            answer=answer_str,
            difficulty=difficulty,
            seed={"expr": str(expr), "a": a, "b": b, "level": level},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_answer = problem.answer.strip()
        try:
            submitted_expr = parse_user_expr(submitted)
            answer_expr = parse_user_expr(norm_answer)
            correct = sp.simplify(submitted_expr - answer_expr) == 0
        except Exception:  # broad on purpose -- garbage input fails in many different ways
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=str(submitted).strip(),
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )
