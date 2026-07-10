"""
In-memory mastery store, keyed by (user_id, drill_id).

This is the missing link between the algorithm that already existed
(engine/mastery.py's update function, engine/difficulty.py's settings
calculator) and the live API -- without persistent state somewhere,
there's nothing for the algorithm to update between requests.

TODO: swap this dict for real DB-backed storage (app/models/, app/db/)
before this needs to survive a server restart or support concurrent users
at scale. Fine for local single-player prototyping in the meantime --
defaults to a single "local" user if the frontend doesn't send one.
"""

from __future__ import annotations

from collections import deque

DEFAULT_USER = "local"
ROLLING_WINDOW_SIZE = 10  # how many recent attempts define "recent accuracy" for a drill

# {user_id: {drill_id: mastery_float}}
_MASTERY: dict[str, dict[str, float]] = {}

# {user_id: {drill_id: attempt_count}} -- used to derive "first exposure"
_ATTEMPT_COUNTS: dict[str, dict[str, int]] = {}

# {user_id: {drill_id: deque[bool]}} -- last ROLLING_WINDOW_SIZE correct/incorrect
# results, used to accelerate mastery progression when recent accuracy is high
# (see engine/mastery.py's accuracy_speed_multiplier).
_ROLLING_RESULTS: dict[str, dict[str, deque]] = {}


def get_mastery(drill_id: str, user_id: str = DEFAULT_USER) -> float:
    return _MASTERY.get(user_id, {}).get(drill_id, 0.0)


def is_first_exposure(drill_id: str, user_id: str = DEFAULT_USER) -> bool:
    return _ATTEMPT_COUNTS.get(user_id, {}).get(drill_id, 0) == 0


def get_rolling_accuracy(drill_id: str, user_id: str = DEFAULT_USER) -> float:
    """Fraction correct over the last ROLLING_WINDOW_SIZE attempts on this
    drill (0.0 if there's no history yet -- deliberately neutral/low so a
    brand new drill doesn't get an unearned speed boost)."""
    window = _ROLLING_RESULTS.get(user_id, {}).get(drill_id)
    if not window:
        return 0.0
    return sum(window) / len(window)


def record_attempt(drill_id: str, new_mastery: float, user_id: str = DEFAULT_USER, correct: bool | None = None) -> None:
    _MASTERY.setdefault(user_id, {})[drill_id] = new_mastery
    _ATTEMPT_COUNTS.setdefault(user_id, {})
    _ATTEMPT_COUNTS[user_id][drill_id] = _ATTEMPT_COUNTS[user_id].get(drill_id, 0) + 1

    if correct is not None:
        user_windows = _ROLLING_RESULTS.setdefault(user_id, {})
        window = user_windows.setdefault(drill_id, deque(maxlen=ROLLING_WINDOW_SIZE))
        window.append(correct)


def get_all_mastery(user_id: str = DEFAULT_USER) -> dict[str, float]:
    return dict(_MASTERY.get(user_id, {}))


def reset(user_id: str = DEFAULT_USER) -> None:
    """Mostly useful for tests / a 'reset my progress' button."""
    _MASTERY.pop(user_id, None)
    _ATTEMPT_COUNTS.pop(user_id, None)
    _ROLLING_RESULTS.pop(user_id, None)
