"""
Algebraic manipulation drill: combine like terms at low difficulty,
expand binomial products at higher difficulty.

Like derivatives, there's no single canonical string form of "simplified,"
so checking is done via symbolic equivalence (sp.simplify(submitted - target) == 0)
rather than string matching -- see docs/DRILL_AUTHORING.md.

Display uses implicit multiplication ("6x" not "6*x") via expr_utils --
parse_user_expr() (also implicit-multiplication-aware) is what makes sure
a user typing either "6x" or "6*x" is accepted as the same answer.
"""

from __future__ import annotations

import random

import sympy as sp

from app.drills.base import CheckResult, Drill, Problem
from app.drills.expr_utils import parse_user_expr, pretty_str

x = sp.symbols("x")


class AlgebraicManipulationDrill(Drill):
    """
    difficulty < 0.5: combine like terms in a linear expression
                       (e.g. "3x + 5 + 2x - 1" -> simplify).
    difficulty >= 0.5: expand a product of two binomials
                       (e.g. "(2x + 3)(x - 4)" -> expand).
    """

    id = "algebraic-manipulation"

    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        rng = random.Random(rng_seed)

        if difficulty < 0.5:
            num_terms = 3 + int(difficulty * 6)  # 3-6 terms
            expr = sp.Integer(0)
            display_terms = []
            for _ in range(num_terms):
                coeff = rng.randint(-9, 9)
                if coeff == 0:
                    continue
                is_x_term = rng.choice([True, False])
                term = coeff * x if is_x_term else sp.Integer(coeff)
                expr += term
                display_terms.append(pretty_str(term))
            prompt_expr = " + ".join(display_terms).replace("+ -", "- ")
            target = sp.expand(expr)
            prompt = f"Simplify: {prompt_expr}"
            hints = [
                "Group the x-terms together, then group the constant terms together.",
                "Add up the coefficients of the x-terms; separately add up the plain numbers.",
                f"The answer is {pretty_str(target)}.",
            ]
        else:
            a1, b1 = rng.randint(-9, 9) or 1, rng.randint(-9, 9)
            a2, b2 = rng.randint(-9, 9) or 1, rng.randint(-9, 9)
            expr = (a1 * x + b1) * (a2 * x + b2)
            target = sp.expand(expr)
            prompt = f"Expand: ({pretty_str(a1 * x + b1)})({pretty_str(a2 * x + b2)})"
            hints = [
                "Use FOIL: First, Outer, Inner, Last.",
                f"First: {pretty_str(a1 * x)} x {pretty_str(a2 * x)}. Outer: {pretty_str(a1 * x)} x {b2}. "
                f"Inner: {b1} x {pretty_str(a2 * x)}. Last: {b1} x {b2}.",
                f"The answer is {pretty_str(target)}.",
            ]

        answer = pretty_str(target)
        return Problem(
            drill_id=self.id,
            prompt=prompt,
            answer=answer,
            difficulty=difficulty,
            seed={"target": answer},
            hints=hints,
        )

    def check(self, problem: Problem, submitted: str) -> CheckResult:
        norm_answer = problem.answer.strip()
        try:
            submitted_expr = parse_user_expr(submitted, {"x": x})
            answer_expr = parse_user_expr(norm_answer, {"x": x})
            correct = sp.simplify(submitted_expr - answer_expr) == 0
        except Exception:  # broad on purpose -- garbage input fails in many different ways
            correct = False

        return CheckResult(
            correct=correct,
            normalized_submitted=str(submitted).strip(),
            normalized_answer=norm_answer,
            feedback=None if correct else f"Not quite -- the answer was {norm_answer}.",
        )
