"""
Player profile: persistent, file-backed (JSON) so it survives backend
restarts. v3 schema -- see app/engine/pp.py's docstring for why pp
accounting changed from a per-session/weightage model back to a
per-question one.

Two DIFFERENT counters that are easy to conflate, kept deliberately
separate per an explicit design requirement:
  - play_count:         how many times a drill was OPENED (a practice
                         session or warm-up started) -- osu!'s real
                         "Play Count" is exactly this (once per beatmap
                         play attempt, not once per note hit).
  - questions_answered:  how many individual questions were attempted --
                         a much larger, faster-growing number. This is
                         what earlier versions of this file mistakenly
                         called "play_count."

  osu! profile page shows          -> math-osu equivalent (this module)
  ---------------------------------------------------------------------
  Performance points (pp)          -> total_pp (running sum, see pp.py)
  Play count                       -> play_count (drill-open count)
  Rank/pp graph over time          -> pp_history (list of {date, total_pp})
  Monthly playcount graph          -> plays_by_month ("YYYY-MM" -> opens)
  Max combo                        -> max_combo_lifetime
  Join date                        -> joined_at
  Best performance list            -> recent_sessions (logged at session
                                       end -- for DISPLAY only; doesn't
                                       affect total_pp, which already
                                       accumulated per-question)
  Most played beatmaps             -> per_drill_stats sorted by play_count

Storage: a single JSON file at backend/data/profiles.json (created lazily,
gitignored). Intentionally simple -- fine for a single local player.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.engine.pp import compute_question_pp

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PROFILES_PATH = DATA_DIR / "profiles.json"

PP_HISTORY_LIMIT = 1000
RECENT_SESSIONS_LIMIT = 50

_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _default_profile(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "joined_at": _now_iso(),
        "last_played_at": None,
        "total_pp": 0.0,
        "play_count": 0,          # drill OPENS, not questions answered
        "questions_answered": 0,  # total questions attempted, lifetime
        "max_combo_lifetime": 0,
        "tier_counts": {"300": 0, "100": 0, "50": 0, "miss": 0},
        "plays_by_month": {},     # "YYYY-MM" -> drill-open count that month
        "pp_history": [],         # [{"date": iso, "total_pp": float}, ...]
        "per_drill_stats": {},    # drill_id -> {play_count, questions_answered, correct_reps, best_mastery}
        "recent_sessions": [],    # [{drill_id, date, accuracy_pct, pp_earned, max_combo}, ...] most recent first
    }


def _load_all() -> dict[str, dict[str, Any]]:
    if not PROFILES_PATH.exists():
        return {}
    try:
        with open(PROFILES_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(all_profiles: dict[str, dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILES_PATH, "w") as f:
        json.dump(all_profiles, f, indent=2)


def _drill_stats(profile: dict[str, Any], drill_id: str) -> dict[str, Any]:
    return profile["per_drill_stats"].setdefault(
        drill_id, {"play_count": 0, "questions_answered": 0, "correct_reps": 0, "best_mastery": 0.0}
    )


def get_profile(user_id: str) -> dict[str, Any]:
    with _lock:
        all_profiles = _load_all()
        return all_profiles.get(user_id) or _default_profile(user_id)


def lifetime_accuracy(profile: dict[str, Any]) -> float:
    tc = profile["tier_counts"]
    total = tc["300"] + tc["100"] + tc["50"] + tc["miss"]
    if total == 0:
        return 100.0
    weighted = 300 * tc["300"] + 100 * tc["100"] + 50 * tc["50"]
    return round((weighted / (300 * total)) * 100, 2)


def questions_this_month(profile: dict[str, Any]) -> int:
    """Kept for backwards display compatibility -- counts drill OPENS this
    month (see plays_by_month), matching osu!'s monthly playcount graph."""
    return profile["plays_by_month"].get(_current_month_key(), 0)


