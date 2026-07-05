import json

from app.drills.arithmetic import SqrtsDrill
from app.drills.calculus import DerivativesDrill
from app.engine.scheduler import ShuffleBag, get_next_problem, reset


def _key(problem):
    return json.dumps(problem.seed, sort_keys=True, default=str)


def test_no_repeats_within_a_single_cycle():
    reset()
    drill = DerivativesDrill()
    bag = ShuffleBag(drill=drill, difficulty=0.2)

    pool_size = None
    seen_in_cycle = []
    for _ in range(200):
        problem = bag.next()
        key = _key(problem)
        if bag.position == 1 and pool_size is not None:
            # we just rolled over into a new cycle -- verify the previous
            # cycle had zero internal repeats before resetting our tracker
            assert len(seen_in_cycle) == len(set(seen_in_cycle)), "repeat found within a cycle"
            seen_in_cycle = []
        pool_size = bag.pool_size
        seen_in_cycle.append(key)

    # final partial cycle should also have no internal repeats
    assert len(seen_in_cycle) == len(set(seen_in_cycle))


def test_pool_smaller_than_target_for_a_constrained_drill():
    """SqrtsDrill at low difficulty only has a limited range of perfect
    squares -- the pool should end up smaller than POOL_TARGET_SIZE rather
    than looping forever trying to find more uniques."""
    reset()
    drill = SqrtsDrill()
    bag = ShuffleBag(drill=drill, difficulty=0.0)
    bag.next()  # triggers pool build
    assert 0 < bag.pool_size <= 50


def test_reshuffle_happens_after_full_cycle_and_boundary_can_repeat():
    reset()
    drill = DerivativesDrill()
    bag = ShuffleBag(drill=drill, difficulty=0.3)

    first_problem = bag.next()
    first_key = _key(first_problem)
    pool_size = None

    # draw exactly one full cycle worth (minus the one we already drew)
    while True:
        p = bag.next()
        if pool_size is None:
            pool_size = bag.pool_size
        if bag.position == 1:  # just reshuffled -- a new cycle started
            break

    # the draw immediately after reshuffling CAN legally be the same as the
    # very first problem shown (shuffle-bag boundary behavior) -- what we're
    # really testing is that reshuffling happened at all and didn't crash.
    assert bag.cycles_completed >= 2


def test_last_shown_is_tracked():
    reset()
    drill = DerivativesDrill()
    bag = ShuffleBag(drill=drill, difficulty=0.2)
    problem = bag.next()
    key = _key(problem)
    assert key in bag.last_shown
    assert bag.last_shown[key] > 0


def test_get_next_problem_is_stable_per_user_drill_bucket():
    reset()
    drill = DerivativesDrill()
    seen_a = [_key(get_next_problem(drill, 0.25, "user_a")) for _ in range(10)]
    seen_b = [_key(get_next_problem(drill, 0.25, "user_b")) for _ in range(10)]
    # different users get independently-tracked bags -- no shared state
    assert len(set(seen_a)) == 10  # no repeats within first 10 draws for user_a
    assert len(set(seen_b)) == 10  # same for user_b, independently
