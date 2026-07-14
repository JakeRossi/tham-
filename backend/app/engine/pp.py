"""
PP (performance points) -- v4.

v1 awarded pp per question with an unbounded formula (too generous). v2
tried to mirror osu!'s best-score/weightage/bonus system applied per
DRILL, but that awarded too much pp per sitting. v3 went to a pure
per-question running sum with hard caps -- simple and well-behaved, but
lost osu!'s real "only your best plays count" property (a mediocre play
could never make your total pp go DOWN, but it could also never be
"wasted" the way a real osu! score outside your top plays is). v4 keeps
v3's per-question cap/leveling formula (still governs how much any single
question can ever be worth) but changes how those add up into a lifetime
total, to match osu!'s actual top-N-plays design:

  - Each drill CATEGORY has a hard ceiling on pp-per-question, ever:
        arithmetic family (add/sub/mul/div/squares/sqrts/cubes/cbrts): 2pp
        trig-values: 4pp   |  algebraic-manipulation: 3pp
        derivatives: 5pp   |  integrals: 7pp
        rref: 4pp          |  ode-pde: 10pp
  - Within that ceiling, how much a single correct answer is worth
    depends on how many correct reps you've ever done on that SPECIFIC
    drill: the first ~10 reps are worth 1pp each, the next ~20 (up to 30
    total) are worth 2pp each, the next ~30 (up to 60 total) are worth
    3pp each, and so on -- each level requires MORE additional reps than
    the last (a triangular-number threshold), until the drill's category
    cap is reached.
  - Hint tiers still matter: a "300" (no hints) earns the full amount for
    your current level, "100" (1 hint) earns 60% of it, "50" (2 hints)
    earns 30%, and a miss (wrong, or the answer fully revealed) earns 0.
  - Each finished SESSION on a drill sums its questions' pp into one
    "play" value -- analogous to one score on one osu! beatmap. Only your
    best TOP_N_PLAYS=200 plays (across every drill, not deduplicated by
    drill) count towards total_pp, combined with osu!'s real weightage
    decay (0.95^(n-1) for the nth-best play). A new, worse play never
    lowers your total if your existing top 200 are already better --
    matching osu!'s actual "your best plays define your pp" design,
    which a pure running sum (v3) didn't have.

This isn't a literal reproduction of osu!'s real formula (which computes
pp from analyzed beatmap object placement) -- it's a simpler system tuned
to the same *spirit*: pp should be hard-won, grinding easy content should
never be more efficient than tackling hard content well, and your total
should reflect your best performances, not just how much you've played.
"""

from __future__ import annotations

import math

# Hard per-question pp ceiling by drill. All 8 "basic arithmetic" drills
# share one ceiling; everything else has its own.
_ARITHMETIC_DRILLS = {
    "addition", "subtraction", "multiplication", "division",
    "squares", "sqrts", "cubes", "cbrts",
}

QUESTION_PP_CAP = {
    "trig-values": 4,
    "algebraic-manipulation": 3,
    "limits": 4,
    "derivatives": 5,
    "integrals": 7,
    "rref": 4,
    "ode-pde": 10,
}
DEFAULT_ARITHMETIC_CAP = 2

# Judgement tier -> fraction of the current level's pp value earned.
TIER_MULTIPLIER = {"300": 1.0, "100": 0.6, "50": 0.3, "miss": 0.0}


def question_pp_cap(drill_id: str) -> int:
    if drill_id in _ARITHMETIC_DRILLS:
        return DEFAULT_ARITHMETIC_CAP
    return QUESTION_PP_CAP.get(drill_id, DEFAULT_ARITHMETIC_CAP)


def pp_level_for_reps(correct_reps: int) -> int:
    """
    Triangular-threshold leveling: level 1 for reps 0-9, level 2 for
    10-29, level 3 for 30-59, level 4 for 60-99, ... -- level k starts at
    cumulative rep count 5*k*(k-1) (a triangular number scaled by 10),
    which is what produces the "1-10, 10-30, 30-60, ..." pattern.
    Uncapped -- callers combine this with question_pp_cap().
    """
    if correct_reps < 10:
        return 1
    # Solve k(k-1)/2 <= reps/10 for the largest integer k, then level = k+1.
    k = int((-1 + math.sqrt(1 + 8 * (correct_reps / 10))) / 2)
    return k + 1


def judgement_tier(hints_revealed: int, correct: bool) -> str:
    """
    Classifies one answered question into an osu-style accuracy judgement.
    hints_revealed >= 3 means the final hint (which states the answer
    outright) was used -- graded like a miss even if technically correct.
    """
    if not correct:
        return "miss"
    if hints_revealed <= 0:
        return "300"
    if hints_revealed == 1:
        return "100"
    if hints_revealed == 2:
        return "50"
    return "miss"


def accuracy_fraction_from_tiers(tier_counts: dict[str, int]) -> float:
    """Same weighting osu! uses: (300*c300 + 100*c100 + 50*c50) / (300*total)."""
    total = sum(tier_counts.get(k, 0) for k in ("300", "100", "50", "miss"))
    if total == 0:
        return 0.0
    weighted = 300 * tier_counts.get("300", 0) + 100 * tier_counts.get("100", 0) + 50 * tier_counts.get("50", 0)
    return weighted / (300 * total)


def compute_question_pp(
    drill_id: str,
    hints_revealed: int,
    correct: bool,
    correct_reps_before_this_question: int,
) -> tuple[float, str, int]:
    """
    Returns (pp_earned, tier, level). A miss earns 0 pp and doesn't
    advance the leveling curve (correct_reps only counts CORRECT answers,
    tracked by the caller/profile store).
    """
    tier = judgement_tier(hints_revealed, correct)
    if tier == "miss":
        return 0.0, tier, pp_level_for_reps(correct_reps_before_this_question)

    cap = question_pp_cap(drill_id)
    level = min(pp_level_for_reps(correct_reps_before_this_question), cap)
    pp_earned = round(level * TIER_MULTIPLIER[tier], 2)
    return pp_earned, tier, level


# ---------------------------------------------------------------------------
# Aggregation: total_pp is NOT a running sum of every question ever answered
# (that would let raw volume dominate). Instead, each finished SESSION on a
# drill produces one "play" value (the sum of that session's per-question
# pp, each already capped/leveled by compute_question_pp above) -- directly
# analogous to one score on one osu! beatmap. Only the best TOP_N_PLAYS of
# those, combined with osu's real weightage decay (0.95^(n-1) for the nth-
# best), count towards total_pp. A new, worse play doesn't reduce your
# total if your existing top plays are already better -- matching osu!'s
# actual "your best scores define your pp" design.
# ---------------------------------------------------------------------------

TOP_N_PLAYS = 200
WEIGHT_DECAY = 0.95


def total_pp_from_plays(play_pp_values: list[float]) -> float:
    """Takes every recorded play's pp value, keeps only the best
    TOP_N_PLAYS, and combines them with weightage decay."""
    top_plays = sorted(play_pp_values, reverse=True)[:TOP_N_PLAYS]
    return round(sum(p * (WEIGHT_DECAY ** i) for i, p in enumerate(top_plays)), 2)
