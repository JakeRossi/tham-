"""
Leveled function-generation library for derivatives/integrals, so these
drills produce genuine variety (polynomials, trig, exponentials, and
combinations via product/quotient/chain rule) instead of only
polynomials, with a real progression from simple to hard.

How level maps to difficulty: the continuous 0.0-1.0 difficulty coming
from the mastery system (already accelerated by combo/accuracy -- see
engine/mastery.py) is bucketed into a discrete content level via
level_for_difficulty(). Progressing through levels IS progressing through
difficulty; a player on a long combo or high accuracy climbs mastery
faster, which reaches each new level's difficulty threshold sooner.

Level scheme (single variable), used for both derivatives and integrals
(integrals cap out earlier -- not every product/quotient has an
elementary antiderivative, so higher integral levels stay within patterns
sympy can reliably solve, verified defensively at generation time):
  1: single polynomial term (power rule)
  2: sum of 2 polynomial terms
  3: sum of 2-3 polynomial terms (a small full polynomial)
  4: single trig term: sin(ax) or cos(ax)
  5: single exponential term: exp(ax)
  6: sum mixing polynomial + trig/exp
  7: product of two simple terms (product rule)
  8: quotient of two simple terms (quotient rule)
  9: chain rule composition
  10 ("hardest single-variable"): combined product/quotient/chain

Level scheme (two-variable partials), reusing the same building blocks
but with expressions in x AND y, partial w.r.t. a randomly chosen variable:
  11: simple 2-var polynomial partial
  12: 2-var polynomial with one trig/exp term mixed in
  13: product rule across x and y, e.g. d/dx[x^2 * sin(y)]
  14: quotient rule across x and y
  15: chain rule across x and y, e.g. d/dx[sin(x*y)]
  16 ("hardest 2-var partial"): combined

NOT implemented: 3+ variable calculus -- see docs/DRILL_AUTHORING.md for
what a follow-up extension would need.
"""

from __future__ import annotations

import random

import sympy as sp

x, y = sp.symbols("x y")

MAX_LEVEL_SINGLE_VAR = 10
MAX_LEVEL_TWO_VAR = 16
MAX_LEVEL_INTEGRAL = 9  # integrals stay within patterns with guaranteed elementary antiderivatives


def level_for_difficulty(difficulty: float, max_level: int = MAX_LEVEL_SINGLE_VAR) -> int:
    """Maps 0.0-1.0 difficulty onto a discrete content level 1..max_level."""
    level = 1 + int(difficulty * (max_level - 1) + 0.5)
    return max(1, min(max_level, level))


def level_for_difficulty_derivative(difficulty: float) -> int:
    """
    0.0-0.5 spans single-variable levels 1-10.
    0.5-1.0 spans two-variable partial levels 11-16.
    """
    if difficulty < 0.5:
        return level_for_difficulty(difficulty / 0.5, MAX_LEVEL_SINGLE_VAR)
    span = MAX_LEVEL_TWO_VAR - MAX_LEVEL_SINGLE_VAR
    level = MAX_LEVEL_SINGLE_VAR + 1 + int(((difficulty - 0.5) / 0.5) * span)
    return max(MAX_LEVEL_SINGLE_VAR + 1, min(MAX_LEVEL_TWO_VAR, level))


# ---- building-block atoms ----

def _nonzero_coeff(rng: random.Random, low: int = -9, high: int = 9) -> int:
    c = rng.randint(low, high)
    return c if c != 0 else rng.choice([1, -1])


def _poly_term(rng: random.Random, var: sp.Symbol, max_degree: int = 3) -> sp.Expr:
    coeff = _nonzero_coeff(rng)
    degree = rng.randint(0, max_degree)
    return coeff * var**degree


def _poly_term_nonconstant(rng: random.Random, var: sp.Symbol, max_degree: int = 3) -> sp.Expr:
    """Same as _poly_term but degree is always >= 1 -- used where a
    standalone poly term controls a whole variable's dependency (e.g. one
    side of a 2-var partial), so it can't degenerate into a trivial
    constant that makes the whole partial derivative zero."""
    coeff = _nonzero_coeff(rng)
    degree = rng.randint(1, max(1, max_degree))
    return coeff * var**degree


def _trig_atom(rng: random.Random, var: sp.Expr) -> sp.Expr:
    func = rng.choice([sp.sin, sp.cos])
    a = rng.randint(1, 3)
    return func(a * var)


def _exp_atom(rng: random.Random, var: sp.Expr) -> sp.Expr:
    a = rng.randint(1, 3)
    return sp.exp(a * var)


def _simple_atom(rng: random.Random, var: sp.Expr) -> sp.Expr:
    return rng.choice([
        lambda: _poly_term(rng, var, 2),
        lambda: _trig_atom(rng, var),
        lambda: _exp_atom(rng, var),
    ])()


# ---- single-variable expression generation (derivatives -- always safe,
#      sp.diff never fails to produce SOME closed form) ----