def record_session_start(user_id: str, drill_id: str) -> dict[str, Any]:
    """Call once each time a drill is opened (a practice session or one
    drill within a warm-up starts) -- this is the REAL play-count metric,
    separate from how many questions get answered once it's open."""
    with _lock:
        all_profiles = _load_all()
        profile = all_profiles.get(user_id) or _default_profile(user_id)

        profile["play_count"] += 1
        _drill_stats(profile, drill_id)["play_count"] += 1

        month_key = _current_month_key()
        profile["plays_by_month"][month_key] = profile["plays_by_month"].get(month_key, 0) + 1
        profile["last_played_at"] = _now_iso()

        all_profiles[user_id] = profile
        _save_all(all_profiles)
        return profile


def record_question(
    user_id: str, drill_id: str, hints_revealed: int, correct: bool,
) -> tuple[dict[str, Any], float, str, int]:
    """
    Awards pp for ONE answered question and updates all the lifetime
    counters. Returns (profile, pp_earned, tier, level).
    """
    with _lock:
        all_profiles = _load_all()
        profile = all_profiles.get(user_id) or _default_profile(user_id)
        stats = _drill_stats(profile, drill_id)

        pp_earned, tier, level = compute_question_pp(
            drill_id, hints_revealed, correct, correct_reps_before_this_question=stats["correct_reps"],
        )

        if correct and tier != "miss":
            stats["correct_reps"] += 1

        stats["questions_answered"] += 1
        profile["questions_answered"] += 1
        profile["tier_counts"][tier] = profile["tier_counts"].get(tier, 0) + 1
        profile["total_pp"] = round(profile["total_pp"] + pp_earned, 2)
        profile["last_played_at"] = _now_iso()

        if pp_earned > 0:
            profile["pp_history"].append({"date": _now_iso(), "total_pp": profile["total_pp"]})
            if len(profile["pp_history"]) > PP_HISTORY_LIMIT:
                profile["pp_history"] = profile["pp_history"][-PP_HISTORY_LIMIT:]

        all_profiles[user_id] = profile
        _save_all(all_profiles)
        return profile, pp_earned, tier, level


def record_session_end(
    user_id: str,
    drill_id: str,
    tier_counts: dict[str, int],
    max_combo: int,
    pp_earned_this_session: float,
    mastery_after: float | None = None,
) -> dict[str, Any]:
    """
    Logs a finished session for DISPLAY purposes (the profile screen's
    "recent sessions" / best-performance-style list) and updates
    best_mastery/max_combo_lifetime. Does NOT touch total_pp -- that's
    already been accumulated question-by-question via record_question().
    """
    total_attempts = sum(tier_counts.get(k, 0) for k in ("300", "100", "50", "miss"))
    with _lock:
        all_profiles = _load_all()
        profile = all_profiles.get(user_id) or _default_profile(user_id)

        if total_attempts == 0:
            return profile

        stats = _drill_stats(profile, drill_id)
        if mastery_after is not None:
            stats["best_mastery"] = max(stats["best_mastery"], mastery_after)

        profile["max_combo_lifetime"] = max(profile["max_combo_lifetime"], max_combo)

        accuracy_pct = round(
            (300 * tier_counts.get("300", 0) + 100 * tier_counts.get("100", 0) + 50 * tier_counts.get("50", 0))
            / (300 * total_attempts) * 100,
            2,
        )
        profile["recent_sessions"].insert(0, {
            "drill_id": drill_id,
            "date": _now_iso(),
            "accuracy_pct": accuracy_pct,
            "pp_earned": round(pp_earned_this_session, 2),
            "max_combo": max_combo,
        })
        profile["recent_sessions"] = profile["recent_sessions"][:RECENT_SESSIONS_LIMIT]

        all_profiles[user_id] = profile
        _save_all(all_profiles)
        return profile


def reset(user_id: str | None = None) -> None:
    """Mostly for tests -- clear one profile or all of them."""
    with _lock:
        all_profiles = _load_all()
        if user_id is None:
            all_profiles = {}
        else:
            all_profiles.pop(user_id, None)
        _save_all(all_profiles)
