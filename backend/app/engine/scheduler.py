"""
No-repeat-until-exhausted question scheduling -- a "shuffle bag" (the same
technique Tetris uses for piece randomization): build a pool of N unique
problems for a given drill + difficulty tier, hand them out in random
order with no repeats, and only once every problem in the pool has been
shown does it reshuffle and start a new cycle. The item right at that
boundary CAN legally repeat (e.g. ...8, 3, 6, 2, 10, 7, 9, 4 | 1, 5, ...)
-- that's expected shuffle-bag behavior, not a bug.

Exact enumeration of "all possible non-repeating problems" (true n-choose-k
combinatorics) is only practical for the simplest, smallest-parameter-space
drills (e.g. addition's pool is bounded by (high-low+1)^2 integer pairs).
For anything with a much larger or effectively unbounded space (e.g. random
polynomial coefficients for derivatives), we approximate the pool by
sampling up to POOL_TARGET_SIZE distinct parameter sets. This is
practically indistinguishable from true exhaustive enumeration for the
purpose it serves here: not seeing the identical problem again too soon.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field

from app.drills.base import Drill, Problem

POOL_TARGET_SIZE = 50
MAX_GENERATION_ATTEMPTS = POOL_TARGET_SIZE * 6  # give up looking for more uniques after this many tries


def difficulty_bucket(difficulty: float) -> float:
    """
    Round to the nearest 0.1 so mastery's continuously-changing float
    doesn't spawn a brand new (size-1) pool on every single attempt --
    the shuffle bag needs a stable difficulty tier to build a pool against.
    """
    return round(difficulty, 1)


def _seed_key(seed: dict) -> str:
    return json.dumps(seed, sort_keys=True, default=str)


@dataclass
class ShuffleBag:
    drill: Drill
    difficulty: float
    pool: list[Problem] = field(default_factory=list)
    order: list[int] = field(default_factory=list)
    position: int = 0
    last_shown: dict[str, float] = field(default_factory=dict)  # seed_key -> unix timestamp
    cycles_completed: int = 0
    _rng: random.Random = field(default_factory=random.Random)

    def _build_pool(self) -> None:
        seen_keys: set[str] = set()
        attempts = 0
        gen_seed = 0
        while len(self.pool) < POOL_TARGET_SIZE and attempts < MAX_GENERATION_ATTEMPTS:
            problem = self.drill.generate(self.difficulty, rng_seed=gen_seed)
            key = _seed_key(problem.seed)
            if key not in seen_keys:
                seen_keys.add(key)
                self.pool.append(problem)
            gen_seed += 1
            attempts += 1
        # The pool may end up smaller than POOL_TARGET_SIZE if the drill's
        # parameter space at this difficulty is genuinely smaller than that
        # -- that's fine, it just means a shorter no-repeat cycle.

    def _reshuffle(self) -> None:
        self.order = list(range(len(self.pool)))
        self._rng.shuffle(self.order)
        self.position = 0
        self.cycles_completed += 1

    def next(self) -> Problem:
        if not self.pool:
            self._build_pool()
            self._reshuffle()
        elif self.position >= len(self.order):
            self._reshuffle()

        idx = self.order[self.position]
        self.position += 1
        problem = self.pool[idx]
        self.last_shown[_seed_key(problem.seed)] = time.time()
        return problem

    @property
    def pool_size(self) -> int:
        return len(self.pool)


# (user_id, drill_id, difficulty_bucket) -> ShuffleBag
_BAGS: dict[tuple[str, str, float], ShuffleBag] = {}


def get_next_problem(drill: Drill, difficulty: float, user_id: str) -> Problem:
    bucket = difficulty_bucket(difficulty)
    key = (user_id, drill.id, bucket)
    bag = _BAGS.get(key)
    if bag is None:
        bag = ShuffleBag(drill=drill, difficulty=bucket)
        _BAGS[key] = bag
    return bag.next()


def get_bag(drill_id: str, difficulty: float, user_id: str) -> ShuffleBag | None:
    """Mostly for tests/inspection -- look up a bag without creating one."""
    return _BAGS.get((user_id, drill_id, difficulty_bucket(difficulty)))


def reset(user_id: str | None = None) -> None:
    """Clear all bags, or just the ones for one user (mostly for tests)."""
    if user_id is None:
        _BAGS.clear()
    else:
        for key in [k for k in _BAGS if k[0] == user_id]:
            _BAGS.pop(key)
