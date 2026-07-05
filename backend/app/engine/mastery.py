"""
Per-user, per-concept mastery tracking.

Starts with a simple Elo-style update (cheap, well-understood, easy to
reason about) rather than full Bayesian Knowledge Tracing. Swap this out
for BKT/IRT later if the simple version isn't discriminating well enough --
the interface (update / get) is what the rest of the app depends on, so the
internals can change freely.

Mastery is stored as a float in [0.0, 1.0], where:
  0.0 = never attempted / total failure
  1.0 = consistently fast + correct at high difficulty
"""

from __future__ import annotations

K_FACTOR = 0.08  # how much a single attempt can move the mastery estimate


def update_mastery(
    current_mastery: float,
    problem_difficulty: float,
    correct: bool,
    used_hint: bool,
    time_taken_seconds: float,
    time_limit_seconds: float,
) -> float:
    """
    Returns the new mastery value after one attempt.

    Correct + fast + no hints on a hard problem -> big upward move.
    Wrong, or correct-but-needed-hints/ran-out-of-time -> downward or flat move.
    """
    # "Performance" for this single attempt, roughly analogous to a game score
    # against an opponent of strength == problem_difficulty.
    if correct:
        speed_bonus = max(0.0, 1.0 - (time_taken_seconds / max(time_limit_seconds, 1)))
        hint_penalty = 0.3 if used_hint else 0.0
        performance = min(1.0, 0.7 + 0.3 * speed_bonus - hint_penalty)
    else:
        performance = 0.0

    # Elo-like expected score based on how hard the problem was relative to current mastery.
    expected = current_mastery
    delta = K_FACTOR * (performance - expected) * (0.5 + problem_difficulty)

    return max(0.0, min(1.0, current_mastery + delta))


def is_weak_concept(mastery: float, threshold: float = 0.4) -> bool:
    """Used by the warm-up mechanic to decide which concepts need more reps."""
    return mastery < threshold
