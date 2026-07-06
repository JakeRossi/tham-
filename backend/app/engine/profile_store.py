"""
Player profile: persistent, file-backed (JSON) so it survives backend
restarts. Rebuilt so pp accounting actually matches osu!'s real mechanics
(see app/engine/pp.py's module docstring) -- total_pp is DERIVED from each
drill's best-ever session score, combined via osu's weightage decay, not
accumulated per question.

  osu! profile page shows          -> math-osu equivalent (this module)
  ---------------------------------------------------------------------
  Performance points (pp)          -> total_pp (derived, see pp.py)
  Play count                       -> play_count (lifetime questions answered)
  Ranked score / accuracy          -> lifetime_accuracy (weighted 300/100/50/miss)
  Max combo                        -> max_combo_lifetime
  Join date                        -> joined_at
  Monthly playcount graph          -> plays_by_month (dict of "YYYY-MM" -> count)
  Best score per beatmap           -> per_drill_stats[drill_id]["best_pp"]

Storage: a single JSON file at backend/data/profiles.json (created lazily,
gitignored). Intentionally simple -- fine for a single local player;
swap for a real DB before this needs concurrent multi-user writes.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.engine.pp import accuracy_fraction_from_tiers, compute_run_pp, total_pp_from_best_scores

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
        "per_drill_stats": {},  # drill_id -> {"play_count", "best_mastery", "best_pp"}
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


def _recompute_total_pp(profile: dict[str, Any]) -> None:
    best_scores = {
        drill_id: stats.get("best_pp", 0.0) for drill_id, stats in profile["per_drill_stats"].items()
    }
    profile["total_pp"] = total_pp_from_best_scores(best_scores)


def get_profile(user_id: str) -> dict[str, Any]:
    with _lock:
        all_profiles = _load_all()
        profile = all_profiles.get(user_id) or _default_profile(user_id)
        _recompute_total_pp(profile)  # defensive -- always derive fresh, never trust a stale cached value
        return profile


def lifetime_accuracy(profile: dict[str, Any]) -> float:
    return round(accuracy_fraction_from_tiers(profile["tier_counts"]) * 100, 2) if sum(
        profile["tier_counts"].values()
    ) else 100.0


def questions_this_month(profile: dict[str, Any]) -> int:
    return profile["plays_by_month"].get(_current_month_key(), 0)


def record_session(
    user_id: str,
    drill_id: str,
    tier_counts: dict[str, int],
    max_combo: int,
    mastery_after: float | None = None,
) -> tuple[dict[str, Any], float, bool]:
    """
    Records one finished play session on one drill -- analogous to
    finishing one osu! beatmap. Computes this run's pp value, and if it
    beats the drill's previous best, updates it (only your best score per
    drill counts towards total_pp, exactly like osu!'s per-beatmap best
    score). Returns (updated_profile, run_pp, is_new_best_for_drill).
    """
    total_attempts = sum(tier_counts.get(k, 0) for k in ("300", "100", "50", "miss"))
    with _lock:
        all_profiles = _load_all()
        profile = all_profiles.get(user_id) or _default_profile(user_id)

        if total_attempts == 0:
            _recompute_total_pp(profile)
            return profile, 0.0, False

        accuracy_fraction = accuracy_fraction_from_tiers(tier_counts)
        run_pp = compute_run_pp(drill_id, accuracy_fraction, max_combo)

        drill_stats = profile["per_drill_stats"].setdefault(
            drill_id, {"play_count": 0, "best_mastery": 0.0, "best_pp": 0.0}
        )
        drill_stats["play_count"] += total_attempts
        if mastery_after is not None:
            drill_stats["best_mastery"] = max(drill_stats["best_mastery"], mastery_after)

        is_new_best = run_pp > drill_stats["best_pp"]
        if is_new_best:
            drill_stats["best_pp"] = run_pp

        # Lifetime aggregate bookkeeping (accuracy display, monthly activity,
        # overall play count) -- separate from the per-drill best-score pp math.
        for tier in ("300", "100", "50", "miss"):
            profile["tier_counts"][tier] = profile["tier_counts"].get(tier, 0) + tier_counts.get(tier, 0)
        profile["play_count"] += total_attempts
        profile["max_combo_lifetime"] = max(profile["max_combo_lifetime"], max_combo)

        month_key = _current_month_key()
        profile["plays_by_month"][month_key] = profile["plays_by_month"].get(month_key, 0) + total_attempts

        profile["last_played_at"] = _now_iso()

        _recompute_total_pp(profile)
        all_profiles[user_id] = profile
        _save_all(all_profiles)
        return profile, run_pp, is_new_best


def get_lifetime_play_count(user_id: str) -> int:
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
