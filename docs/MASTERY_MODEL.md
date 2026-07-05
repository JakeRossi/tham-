# Mastery model

## Current implementation (simple, deliberately)

`backend/app/engine/mastery.py` tracks a single float per (user, concept)
in `[0.0, 1.0]`. Every attempt nudges it via an Elo-style update:

- correct + fast + no hints on a hard problem -> big upward move
- wrong, or correct-but-slow/hint-assisted -> flat or downward move

The magnitude of the move scales with `K_FACTOR` and the problem's
difficulty, so getting an easy problem right barely moves the needle,
while nailing a hard one does.

This is intentionally simple. It's *not* Bayesian Knowledge Tracing or
IRT -- those model "probability the learner has mastered this skill"
more rigorously, accounting for guessing/slipping probabilities, but need
more data and tuning to get right. Start here, swap later if the simple
version isn't discriminating well (e.g. if mastery scores don't track
with how a user actually feels about a concept).

## How mastery feeds the rest of the app

- **Difficulty** (`engine/difficulty.py`): higher mastery -> harder
  problems, less time, fewer/later hints. First-time learners get a fixed
  easy/generous setting regardless of their (necessarily near-zero)
  mastery score, because the *reason* for low mastery matters -- "never
  seen this" and "seen it, still struggling" should feel different.
- **Warm-up** (`engine/warmup.py`): concepts below a mastery threshold
  (default 0.4, see `is_weak_concept`) get extra reps beyond the initial
  20-question round, up to a safety cap of extension rounds.
- **(Not yet built) Session problem selection**: outside of warm-up, the
  app should weight problem selection toward weaker concepts rather than
  uniform-random across the map's drills -- this doesn't exist yet, it's
  a natural next feature once persistence exists.

## Open questions worth deciding before this scales

- Should mastery decay over time if a concept isn't practiced? (Spaced-
  repetition-style forgetting curve -- probably yes, eventually.)
- Should "first exposure" be tracked explicitly per user/concept, or
  inferred from attempt count == 0? Currently the API assumes the caller
  (frontend) knows and passes it in -- there's no server-side tracking of
  "have I seen this before" yet.
- How much should hint usage penalize mastery vs. just slow down score
  gain? Right now a used hint caps performance at 0.4 for that attempt
  even if ultimately correct -- tune this once you have real usage data.