def generate_single_var_expr(rng: random.Random, level: int) -> sp.Expr:
    level = max(1, min(MAX_LEVEL_SINGLE_VAR, level))
    if level == 1:
        return _poly_term(rng, x, 3)
    if level == 2:
        return _poly_term(rng, x, 2) + _poly_term(rng, x, 2)
    if level == 3:
        return sum(_poly_term(rng, x, 3) for _ in range(rng.randint(2, 3)))
    if level == 4:
        return _nonzero_coeff(rng) * _trig_atom(rng, x)
    if level == 5:
        return _nonzero_coeff(rng) * _exp_atom(rng, x)
    if level == 6:
        return _poly_term(rng, x, 2) + _simple_atom(rng, x)
    if level == 7:
        return _simple_atom(rng, x) * _simple_atom(rng, x)
    if level == 8:
        numerator = _simple_atom(rng, x)
        denominator = _poly_term(rng, x, 1) + rng.randint(1, 5)  # never identically zero
        return numerator / denominator
    if level == 9:
        inner = _poly_term(rng, x, 2)
        outer = rng.choice([sp.sin, sp.cos, sp.exp])
        return outer(inner)
    # level 10: combined product/quotient/chain
    combo = rng.choice(["product_chain", "quotient_chain", "triple_product"])
    if combo == "triple_product":
        return _simple_atom(rng, x) * _simple_atom(rng, x) * _poly_term(rng, x, 1)
    inner = _poly_term(rng, x, 2)
    outer = rng.choice([sp.sin, sp.cos, sp.exp])
    chain_part = outer(inner)
    if combo == "product_chain":
        return _poly_term(rng, x, 1) * chain_part
    denominator = _poly_term(rng, x, 1) + rng.randint(1, 5)
    return chain_part / denominator


def generate_two_var_expr(rng: random.Random, level: int) -> sp.Expr:
    level = max(MAX_LEVEL_SINGLE_VAR + 1, min(MAX_LEVEL_TWO_VAR, level))
    if level == 11:
        return _poly_term_nonconstant(rng, x, 2) + _poly_term_nonconstant(rng, y, 2)
    if level == 12:
        return _poly_term_nonconstant(rng, x, 2) + _simple_atom(rng, y)
    if level == 13:
        return _poly_term_nonconstant(rng, x, 2) * _simple_atom(rng, y)
    if level == 14:
        numerator = _poly_term_nonconstant(rng, x, 2)
        denominator = _poly_term_nonconstant(rng, y, 1) + rng.randint(1, 5)
        return numerator / denominator
    if level == 15:
        outer = rng.choice([sp.sin, sp.cos, sp.exp])
        a = _nonzero_coeff(rng, -5, 5)
        return outer(a * x * y)
    # level 16: combined
    outer = rng.choice([sp.sin, sp.cos])
    a = _nonzero_coeff(rng, -3, 3)
    return _poly_term_nonconstant(rng, x, 1) * outer(a * x * y)


# ---- single-variable integrand generation (integrals -- must verify the
#      result is actually elementary-integrable, since not every product/
#      quotient has a closed-form antiderivative) ----

_NON_ELEMENTARY_MARKERS = (
    "Si", "Ci", "erf", "erfi", "li", "Ei", "Integral", "uppergamma", "lowergamma",
)


def _is_elementary_antiderivative(antideriv: sp.Expr) -> bool:
    s = str(antideriv)
    return not any(marker in s for marker in _NON_ELEMENTARY_MARKERS)


def _build_integrand_candidate(rng: random.Random, level: int) -> sp.Expr:
    if level == 1:
        return _poly_term(rng, x, 3)
    if level == 2:
        return _poly_term(rng, x, 2) + _poly_term(rng, x, 2)
    if level == 3:
        return sum(_poly_term(rng, x, 3) for _ in range(rng.randint(2, 3)))
    if level == 4:
        return _nonzero_coeff(rng) * _trig_atom(rng, x)
    if level == 5:
        return _nonzero_coeff(rng) * _exp_atom(rng, x)
    if level == 6:
        return _poly_term(rng, x, 2) + _simple_atom(rng, x)
    if level == 7:
        return _poly_term(rng, x, rng.randint(1, 2)) * _trig_atom(rng, x)
    if level == 8:
        return _poly_term(rng, x, rng.randint(1, 2)) * _exp_atom(rng, x)
    # level 9: u-substitution pattern, CONSTRUCTED (not just random-then-
    # checked) so it's guaranteed integrable: integrand = g'(x) * f(g(x))
    # for f in {sin, cos, exp}, since that's exactly the chain rule run
    # backwards.
    a = rng.randint(1, 3)
    b = rng.randint(-3, 3)
    inner = a * x**2 + b * x
    inner_deriv = sp.diff(inner, x)
    outer_kind = rng.choice(["sin", "cos", "exp"])
    if outer_kind == "sin":
        return inner_deriv * sp.cos(inner)   # d/dx sin(inner) = inner_deriv*cos(inner)
    if outer_kind == "cos":
        return -inner_deriv * sp.sin(inner)  # d/dx cos(inner) = -inner_deriv*sin(inner)
    return inner_deriv * sp.exp(inner)       # d/dx exp(inner) = inner_deriv*exp(inner)


def generate_single_var_integrand(rng: random.Random, level: int, max_attempts: int = 20) -> sp.Expr:
    """
    Builds an integrand at the given level, verifying at generation time
    that sympy can actually produce an elementary antiderivative --
    retrying with fresh random parameters at the SAME level if not, and
    falling back to a guaranteed-safe low-level integrand if all retries
    fail (should be rare; levels 1-6 and 9 are inherently always
    integrable, only 7-8 ever need a retry).
    """
    level = max(1, min(MAX_LEVEL_INTEGRAL, level))
    for _ in range(max_attempts):
        candidate = _build_integrand_candidate(rng, level)
        try:
            antideriv = sp.integrate(candidate, x)
        except Exception:
            continue
        if _is_elementary_antiderivative(antideriv):
            return candidate
    return _poly_term(rng, x, 2)  # safe fallback -- always integrable
