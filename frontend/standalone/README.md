# Standalone frontend (no build step)

A single-file, dependency-free UI so you can actually play against the
backend right now, before the real Vite/React app (`frontend/src/`) has
any screens built. This is meant as a working prototype / reference for
what the eventual React app should do -- not the final UI.

## Run it

1. Start the backend (see the root `README.md`):
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Serve this folder (don't just double-click `index.html` -- some
   browsers restrict `fetch()` from `file://` pages in ways that cause
   confusing failures; a tiny local server avoids that entirely):
   ```bash
   cd frontend/standalone
   python3 -m http.server 5500
   ```

3. Open **http://localhost:5500** in your browser.

That's it -- pick a drill card to practice it directly, or hit "Warm Up"
to run the 20-question calibration round across every drill.

## What it does

- **Song select**: pulls the list of implemented drills from
  `GET /api/maps/builtin`, color-coded by category.
- **Practice mode**: calls `GET /api/problems/next/{drill_id}`, which
  runs the real mastery -> difficulty/hint algorithm (not a fixed
  difficulty) -- so hints and problem difficulty should visibly shift as
  you play more of one drill.
- **Warm-up mode**: drives `POST /api/sessions/warmup/*`, matching the
  original "20 questions, extend the ones you're weak on" design.
- **Scoring**: osu!-style combo multiplier + speed bonus, S/A/B/C/D rank
  at the end based on accuracy.

## Known limitations (intentional, for a fast first playable build)

- No persistence -- mastery lives in the backend's in-memory store and
  resets when the backend restarts (see `app/engine/user_state.py`).
- Single implicit user (`"local"`) -- no login/accounts yet.
- No leaderboard UI yet, even though the backend has a (stubbed)
  leaderboard endpoint.
- Styling is intentionally simple CSS, not the eventual polished
  React/Tailwind app -- treat this as a functional reference, not a
  design target to preserve.
