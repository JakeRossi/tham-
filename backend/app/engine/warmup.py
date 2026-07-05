"""
The warm-up mechanic: fire 20 problems spread across all drills in the
current map, then keep drilling any concept the user did badly on until
they clear a threshold -- so a session always ends with a real read on
where the user's weak points are, without them having to think about it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.drills.base import Drill
from app.engine.mastery import is_weak_concept, update_mastery
from app.engine.scheduler import get_next_problem

INITIAL_ROUND_SIZE = 20
EXTENSION_BATCH_SIZE = 5
MAX_EXTENSION_ROUNDS = 4  # safety cap so a warm-up can't run forever


@dataclass
class WarmupState:
    concept_mastery: dict[str, float] = field(default_factory=dict)
    concept_attempts: dict[str, int] = field(default_factory=dict)
    round_number: int = 0
    complete: bool = False


class WarmupSession:
    """
    Usage:
        session = WarmupSession(drills=[AdditionDrill(), DerivativesDrill(), ...])
        problem = session.next_problem()
        ... user answers ...
        session.record_attempt(problem, correct=True, used_hint=False, time_taken=4.2, time_limit=20)
        # repeat until session.state.complete
    """

    def __init__(self, drills: list[Drill], rng_seed: int | None = None):
        self.drills = {d.id: d for d in drills}
        self.state = WarmupState()
        self._queue: list[str] = []
        # Gives this session its own private shuffle-bag namespace (see
        # engine/scheduler.py) so repeated problems from the same drill
        # within one warm-up don't collide with the drill's regular
        # practice-mode bags, and so each drill still cycles through
        # unique problems rather than the old bug of reusing one fixed
        # rng_seed for every draw (which generated the SAME problem
        # every time).
        self._scheduler_user_id = f"warmup-{uuid.uuid4()}"
        self._build_initial_queue()

    def _build_initial_queue(self) -> None:
        # Spread INITIAL_ROUND_SIZE problems as evenly as possible across drills.
        n = len(self.drills)
        base = INITIAL_ROUND_SIZE // n
        remainder = INITIAL_ROUND_SIZE % n
        for i, drill_id in enumerate(self.drills):
            count = base + (1 if i < remainder else 0)
            self._queue.extend([drill_id] * count)

    def next_problem(self):
        if not self._queue:
            self._maybe_extend_or_finish()
        if self.state.complete or not self._queue:
            return None
        drill_id = self._queue.pop(0)
        drill = self.drills[drill_id]
        current_mastery = self.state.concept_mastery.get(drill_id, 0.0)
        return get_next_problem(drill, max(0.1, current_mastery), self._scheduler_user_id)

    def record_attempt(
        self,
        drill_id: str,
        correct: bool,
        used_hint: bool,
        time_taken_seconds: float,
        time_limit_seconds: float,
    ) -> None:
        current = self.state.concept_mastery.get(drill_id, 0.0)
        updated = update_mastery(
            current_mastery=current,
            problem_difficulty=max(0.1, current),
            correct=correct,
            used_hint=used_hint,
            time_taken_seconds=time_taken_seconds,
            time_limit_seconds=time_limit_seconds,
        )
        self.state.concept_mastery[drill_id] = updated
        self.state.concept_attempts[drill_id] = self.state.concept_attempts.get(drill_id, 0) + 1

    def _maybe_extend_or_finish(self) -> None:
        self.state.round_number += 1
        weak_concepts = [
            drill_id
            for drill_id, mastery in self.state.concept_mastery.items()
            if is_weak_concept(mastery)
        ]
        if not weak_concepts or self.state.round_number > MAX_EXTENSION_ROUNDS:
            self.state.complete = True
            return
        for drill_id in weak_concepts:
            self._queue.extend([drill_id] * EXTENSION_BATCH_SIZE)
