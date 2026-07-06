"""
Player profile: persistent, file-backed (JSON) so it survives backend
restarts, unlike the in-memory mastery/scheduler state elsewhere. Modeled
loosely on what an osu! profile page shows:

  osu! profile page shows          -> math-osu equivalent (this module)
  ---------------------------------------------------------------------
  Performance points (pp)          -> total_pp
  Play count                       -> play_count (lifetime questions answered)
  Ranked score / accuracy          -> lifetime_accuracy (weighted 300/100/50/miss)
  Max combo                        -> max_combo_lifetime
  Join date                        -> joined_at
  Monthly playcount graph          -> plays_by_month (dict of "YYYY-MM" -> count)
  Per-mode stats                   -> per_drill_stats (per drill_id: play_count, mastery)

Storage: a single JSON file at backend/data/profiles.json (created lazily,
gitignored). This is intentionally simple -- fine for a single local
player; swap for a real DB (see app/models/, app/db/) before this needs
to support concurrent multi-user writes safely.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PROFILES_PATH = DATA_DIR / "profiles.json"

_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _default_profile(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "joined_at": _now_iso(),
        "total_pp": 0.0,
        "play_count": 0,
        "max_combo_lifetime": 0,
        "tier_counts": {"300": 0, "100": 0, "50": 0, "miss": 0},
        "plays_by_month": {},
        "per_drill_stats": {},  # drill_id -> {"play_count": int, "best_mastery": float}
        "last_played_at": None,
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
    return profile["plays_by_month"].get(_current_month_key(), 0)


def record_attempt(
    user_id: str,
    drill_id: str,
    tier: str,
    pp_earned: float,
    combo_after: int,
    mastery_after: float,
) -> dict[str, Any]:
    """Updates and persists the profile after one graded attempt. Returns
    the updated profile."""
    with _lock:
        all_profiles = _load_all()
        profile = all_profiles.get(user_id) or _default_profile(user_id)

        profile["total_pp"] = round(profile["total_pp"] + pp_earned, 2)
        profile["play_count"] += 1
        profile["max_combo_lifetime"] = max(profile["max_combo_lifetime"], combo_after)
        profile["tier_counts"][tier] = profile["tier_counts"].get(tier, 0) + 1

        month_key = _current_month_key()
        profile["plays_by_month"][month_key] = profile["plays_by_month"].get(month_key, 0) + 1

        drill_stats = profile["per_drill_stats"].setdefault(
            drill_id, {"play_count": 0, "best_mastery": 0.0}
        )
        drill_stats["play_count"] += 1
        drill_stats["best_mastery"] = max(drill_stats["best_mastery"], mastery_after)

        profile["last_played_at"] = _now_iso()

        all_profiles[user_id] = profile
        _save_all(all_profiles)
        return profile


def get_lifetime_play_count(user_id: str) -> int:
    """Cheap read used by pp.py's volume bonus -- doesn't need the full profile."""
    return get_profile(user_id)["play_count"]


def reset(user_id: str | None = None) -> None:
    """Mostly for tests -- clear one profile or all of them."""
    with _lock:
        all_profiles = _load_all()
        if user_id is None:
            all_profiles = {}
        else:
            all_profiles.pop(user_id, None)
        _save_all(all_profiles)
