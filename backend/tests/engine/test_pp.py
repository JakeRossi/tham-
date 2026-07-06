from app.engine.pp import (
    accuracy_fraction_from_tiers,
    bonus_pp,
    combo_factor,
    compute_run_pp,
    difficulty_weight,
    judgement_tier,
    total_pp_from_best_scores,
    weighted_total_pp,
)


def test_difficulty_weight_increases_along_the_progression():
    assert difficulty_weight("addition") < difficulty_weight("derivatives")
    assert difficulty_weight("derivatives") < difficulty_weight("rref")
    assert difficulty_weight("addition") == 1.0


def test_unknown_drill_id_does_not_crash():
    assert difficulty_weight("some-future-drill") > 0


def test_judgement_tier_mapping():
    assert judgement_tier(0, correct=True) == "300"
    assert judgement_tier(1, correct=True) == "100"
    assert judgement_tier(2, correct=True) == "50"
    assert judgement_tier(3, correct=True) == "miss"
    assert judgement_tier(0, correct=False) == "miss"


def test_accuracy_fraction_from_tiers():
    # all 300s -> 100% accuracy
    assert accuracy_fraction_from_tiers({"300": 10, "100": 0, "50": 0, "miss": 0}) == 1.0
    # all misses -> 0% accuracy
    assert accuracy_fraction_from_tiers({"300": 0, "100": 0, "50": 0, "miss": 10}) == 0.0
    # empty session -> 0, not a division error
    assert accuracy_fraction_from_tiers({"300": 0, "100": 0, "50": 0, "miss": 0}) == 0.0


def test_80_percent_accuracy_is_roughly_two_thirds_the_value_of_95_percent():
    """osu!'s own documented example: an 80% full combo can be worth
    roughly 2/3 of a 95% accuracy score. This is the anchor the
    ACCURACY_EXPONENT constant was fit against."""
    pp_95 = compute_run_pp("addition", 0.95, max_combo=500)
    pp_80 = compute_run_pp("addition", 0.80, max_combo=500)
    ratio = pp_80 / pp_95
    assert 0.55 < ratio < 0.75  # roughly 2/3, generous tolerance


def test_harder_drill_earns_more_run_pp_for_identical_performance():
    pp_easy = compute_run_pp("addition", accuracy_fraction=0.95, max_combo=100)
    pp_hard = compute_run_pp("rref", accuracy_fraction=0.95, max_combo=100)
    assert pp_hard > pp_easy


def test_bigger_combo_earns_more_run_pp():
    pp_low = compute_run_pp("derivatives", accuracy_fraction=0.95, max_combo=5)
    pp_high = compute_run_pp("derivatives", accuracy_fraction=0.95, max_combo=200)
    assert pp_high > pp_low


def test_combo_factor_diminishing_returns():
    """Logarithmic growth means each ADDITIONAL combo point contributes less
    than the previous one on average -- not that doublings shrink (a log
    curve adds roughly the same amount per doubling; it's the per-point
    marginal contribution that shrinks as combo grows)."""
    marginal_gain_early = (combo_factor(10) - combo_factor(0)) / 10
    marginal_gain_late = (combo_factor(200) - combo_factor(100)) / 100
    assert marginal_gain_late < marginal_gain_early


def test_weightage_system_matches_osu_formula():
    """osu!'s weightage: Total pp = p * 0.95^(n-1) for the nth-best score."""
    scores = [100.0, 100.0, 90.0, 80.0]
    total = weighted_total_pp(scores)
    expected = 100.0 * (0.95 ** 0) + 100.0 * (0.95 ** 1) + 90.0 * (0.95 ** 2) + 80.0 * (0.95 ** 3)
    assert abs(total - round(expected, 2)) < 0.01


def test_weightage_sorts_before_applying_decay():
    """Order of the input list shouldn't matter -- the biggest score always
    gets the least decay, regardless of what order it's passed in."""
    assert weighted_total_pp([50.0, 100.0, 80.0]) == weighted_total_pp([100.0, 80.0, 50.0])


def test_bonus_pp_matches_documented_formula():
    # osu!'s docs state ~413.894 bonus pp for 1000 scores
    assert abs(bonus_pp(1000) - 413.89) < 0.1


def test_bonus_pp_is_small_for_few_drills():
    # Only 14 drills exist -- the bonus should be modest, not anywhere near the 1000-map cap
    assert bonus_pp(14) < 30


def test_bonus_pp_zero_for_no_drills_played():
    assert bonus_pp(0) == 0.0


def test_total_pp_only_counts_positive_best_scores():
    totals = total_pp_from_best_scores({"addition": 50.0, "subtraction": 0.0, "derivatives": 80.0})
    # should be the same as if "subtraction" (0.0, i.e. never played) weren't there at all
    totals_without_zero = total_pp_from_best_scores({"addition": 50.0, "derivatives": 80.0})
    assert totals == totals_without_zero


def test_total_pp_rewards_a_few_great_scores_over_many_mediocre_ones():
    """Mirrors osu!'s actual design goal: a couple of excellent scores on
    hard drills should outweigh a pile of so-so scores on easy ones --
    using realistic run_pp values (not arbitrary constants), since the
    weightage decay's self-limiting effect only shows up at realistic
    score magnitudes."""
    few_great = total_pp_from_best_scores({
        "ode-pde": compute_run_pp("ode-pde", accuracy_fraction=0.98, max_combo=100),
        "rref": compute_run_pp("rref", accuracy_fraction=0.98, max_combo=100),
    })
    many_mediocre = total_pp_from_best_scores({
        drill_id: compute_run_pp(drill_id, accuracy_fraction=0.75, max_combo=15)
        for drill_id in ["addition", "subtraction", "multiplication", "division",
                          "squares", "sqrts", "cubes", "cbrts"]
    })
    assert few_great > many_mediocre
