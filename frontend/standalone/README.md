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
  `GET /api/maps/builtin`, ordered by difficulty (not alphabetically) and
  color-coded by category.
- **Practice mode**: calls `GET /api/problems/next/{drill_id}`, which
  runs the real mastery -> difficulty/hint algorithm (not a fixed
  difficulty) -- so hints and problem difficulty should visibly shift as
  you play more of one drill. Questions won't repeat until every problem
  in the current difficulty tier's pool has been shown once (shuffle-bag
  scheduling -- see `backend/app/engine/scheduler.py`).
- **Warm-up mode**: drives `POST /api/sessions/warmup/*`, matching the
  original "20 questions, extend the ones you're weak on" design.
- **Scoring**: osu!-style hint tiers -- answering with no hints scores
  "300", one hint scores "100", two hints scores "50" (combo keeps
  climbing through all of these); revealing the final hint (which states
  the answer outright) breaks your combo and counts as a miss for
  accuracy, even if you then type the right answer.
- **Math notation**: derivatives, integrals, squares, sqrts, cubes, cbrts,
  and RREF all render as real LaTeX (via KaTeX) -- exponents, radicals,
  and whole matrices, not ASCII text; trig shows an actual pi symbol
  (rendered via LaTeX), not the word "pi"; algebra/derivative/integral/ODE
  answers accept "6x" and "6\*x" interchangeably; trig values are in
  radians rather than degrees.
- **Warm-up drill selection**: clicking "Warm Up" opens a checklist of
  every implemented drill (checked by default) so you can exclude
  anything you don't want mixed in yet (e.g. skip RREF/ODE until you've
  covered the basics).
- **Whiteboard**: a larger always-visible drawing canvas under the answer
  box for scratch work (not graded), with color swatches, Ctrl+Z undo,
  and a "Fullscreen" button that pins the current question in the
  corner, gives you the whole screen to draw on, and keeps the answer box
  reachable in a floating bar at the bottom. Fullscreen and inline share
  the same drawing (a single offscreen canvas both views render from), so
  nothing is lost switching between them.
- **Fill-in-the-blank matrix input for RREF**: instead of typing a raw
  list, you get an actual bracketed grid of number boxes matching the
  matrix's dimensions -- blank cells default to 0.
- **Question count**: the HUD shows how many questions you've answered
  this session, alongside score/combo/accuracy.
- **PP + player profile, v3**: pp is awarded per question, hard-capped
  per drill category (2pp for basic arithmetic up to 10pp for ODE/PDE),
  and slow to level up (the first ~10 correct reps on a drill are worth
  1pp each, the next ~20 worth 2pp each, and so on) -- deliberately slow,
  the same way real pp is hard-won. Click "View profile" in the header
  for a pp-over-time trend graph, a monthly play-history graph, a
  best-performance list, and a most-played-drills list. **Play count**
  (drill opens) and **questions answered** (individual questions
  attempted) are tracked as two separate numbers, not conflated.
- **LaTeX math input**: the answer box (MathQuill) supports typing `/`
  for a fraction, `sqrt`/`nthroot` for a root, `^` for an exponent --
  same idea as Desmos or dailyintegral.org. Requires internet access to
  load from its CDN; falls back to a plain text box if that fails.
- S/A/B/C/D rank at the end based on that weighted accuracy.

## Known limitations (intentional, for a fast first playable build)

- No persistence -- mastery lives in the backend's in-memory store and
  resets when the backend restarts (see `app/engine/user_state.py`).
- Single implicit user (`"local"`) -- no login/accounts yet.
- No leaderboard UI yet, even though the backend has a (stubbed)
  leaderboard endpoint.
- Styling is intentionally simple CSS, not the eventual polished
  React/Tailwind app -- treat this as a functional reference, not a
  design target to preserve.
