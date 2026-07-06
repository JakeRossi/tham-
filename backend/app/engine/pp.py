"""
PP (performance points), loosely inspired by osu!'s pp system -- NOT a
reproduction of osu's actual (proprietary, map-object-density-based)
formula, since that doesn't translate to a continuous drilling app with
no fixed "map length." Instead this is an original formula built from the
same ingredients osu!'s system is known for:

  - accuracy tier per answer (osu's 300/100/50/miss judgements)
  - combo (bigger streaks are worth more)
  - "difficulty" of what you played (osu: star rating; here: how far
    along the drill progression the drill is -- addition is easy,
    ODE/PDE and RREF are hard, see DRILL_DIFFICULTY_ORDER)
  - overall volume of play (osu doesn't really do this, but it was asked
    for explicitly: more lifetime reps -> slightly more pp per question,
    like a modest "experience" bonus, capped so it can't run away)

PP is awarded per-answer and accumulates into a lifetime total (see
profile_store.py) -- a different design than osu (which computes pp per
completed map play), chosen because practice sessions here are
open-ended, not fixed-length "maps."
"""

from __future__ import annotations

BASE_PP = 10.0

# Same order as the frontend's difficulty-ordered drill list -- earlier
# entries are "easier" and worth less pp per question, later ones "harder"
# and worth more. Kept here (not imported from anywhere) since the
# frontend list is presentation-layer JS and this is backend scoring.
DRILL_DIFFICULTY_ORDER = [
    "addition", "subtraction", "multiplication", "division",
    "squares", "sqrts", "cubes", "cbrts",
    "trig-values", "algebraic-manipulation",
    "derivatives", "integrals", "ode-pde", "rref",
]

# 1.0 for the first (easiest) drill, up to ~5.5 for the last (hardest).
DIFFICULTY_WEIGHT_STEP = 0.35


def difficulty_weight(drill_id: str) -> float:
    try:
        index = DRILL_DIFFICULTY_ORDER.index(drill_id)
    except ValueError:
        index = len(DRILL_DIFFICULTY_ORDER) // 2  # unknown drill -- assume mid-difficulty
    return 1.0 + index * DIFFICULTY_WEIGHT_STEP


# osu-style judgement tiers. "miss" covers both a wrong answer AND a
# correct-but-fully-hint-revealed answer (see app/api/problems.py) --
# being told the answer outright is graded like a miss even though the
# backend's check() still confirms it's "correct."
TIER_VALUES = {"300": 300, "100": 100, "50": 50, "miss": 0}


def judgement_tier(hints_revealed: int, correct: bool) -> str:
    """Mirrors the frontend's judgementForHints logic, but is the
    authoritative version used for actual pp/profile accounting."""
    if not correct:
        return "miss"
    if hints_revealed <= 0:
        return "300"
    if hints_revealed == 1:
        return "100"
    if hints_revealed == 2:
        return "50"
    return "miss"  # the 3rd hint IS the answer -- fully revealed


def volume_bonus(lifetime_play_count: int) -> float:
    """Modest, capped bonus for total lifetime reps -- 1.0x at 0 plays,
    scaling up to 1.5x by 500 lifetime plays, capped there."""
    return min(1.5, 1.0 + lifetime_play_count / 1000)


def combo_multiplier(combo_after: int) -> float:
    """Bigger combos are worth modestly more, capped so a single very long
    combo can't dominate the formula (osu's own combo scaling is also
    sub-linear for this reason)."""
    return 1.0 + min(combo_after, 200) / 100  # 1.0x at combo 0, up to 3.0x at combo 200+


def compute_pp(
    drill_id: str,
    hints_revealed: int,
    correct: bool,
    combo_after: int,
    lifetime_play_count_before_this_attempt: int,
) -> tuple[float, str]:
    """
    Returns (pp_earned, tier). A miss (wrong answer OR fully-revealed
    answer) always earns 0 pp -- matching the "misses should cost you"
    principle from osu, where missed notes contribute nothing.
    """
    tier = judgement_tier(hints_revealed, correct)
    tier_value = TIER_VALUES[tier]
    if tier_value == 0:
        return 0.0, tier

    pp = (
        BASE_PP
        * (tier_value / 300)                      # accuracy tier, normalized to 300=1.0
        * difficulty_weight(drill_id)
        * combo_multiplier(combo_after)
        * volume_bonus(lifetime_play_count_before_this_attempt)
    )
    return round(pp, 2), tier
