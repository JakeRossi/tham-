from app.engine.pp import compute_pp, difficulty_weight, judgement_tier


def test_difficulty_weight_increases_along_the_progression():
    assert difficulty_weight("addition") < difficulty_weight("derivatives")
    assert difficulty_weight("derivatives") < difficulty_weight("rref")
    assert difficulty_weight("addition") == 1.0  # first in the order, baseline weight


def test_unknown_drill_id_does_not_crash():
    w = difficulty_weight("some-future-drill")
    assert w > 0


def test_judgement_tier_mapping():
    assert judgement_tier(0, correct=True) == "300"
    assert judgement_tier(1, correct=True) == "100"
    assert judgement_tier(2, correct=True) == "50"
    assert judgement_tier(3, correct=True) == "miss"  # 3rd hint reveals the answer
    assert judgement_tier(0, correct=False) == "miss"


def test_miss_always_earns_zero_pp():
    pp, tier = compute_pp("addition", hints_revealed=0, correct=False, combo_after=50,
                           lifetime_play_count_before_this_attempt=1000)
    assert pp == 0.0
    assert tier == "miss"

    pp2, tier2 = compute_pp("rref", hints_revealed=3, correct=True, combo_after=50,
                             lifetime_play_count_before_this_attempt=1000)
    assert pp2 == 0.0
    assert tier2 == "miss"


def test_harder_drill_earns_more_pp_for_identical_performance():
    pp_easy, _ = compute_pp("addition", hints_revealed=0, correct=True, combo_after=10,
                             lifetime_play_count_before_this_attempt=0)
    pp_hard, _ = compute_pp("rref", hints_revealed=0, correct=True, combo_after=10,
                             lifetime_play_count_before_this_attempt=0)
    assert pp_hard > pp_easy


def test_bigger_combo_earns_more_pp():
    pp_low_combo, _ = compute_pp("derivatives", hints_revealed=0, correct=True, combo_after=1,
                                  lifetime_play_count_before_this_attempt=0)
    pp_high_combo, _ = compute_pp("derivatives", hints_revealed=0, correct=True, combo_after=100,
                                   lifetime_play_count_before_this_attempt=0)
    assert pp_high_combo > pp_low_combo


def test_more_hints_earns_less_pp():
    pp_no_hints, _ = compute_pp("derivatives", hints_revealed=0, correct=True, combo_after=10,
                                 lifetime_play_count_before_this_attempt=0)
    pp_one_hint, _ = compute_pp("derivatives", hints_revealed=1, correct=True, combo_after=10,
                                 lifetime_play_count_before_this_attempt=0)
    pp_two_hints, _ = compute_pp("derivatives", hints_revealed=2, correct=True, combo_after=10,
                                  lifetime_play_count_before_this_attempt=0)
    assert pp_no_hints > pp_one_hint > pp_two_hints > 0


def test_more_lifetime_volume_earns_more_pp_per_question():
    pp_new_player, _ = compute_pp("addition", hints_revealed=0, correct=True, combo_after=10,
                                   lifetime_play_count_before_this_attempt=0)
    pp_veteran, _ = compute_pp("addition", hints_revealed=0, correct=True, combo_after=10,
                                lifetime_play_count_before_this_attempt=2000)
    assert pp_veteran > pp_new_player


def test_volume_bonus_is_capped():
    from app.engine.pp import volume_bonus
    assert volume_bonus(100000) <= 1.5
