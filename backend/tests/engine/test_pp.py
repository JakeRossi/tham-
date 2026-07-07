from app.engine.pp import (
    compute_question_pp,
    judgement_tier,
    pp_level_for_reps,
    question_pp_cap,
)


def test_arithmetic_family_shares_the_2pp_cap():
    for drill_id in ["addition", "subtraction", "multiplication", "division",
                      "squares", "sqrts", "cubes", "cbrts"]:
        assert question_pp_cap(drill_id) == 2


def test_per_drill_caps_match_spec():
    assert question_pp_cap("trig-values") == 4
    assert question_pp_cap("algebraic-manipulation") == 3
    assert question_pp_cap("derivatives") == 5
    assert question_pp_cap("integrals") == 7
    assert question_pp_cap("rref") == 4
    assert question_pp_cap("ode-pde") == 10


def test_leveling_thresholds_match_the_requested_progression():
    # reps 0-9 -> level 1, 10-29 -> level 2, 30-59 -> level 3, 60-99 -> level 4
    assert pp_level_for_reps(0) == 1
    assert pp_level_for_reps(9) == 1
    assert pp_level_for_reps(10) == 2
    assert pp_level_for_reps(29) == 2
    assert pp_level_for_reps(30) == 3
    assert pp_level_for_reps(59) == 3
    assert pp_level_for_reps(60) == 4
    assert pp_level_for_reps(99) == 4
    assert pp_level_for_reps(100) == 5


def test_leveling_thresholds_require_increasingly_more_reps_per_level():
    """Level 2 needs +10 reps, level 3 needs +20 more, level 4 needs +30
    more -- each level costs more than the last (the 'exponentially
    harder' requirement)."""
    thresholds = []
    last_level = 1
    for reps in range(0, 200):
        level = pp_level_for_reps(reps)
        if level != last_level:
            thresholds.append(reps)
            last_level = level
    gaps = [thresholds[i] - (thresholds[i - 1] if i > 0 else 0) for i in range(len(thresholds))]
    assert gaps == sorted(gaps)  # each gap is >= the previous one


def test_question_pp_capped_even_with_huge_rep_count():
    pp_earned, tier, level = compute_question_pp(
        "addition", hints_revealed=0, correct=True, correct_reps_before_this_question=100_000,
    )
    assert level == 2  # arithmetic caps at 2, however many reps you have
    assert pp_earned == 2.0


def test_hardest_drill_needs_hundreds_of_reps_to_reach_its_cap():
    _, _, level_early = compute_question_pp("ode-pde", 0, True, correct_reps_before_this_question=10)
    _, _, level_late = compute_question_pp("ode-pde", 0, True, correct_reps_before_this_question=600)
    assert level_early < question_pp_cap("ode-pde")
    assert level_late == question_pp_cap("ode-pde")


def test_miss_earns_zero_pp():
    pp_earned, tier, _ = compute_question_pp("ode-pde", 0, correct=False, correct_reps_before_this_question=600)
    assert pp_earned == 0.0
    assert tier == "miss"

    pp_earned2, tier2, _ = compute_question_pp("ode-pde", 3, correct=True, correct_reps_before_this_question=600)
    assert pp_earned2 == 0.0  # 3rd hint reveals the answer -- graded as miss
    assert tier2 == "miss"


def test_hint_tiers_scale_pp_down_not_to_zero():
    pp_300, _, _ = compute_question_pp("derivatives", 0, True, correct_reps_before_this_question=200)
    pp_100, _, _ = compute_question_pp("derivatives", 1, True, correct_reps_before_this_question=200)
    pp_50, _, _ = compute_question_pp("derivatives", 2, True, correct_reps_before_this_question=200)
    assert pp_300 > pp_100 > pp_50 > 0


def test_judgement_tier_mapping():
    assert judgement_tier(0, correct=True) == "300"
    assert judgement_tier(1, correct=True) == "100"
    assert judgement_tier(2, correct=True) == "50"
    assert judgement_tier(3, correct=True) == "miss"
    assert judgement_tier(0, correct=False) == "miss"


def test_early_reps_are_worth_only_one_pp_regardless_of_drill():
    """Even the hardest drill's first ~10 correct reps are worth the same
    modest 1pp as arithmetic's -- the cap difference only shows up once
    you've built up a lot of reps."""
    pp_easy, _, _ = compute_question_pp("addition", 0, True, correct_reps_before_this_question=0)
    pp_hard, _, _ = compute_question_pp("ode-pde", 0, True, correct_reps_before_this_question=0)
    assert pp_easy == pp_hard == 1.0
