# math-osu

A low-friction drilling tool for math (and eventually physics), styled after
osu!'s rhythm-game feedback loop. Upload a textbook or use the built-in
drills; problems are generated on the fly, hints scale with how well you
know the concept, and everyone using the same textbook lands on the same
leaderboard ("map").

## Status

Early scaffold. Working today:
- `addition` / `subtraction` drills (arithmetic)
- `derivatives` drill (single-variable + partial, sympy-backed, accepts
  any algebraically equivalent answer)
- Warm-up mechanic: 20-question calibration round that extends practice
  for any concept you're weak on
- FastAPI skeleton with problem generation, warm-up sessions, leaderboard
  and textbook-upload endpoints (leaderboard + upload are stubs)

Not built yet: everything in `content/builtin-drills/*.json` with
`"implemented": false`, the textbook parsing pipeline, the real frontend,
persistent storage (everything is in-memory right now).

## Repo layout

- `backend/` -- FastAPI app, drill generators, adaptive-difficulty engine
- `frontend/` -- React/Vite app (styled to look like osu!; good target for Lovable)
- `content/` -- drill configs + JSON schemas, and generated textbook "maps"
- `docs/` -- architecture notes, how to author a new drill, how mastery/hints work
- `scripts/` -- dev setup helpers

See `docs/ARCHITECTURE.md` for the full picture.

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
