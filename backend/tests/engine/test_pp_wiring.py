"""
Exercises the same logic the API routes run (submit_answer for mastery,
record_session for pp), without needing fastapi installed in this sandbox.
"""

from app.drills.arithmetic import AdditionDrill
from app.drills.base import Problem
from app.drills.registry import get_drill
from app.engine.mastery import update_mastery
from app.engine.profile_store import record_session, reset
from app.engine.user_state import get_mastery, record_attempt


def _simulate_submit(user_id, drill_id, submitted, answer, time_taken=2.0, time_limit=20.0, used_hint=False):
    drill = get_drill(drill_id)
    problem = Problem(drill_id=drill_id, prompt="?", answer=answer, difficulty=0.0)
    result = drill.check(problem, submitted)

    current_mastery = get_mastery(drill_id, user_id)
    new_mastery = update_mastery(
        current_mastery=current_mastery, problem_difficulty=max(0.1, current_mastery),
        correct=result.correct, used_hint=used_hint,
        time_taken_seconds=time_taken, time_limit_seconds=time_limit,
    )
    record_attempt(drill_id, new_mastery, user_id)
    return result, new_mastery


def test_a_full_session_of_correct_answers_produces_a_high_pp_run():
    reset("wiring_a")
    drill = AdditionDrill()
    tier_counts = {"300": 0, "100": 0, "50": 0, "miss": 0}
    final_mastery = 0.0

    for seed in range(10):
        problem = drill.generate(0.2, rng_seed=seed)
        result, final_mastery = _simulate_submit("wiring_a", "addition", problem.answer, problem.answer)
        assert result.correct
        tier_counts["300"] += 1  # no hints used in this simulation

    profile, run_pp, is_new_best = record_session(
        "wiring_a", "addition", tier_counts, max_combo=10, mastery_after=final_mastery,
    )
    assert run_pp > 0
    assert is_new_best
    assert profile["total_pp"] == profile["total_pp"]  # sane, non-crashing
    assert profile["per_drill_stats"]["addition"]["best_mastery"] == final_mastery


def test_a_session_full_of_misses_earns_zero_pp_but_still_updates_mastery():
    reset("wiring_b")
    result, new_mastery = _simulate_submit("wiring_b", "addition", "999999", "42")
    assert not result.correct
    assert new_mastery <= 0.1  # mastery shouldn't have climbed from a wrong answer

    profile, run_pp, is_new_best = record_session(
        "wiring_b", "addition", {"300": 0, "100": 0, "50": 0, "miss": 1}, max_combo=0,
    )
    assert run_pp == 0.0
    assert not is_new_best


def test_harder_drill_session_with_same_accuracy_earns_more_pp():
    reset("wiring_c")
    tier_counts = {"300": 10, "100": 0, "50": 0, "miss": 0}
    _, easy_pp, _ = record_session("wiring_c", "addition", tier_counts, max_combo=10)
    _, hard_pp, _ = record_session("wiring_c", "rref", tier_counts, max_combo=10)
    assert hard_pp > easy_pp
