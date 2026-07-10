# math-osu

A low-friction drilling tool for math (and eventually physics), styled after
osu!'s rhythm-game feedback loop. Upload a textbook or use the built-in
drills; problems are generated on the fly, hints scale with how well you
know the concept, and everyone using the same textbook lands on the same
leaderboard ("map").

## Status

Working today:
- **All 14 drills implemented**, with **derivatives and integrals now
  genuinely varied** (polynomials, trig, exponentials, product/quotient/
  chain rule, up to 2-variable partials) instead of only polynomials --
  see `backend/app/drills/function_library.py` for the 16-level content
  progression. 98 backend tests passing.
- **Mastery -> difficulty/hints algorithm, now combo/accuracy-
  accelerated**: a long combo or high recent accuracy speeds up how fast
  you climb through difficulty (either signal alone helps; a big combo
  helps more than merely-high accuracy) -- see `backend/app/engine/mastery.py`.
- **In-game mods**: click a drill to choose "adaptive" (default) or a
  specific starting difficulty level (1-10); arithmetic drills also let
  you lock in a specific digit count (1-4).
- **Shuffle-bag question scheduling**, now with a defensive early-exit if
  a drill/level's parameter space turns out smaller than expected -- this
  is what was behind an earlier bug where partial-derivative questions
  got stuck repeating. See `backend/app/engine/scheduler.py`.
- **osu!-style hint scoring**: no hints = "300", one hint = "100", two
  hints = "50" (combo keeps climbing through all of these); revealing the
  final hint (which states the answer) breaks combo and counts as a miss.
- **PP (performance points)**: awarded per question with hard per-drill
  caps and slow logarithmic leveling (see `backend/app/engine/pp.py`),
  but total_pp is the weighted sum of your best 200 finished-session
  "plays" across all drills (osu!'s real 0.95^n weightage) -- a worse
  play literally cannot lower your total if better plays already exist.
- **Player profile with real graphs**: a pp-over-time trend chart and a
  monthly play-history chart (both hand-rolled SVG, no charting library),
  plus a best-performance list and a most-played-drills list -- loosely
  modeled on an osu! profile page. Correctly distinguishes **play count**
  (how many times you've opened a drill -- osu!'s real "Play Count"
  metric) from **questions answered** (how many individual questions
  you've attempted, a much larger number).
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
  prompt box, a whiteboard canvas (with fullscreen mode, undo, color
  picker) for scratch work, a fill-in-the-blank matrix input for RREF,
  and a clickable logo to return home. See `frontend/standalone/README.md`
  to run it.

**Known bug fixed**: if you saw "Failed to fetch" errors with gameplay
seemingly stuck on the same question, it was caused by `uvicorn --reload`
watching (and restarting the server in reaction to changes in)
`backend/data/profiles.json`, which gets rewritten on every answered
question -- see the run instructions below for the fix (`--reload-dir app`).

Not built yet: the polished React app in `frontend/src/` (the standalone
HTML is a functional stand-in for now), a real database (profile storage
is a single JSON file, fine for one local player), textbook
upload/parsing, real leaderboards, and 3+ variable calculus.

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
cd backend && uvicorn app.main:app --reload --reload-dir app &
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
uvicorn app.main:app --reload --reload-dir app   # start the API at http://localhost:8000
```

**Important: always include `--reload-dir app`.** Without it, uvicorn's
`--reload` watches the entire `backend/` folder for changes -- including
`backend/data/profiles.json`, which gets rewritten on every answered
question. Uvicorn treats that write as "code changed" and restarts the
whole server mid-session, which drops the connection and shows up as
"Failed to fetch" errors with the game seemingly frozen on the last
question you saw. `--reload-dir app` restricts the watcher to the actual
source code.

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
