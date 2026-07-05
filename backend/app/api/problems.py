from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.drills.registry import get_drill

router = APIRouter()


class GenerateRequest(BaseModel):
    drill_id: str
    difficulty: float = 0.3
    rng_seed: int | None = None


class SubmitRequest(BaseModel):
    drill_id: str
    prompt: str
    answer: str          # canonical answer, echoed back by the client from the generate response
    submitted: str


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
        "answer": problem.answer,     # NOTE: fine for local/dev; see docs/ARCHITECTURE.md
        "difficulty": problem.difficulty,
        "hints": problem.hints,
    }


@router.post("/submit")
def submit_answer(req: SubmitRequest):
    try:
        drill = get_drill(req.drill_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Reconstruct a minimal Problem object just for checking.
    from app.drills.base import Problem
    problem = Problem(drill_id=req.drill_id, prompt=req.prompt, answer=req.answer, difficulty=0.0)
    result = drill.check(problem, req.submitted)
    return {
        "correct": result.correct,
        "normalized_submitted": result.normalized_submitted,
        "normalized_answer": result.normalized_answer,
        "feedback": result.feedback,
    }
