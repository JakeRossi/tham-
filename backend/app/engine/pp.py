"""
PP (performance points), rebuilt to actually follow osu!'s documented
mechanics (see the osu! wiki's "Performance points" article) rather than
awarding pp per individual question, which is NOT how osu! works.

How osu! actually does it, and the mapping used here:

  osu! concept                          math-osu equivalent
  ------------------------------------------------------------------
  One score on one beatmap              One finished session on one drill
  Star rating (beatmap difficulty)      difficulty_weight(drill_id) --
                                         position in the difficulty
                                         progression (addition easy,
                                         rref/ode-pde hard)
  Aim/speed/strain (performance)         combo_factor(max_combo) -- a
                                         (rough) stand-in for "how much
                                         sustained difficulty you handled"
  Accuracy (heavily, non-linearly        accuracy_fraction ** ACCURACY_EXPONENT
  weighted -- osu notes an 80% FC        (osu's own docs give an example:
  can be worth ~2/3 of a 95% score)      an 80% FC is worth about 2/3 of a
                                         95% score -- ACCURACY_EXPONENT=2.5
                                         reproduces that ratio: see
                                         test_pp.py)
  Only your BEST score per beatmap       best_pp per drill_id, only
  counts towards total pp                replaced if a session beats it
  Weightage: nth-best score counts       weighted_total_pp(): identical
  for 0.95^(n-1) of its value            formula, applied across your
                                         best score on each of the (up to
                                         14) drills instead of thousands
                                         of beatmaps
  Bonus pp for breadth of maps played:   bonus_pp(): the exact documented
  416.6667 * (1 - 0.995^min(N,1000))     formula, where N = number of
                                         drills you have ANY best score on
                                         (naturally capped at 14 here,
                                         since that's all there is)

This is still an adaptation, not a byte-for-byte port -- osu!'s real
aim/speed/strain values come from analyzing beatmap object placement,
which has no equivalent in a drilling app. The accuracy/weightage/bonus
mechanics, though, are taken directly from the documented formulas.
"""

from __future__ import annotations

import math

BASE_PP = 50.0

# Same order as the frontend's difficulty-ordered drill list -- earlier
# entries are "easier" (lower star-rating equivalent), later ones "harder".
DRILL_DIFFICULTY_ORDER = [
    "addition", "subtraction", "multiplication", "division",
    "squares", "sqrts", "cubes", "cbrts",
    "trig-values", "algebraic-manipulation",
    "derivatives", "integrals", "ode-pde", "rref",
]
DIFFICULTY_WEIGHT_STEP = 0.35  # 1.0 for the easiest drill, ~5.55 for the hardest

# Fit so that (0.80/0.95) ** ACCURACY_EXPONENT ≈ 0.66, matching osu!'s own
# documented example that an 80% full-combo is worth roughly 2/3 of a 95%
# accuracy score.
ACCURACY_EXPONENT = 2.5

# osu!'s weightage system: Total pp = p * 0.95^(n-1) for the nth-best score.
WEIGHT_DECAY = 0.95

# osu!'s documented bonus-pp formula for number of ranked maps scored on.
BONUS_MAX = 416.6667
BONUS_DECAY = 0.995


def difficulty_weight(drill_id: str) -> float:
    try:
        index = DRILL_DIFFICULTY_ORDER.index(drill_id)
    except ValueError:
        index = len(DRILL_DIFFICULTY_ORDER) // 2  # unknown drill -- assume mid-difficulty
    return 1.0 + index * DIFFICULTY_WEIGHT_STEP


def combo_factor(max_combo: int) -> float:
    """Rough stand-in for osu's aim/speed/strain contribution: sustaining a
    longer combo reflects handling more of the drill's difficulty
    consistently, with diminishing returns rather than unbounded scaling."""
    return 1.0 + math.log10(1 + max(0, max_combo)) / 2


def judgement_tier(hints_revealed: int, correct: bool) -> str:
    """
    Classifies a single answered question into an osu-style accuracy
    judgement. This is ONLY used to build up a session's tier_counts for
    the accuracy calculation below -- it does NOT award pp by itself
    (osu!'s 300/100/50 are accuracy judgements, not currency).
    """
    if not correct:
        return "miss"
    if hints_revealed <= 0:
        return "300"
    if hints_revealed == 1:
        return "100"
    if hints_revealed == 2:
        return "50"
    return "miss"  # the 3rd hint IS the answer -- fully revealed


def accuracy_fraction_from_tiers(tier_counts: dict[str, int]) -> float:
    """Same weighting osu! uses: (300*c300 + 100*c100 + 50*c50) / (300*total)."""
    total = sum(tier_counts.get(k, 0) for k in ("300", "100", "50", "miss"))
    if total == 0:
        return 0.0
    weighted = 300 * tier_counts.get("300", 0) + 100 * tier_counts.get("100", 0) + 50 * tier_counts.get("50", 0)
    return weighted / (300 * total)


def compute_run_pp(drill_id: str, accuracy_fraction: float, max_combo: int) -> float:
    """
    The raw pp value ONE finished session on ONE drill is worth --
    analogous to what a single score on a single osu! beatmap is worth,
    BEFORE the weightage system reduces it based on ranking among your
    other best scores.
    """
    accuracy_fraction = max(0.0, min(1.0, accuracy_fraction))
    return round(
        BASE_PP * difficulty_weight(drill_id) * (accuracy_fraction ** ACCURACY_EXPONENT) * combo_factor(max_combo),
        2,
    )


def weighted_total_pp(best_pp_values: list[float]) -> float:
    """osu!'s weightage system applied across your best score on each drill:
    best score counts fully, 2nd-best counts for 95% of its value, 3rd-best
    for 95%^2, and so on."""
    sorted_desc = sorted(best_pp_values, reverse=True)
    return round(sum(p * (WEIGHT_DECAY ** i) for i, p in enumerate(sorted_desc)), 2)


def bonus_pp(num_drills_with_a_score: int) -> float:
    """osu!'s documented bonus-pp formula, verbatim. N is naturally capped
    at 14 here (the number of drills), so the bonus will always be modest
    -- but it's the same formula, not a rescaled approximation."""
    n = min(num_drills_with_a_score, 1000)
    return round(BONUS_MAX * (1 - BONUS_DECAY ** n), 2)


def total_pp_from_best_scores(per_drill_best_pp: dict[str, float]) -> float:
    """Given each drill's best-ever run_pp, computes the profile's total pp:
    weighted sum of best scores, plus the breadth-of-play bonus."""
    best_values = [v for v in per_drill_best_pp.values() if v > 0]
    return round(weighted_total_pp(best_values) + bonus_pp(len(best_values)), 2)
