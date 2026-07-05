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
  RREF, ODE basics). 74 backend tests passing.
- **Mastery -> difficulty/hints algorithm is fully wired into the live
  API** (`GET /api/problems/next/{drill_id}`): problem difficulty, time
  limit, hint count, and hint delay all actually change based on how
  well you're doing, not a fixed value.
- **Warm-up mechanic**: 20-question calibration round that extends
  practice for anything you're weak on, exposed via
  `POST /api/sessions/warmup/*`.
- **A playable UI** at `frontend/standalone/index.html` -- no build step,
  osu!-styled, pick a drill and play, or run the full warm-up. See
  `frontend/standalone/README.md` to run it.

Not built yet: the polished React app in `frontend/src/` (the standalone
HTML is a functional stand-in for now), persistent storage (everything's
in-memory and resets on backend restart), textbook upload/parsing, and
real leaderboards (endpoint exists, but stores nothing durable yet).

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
