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

Progression speed also responds to the CURRENT session's combo and rolling
accuracy: a high combo or high accuracy accelerates how fast mastery (and
therefore difficulty/level) climbs, so a player doing well blows through
easy content quickly, while someone still finding their footing progresses
more gradually. combo and high accuracy are OR'd together (whichever gives
the bigger speed boost wins) -- a long combo alone is enough to accelerate,
same as a high accuracy alone, matching the intent that either signal
should speed things up.
"""

from __future__ import annotations

K_FACTOR = 0.08  # how much a single attempt can move the mastery estimate


def combo_speed_multiplier(combo: int) -> float:
    """Up to 3x acceleration at combo 50+, scaling smoothly from there."""
    return 1.0 + min(max(combo, 0), 50) / 25.0


def accuracy_speed_multiplier(rolling_accuracy: float) -> float:
    """A sustained ~95%+ accuracy accelerates progression a lot; ~85-95%
    (e.g. "fairly high," per the 90% example) accelerates it some; below
    that, no bonus -- baseline pace."""
    if rolling_accuracy >= 0.95:
        return 1.5
    if rolling_accuracy >= 0.85:
        return 1.2
    return 1.0


def update_mastery(
    current_mastery: float,
    problem_difficulty: float,
    correct: bool,
    used_hint: bool,
    time_taken_seconds: float,
    time_limit_seconds: float,
    combo: int = 0,
    rolling_accuracy: float = 0.0,
) -> float:
    """
    Returns the new mastery value after one attempt.

    Correct + fast + no hints on a hard problem -> big upward move.
    Wrong, or correct-but-needed-hints/ran-out-of-time -> downward or flat move.
    A high combo or high recent accuracy multiplies whatever move this
    attempt would otherwise produce (see combo_speed_multiplier /
    accuracy_speed_multiplier above) -- it doesn't change the SIGN of the
    move, just how big a correct answer's upward move is, or how sharp a
    wrong answer's downward move is.
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
    speed_multiplier = max(combo_speed_multiplier(combo), accuracy_speed_multiplier(rolling_accuracy))
    delta = K_FACTOR * (performance - expected) * (0.5 + problem_difficulty) * speed_multiplier

    return max(0.0, min(1.0, current_mastery + delta))


def is_weak_concept(mastery: float, threshold: float = 0.4) -> bool:
    """Used by the warm-up mechanic to decide which concepts need more reps."""
    return mastery < threshold
