# Architecture

## Core loop

1. User picks a **map** (a builtin drillset, or an uploaded textbook that's
   been parsed into one) -- analogous to picking a song in osu!.
2. If it's their first session with that map (or they explicitly ask for
   warm-up), they go through `WarmupSession` (`backend/app/engine/warmup.py`):
   20 problems spread across every drill in the map, with extension rounds
   for anything they're weak on. This produces an initial per-concept
   mastery vector.
3. In normal play, `engine/difficulty.py` turns the current mastery vector
   into concrete parameters for the next problem: difficulty, time limit,
   hint count, hint delay.
4. `Drill.generate()` produces a problem at that difficulty. `Drill.check()`
   grades the submitted answer -- for math with multiple valid forms (like
   derivatives), this is a symbolic equivalence check via sympy, not string
   matching.
5. Each attempt feeds back into `engine/mastery.py`'s Elo-style update,
   which adjusts the mastery vector for next time.
6. Score/combo (osu!-style) gets submitted to `leaderboards.py`, scoped to
   the map_hash -- so only people using the identical drillset/textbook
   compete against each other.

## Why drills are generators, not question banks

A fixed bank of questions runs out, gets memorized, and can't scale
difficulty smoothly. Each drill in `backend/app/drills/` is a parametric
generator: given a difficulty float (0.0-1.0), it produces a new, unique
problem plus its canonical answer plus a sequence of progressive hints.
This is what lets warm-up and adaptive difficulty work at all -- the engine
just asks a drill for "something at difficulty 0.6" and gets a fresh
problem every time.

## Why sympy for calculus/algebra drills

Two reasons:
- **Generation**: sympy can build random polynomials/expressions and
  compute their derivative/integral/simplification exactly, so the
  generator and the answer key can never drift apart.
- **Checking**: `sp.simplify(submitted - answer) == 0` accepts any
  algebraically equivalent form of the answer. Without this, a user who
  correctly writes `5 + 2*x` instead of `2*x + 5` would be marked wrong,
  which would be a bad, unfair experience for a math drilling tool
  specifically.

## What's stubbed vs real right now

Real (has passing tests): `AdditionDrill`, `SubtractionDrill`,
`DerivativesDrill`, `WarmupSession`, `update_mastery`.

Stubbed (compiles, returns plausible-looking data, not wired to a real
DB or algorithm yet): `leaderboards.py` (in-memory list), `uploads.py`
(returns a hash of raw bytes, not parsed content), `maps.py` (only reads
builtin JSON, textbook-maps/ directory is never populated),
`app/models/*` and `app/db/*` (empty -- no persistence layer exists yet;
everything lives in process memory and resets when the server restarts).

## Suggested build order from here

1. Pick a DB (Postgres is the obvious default) and fill in `app/models/`
   + `app/db/session.py` + alembic migrations. Move `WarmupSession` state
   and leaderboard entries out of in-memory dicts.
2. Implement 2-3 more drills (multiplication/division are the easiest next
   step; RREF is a good sympy showcase -- `sp.Matrix.rref()` does the heavy
   lifting).
3. Build the actual frontend screens against the existing API, even before
   ingestion or auth exist -- `content/builtin-drills/` gives you real
   content to build against today.
4. Textbook ingestion last -- it's the highest-effort, highest-ambiguity
   piece (parsing arbitrary PDF exercise formats), and the rest of the app
   works fine without it in the meantime.
