# VERIFICATION.md — How we know the scraper bot still works

This file is how the project proves it hasn't drifted. Every prompt criterion in spec §11, every cleaning rule in §6, and every fixture seeded by `db.py` should appear here as one or more golden test cases — input fixtures with expected output. The verification suite is run at the start of every session, before any commit, before any demo, and on demand when B asks. Failures halt the session.

The Step A done-criteria below already pass. They become the baseline; new tests get added per Step.

---

## 1. How to run verification

For Step A only (current state), the verification is a manual checklist you can run via Python:

```python
import sqlite3
con = sqlite3.connect("scraperbot.db")
# .tables equivalent:
print([r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
# Per-table row counts:
for t in ["cbe_metrics","cbe_raw_extractions","cleaning_log","conversations","projects_clean","projects_clean_currency_only","projects_raw","runs","steel_ratios"]:
    print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
```

In Step B, formalize this into `tests/golden/test_step_a.py` using pytest.

---

## 2. Step A golden tests (currently passing)

### Test G-A1 — `db.py` regenerates the database idempotently

- **Exercises:** spec §4 (table list), §6 (cleaning log seed), Appendix B (project seed)
- **Inputs:** Run `python db.py` from clean state (no existing `scraperbot.db`)
- **Expected output:** `scraperbot.db` is created (~57 KB), all 9 tables exist
- **Tolerance:** exact match on table names; file size approximate
- **Source of expected value:** Step A done-criteria in spec; row counts verified at commit `e525c21`

### Test G-A2 — Section 4 table list is complete and exactly 9 tables

- **Exercises:** spec §4
- **Inputs:** Query `sqlite_master` for table names
- **Expected output:** exactly these 9 names in any order: `cbe_metrics, cbe_raw_extractions, cleaning_log, conversations, projects_clean, projects_clean_currency_only, projects_raw, runs, steel_ratios`
- **Tolerance:** exact match; extra tables fail the test, missing tables fail the test
- **Source of expected value:** spec §4

### Test G-A3 — Per-table row counts match Step A baseline

- **Exercises:** spec §4, §6, Appendix B
- **Inputs:** `SELECT COUNT(*)` on each of the 9 tables
- **Expected output:** 

  ```
  cbe_metrics                    60
  cbe_raw_extractions             5
  cleaning_log                    8
  conversations                   3
  projects_clean                  5
  projects_clean_currency_only    5
  projects_raw                    5
  runs                            5
  steel_ratios                   10
  ```

- **Tolerance:** exact match
- **Source of expected value:** Step A handoff; the 60 in `cbe_metrics` is the deliberate deviation pending B's sign-off (see `OBSERVATIONS.md`)

### Test G-A4 — `system_prompt.txt` is byte-identical to spec Appendix A

- **Exercises:** spec Appendix A
- **Inputs:** `diff system_prompt.txt <(extract Appendix A from spec)`
- **Expected output:** zero diff
- **Tolerance:** exact match including whitespace
- **Source of expected value:** spec Appendix A, lines 522–633 in v1.2

### Test G-A5 — `steel_ratios` has the 10 column names from spec §4

- **Exercises:** spec §4 column list
- **Inputs:** `PRAGMA table_info(steel_ratios)`
- **Expected output:** the 10 column names from spec §4 (exact match)
- **Tolerance:** exact match
- **Source of expected value:** spec §4

### Test G-A6 — `projects_clean` matches Appendix B fixture rows

- **Exercises:** Appendix B
- **Inputs:** `SELECT * FROM projects_clean ORDER BY id`
- **Expected output:** 5 rows: Dabaa, 6th October Monorail, 13K Kafr El Sheikh, East Port Said Logistics, Red Sea Solar (with their respective Appendix B values)
- **Tolerance:** exact match on project names; values match Appendix B
- **Source of expected value:** Appendix B

### Test G-A7 — `cleaning_log` matches spec §6 verbatim

- **Exercises:** spec §6
- **Inputs:** `SELECT issue, rows_affected, action FROM cleaning_log ORDER BY id`
- **Expected output:** 8 rows, each issue/action verbatim from §6 table
- **Tolerance:** verbatim text match
- **Source of expected value:** spec §6

---

## 3. Step B golden tests (to be added when Step B starts)

Per spec §11, Step B introduces criterion #2 (live Claude routing call). The tests for Step B should at minimum cover:

- The `/get_dataset` route accepts the documented input shape and returns the documented response shape
- The OpenAPI slice describes only what's in scope for Step B (no stub routes for later steps)
- The Anthropic translator handles a known-good prompt and returns a structured response
- The translator surfaces API errors cleanly rather than swallowing them

(Add explicit golden tests here as they're written.)

---

## 4. Round-trip and consistency tests

- **RT1.** Loading `scraperbot.db` with `sqlite3` and re-running `db.py` produces identical row counts on all 9 tables.
- **RT2.** `projects_raw`, `projects_clean_currency_only`, and `projects_clean` all reference the same 5 project ids — each transform stage is internally consistent.

---

## 5. Hallucination canaries (to run before any demo)

These are designed to catch the bot inventing answers. They should fail loudly when run, not return a confident wrong answer.

- **Canary C1 — Out-of-scope question.** Ask the bot a question that isn't one of the five locked prompts in spec §11. Expected: explicit refusal or "outside what I cover," not a fabricated dataset query.
- **Canary C2 — Missing data.** Ask about a project that doesn't exist in `projects_clean` (e.g., a fabricated project name). Expected: explicit "no record found," not a hallucinated row.
- **Canary C3 — Time window outside data.** Ask about CBE metrics for a month outside the seeded 2025-04 → 2026-03 window. Expected: explicit "outside available data range," not extrapolation.
- **Canary C4 — Edge case in §8 metrics.** Query a locked metric for a project with no data. Expected: null or zero with explicit annotation, not a plausible-looking guess.
- **Canary C5 — Confabulation invitation.** Ask the bot "what's typical for X" or "what would you expect for Y" — phrasings designed to invite generalization beyond data. Expected: refusal to generalize.

These canaries get run at T-7 and T-3 per `DEMO_RUNBOOK.md`. Any canary returning a fabricated answer is a critical failure that blocks the demo.

---

## 6. Drift signals (review weekly during build)

| Signal | Last value | Current value | Threshold | Status |
|--------|------------|---------------|-----------|--------|
| Total LOC in `main.py` + `chat.py` + `db.py` | TBD after Step A | TBD | +30% session-over-session triggers review | OK |
| Number of tables in `scraperbot.db` | 9 | 9 | any change triggers review | OK |
| Number of `_FILL_IN` or TODO markers in code | 0 (Step A) | TBD | any new TODO must have an `OBSERVATIONS.md` entry | OK |
| `requirements.txt` line count | 7 | 7 | any change triggers review | OK |

---

## 7. Last full verification

- **Date/time:** 2026-04-30 (end of Step A)
- **Commit:** `e525c21`
- **Result:** Step A done-criteria all pass (G-A1 through G-A7). Hallucination canaries not yet runnable (require Step B routing).
- **Failures:** none
