# math-osu

A low-friction drilling tool for math (and eventually physics), styled after
osu!'s rhythm-game feedback loop. Upload a textbook or use the built-in
drills; problems are generated on the fly, hints scale with how well you
know the concept, and everyone using the same textbook lands on the same
leaderboard ("map").

## Status

Working today:
- **All 14 drills implemented** with generation + answer-checking tests
  (addition, subtraction, multiplication, division, squares, sqrts, cubes,
  cbrts, trig values, algebraic manipulation, derivatives, integrals,
  RREF, ODE basics). 75 backend tests passing.
- **Mastery -> difficulty/hints algorithm is fully wired into the live
  API** (`GET /api/problems/next/{drill_id}`): problem difficulty, time
  limit, hint count, and hint delay all actually change based on how
  well you're doing, not a fixed value.
- **Shuffle-bag question scheduling**: each drill/difficulty tier won't
  repeat a problem until every problem in its pool has been shown once
  (see `backend/app/engine/scheduler.py`).
- **osu!-style hint scoring**: no hints = "300", one hint = "100", two
  hints = "50" (combo keeps climbing through all of these); revealing the
  final hint (which states the answer) breaks combo and counts as a miss.
- **PP (performance points), v3**: awarded per QUESTION, not per session --
  each drill category has a hard, permanent ceiling on pp-per-question
  (2pp for basic arithmetic, up to 10pp for ODE/PDE), and how close you
  get to that ceiling on any given question depends on how many CORRECT
  reps you've ever done on that specific drill, via a slow logarithmic
  leveling curve (first ~10 reps worth 1pp each, next ~20 worth 2pp each,
  next ~30 worth 3pp each, and so on -- see `backend/app/engine/pp.py`).
  Hint tiers still scale pp down (a "100" earns 60%, a "50" earns 30%, a
  miss earns 0%). total_pp is a plain running sum -- no session weightage,
  no best-score-per-drill, matching a much slower, more realistic
  accumulation curve than the earlier two attempts at this system.
- **Player profile with real graphs**: a pp-over-time trend chart and a
  monthly play-history chart (both hand-rolled SVG, no charting library),
  plus a best-performance list and a most-played-drills list -- loosely
  modeled on an osu! profile page. Correctly distinguishes **play count**
  (how many times you've opened a drill -- osu!'s real "Play Count"
  metric) from **questions answered** (how many individual questions
  you've attempted, a much larger number) -- these used to be conflated.
- **LaTeX-aware math input**: the answer box is a real math editor
  (MathQuill) -- type `/` for a fraction with editable numerator/
  denominator, `sqrt` or `nthroot` for a root symbol, `^` for an
  exponent slot, same idea as Desmos or dailyintegral.org's input.
- **Implicit multiplication everywhere it matters**: prompts/answers show
  "6x" not "6\*x", and "6x"/"6\*x" are accepted as identical answers
  (`backend/app/drills/expr_utils.py`).
- **LaTeX rendering** for derivatives, integrals, squares/roots, RREF
  matrices, and trig (with an actual pi symbol, not the word "pi") via
  KaTeX in the frontend; trig values are in radians, not degrees.
- **Warm-up mechanic** with drill selection: 20-question calibration round
  that extends practice for anything you're weak on, and you choose which
  drills are in scope before starting.
- **A playable UI** at `frontend/standalone/index.html` -- no build step,
  osu!-styled, difficulty-ordered drill list, rectangular auto-sizing
  prompt box, a whiteboard canvas (with fullscreen mode) for scratch work,
  and a fill-in-the-blank matrix input for RREF. See
  `frontend/standalone/README.md` to run it.

Not built yet: the polished React app in `frontend/src/` (the standalone
HTML is a functional stand-in for now), a real database (profile storage
is a single JSON file, fine for one local player), textbook
upload/parsing, and real leaderboards (endpoint exists, but stores
nothing durable yet).

## Repo layout

- `backend/` -- FastAPI app, drill generators, adaptive-difficulty engine
- `frontend/` -- React/Vite app (styled to look like osu!; good target for Lovable)
- `content/` -- drill configs + JSON schemas, and generated textbook "maps"
- `docs/` -- architecture notes, how to author a new drill, how mastery/hints work
- `scripts/` -- dev setup helpers

See `docs/ARCHITECTURE.md` for the full picture.

## Play it right now

The fastest path to actually playing:
```bash
cd backend && uvicorn app.main:app --reload &
cd frontend/standalone && python3 -m http.server 5500
```
Then open http://localhost:5500. See `frontend/standalone/README.md` for details.

## Getting started (backend)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                            # run the test suite
uvicorn app.main:app --reload     # start the API at http://localhost:8000
```

Check it's alive:

```bash
curl http://localhost:8000/api/health
```

Generate a problem:

```bash
curl -X POST http://localhost:8000/api/problems/generate \
  -H "Content-Type: application/json" \
  -d '{"drill_id": "derivatives", "difficulty": 0.3}'
```

## Getting started (frontend)

```bash
cd frontend
npm install
npm run dev
```

This is currently a bare Vite/React skeleton -- no actual game screens yet.
If you're prototyping the look/feel in Lovable, point it at `frontend/` and
use `frontend/src/lib/api.ts` as the contract for what the backend returns.

## Adding a new drill

See `docs/DRILL_AUTHORING.md`. Short version: implement a `Drill` subclass
in `backend/app/drills/`, register it in `backend/app/drills/registry.py`,
add a config file in `content/builtin-drills/`, write tests proving the
generator and checker are correct.

## Contributing your own textbook

Not wired up yet -- `backend/app/api/uploads.py` currently just hashes the
raw file and returns a placeholder. The real pipeline lives in
`backend/app/ingestion/` (all stubs right now). See `docs/MAP_HASHING.md`
for how map identity is supposed to work once it's built.
