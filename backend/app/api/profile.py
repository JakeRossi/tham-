"""
Player profile endpoints -- osu-profile-inspired stats (pp, play count,
accuracy, max combo, monthly activity, per-drill breakdown), and the
session-end pp recording call. See app/engine/profile_store.py and
app/engine/pp.py for the actual mechanics.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.engine.profile_store import (
    get_profile,
    lifetime_accuracy,
    questions_this_month,
    record_session,
)
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


class RecordSessionRequest(BaseModel):
    """
    Called once a play session on a drill wraps up (session ends, warm-up
    completes, etc.) -- analogous to finishing one osu! beatmap play.
    tier_counts should be the session's judgement tally, e.g.
    {"300": 8, "100": 2, "50": 0, "miss": 1}.
    """
    drill_id: str
    tier_counts: dict[str, int]
    max_combo: int
    mastery_after: float | None = None
    user_id: str = DEFAULT_USER


@router.post("/record-session")
def record_session_endpoint(req: RecordSessionRequest):
    profile, run_pp, is_new_best = record_session(
        user_id=req.user_id,
        drill_id=req.drill_id,
        tier_counts=req.tier_counts,
        max_combo=req.max_combo,
        mastery_after=req.mastery_after,
    )
    return {
        "run_pp": run_pp,
        "is_new_best": is_new_best,
        "total_pp": profile["total_pp"],
        "best_pp_for_drill": profile["per_drill_stats"].get(req.drill_id, {}).get("best_pp", 0.0),
    }
