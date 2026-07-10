from app.engine.mastery import (
    accuracy_speed_multiplier,
    combo_speed_multiplier,
    update_mastery,
)


def test_combo_speed_multiplier_increases_with_combo():
    assert combo_speed_multiplier(0) == 1.0
    assert combo_speed_multiplier(25) > combo_speed_multiplier(10)
    assert combo_speed_multiplier(50) > combo_speed_multiplier(25)


def test_combo_speed_multiplier_caps_at_3x():
    assert combo_speed_multiplier(50) == 3.0
    assert combo_speed_multiplier(500) == 3.0  # doesn't keep climbing past the cap


def test_accuracy_speed_multiplier_tiers():
    assert accuracy_speed_multiplier(0.5) == 1.0
    assert accuracy_speed_multiplier(0.90) == 1.2   # "fairly high," per the 90% example
    assert accuracy_speed_multiplier(0.97) == 1.5   # very high


def test_high_combo_makes_mastery_climb_faster_than_baseline():
    baseline = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=0, rolling_accuracy=0.0,
    )
    with_combo = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=50, rolling_accuracy=0.0,
    )
    assert with_combo > baseline


def test_high_accuracy_alone_also_accelerates_progression():
    baseline = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=0, rolling_accuracy=0.0,
    )
    with_accuracy = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=0, rolling_accuracy=0.97,
    )
    assert with_accuracy > baseline


def test_combo_accelerates_more_than_moderate_accuracy():
    """Per the request: a big combo should speed things up more than a
    merely 'fairly high' (~90%) accuracy, even though both help."""
    with_moderate_accuracy = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=0, rolling_accuracy=0.90,
    )
    with_big_combo = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=50, rolling_accuracy=0.0,
    )
    assert with_big_combo > with_moderate_accuracy


def test_combo_and_accuracy_use_whichever_is_bigger_not_both_stacked():
    """OR semantics, not multiplicative stacking -- a huge combo AND high
    accuracy together shouldn't multiply into an absurd speed."""
    combo_only = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=50, rolling_accuracy=0.0,
    )
    both = update_mastery(
        current_mastery=0.3, problem_difficulty=0.5, correct=True, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=50, rolling_accuracy=0.97,
    )
    assert combo_only == both  # combo's 3.0x already beats accuracy's 1.5x -- max(), not sum


def test_wrong_answer_still_moves_mastery_down_regardless_of_combo():
    result = update_mastery(
        current_mastery=0.6, problem_difficulty=0.5, correct=False, used_hint=False,
        time_taken_seconds=2, time_limit_seconds=20, combo=50, rolling_accuracy=0.0,
    )
    assert result < 0.6
