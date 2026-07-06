"""
Player profile endpoint -- osu-profile-inspired stats (pp, play count,
accuracy, max combo, monthly activity, per-drill breakdown). See
app/engine/profile_store.py for the storage layer.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.engine.profile_store import get_profile, lifetime_accuracy, questions_this_month
from app.engine.user_state import DEFAULT_USER

router = APIRouter()


@router.get("/{user_id}")
def get_player_profile(user_id: str = DEFAULT_USER):
    profile = get_profile(user_id)
    return {
        **profile,
        "lifetime_accuracy": lifetime_accuracy(profile),
        "questions_this_month": questions_this_month(profile),
    }
