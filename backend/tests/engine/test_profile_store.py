from app.engine import profile_store


def test_new_profile_has_sane_defaults():
    profile_store.reset("prof_a")
    profile = profile_store.get_profile("prof_a")
    assert profile["total_pp"] == 0.0
    assert profile["play_count"] == 0
    assert profile["max_combo_lifetime"] == 0
    assert profile_store.lifetime_accuracy(profile) == 100.0
    assert profile_store.questions_this_month(profile) == 0


def test_record_session_updates_expected_fields():
    profile_store.reset("prof_b")
    profile, run_pp, is_new_best = profile_store.record_session(
        "prof_b", "addition", tier_counts={"300": 8, "100": 2, "50": 0, "miss": 0}, max_combo=10,
    )
    assert run_pp > 0
    assert is_new_best is True
    assert profile["play_count"] == 10
    assert profile["per_drill_stats"]["addition"]["play_count"] == 10
    assert profile["per_drill_stats"]["addition"]["best_pp"] == run_pp
    assert profile["total_pp"] > 0
    assert profile_store.questions_this_month(profile) == 10


def test_empty_session_does_nothing():
    profile_store.reset("prof_c")
    profile, run_pp, is_new_best = profile_store.record_session(
        "prof_c", "addition", tier_counts={"300": 0, "100": 0, "50": 0, "miss": 0}, max_combo=0,
    )
    assert run_pp == 0.0
    assert is_new_best is False
    assert profile["play_count"] == 0


def test_only_best_session_per_drill_counts_towards_pp():
    """Mirrors osu!: only your best score on a beatmap counts -- a worse
    follow-up session shouldn't lower your recorded best."""
    profile_store.reset("prof_d")
    _, first_pp, _ = profile_store.record_session(
        "prof_d", "addition", {"300": 10, "100": 0, "50": 0, "miss": 0}, max_combo=50,
    )
    profile, second_pp, is_new_best = profile_store.record_session(
        "prof_d", "addition", {"300": 0, "100": 0, "50": 0, "miss": 10}, max_combo=0,
    )
    assert second_pp == 0.0  # all misses
    assert is_new_best is False
    assert profile["per_drill_stats"]["addition"]["best_pp"] == first_pp  # unchanged, not overwritten with 0


def test_better_session_does_replace_the_best():
    profile_store.reset("prof_e")
    _, first_pp, _ = profile_store.record_session(
        "prof_e", "addition", {"300": 5, "100": 5, "50": 0, "miss": 0}, max_combo=5,
    )
    profile, second_pp, is_new_best = profile_store.record_session(
        "prof_e", "addition", {"300": 20, "100": 0, "50": 0, "miss": 0}, max_combo=20,
    )
    assert second_pp > first_pp
    assert is_new_best is True
    assert profile["per_drill_stats"]["addition"]["best_pp"] == second_pp


def test_total_pp_aggregates_across_multiple_drills_with_weightage():
    profile_store.reset("prof_f")
    profile_store.record_session("prof_f", "addition", {"300": 10, "100": 0, "50": 0, "miss": 0}, max_combo=50)
    profile = profile_store.get_profile("prof_f")
    pp_after_one_drill = profile["total_pp"]

    profile_store.record_session("prof_f", "rref", {"300": 10, "100": 0, "50": 0, "miss": 0}, max_combo=50)
    profile = profile_store.get_profile("prof_f")
    pp_after_two_drills = profile["total_pp"]

    assert pp_after_two_drills > pp_after_one_drill


def test_lifetime_accuracy_weighted_correctly():
    profile_store.reset("prof_g")
    profile_store.record_session("prof_g", "addition", {"300": 1, "100": 0, "50": 0, "miss": 1}, max_combo=1)
    profile = profile_store.get_profile("prof_g")
    # (300*1 + 0) / (300*2) = 0.5 -> 50%
    assert profile_store.lifetime_accuracy(profile) == 50.0


def test_profiles_persist_across_separate_get_calls():
    profile_store.reset("prof_h")
    profile_store.record_session("prof_h", "addition", {"300": 5, "100": 0, "50": 0, "miss": 0}, max_combo=5)
    reloaded = profile_store.get_profile("prof_h")
    assert reloaded["total_pp"] > 0
    assert profile_store.PROFILES_PATH.exists()


def test_different_users_are_independent():
    profile_store.reset("prof_i1")
    profile_store.reset("prof_i2")
    profile_store.record_session("prof_i1", "addition", {"300": 5, "100": 0, "50": 0, "miss": 0}, max_combo=5)
    profile_i2 = profile_store.get_profile("prof_i2")
    assert profile_i2["total_pp"] == 0.0


def test_mastery_after_tracked_per_drill():
    profile_store.reset("prof_j")
    profile, _, _ = profile_store.record_session(
        "prof_j", "addition", {"300": 5, "100": 0, "50": 0, "miss": 0}, max_combo=5, mastery_after=0.6,
    )
    assert profile["per_drill_stats"]["addition"]["best_mastery"] == 0.6
