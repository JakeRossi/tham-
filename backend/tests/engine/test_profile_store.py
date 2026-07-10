from app.engine import profile_store


def test_new_profile_defaults():
    profile_store.reset("prof_a")
    profile = profile_store.get_profile("prof_a")
    assert profile["total_pp"] == 0.0
    assert profile["play_count"] == 0
    assert profile["questions_answered"] == 0
    assert profile_store.lifetime_accuracy(profile) == 100.0


def test_session_start_increments_play_count_not_questions_answered():
    profile_store.reset("prof_b")
    profile = profile_store.record_session_start("prof_b", "addition")
    assert profile["play_count"] == 1
    assert profile["questions_answered"] == 0  # opening a drill isn't answering a question
    assert profile["per_drill_stats"]["addition"]["play_count"] == 1
    assert profile_store.questions_this_month(profile) == 1  # play-count-based, not questions


def test_record_question_increments_questions_answered_not_play_count():
    profile_store.reset("prof_c")
    profile, pp_earned, tier, level = profile_store.record_question(
        "prof_c", "addition", hints_revealed=0, correct=True,
    )
    assert profile["questions_answered"] == 1
    assert profile["play_count"] == 0
    assert pp_earned == 1.0  # first correct rep, tier 300, level 1
    assert tier == "300"
    assert level == 1


def test_record_question_does_not_touch_total_pp():
    """v4: only a finished SESSION (record_session_end) can change
    total_pp -- individual question awards are tracked for the leveling
    curve and live UI feedback, but don't accumulate directly."""
    profile_store.reset("prof_d")
    for _ in range(5):
        profile, _, _, _ = profile_store.record_question("prof_d", "addition", 0, True)
    assert profile["total_pp"] == 0.0


def test_miss_does_not_advance_correct_reps_or_earn_pp():
    profile_store.reset("prof_e")
    profile, pp_earned, tier, _ = profile_store.record_question("prof_e", "addition", 0, False)
    assert pp_earned == 0.0
    assert tier == "miss"
    assert profile["per_drill_stats"]["addition"]["correct_reps"] == 0
    assert profile["questions_answered"] == 1


def test_pp_ramps_up_as_correct_reps_accumulate():
    profile_store.reset("prof_f")
    pps = []
    for _ in range(35):
        _, pp_earned, _, _ = profile_store.record_question("prof_f", "addition", 0, True)
        pps.append(pp_earned)
    assert pps[0] == 1.0
    assert pps[15] == 2.0
    assert pps[31] == 2.0  # arithmetic caps at 2


def test_session_end_sets_total_pp_from_the_play():
    profile_store.reset("prof_g")
    profile = profile_store.record_session_end(
        "prof_g", "addition", tier_counts={"300": 5, "100": 0, "50": 0, "miss": 0},
        max_combo=5, pp_earned_this_session=5.0, mastery_after=0.4,
    )
    assert profile["total_pp"] == 5.0
    assert len(profile["recent_sessions"]) == 1
    assert profile["recent_sessions"][0]["pp_earned"] == 5.0
    assert profile["recent_sessions"][0]["accuracy_pct"] == 100.0
    assert profile["per_drill_stats"]["addition"]["best_mastery"] == 0.4
    assert len(profile["all_plays"]) == 1
    assert profile["all_plays"][0]["pp"] == 5.0


def test_a_worse_play_never_lowers_total_pp():
    """The core ask: if you already have 200 plays worth 100pp each, a
    new 90pp play must NOT change your total."""
    profile_store.reset("prof_h")
    for _ in range(200):
        profile = profile_store.record_session_end(
            "prof_h", "addition", {"300": 10, "100": 0, "50": 0, "miss": 0}, max_combo=10,
            pp_earned_this_session=100.0,
        )
    total_before = profile["total_pp"]
    assert total_before == round(sum(100.0 * (0.95 ** i) for i in range(200)), 2)

    profile = profile_store.record_session_end(
        "prof_h", "addition", {"300": 9, "100": 1, "50": 0, "miss": 0}, max_combo=9,
        pp_earned_this_session=90.0,
    )
    assert profile["total_pp"] == total_before  # unchanged -- 90 doesn't crack the top 200 of 100s


def test_a_better_play_does_increase_total_pp():
    profile_store.reset("prof_i")
    for _ in range(5):
        profile = profile_store.record_session_end(
            "prof_i", "addition", {"300": 10, "100": 0, "50": 0, "miss": 0}, max_combo=10,
            pp_earned_this_session=10.0,
        )
    total_before = profile["total_pp"]
    profile = profile_store.record_session_end(
        "prof_i", "rref", {"300": 10, "100": 0, "50": 0, "miss": 0}, max_combo=10,
        pp_earned_this_session=500.0,
    )
    assert profile["total_pp"] > total_before


def test_only_top_200_plays_count():
    profile_store.reset("prof_j")
    for i in range(210):
        profile = profile_store.record_session_end(
            "prof_j", "addition", {"300": 1, "100": 0, "50": 0, "miss": 0}, max_combo=1,
            pp_earned_this_session=float(i + 1),  # 1..210, strictly increasing
        )
    from app.engine.pp import total_pp_from_plays
    best_200 = list(range(11, 211))  # the top 200 values from 1..210
    assert profile["total_pp"] == total_pp_from_plays([float(v) for v in best_200])


def test_empty_session_end_does_nothing():
    profile_store.reset("prof_k")
    profile = profile_store.record_session_end("prof_k", "addition", {"300": 0, "100": 0, "50": 0, "miss": 0}, 0, 0.0)
    assert profile["recent_sessions"] == []
    assert profile["all_plays"] == []


def test_zero_pp_session_is_not_recorded_as_a_play():
    profile_store.reset("prof_l")
    profile = profile_store.record_session_end(
        "prof_l", "addition", {"300": 0, "100": 0, "50": 0, "miss": 5}, max_combo=0, pp_earned_this_session=0.0,
    )
    assert profile["all_plays"] == []
    assert len(profile["recent_sessions"]) == 1  # still logged for display purposes


def test_different_users_independent():
    profile_store.reset("prof_m1")
    profile_store.reset("prof_m2")
    profile_store.record_session_end("prof_m1", "addition", {"300": 1, "100": 0, "50": 0, "miss": 0}, 1, 5.0)
    profile2 = profile_store.get_profile("prof_m2")
    assert profile2["total_pp"] == 0.0


def test_profile_persists_across_calls():
    profile_store.reset("prof_n")
    profile_store.record_session_end("prof_n", "addition", {"300": 1, "100": 0, "50": 0, "miss": 0}, 1, 5.0)
    reloaded = profile_store.get_profile("prof_n")
    assert reloaded["total_pp"] == 5.0
    assert profile_store.PROFILES_PATH.exists()
