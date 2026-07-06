"""
Problem generation + submission, now driven by the mastery/difficulty
algorithm instead of a caller-supplied difficulty number.

Flow:
  GET  /next/{drill_id}     -> looks up current mastery, computes
                                DifficultySettings (problem difficulty,
                                time limit, hint budget/delay), generates
                                a problem at that difficulty, and returns
                                only as many hints as the settings allow.
  POST /submit               -> grades the answer AND feeds the outcome
                                back into the mastery update, so the next
                                /next call reflects it.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.drills.base import Problem
from app.drills.registry import get_drill
from app.engine.difficulty import settings_for_mastery
from app.engine.mastery import update_mastery
from app.engine.pp import compute_pp
from app.engine.profile_store import get_lifetime_play_count, record_attempt as record_profile_attempt
from app.engine.scheduler import get_next_problem as get_next_scheduled_problem
from app.engine.user_state import DEFAULT_USER, get_mastery, is_first_exposure, record_attempt

router = APIRouter()


@router.get("/next/{drill_id}")
def next_problem(drill_id: str, user_id: str = DEFAULT_USER):
    try:
        drill = get_drill(drill_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    mastery = get_mastery(drill_id, user_id)
    first_exposure = is_first_exposure(drill_id, user_id)
    settings = settings_for_mastery(mastery, first_exposure)

    # Shuffle-bag scheduling: won't repeat a problem until every problem in
    # the pool for this drill/difficulty tier has been shown once.
    problem = get_next_scheduled_problem(drill, settings.problem_difficulty, user_id)
    visible_hints = problem.hints[: settings.max_hints]

    return {
        "drill_id": problem.drill_id,
        "prompt": problem.prompt,
        "answer": problem.answer,   # fine for local/dev; see docs/ARCHITECTURE.md
        "difficulty": problem.difficulty,
        "hints": visible_hints,
        "seed": problem.seed,  # exposes e.g. matrix shape for rref's fill-in-the-blank UI
        "max_hints": settings.max_hints,
        "time_limit_seconds": settings.time_limit_seconds,
        "hint_delay_seconds": settings.hint_delay_seconds,
        "current_mastery": mastery,
        "is_first_exposure": first_exposure,
    }


class SubmitRequest(BaseModel):
    drill_id: str
    prompt: str
    answer: str            # canonical answer, echoed back from /next
    submitted: str
    used_hint: bool = False
    time_taken_seconds: float = 0.0
    time_limit_seconds: float = 20.0
    user_id: str = DEFAULT_USER


@router.post("/submit")
def submit_answer(req: SubmitRequest):
    """Grades the answer and updates mastery. Does NOT touch pp/profile --
    see /record-pp below, called separately once the frontend knows the
    combo outcome (which depends on this call's result)."""
    try:
        drill = get_drill(req.drill_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    problem = Problem(drill_id=req.drill_id, prompt=req.prompt, answer=req.answer, difficulty=0.0)
    result = drill.check(problem, req.submitted)

    current_mastery = get_mastery(req.drill_id, req.user_id)
    new_mastery = update_mastery(
        current_mastery=current_mastery,
        problem_difficulty=max(0.1, current_mastery),
        correct=result.correct,
        used_hint=req.used_hint,
        time_taken_seconds=req.time_taken_seconds,
        time_limit_seconds=req.time_limit_seconds,
    )
    record_attempt(req.drill_id, new_mastery, req.user_id)

    return {
        "correct": result.correct,
        "normalized_submitted": result.normalized_submitted,
        "normalized_answer": result.normalized_answer,
        "feedback": result.feedback,
        "new_mastery": new_mastery,
    }


class RecordPpRequest(BaseModel):
    """
    Called right after /submit, once the frontend has resolved its local
    judgement/combo logic from the submit result (see frontend
    judgementForHints()). Kept as a separate call rather than folded into
    /submit because combo_after can only be known by the CALLER after it
    has seen whether the answer was correct -- it can't be computed inside
    the same request that determines correctness.
    """
    drill_id: str
    correct: bool
    hints_revealed: int = 0
    combo_after: int = 0
    user_id: str = DEFAULT_USER


@router.post("/record-pp")
def record_pp(req: RecordPpRequest):
    mastery = get_mastery(req.drill_id, req.user_id)  # already updated by /submit
    lifetime_plays_before = get_lifetime_play_count(req.user_id)
    pp_earned, tier = compute_pp(
        drill_id=req.drill_id,
        hints_revealed=req.hints_revealed,
        correct=req.correct,
        combo_after=req.combo_after,
        lifetime_play_count_before_this_attempt=lifetime_plays_before,
    )
    profile = record_profile_attempt(
        user_id=req.user_id,
        drill_id=req.drill_id,
        tier=tier,
        pp_earned=pp_earned,
        combo_after=req.combo_after,
        mastery_after=mastery,
    )
    return {"tier": tier, "pp_earned": pp_earned, "total_pp": profile["total_pp"]}


class GenerateRequest(BaseModel):
    """Kept for direct/manual testing without going through the mastery
    algorithm -- e.g. previewing a drill at a specific difficulty."""
    drill_id: str
    difficulty: float = 0.3
    rng_seed: int | None = None


@router.post("/generate")
def generate_problem(req: GenerateRequest):
    try:
        drill = get_drill(req.drill_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    problem = drill.generate(req.difficulty, rng_seed=req.rng_seed)
    return {
        "drill_id": problem.drill_id,
        "prompt": problem.prompt,
        "answer": problem.answer,
        "difficulty": problem.difficulty,
        "hints": problem.hints,
    }
