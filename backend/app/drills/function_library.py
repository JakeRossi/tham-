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

Integral level scheme (single variable), separate from the derivative
scheme above since not every derivative-level pattern has a guaranteed
elementary antiderivative -- see the comment above
generate_single_var_integrand for the full breakdown. Short version:
basic antiderivative table (1-2) -> u-substitution (3) -> integration by
parts (4) -> harder u-sub/IBP (5-6) -> cyclic integration by parts (7) ->
simple partial fractions (8) -> combined (9).
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
#
# Level ordering here deliberately follows a typical Calc 2 difficulty
# curve rather than "however complex the expression looks": basic
# antiderivative table first, then u-substitution (intermediate --
# running the chain rule backwards), then integration by parts
# (intermediate-hard -- running the product rule backwards), THEN into
# genuinely harder combined/cyclic/rational-function territory for the
# upper levels. An earlier version of this had u-substitution sitting
# near the very top of the scale where it didn't belong, with nothing
# meaningfully harder above integration by parts -- fixed here.
#
#   1: single term from the basic antiderivative table (poly, trig, or exp)
#   2: sum of 2-3 such terms
#   3: u-substitution -- g'(x) * f(g(x)), quadratic inner
#   4: integration by parts -- (degree-1 poly) * (trig or exp)
#   5: harder u-substitution -- cubic inner, or a trig-composed-with-trig pattern
#   6: harder integration by parts -- degree-2 poly * (trig or exp)
#   7: cyclic integration by parts -- exp(ax)*sin(bx) or exp(ax)*cos(bx),
#      the classic "integrate by parts twice, solve algebraically for the
#      integral" pattern
#   8: simple partial fractions -- 1/((x+a)(x+b)) for distinct integer roots
#   9 ("hardest"): combined -- u-substitution feeding into integration by
#      parts, or a scaled/shifted version of the cyclic IBP pattern

_NON_ELEMENTARY_MARKERS = (
    "Si", "Ci", "erf", "erfi", "li", "Ei", "Integral", "uppergamma", "lowergamma",
)


def _is_elementary_antiderivative(antideriv: sp.Expr) -> bool:
    s = str(antideriv)
    return not any(marker in s for marker in _NON_ELEMENTARY_MARKERS)


def _u_sub_pattern(rng: random.Random, inner_max_degree: int = 2) -> sp.Expr:
    """g'(x) * f(g(x)) for f in {sin, cos, exp} -- CONSTRUCTED (not
    random-then-checked) so it's guaranteed integrable, since that's
    exactly the chain rule run backwards."""
    if inner_max_degree >= 3 and rng.random() < 0.5:
        a = rng.randint(1, 2)
        inner = a * x**3 + rng.randint(-3, 3) * x
    else:
        a = rng.randint(1, 3)
        b = rng.randint(-3, 3)
        inner = a * x**2 + b * x
    inner_deriv = sp.diff(inner, x)
    outer_kind = rng.choice(["sin", "cos", "exp"])
    if outer_kind == "sin":
        return inner_deriv * sp.cos(inner)
    if outer_kind == "cos":
        return -inner_deriv * sp.sin(inner)
    return inner_deriv * sp.exp(inner)


def _cyclic_ibp_pattern(rng: random.Random) -> sp.Expr:
    """exp(ax)*sin(bx) or exp(ax)*cos(bx) -- the classic pattern where you
    integrate by parts twice and solve algebraically for the original
    integral. sympy handles this reliably."""
    a = rng.randint(1, 3)
    b = rng.randint(1, 3)
    trig = rng.choice([sp.sin, sp.cos])
    return sp.exp(a * x) * trig(b * x)


def _partial_fractions_pattern(rng: random.Random) -> sp.Expr:
    """1 / ((x+a)(x+b)) for distinct integer roots -- simple partial
    fractions, which sympy's integrate() handles reliably via apart()."""
    a = rng.randint(-6, 6)
    b = rng.randint(-6, 6)
    while b == a:
        b = rng.randint(-6, 6)
    return 1 / ((x + a) * (x + b))


def _poly_times_cyclic_pattern(rng: random.Random) -> sp.Expr:
    """x * exp(ax) * sin(bx) or x * exp(ax) * cos(bx) -- a polynomial
    multiplying a cyclic-IBP integrand, which needs repeated integration
    by parts (reduce the polynomial factor, THEN solve the remaining
    cyclic piece algebraically). Meaningfully harder than either technique
    alone, and unambiguously distinct from the plain u-substitution
    pattern used at levels 3/5 -- an earlier version of level 9 sometimes
    fell back to plain u-sub, which looked identical to those easier
    levels and defeated the point of it being "the hardest" tier."""
    a = rng.randint(1, 2)
    b = rng.randint(1, 2)
    trig = rng.choice([sp.sin, sp.cos])
    return _poly_term_nonconstant(rng, x, 1) * sp.exp(a * x) * trig(b * x)


def _build_integrand_candidate(rng: random.Random, level: int) -> sp.Expr:
    if level == 1:
        return rng.choice([
            lambda: _poly_term(rng, x, 3),
            lambda: _nonzero_coeff(rng) * _trig_atom(rng, x),
            lambda: _nonzero_coeff(rng) * _exp_atom(rng, x),
        ])()
    if level == 2:
        return sum(
            rng.choice([
                lambda: _poly_term(rng, x, 2),
                lambda: _nonzero_coeff(rng) * _trig_atom(rng, x),
                lambda: _nonzero_coeff(rng) * _exp_atom(rng, x),
            ])()
            for _ in range(rng.randint(2, 3))
        )
    if level == 3:
        return _u_sub_pattern(rng, inner_max_degree=2)
    if level == 4:
        return _poly_term(rng, x, 1) * rng.choice([lambda: _trig_atom(rng, x), lambda: _exp_atom(rng, x)])()
    if level == 5:
        return _u_sub_pattern(rng, inner_max_degree=3)
    if level == 6:
        return _poly_term(rng, x, 2) * rng.choice([lambda: _trig_atom(rng, x), lambda: _exp_atom(rng, x)])()
    if level == 7:
        return _cyclic_ibp_pattern(rng)
    if level == 8:
        return _partial_fractions_pattern(rng)
    # level 9 ("hardest"): polynomial x cyclic-IBP -- needs repeated
    # integration by parts, unambiguously harder than (and structurally
    # distinct from) the plain u-substitution used at levels 3/5.
    if rng.random() < 0.5:
        return _poly_times_cyclic_pattern(rng)
    return _nonzero_coeff(rng) * _cyclic_ibp_pattern(rng)


def generate_single_var_integrand(rng: random.Random, level: int, max_attempts: int = 20) -> sp.Expr:
    """
    Builds an integrand at the given level, verifying at generation time
    that sympy can actually produce an elementary antiderivative --
    retrying with fresh random parameters at the SAME level if not, and
    falling back to a guaranteed-safe low-level integrand if all retries
    fail (should be rare -- most levels are inherently always integrable
    by construction; only the polynomial-times-trig/exp levels and
    partial fractions ever realistically need a retry).
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
