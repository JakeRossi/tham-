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
    assert profile["play_count"] == 0  # answering a question isn't opening a drill
    assert pp_earned == 1.0  # first correct rep, tier 300, level 1
    assert tier == "300"
    assert level == 1


def test_pp_accumulates_and_history_is_recorded():
    profile_store.reset("prof_d")
    for _ in range(3):
        profile, pp_earned, _, _ = profile_store.record_question("prof_d", "addition", 0, True)
    assert profile["total_pp"] == 3.0
    assert len(profile["pp_history"]) == 3
    assert profile["pp_history"][-1]["total_pp"] == 3.0


def test_miss_does_not_advance_correct_reps_or_earn_pp():
    profile_store.reset("prof_e")
    profile, pp_earned, tier, _ = profile_store.record_question("prof_e", "addition", 0, False)
    assert pp_earned == 0.0
    assert tier == "miss"
    assert profile["per_drill_stats"]["addition"]["correct_reps"] == 0
    assert profile["questions_answered"] == 1  # still counts as an attempt though


def test_pp_ramps_up_as_correct_reps_accumulate():
    profile_store.reset("prof_f")
    pps = []
    for _ in range(35):
        _, pp_earned, _, _ = profile_store.record_question("prof_f", "addition", 0, True)
        pps.append(pp_earned)
    assert pps[0] == 1.0     # first rep, level 1
    assert pps[15] == 2.0    # past the 10-rep threshold, level 2
    assert pps[31] == 2.0    # arithmetic caps at 2 -- even past the 30-rep mark, stays capped


def test_session_end_logs_recent_session_without_touching_total_pp():
    profile_store.reset("prof_g")
    profile_store.record_question("prof_g", "addition", 0, True)  # total_pp becomes 1.0
    profile = profile_store.record_session_end(
        "prof_g", "addition", tier_counts={"300": 5, "100": 0, "50": 0, "miss": 0},
        max_combo=5, pp_earned_this_session=5.0, mastery_after=0.4,
    )
    assert profile["total_pp"] == 1.0  # unaffected by session_end
    assert len(profile["recent_sessions"]) == 1
    assert profile["recent_sessions"][0]["pp_earned"] == 5.0
    assert profile["recent_sessions"][0]["accuracy_pct"] == 100.0
    assert profile["per_drill_stats"]["addition"]["best_mastery"] == 0.4


def test_recent_sessions_most_recent_first():
    profile_store.reset("prof_h")
    profile_store.record_session_end("prof_h", "addition", {"300": 1, "100": 0, "50": 0, "miss": 0}, 1, 1.0)
    profile = profile_store.record_session_end("prof_h", "subtraction", {"300": 1, "100": 0, "50": 0, "miss": 0}, 1, 2.0)
    assert profile["recent_sessions"][0]["drill_id"] == "subtraction"
    assert profile["recent_sessions"][1]["drill_id"] == "addition"


def test_empty_session_end_does_nothing():
    profile_store.reset("prof_i")
    profile = profile_store.record_session_end("prof_i", "addition", {"300": 0, "100": 0, "50": 0, "miss": 0}, 0, 0.0)
    assert profile["recent_sessions"] == []


def test_different_users_independent():
    profile_store.reset("prof_j1")
    profile_store.reset("prof_j2")
    profile_store.record_question("prof_j1", "addition", 0, True)
    profile2 = profile_store.get_profile("prof_j2")
    assert profile2["total_pp"] == 0.0


def test_profile_persists_across_calls():
    profile_store.reset("prof_k")
    profile_store.record_question("prof_k", "addition", 0, True)
    reloaded = profile_store.get_profile("prof_k")
    assert reloaded["total_pp"] == 1.0
    assert profile_store.PROFILES_PATH.exists()
