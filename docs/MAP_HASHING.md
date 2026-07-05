# Map hashing (shared leaderboards)

## The goal

Two people who upload the same textbook (same edition) should land on the
same leaderboard, the same way two osu! players with the same `.osu`
beatmap file compete on the same map leaderboard.

## Why you can't hash the raw uploaded file

Two scans/exports of "the same" textbook are essentially never
byte-identical: different scan quality, different PDF export settings,
OCR noise, metadata differences, etc. Hashing raw bytes would give every
single user their own private "leaderboard of one," which defeats the
entire point.

## The actual plan (not yet implemented)

1. Parse the upload into a **structured** representation: a list of
   `(chapter, problem_number, problem_text, answer)` tuples, normalized
   (whitespace collapsed, consistent number formatting, etc.) -- this is
   `app/ingestion/textbook_parser.py` + `problem_extractor.py`.
2. Hash *that structured representation*, not the raw file. Two different
   scans of the same edition should, after parsing/normalization, produce
   the same structured data, and therefore the same hash.
3. That hash becomes the `map_hash` used everywhere else (leaderboards,
   session state, `content/textbook-maps/{map_hash}/`).
4. Store `meta.json` alongside the parsed problems with whatever edition
   info was extractable (title, author, ISBN if present) -- best-effort,
   not load-bearing for the hash itself.

## Known hard edge cases (worth deciding on deliberately, not accidentally)

- **Different editions of the same book** (e.g. 3rd vs 4th edition) will
  usually have renumbered/reworded problems -- these should probably NOT
  share a map, since the exercise sets genuinely differ. The parser
  doesn't need to detect edition explicitly; different content naturally
  hashes differently, which is the correct behavior here.
- **Partial uploads** (someone uploads only chapter 3) vs. full-book
  uploads -- decide whether these should be sub-maps of the full book's
  hash or entirely separate maps. Leaning toward: hash is computed per
  chapter/section, and a "full book" map is really just a bundle of
  chapter-level map hashes -- but this isn't decided yet.
- **OCR errors** causing two honestly-identical textbooks to parse
  slightly differently. Some fuzziness/normalization tolerance will
  probably be needed before hashing (e.g. fuzzy-matching problem text
  rather than exact string comparison) -- not designed yet.
