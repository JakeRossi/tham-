"""
Warm-up + regular drill session endpoints.

Currently in-memory only (dict keyed by session_id) -- fine for local dev
and prototyping against the frontend. Swap for a real DB-backed store
(see app/models/) before this needs to survive a server restart or
support multiple backend instances.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.drills.registry import REGISTRY
from app.engine.warmup import WarmupSession

router = APIRouter()

_ACTIVE_SESSIONS: dict[str, WarmupSession] = {}


class StartWarmupRequest(BaseModel):
    drill_ids: list[str] | None = None   # None = use every registered drill
    rng_seed: int | None = None


class RecordAttemptRequest(BaseModel):
    session_id: str
    drill_id: str
    correct: bool
    used_hint: bool
    time_taken_seconds: float
    time_limit_seconds: float = 20.0


@router.post("/warmup/start")
def start_warmup(req: StartWarmupRequest):
    drill_ids = req.drill_ids or list(REGISTRY.keys())
    drills = [REGISTRY[d] for d in drill_ids if d in REGISTRY]
    if not drills:
        raise HTTPException(status_code=400, detail="No valid drill_ids provided.")

    session_id = str(uuid.uuid4())
    _ACTIVE_SESSIONS[session_id] = WarmupSession(drills, rng_seed=req.rng_seed)
    return {"session_id": session_id}


@router.get("/warmup/{session_id}/next")
def next_warmup_problem(session_id: str):
    session = _ACTIVE_SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id.")

    problem = session.next_problem()
    if problem is None:
        return {"complete": True, "mastery": session.state.concept_mastery}

    return {
        "complete": False,
        "drill_id": problem.drill_id,
        "prompt": problem.prompt,
        "answer": problem.answer,
        "hints": problem.hints,
    }


@router.post("/warmup/attempt")
def record_warmup_attempt(req: RecordAttemptRequest):
    session = _ACTIVE_SESSIONS.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id.")

    session.record_attempt(
        drill_id=req.drill_id,
        correct=req.correct,
        used_hint=req.used_hint,
        time_taken_seconds=req.time_taken_seconds,
        time_limit_seconds=req.time_limit_seconds,
    )
    return {"mastery": session.state.concept_mastery, "complete": session.state.complete}
