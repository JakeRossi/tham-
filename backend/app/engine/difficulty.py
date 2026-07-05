"""
Translates a user's mastery level for a concept into concrete gameplay
parameters: how hard the next problem should be, how much time they get,
and how many hints are available before they "fail" the problem.

This is intentionally simple to start -- tune the curves once you have
real usage data.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DifficultySettings:
    problem_difficulty: float   # 0.0-1.0, passed straight into Drill.generate()
    time_limit_seconds: float
    max_hints: int
    hint_delay_seconds: float    # how long to wait before first hint becomes available


def settings_for_mastery(mastery: float, is_first_exposure: bool) -> DifficultySettings:
    """
    mastery: 0.0 (never seen it) - 1.0 (fully mastered), from engine/mastery.py
    is_first_exposure: True if the user is learning this concept for the first time
                        (as opposed to drilling something they've seen before)

    First-time learners get more hints, more time, easier problems, regardless
    of an otherwise-computed mastery score (mastery may be 0 either way, but the
    *reason* it's 0 matters for how much support to give).
    """
    if is_first_exposure:
        return DifficultySettings(
            problem_difficulty=0.15,
            time_limit_seconds=90,
            max_hints=3,
            hint_delay_seconds=10,
        )

    # Returning learner: scale down support as mastery climbs.
    problem_difficulty = min(1.0, 0.2 + mastery * 0.8)
    max_hints = max(0, 3 - round(mastery * 3))          # 3 hints at mastery=0, 0 at mastery=1
    time_limit = max(15, 60 - mastery * 40)              # 60s -> 20s as mastery climbs
    hint_delay = max(3, 20 - mastery * 15)                # hints become available sooner if struggling

    return DifficultySettings(
        problem_difficulty=problem_difficulty,
        time_limit_seconds=time_limit,
        max_hints=max_hints,
        hint_delay_seconds=hint_delay,
    )
