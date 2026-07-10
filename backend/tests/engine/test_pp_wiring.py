from app.engine.profile_store import get_profile, record_question, record_session_end, record_session_start, reset


def test_full_flow_session_start_questions_then_session_end():
    reset("flow_a")

    # Opening the drill increments play_count only.
    profile = record_session_start("flow_a", "derivatives")
    assert profile["play_count"] == 1
    assert profile["questions_answered"] == 0

    # Answer a few questions -- pp accumulates, questions_answered climbs.
    total_pp_earned_this_session = 0.0
    tier_counts = {"300": 0, "100": 0, "50": 0, "miss": 0}
    for i in range(5):
        profile, pp_earned, tier, level = record_question("flow_a", "derivatives", 0, True)
        total_pp_earned_this_session += pp_earned
        tier_counts[tier] += 1

    assert profile["questions_answered"] == 5
    assert profile["play_count"] == 1  # unchanged by answering questions
    assert profile["total_pp"] == 0.0  # v4: total_pp doesn't move until the session ends

    # Session ends -- this play now competes for a top-200 spot, which
    # sets total_pp (since it's the only play so far, it wins outright).
    profile = record_session_end(
        "flow_a", "derivatives", tier_counts, max_combo=5,
        pp_earned_this_session=total_pp_earned_this_session, mastery_after=0.3,
    )
    assert profile["total_pp"] == total_pp_earned_this_session
    assert len(profile["recent_sessions"]) == 1
    assert profile["recent_sessions"][0]["pp_earned"] == total_pp_earned_this_session


def test_opening_the_same_drill_twice_counts_two_plays():
    reset("flow_b")
    record_session_start("flow_b", "addition")
    profile = record_session_start("flow_b", "addition")
    assert profile["play_count"] == 2
    assert profile["per_drill_stats"]["addition"]["play_count"] == 2


def test_warmup_style_multi_drill_open_counts_each_drill():
    """Simulates a warm-up opening several drills at once -- each should
    register its own play-count increment."""
    reset("flow_c")
    for drill_id in ["addition", "subtraction", "derivatives"]:
        record_session_start("flow_c", drill_id)
    profile = get_profile("flow_c")
    assert profile["play_count"] == 3
    assert profile["per_drill_stats"]["addition"]["play_count"] == 1
    assert profile["per_drill_stats"]["derivatives"]["play_count"] == 1
