"""
TODO: stub only. Once app/models/leaderboard_entry.py + a real DB session
(app/db/session.py) exist, replace the in-memory list below with real
queries: top N scores for a given map_hash, a user's rank, etc.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_FAKE_ENTRIES: list[dict] = []  # placeholder until DB models are wired up


class SubmitScoreRequest(BaseModel):
    map_hash: str
    username: str
    score: int
    accuracy: float
    max_combo: int


@router.post("/submit")
def submit_score(req: SubmitScoreRequest):
    _FAKE_ENTRIES.append(req.model_dump())
    return {"ok": True}


@router.get("/{map_hash}")
def get_leaderboard(map_hash: str, limit: int = 50):
    entries = [e for e in _FAKE_ENTRIES if e["map_hash"] == map_hash]
    entries.sort(key=lambda e: e["score"], reverse=True)
    return {"map_hash": map_hash, "entries": entries[:limit]}
