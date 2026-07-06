"""
Exercises the same logic app/api/problems.py's submit_answer() runs,
without needing fastapi installed in this sandbox -- proves the whole
grade -> pp -> profile pipeline is actually wired together correctly.
"""

from app.drills.arithmetic import AdditionDrill
from app.drills.registry import get_drill
from app.engine.mastery import update_mastery
from app.engine.pp import compute_pp
from app.engine.profile_store import get_lifetime_play_count, record_attempt as record_profile_attempt, reset
from app.engine.user_state import get_mastery, record_attempt


def _simulate_submit(user_id, drill_id, submitted, answer, hints_revealed, combo_after,
                      time_taken=2.0, time_limit=20.0):
    drill = get_drill(drill_id)
    from app.drills.base import Problem
    problem = Problem(drill_id=drill_id, prompt="?", answer=answer, difficulty=0.0)
    result = drill.check(problem, submitted)

    current_mastery = get_mastery(drill_id, user_id)
    new_mastery = update_mastery(
        current_mastery=current_mastery, problem_difficulty=max(0.1, current_mastery),
        correct=result.correct, used_hint=hints_revealed > 0,
        time_taken_seconds=time_taken, time_limit_seconds=time_limit,
    )
    record_attempt(drill_id, new_mastery, user_id)

    lifetime_before = get_lifetime_play_count(user_id)
    pp_earned, tier = compute_pp(drill_id, hints_revealed, result.correct, combo_after, lifetime_before)
    profile = record_profile_attempt(user_id, drill_id, tier, pp_earned, combo_after, new_mastery)
    return result, pp_earned, tier, profile


def test_correct_answer_with_no_hints_earns_pp_and_updates_profile():
    reset("pp_wiring_user_a")
    drill = AdditionDrill()
    problem = drill.generate(0.2, rng_seed=1)

    result, pp_earned, tier, profile = _simulate_submit(
        "pp_wiring_user_a", "addition", problem.answer, problem.answer,
        hints_revealed=0, combo_after=1,
    )
    assert result.correct
    assert tier == "300"
    assert pp_earned > 0
    assert profile["total_pp"] == pp_earned
    assert profile["play_count"] == 1


def test_revealed_answer_earns_zero_pp_even_though_correct():
    reset("pp_wiring_user_b")
    drill = AdditionDrill()
    problem = drill.generate(0.2, rng_seed=1)

    result, pp_earned, tier, profile = _simulate_submit(
        "pp_wiring_user_b", "addition", problem.answer, problem.answer,
        hints_revealed=3, combo_after=0,   # 3rd hint reveals the answer
    )
    assert result.correct  # backend still confirms the answer is right...
    assert tier == "miss"  # ...but it's graded like a miss
    assert pp_earned == 0.0
    assert profile["tier_counts"]["miss"] == 1


def test_wrong_answer_earns_zero_pp():
    reset("pp_wiring_user_c")
    result, pp_earned, tier, profile = _simulate_submit(
        "pp_wiring_user_c", "addition", "999999999", "42",
        hints_revealed=0, combo_after=0,
    )
    assert not result.correct
    assert tier == "miss"
    assert pp_earned == 0.0


def test_pp_accumulates_across_multiple_attempts():
    reset("pp_wiring_user_d")
    drill = AdditionDrill()
    total_expected = 0.0
    for seed in range(5):
        problem = drill.generate(0.2, rng_seed=seed)
        _, pp_earned, _, profile = _simulate_submit(
            "pp_wiring_user_d", "addition", problem.answer, problem.answer,
            hints_revealed=0, combo_after=seed + 1,
        )
        total_expected += pp_earned
    assert profile["play_count"] == 5
    assert abs(profile["total_pp"] - round(total_expected, 2)) < 0.01
