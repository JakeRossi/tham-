"""
Player profile endpoints. See app/engine/profile_store.py and
app/engine/pp.py's module docstrings for the mechanics.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.engine.profile_store import (
    get_profile,
    lifetime_accuracy,
    questions_this_month,
    record_question,
    record_session_end,
    record_session_start,
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


class SessionStartRequest(BaseModel):
    """Call once each time a drill is opened -- the real 'play count'
    metric, separate from how many questions get answered once open."""
    drill_id: str
    user_id: str = DEFAULT_USER


@router.post("/session-started")
def session_started(req: SessionStartRequest):
    profile = record_session_start(req.user_id, req.drill_id)
    return {"play_count": profile["play_count"]}


class RecordQuestionRequest(BaseModel):
    """Call right after grading each question -- awards pp immediately,
    same as osu! updating your score live during a play."""
    drill_id: str
    hints_revealed: int = 0
    correct: bool
    user_id: str = DEFAULT_USER


@router.post("/record-question")
def record_question_endpoint(req: RecordQuestionRequest):
    profile, pp_earned, tier, level = record_question(
        req.user_id, req.drill_id, req.hints_revealed, req.correct,
    )
    return {"pp_earned": pp_earned, "tier": tier, "level": level, "total_pp": profile["total_pp"]}


class SessionEndRequest(BaseModel):
    """Call once a session wraps up -- logs it for the profile screen's
    recent-sessions list. Does NOT affect total_pp (already accumulated
    per-question via /record-question)."""
    drill_id: str
    tier_counts: dict[str, int]
    max_combo: int
    pp_earned_this_session: float
    mastery_after: float | None = None
    user_id: str = DEFAULT_USER


@router.post("/session-ended")
def session_ended(req: SessionEndRequest):
    profile = record_session_end(
        user_id=req.user_id,
        drill_id=req.drill_id,
        tier_counts=req.tier_counts,
        max_combo=req.max_combo,
        pp_earned_this_session=req.pp_earned_this_session,
        mastery_after=req.mastery_after,
    )
    return {"total_pp": profile["total_pp"]}
