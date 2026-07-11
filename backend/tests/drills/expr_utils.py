"""
Shared helpers for any drill that shows algebraic expressions with a
variable coefficient (derivatives, integrals, algebraic manipulation,
ODEs). Two problems, one fix each:

1. Display: sympy's default string form of "6*x" reads worse than the
   textbook-standard "6x". pretty_str() cleans that up for anything shown
   to the user (prompts, hints).
2. Checking: once prompts/answers display as "6x", the checker has to
   accept a user typing either "6x" or "6*x" as the same thing.
   parse_user_expr() uses sympy's implicit-multiplication parser instead
   of plain sympify so both forms parse to the identical expression.
"""

from __future__ import annotations

import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)


def parse_user_expr(s: str, local_dict: dict | None = None) -> sp.Expr:
    """
    Parses a math expression string accepting implicit multiplication
    ('6x', '2x(x+1)') and '^' as power, on top of normal syntax
    ('6*x', '2**x'). Used for BOTH the user's submitted answer and the
    internally-stored canonical answer, so a mismatch in notation never
    causes a false "incorrect."

    'e' always resolves to Euler's number (matching how the LaTeX-rendered
    prompts/answers actually show it, e.g. "e^{2x}") -- without this,
    typing "e^(2x)" parses 'e' as an unrelated free symbol instead of
    sympy's E, so it would never match an exp(2x)-based canonical answer.
    'pi' already resolves correctly via sympy's own default parser
    namespace, so it doesn't need the same explicit treatment.
    """
    merged_locals = {"e": sp.E, **(local_dict or {})}
    return parse_expr(s, local_dict=merged_locals, transformations=_TRANSFORMATIONS)


# Only single-letter variables (x, y) get the implicit-multiplication
# display treatment -- deliberately NOT touching function names like
# exp(...), sin(...), sqrt(...), so "3*exp(2*x)" only loses the *inside*
# the parens ("3*exp(2x)"), never becomes the nonsensical "3exp(2x)".
_IMPLICIT_MULT_PATTERNS = [
    (re.compile(r"(?<=\d)\*(?=[xy]\b)"), ""),      # 6*x     -> 6x
    (re.compile(r"(?<=[xy])\*(?=[xy]\b)"), ""),    # x*y     -> xy
    (re.compile(r"(?<=\d)\*(?=\()"), ""),          # 6*(x+1) -> 6(x+1)
    (re.compile(r"(?<=\))\*(?=[xy]\b)"), ""),      # (x+1)*x -> (x+1)x
    (re.compile(r"(?<=\))\*(?=\()"), ""),          # (x+1)*(x-1) -> (x+1)(x-1)
]


def pretty_str(expr: sp.Expr) -> str:
    """Renders a sympy expression with implicit multiplication for display."""
    s = sp.sstr(expr)
    for pattern, repl in _IMPLICIT_MULT_PATTERNS:
        s = pattern.sub(repl, s)
    return s
