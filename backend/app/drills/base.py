"""
Base interface every drill (addition, derivatives, RREF, etc.) implements.

A Drill is a *generator*, not a fixed question bank. Given a difficulty
level (0.0 - 1.0, or discrete tiers -- see engine/difficulty.py), it can
produce an unlimited number of unique problems, check a submitted answer,
and reveal hints progressively.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Problem:
    """A single generated problem instance."""

    drill_id: str                      # e.g. "addition", "derivatives.basic"
    prompt: str                        # human-readable question, e.g. "d/dx (3x^2 + 5x)"
    answer: str                        # canonical answer string (for display / hashing)
    difficulty: float                  # 0.0 (easiest) - 1.0 (hardest), as generated
    seed: dict[str, Any] = field(default_factory=dict)   # raw params, for hint derivation
    hints: list[str] = field(default_factory=list)       # pre-computed, ordered, revealed one at a time


@dataclass
class CheckResult:
    correct: bool
    normalized_submitted: str
    normalized_answer: str
    feedback: str | None = None


class Drill(ABC):
    """Subclass this for every drill family."""

    #: unique slug, must match the filename in content/builtin-drills/
    id: str

    @abstractmethod
    def generate(self, difficulty: float, rng_seed: int | None = None) -> Problem:
        """Produce one new Problem at the given difficulty (0.0-1.0)."""
        raise NotImplementedError

    @abstractmethod
    def check(self, problem: Problem, submitted: str) -> CheckResult:
        """Grade a submitted answer against the problem's canonical answer."""
        raise NotImplementedError

    def hint(self, problem: Problem, level: int) -> str:
        """
        Return the hint text for the given hint level (0-indexed).
        Default implementation just pulls from problem.hints; override for
        anything dynamic (e.g. hints that depend on the user's wrong answer).
        """
        if 0 <= level < len(problem.hints):
            return problem.hints[level]
        return "No further hints available."
