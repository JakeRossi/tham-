"""
Proves the mastery -> difficulty/hints/timing pipeline is actually wired
together, by exercising it the way the API layer does (without needing
fastapi installed -- these call the same underlying functions problems.py
calls, just directly).
"""

from app.drills.registry import get_drill
from app.engine.difficulty import settings_for_mastery
from app.engine.mastery import update_mastery
from app.engine.user_state import get_mastery, is_first_exposure, record_attempt, reset


def _simulate_next_problem(drill_id: str, user_id: str):
    drill = get_drill(drill_id)
    mastery = get_mastery(drill_id, user_id)
    first_exposure = is_first_exposure(drill_id, user_id)
    settings = settings_for_mastery(mastery, first_exposure)
    problem = drill.generate(settings.problem_difficulty, rng_seed=1)
    return problem, settings


def _simulate_submit(drill_id: str, user_id: str, correct: bool, used_hint: bool, time_taken: float, time_limit: float):
    current_mastery = get_mastery(drill_id, user_id)
    new_mastery = update_mastery(
        current_mastery=current_mastery,
        problem_difficulty=max(0.1, current_mastery),
        correct=correct,
        used_hint=used_hint,
        time_taken_seconds=time_taken,
        time_limit_seconds=time_limit,
    )
    record_attempt(drill_id, new_mastery, user_id)
    return new_mastery


def test_first_exposure_gets_generous_settings_regardless_of_mastery():
    reset("test_user_a")
    _, settings = _simulate_next_problem("addition", "test_user_a")
    assert settings.max_hints == 3
    assert settings.time_limit_seconds == 90
    assert settings.problem_difficulty == 0.15


def test_mastery_climbs_with_repeated_correct_fast_answers_and_hints_shrink():
    reset("test_user_b")
    user = "test_user_b"

    # First attempt: first exposure, generous settings, but this doesn't
    # yet reflect mastery gained FROM this attempt -- that only shows up
    # on the *next* /next call, once record_attempt has run.
    _simulate_next_problem("addition", user)
    _simulate_submit("addition", user, correct=True, used_hint=False, time_taken=1.0, time_limit=90)

    mastery_after_one = get_mastery("addition", user)
    assert mastery_after_one > 0.0

    # Simulate several more fast, correct, no-hint attempts.
    for _ in range(15):
        _simulate_next_problem("addition", user)
        _simulate_submit("addition", user, correct=True, used_hint=False, time_taken=1.0, time_limit=20)

    final_mastery = get_mastery("addition", user)
    assert final_mastery > mastery_after_one, "mastery should keep climbing with repeated success"

    _, settings_late = _simulate_next_problem("addition", user)
    assert settings_late.max_hints <= 1, "hints should have shrunk substantially as mastery climbed"
    assert settings_late.problem_difficulty > 0.15, "problems should get harder as mastery climbs"


def test_repeated_failure_keeps_mastery_low_and_hints_generous():
    reset("test_user_c")
    user = "test_user_c"
    _simulate_next_problem("addition", user)  # burn the first-exposure freebie

    for _ in range(10):
        _simulate_next_problem("addition", user)
        _simulate_submit("addition", user, correct=False, used_hint=True, time_taken=20.0, time_limit=20.0)

    mastery = get_mastery("addition", user)
    assert mastery < 0.2, "repeated failure should keep mastery low"

    _, settings = _simulate_next_problem("addition", user)
    assert settings.max_hints >= 2, "struggling learners should keep getting generous hints"


def test_different_users_have_independent_mastery():
    reset("user_x")
    reset("user_y")
    _simulate_next_problem("addition", "user_x")
    _simulate_submit("addition", "user_x", correct=True, used_hint=False, time_taken=1.0, time_limit=20)

    assert get_mastery("addition", "user_x") > 0.0
    assert get_mastery("addition", "user_y") == 0.0
