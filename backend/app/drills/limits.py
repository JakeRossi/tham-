"""
Limits drill: evaluate limits via direct substitution, algebraic
cancellation, L'Hopital's rule, and Taylor series expansion.

Level scheme (0.0-1.0 difficulty -> levels 1-9):
  1: direct substitution (continuous function, no indeterminate form)
  2: 0/0 resolved by factoring/cancellation (rational function)
  3: classic small-angle-style limits at 0 (sin(x)/x family) -- single
     L'Hopital application, or the "known special limit" shortcut
  4: L'Hopital's rule needing two applications
  5: limit at infinity of a rational function (compare degrees)
  6: limit at infinity with exponential/logarithmic dominance
  7: a single Taylor-series-based limit at 0 (e.g. (e^x-1-x)/x^2)
  8: combined -- numerator AND denominator both need series expansion
  9 ("hardest"): combined with more terms on each side

Generation for levels 7-9 uses a small library of functions that vanish
at x=0 (see _VANISHING_ATOMS) combined into sums, with the actual limit
value verified defensively at generation time (sp.limit, retrying with
fresh random parameters if the result isn't a clean finite value) --
not every random combination of vanishing functions produces a
well-behaved limit, so this mirrors the same defensive pattern used for
integrals in function_library.py.
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem
from app.drills.expr_utils import parse_user_expr, pretty_str

x = sp.symbols("x")

MAX_LEVEL = 9


def level_for_difficulty(difficulty: float) -> int:
    level = 1 + int(difficulty * (MAX_LEVEL - 1) + 0.5)
    return max(1, min(MAX_LEVEL, level))


def _nonzero(rng: random.Random, lo: int = -9, hi: int = 9) -> int:
    c = rng.randint(lo, hi)
    return c if c != 0 else rng.choice([1, -1])


def _is_good_finite_limit(value) -> bool:
    if value is None:
        return False
    if value.has(sp.oo, -sp.oo, sp.zoo, sp.nan):
        return False
    if value.is_real is False:
        return False
    return True


_VANISHING_ATOMS = [
    lambda rng: x,
    lambda rng: sp.sin(_nonzero(rng, 1, 3) * x),
    lambda rng: 1 - sp.cos(_nonzero(rng, 1, 3) * x),
    lambda rng: sp.exp(_nonzero(rng, 1, 3) * x) - 1,
    lambda rng: sp.log(1 + _nonzero(rng, 1, 3) * x),
]


def _build_vanishing_sum(rng: random.Random, num_terms: int) -> sp.Expr:
    return sum(_nonzero(rng, 1, 5) * rng.choice(_VANISHING_ATOMS)(rng) for _ in range(num_terms))


def _build_candidate(rng: random.Random, level: int) -> tuple[sp.Expr, sp.Expr]:
    """Returns (expr, approach_point)."""
    if level == 1:
        a = rng.randint(-3, 3)
        max_degree = rng.randint(1, 3)
        expr = sum(_nonzero(rng) * x**d for d in range(max_degree + 1))
        return expr, sp.Integer(a)
    if level == 2:
        a = rng.randint(-4, 4)
        p_extra = _nonzero(rng) * x + _nonzero(rng)
        q_extra = _nonzero(rng) * x + _nonzero(rng)
        return ((x - a) * p_extra) / ((x - a) * q_extra), sp.Integer(a)
    if level == 3:
        k = _nonzero(rng, 1, 4)
        choice = rng.choice(["sin", "tan", "one_minus_cos", "exp_minus_one"])
        if choice == "sin":
            expr = sp.sin(k * x) / x
        elif choice == "tan":
            expr = sp.tan(k * x) / x
        elif choice == "one_minus_cos":
            expr = (1 - sp.cos(k * x)) / x
        else:
            expr = (sp.exp(k * x) - 1) / x
        return expr, sp.Integer(0)
    if level == 4:
        k = _nonzero(rng, 1, 3)
        if rng.random() < 0.5:
            expr = (1 - sp.cos(k * x)) / x**2
        else:
            expr = (k * x - sp.sin(k * x)) / x**3
        return expr, sp.Integer(0)
    if level == 5:
        degree = rng.randint(1, 3)
        num = _nonzero(rng) * x**degree + sum(_nonzero(rng) * x**d for d in range(degree))
        den = _nonzero(rng) * x**degree + sum(_nonzero(rng) * x**d for d in range(degree))
        return num / den, sp.oo
    if level == 6:
        k = rng.randint(1, 2)
        if rng.random() < 0.5:
            n = rng.randint(1, 3)
            expr = x**n / sp.exp(k * x)
        else:
            n = rng.randint(1, 2)
            expr = sp.log(x) / x**n
        return expr, sp.oo
    if level == 7:
        numerator = _build_vanishing_sum(rng, 1)
        denominator = _build_vanishing_sum(rng, rng.randint(1, 2))
        return numerator / denominator, sp.Integer(0)
    if level == 8:
        numerator = _build_vanishing_sum(rng, 2)
        denominator = _build_vanishing_sum(rng, 2)
        return numerator / denominator, sp.Integer(0)
    # level 9: hardest -- more terms on each side
    numerator = _build_vanishing_sum(rng, 3)
    denominator = _build_vanishing_sum(rng, 3)
    return numerator / denominator, sp.Integer(0)


def _approach_latex(a: sp.Expr) -> str:
    return "\\infty" if a == sp.oo else sp.latex(a)


class LimitsDrill(Drill):
    id = "limits"

    def generate(self, difficulty: float, rng_seed: int | None = None, max_attempts: int = 25) -> Problem:
        rng = random.Random(rng_seed)
        level = level_for_difficulty(difficulty)

        expr, approach = x, sp.Integer(0)  # overwritten below once a valid candidate is found
        value = None
        for attempt in range(max_attempts):
            candidate_expr, candidate_approach = _build_candidate(rng, level)
            try:
                candidate_value = sp.limit(candidate_expr, x, candidate_approach)
            except Exception:
                continue
            if _is_good_finite_limit(candidate_value):
                expr, approach, value = candidate_expr, candidate_approach, candidate_value
                break
        if value is None:
            # safe fallback -- always a clean limit
            expr, approach = x, sp.Integer(0)
            value = sp.Integer(0)

        answer_str = pretty_str(sp.simplify(value))
        prompt = f"$$\\lim_{{x \\to {_approach_latex(approach)}}} {sp.latex(expr)}$$"

        hints = [
            "Try direct substitution first. If you get an indeterminate form (0/0 or infinity/infinity), "
            "you'll need another technique -- factoring, L'Hopital's rule, or a Taylor series expansion.",
            "L'Hopital's rule: if the limit is 0/0 or infinity/infinity, the limit of f(x)/g(x) equals the "
            "limit of f'(x)/g'(x) (differentiate top and bottom separately, don't use the quotient rule). "
            "For small-x limits, replacing sin(x), cos(x), e^x, ln(1+x) with their Taylor series near 0 "
            "often works just as well.",
            f"The answer is $$ {sp.latex(sp.simplify(value))} $$",
        ]

        return Problem(
            drill_id=self.id,
            prompt=prompt,
            answer=answer_str,
            difficulty=difficulty,
            seed={"expr": str(expr), "approach": str(approach), "level": level},
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
