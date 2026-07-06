from app.engine import profile_store


def test_new_profile_has_sane_defaults():
    profile_store.reset("test_profile_a")
    profile = profile_store.get_profile("test_profile_a")
    assert profile["total_pp"] == 0.0
    assert profile["play_count"] == 0
    assert profile["max_combo_lifetime"] == 0
    assert profile_store.lifetime_accuracy(profile) == 100.0
    assert profile_store.questions_this_month(profile) == 0


def test_record_attempt_updates_all_the_expected_fields():
    profile_store.reset("test_profile_b")
    profile = profile_store.record_attempt(
        "test_profile_b", drill_id="addition", tier="300", pp_earned=12.5,
        combo_after=5, mastery_after=0.3,
    )
    assert profile["total_pp"] == 12.5
    assert profile["play_count"] == 1
    assert profile["max_combo_lifetime"] == 5
    assert profile["tier_counts"]["300"] == 1
    assert profile["per_drill_stats"]["addition"]["play_count"] == 1
    assert profile["per_drill_stats"]["addition"]["best_mastery"] == 0.3
    assert profile_store.questions_this_month(profile) == 1


def test_pp_and_play_count_accumulate_across_attempts():
    profile_store.reset("test_profile_c")
    profile_store.record_attempt("test_profile_c", "addition", "300", 10.0, 1, 0.1)
    profile = profile_store.record_attempt("test_profile_c", "addition", "100", 5.0, 2, 0.2)
    assert profile["total_pp"] == 15.0
    assert profile["play_count"] == 2


def test_max_combo_lifetime_only_increases():
    profile_store.reset("test_profile_d")
    profile_store.record_attempt("test_profile_d", "addition", "300", 10.0, 50, 0.5)
    profile = profile_store.record_attempt("test_profile_d", "addition", "300", 10.0, 5, 0.5)
    assert profile["max_combo_lifetime"] == 50  # doesn't drop just because this combo was smaller


def test_lifetime_accuracy_weighted_correctly():
    profile_store.reset("test_profile_e")
    profile_store.record_attempt("test_profile_e", "addition", "300", 10.0, 1, 0.1)
    profile_store.record_attempt("test_profile_e", "addition", "miss", 0.0, 0, 0.1)
    profile = profile_store.get_profile("test_profile_e")
    # (300*1 + 0) / (300*2) = 0.5 -> 50%
    assert profile_store.lifetime_accuracy(profile) == 50.0


def test_per_drill_best_mastery_tracks_the_max_not_the_latest():
    profile_store.reset("test_profile_f")
    profile_store.record_attempt("test_profile_f", "addition", "300", 10.0, 1, 0.8)
    profile = profile_store.record_attempt("test_profile_f", "addition", "300", 10.0, 1, 0.3)
    assert profile["per_drill_stats"]["addition"]["best_mastery"] == 0.8


def test_profiles_persist_across_separate_get_calls():
    """Proves this is actually file-backed, not just an in-memory dict that
    happens to work within one test run."""
    profile_store.reset("test_profile_g")
    profile_store.record_attempt("test_profile_g", "addition", "300", 42.0, 3, 0.5)
    # Simulate a "fresh" read the way a new request would see it.
    reloaded = profile_store.get_profile("test_profile_g")
    assert reloaded["total_pp"] == 42.0
    assert profile_store.PROFILES_PATH.exists()


def test_different_users_are_independent():
    profile_store.reset("test_profile_h1")
    profile_store.reset("test_profile_h2")
    profile_store.record_attempt("test_profile_h1", "addition", "300", 10.0, 1, 0.5)
    profile_h2 = profile_store.get_profile("test_profile_h2")
    assert profile_h2["total_pp"] == 0.0
