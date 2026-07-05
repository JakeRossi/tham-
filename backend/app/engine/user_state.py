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

DEFAULT_USER = "local"

# {user_id: {drill_id: mastery_float}}
_MASTERY: dict[str, dict[str, float]] = {}

# {user_id: {drill_id: attempt_count}} -- used to derive "first exposure"
_ATTEMPT_COUNTS: dict[str, dict[str, int]] = {}


def get_mastery(drill_id: str, user_id: str = DEFAULT_USER) -> float:
    return _MASTERY.get(user_id, {}).get(drill_id, 0.0)


def is_first_exposure(drill_id: str, user_id: str = DEFAULT_USER) -> bool:
    return _ATTEMPT_COUNTS.get(user_id, {}).get(drill_id, 0) == 0


def record_attempt(drill_id: str, new_mastery: float, user_id: str = DEFAULT_USER) -> None:
    _MASTERY.setdefault(user_id, {})[drill_id] = new_mastery
    _ATTEMPT_COUNTS.setdefault(user_id, {})
    _ATTEMPT_COUNTS[user_id][drill_id] = _ATTEMPT_COUNTS[user_id].get(drill_id, 0) + 1


def get_all_mastery(user_id: str = DEFAULT_USER) -> dict[str, float]:
    return dict(_MASTERY.get(user_id, {}))


def reset(user_id: str = DEFAULT_USER) -> None:
    """Mostly useful for tests / a 'reset my progress' button."""
    _MASTERY.pop(user_id, None)
    _ATTEMPT_COUNTS.pop(user_id, None)
