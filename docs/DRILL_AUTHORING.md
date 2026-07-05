# Adding a new drill

Use `backend/app/drills/arithmetic.py::AdditionDrill` (simple, no external
libs) or `backend/app/drills/calculus.py::DerivativesDrill` (sympy-backed)
as your template, depending on whether the drill needs symbolic math.

## Steps

1. **Implement the class** in the relevant file under `backend/app/drills/`
   (create a new file if it's a new category, e.g. `linalg.py` for RREF).
   Subclass `Drill` from `base.py` and implement:
   - `generate(difficulty, rng_seed) -> Problem`
   - `check(problem, submitted) -> CheckResult`
   - optionally override `hint(problem, level)` if hints need to be dynamic
     (e.g. depend on the user's specific wrong answer) rather than
     precomputed in `Problem.hints`.

2. **Make difficulty actually do something.** Every drill needs some clear
   mapping from `difficulty: float (0.0-1.0)` to a harder/easier problem --
   more digits, higher degree, more variables, whatever's appropriate. Look
   at `_digits_for_difficulty` in `arithmetic.py` or `_degree_for_difficulty`
   in `calculus.py` for the pattern.

3. **Register it** in `backend/app/drills/registry.py` -- add an instance
   to the `REGISTRY` dict.

4. **Flip `"implemented": true`** in the matching
   `content/builtin-drills/<id>.json` config file.

5. **Write tests** in `backend/tests/drills/test_<category>.py` proving:
   - the generator's answer is actually correct (recompute it independently
     in the test, don't just trust the drill's own math)
   - difficulty scaling does something observable
   - the checker accepts correct answers and rejects wrong ones
   - the checker doesn't crash on garbage input
   - (if applicable) the checker accepts equivalent-but-differently-formatted
     correct answers -- this matters a lot for anything symbolic

6. Run `pytest` from `backend/` and make sure everything passes.

## Notes on specific upcoming drills

- **Multiplication/Division**: same shape as addition/subtraction, just
  swap the operator and decide how division handles remainders/decimals
  across difficulty tiers.
- **Squares/Sqrts/Cubes/Cbrts**: at low difficulty, keep sqrt/cbrt inputs
  as perfect squares/cubes so the answer is a clean integer; at high
  difficulty, allow irrational results and accept answers within some
  epsilon (e.g. `abs(float(submitted) - true_value) < 0.01`) rather than
  exact match.
- **Trig values**: decide up front whether inputs are in degrees or
  radians (or both, difficulty-gated), and whether answers should be exact
  (`sqrt(2)/2`) or decimal -- sympy's `sp.nsimplify` can help accept either.
- **Algebraic manipulation**: this one's fuzzier than the others -- "simplify
  this expression" doesn't have a single canonical target the way a
  derivative does. Consider generating a target simplified form and
  checking `sp.simplify(submitted - target) == 0`, same trick as derivatives.
- **Integrals**: definite integrals of polynomials are a direct extension
  of `DerivativesDrill` (use `sp.integrate(expr, (x, a, b))`). Line
  integrals are meaningfully harder to both generate and grade (need a
  parametrized curve + vector field) -- treat as a stretch goal, not MVP.
- **RREF**: `sympy.Matrix(...).rref()` gives you both problem generation
  (random matrix) and the answer key for free. The interesting design
  question is how to grade partial/step-by-step work vs. just the final
  matrix.
- **ODE/PDE**: start with separable first-order ODEs (`sp.dsolve`) before
  attempting anything more general -- grading arbitrary ODE solutions for
  equivalence is genuinely hard (constants of integration, different valid
  forms) and deserves its own design pass.
