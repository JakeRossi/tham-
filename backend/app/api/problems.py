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
from app.engine.scheduler import get_next_problem as get_next_scheduled_problem
from app.engine.user_state import DEFAULT_USER, get_mastery, get_rolling_accuracy, is_first_exposure, record_attempt

router = APIRouter()


@router.get("/next/{drill_id}")
def next_problem(drill_id: str, user_id: str = DEFAULT_USER, forced_difficulty: float | None = None):
    """
    forced_difficulty (0.0-1.0), when provided, overrides the
    mastery-driven problem difficulty -- this is the hook "in-game mods"
    use (e.g. "start from a specific level" or "only 2-digit numbers,"
    which the frontend translates into a specific difficulty value; see
    docs/DRILL_AUTHORING.md or the frontend's DIGIT_MOD_RANGES). Hint
    count/timing are still driven by mastery either way -- mods customize
    CONTENT difficulty, not the adaptive support system.
    """
    try:
        drill = get_drill(drill_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    mastery = get_mastery(drill_id, user_id)
    first_exposure = is_first_exposure(drill_id, user_id)
    settings = settings_for_mastery(mastery, first_exposure)

    problem_difficulty = settings.problem_difficulty
    if forced_difficulty is not None:
        problem_difficulty = max(0.0, min(1.0, forced_difficulty))

    # Shuffle-bag scheduling: won't repeat a problem until every problem in
    # the pool for this drill/difficulty tier has been shown once.
    problem = get_next_scheduled_problem(drill, problem_difficulty, user_id)
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
    combo: int = 0          # the session combo count GOING INTO this attempt -- accelerates progression
    time_taken_seconds: float = 0.0
    time_limit_seconds: float = 20.0
    user_id: str = DEFAULT_USER


@router.post("/submit")
def submit_answer(req: SubmitRequest):
    """Grades the answer and updates mastery. Does NOT touch pp/profile --
    pp is recorded once per finished SESSION via POST /api/profile/record-session,
    matching how osu! awards pp per completed beatmap play, not per note."""
    try:
        drill = get_drill(req.drill_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    problem = Problem(drill_id=req.drill_id, prompt=req.prompt, answer=req.answer, difficulty=0.0)
    result = drill.check(problem, req.submitted)

    current_mastery = get_mastery(req.drill_id, req.user_id)
    rolling_accuracy = get_rolling_accuracy(req.drill_id, req.user_id)
    new_mastery = update_mastery(
        current_mastery=current_mastery,
        problem_difficulty=max(0.1, current_mastery),
        correct=result.correct,
        used_hint=req.used_hint,
        time_taken_seconds=req.time_taken_seconds,
        time_limit_seconds=req.time_limit_seconds,
        combo=req.combo,
        rolling_accuracy=rolling_accuracy,
    )
    record_attempt(req.drill_id, new_mastery, req.user_id, correct=result.correct)

    return {
        "correct": result.correct,
        "normalized_submitted": result.normalized_submitted,
        "normalized_answer": result.normalized_answer,
        "feedback": result.feedback,
        "new_mastery": new_mastery,
    }


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
