# HANDOFF.md — Session continuity log

This file is the bridge between Claude Code sessions. Updated at the end of every session (or when limits are about to hit). Read at the start of every session, before anything else.

If this file says one thing and the code says another, **the code is the truth** but the discrepancy is itself information — surface it to B.

---

## Last session summary

- **Session ended:** 2026-05-08, after Step B + Step B settle-up + Step C / Appendix B done criterion #3 (all 9 tools landed)
- **Why ended:** All nine §5 FastAPI tools implemented and round-trip validated by codified pytest. Criterion #3 spot-check confirms `query_projects` and `estimate_steel_total` have all six filters optional. Functional smoke test passes on every endpoint. Awaiting B on push and on "go" for Appendix B done criterion #4 (HTTP test script) and #5 (Streamlit chat UI).
- **What got done:**
  - **Push consolidation.** Pushed the 4 commits from the prior Step B / env-setup blocks. `origin/claude/ezz-steel-scraper-step1-yQejR` and `origin/main` both fast-forwarded `9206960..b2c1274`. Same pattern as the recovery consolidation.
  - **Step B settle-up — FINDING 1 fix (CBE branch in `get_dataset`).** Original code returned `cbe_metrics` for `source="cbe"` regardless of `version`, ignoring the spec's intent. Restructured the route to use the unified `_TABLE_MAP` for all `(source, version)` combinations:
    - `("cbe", "raw")` → `cbe_raw_extractions`
    - `("cbe", "clean")` → `cbe_metrics`
    - `("cbe", "currency_only")` → HTTP 400 with a clear error message ("currency_only is not meaningful for CBE metrics")
    - egy_map mappings unchanged.
    - Verified all three cases via curl against a live uvicorn. Commit `b014654`. Single-purpose, isolated.
  - **Step B settle-up — FINDING 2 OBSERVATIONS entry.** `description=` parameter on the route decorator (vs spec §3.1's "docstring" wording) was used for verbatim preservation because FastAPI splits docstrings on first newline into summary/description. Added an open observation dated 2026-05-08 recommending spec v1.3 amend §3.1 to permit both mechanisms. Flag-don't-act on the spec edit per CLAUDE.md §3. Commit `2f5629b`.
  - **Step B settle-up — codified round-trip pytest (G-B1).** Created `tests/test_round_trip.py`. Parametrizes over a `TOOLS` registry; each row pins `(path, spec_line, expected_props, expected_required)`. Test fixture spins up the FastAPI app via `TestClient`, fetches `/openapi.json`, runs the translator, and asserts: (a) byte-identical description against `scraper_bot_demo_spec_v1_2.md` at that line (with `> ` blockquote prefix stripped), backed by sha256 cross-check; (b) `input_schema.properties` types match expectation, no extra schema keys per property; (c) `required` matches expectation (catches both leaked defaulted params and dropped required params). Added VERIFICATION.md §3 G-B1 entry. `pytest==8.3.4` added to `requirements.txt` (B-approved as task directive; same approval pattern as `python-dotenv`). Commit `b484995`.
  - **Step C — remaining 8 §5 tools implemented (`main.py`).** Each tool follows the validated pattern: a module-level `GET_<TOOL>_DESCRIPTION` constant verbatim from spec §5, passed via `description=` to the route decorator. Tool list:
    - `get_cleaning_log(source: str)` — required; reads `cleaning_log` filtered by `source`.
    - `query_projects(governorate=None, category=None, eta_year_min=None, eta_year_max=None, cost_min_egp=None, cost_max_egp=None)` — all six optional; dynamic WHERE clause from non-None filters; reads `projects_clean`.
    - `estimate_steel_total(...)` — identical filter signature to `query_projects`; aggregates `tons_estimated/low/high`, counts insufficient-data projects, returns top 3 by tonnage.
    - `query_cbe_trend(metric, period_start, period_end)` — all three required; reads `cbe_metrics` filtered to range.
    - `compare_cbe_periods(metric, period_a, period_b)` — all three required; returns both values, absolute difference, percent change; 404 if either period missing.
    - `refresh_egy_map()` — no params. Step 1 stub: writes a `runs` row, returns its id and a "live scraping not enabled in Step 1" note. Real scraping is Step 2 per spec §17.
    - `extract_latest_cbe_bulletin()` — no params. Same Step 1 stub pattern as `refresh_egy_map`.
    - `get_run_status()` — no params; reads `runs` ordered by `started_at DESC`.
  - **Step C — translator updated for Optional/`anyOf` parameters (`chat.py`).** FastAPI emits Optional query params as `schema: {anyOf: [{type: <T>}, {type: "null"}], title: ...}` rather than a direct `type`. Added `_param_type()` helper that picks the first non-`"null"` branch when `anyOf` is present. No other changes to the translator.
  - **Round-trip validation (G-B1) on all 9 tools — all PASS.** Test output:
    ```
    tests/test_round_trip.py::test_round_trip[/get_dataset]                 PASSED
    tests/test_round_trip.py::test_round_trip[/get_cleaning_log]            PASSED
    tests/test_round_trip.py::test_round_trip[/query_projects]              PASSED
    tests/test_round_trip.py::test_round_trip[/estimate_steel_total]        PASSED
    tests/test_round_trip.py::test_round_trip[/query_cbe_trend]             PASSED
    tests/test_round_trip.py::test_round_trip[/compare_cbe_periods]         PASSED
    tests/test_round_trip.py::test_round_trip[/refresh_egy_map]             PASSED
    tests/test_round_trip.py::test_round_trip[/extract_latest_cbe_bulletin] PASSED
    tests/test_round_trip.py::test_round_trip[/get_run_status]              PASSED
    9 passed in 0.67s
    ```
  - **Criterion #3 spot-check.** Inspected fresh `/openapi.json`: `query_projects` and `estimate_steel_total` each have all six filter parameters with `required: false`. Zero defaulted params marked required. PASS.
  - **Functional smoke test (not part of formal criteria, included for confidence).** Invoked all 9 endpoints via `TestClient`. All HTTP 200, sensible row counts: get_dataset egy_map/raw → 5 rows; get_dataset cbe/clean → 60 rows; get_cleaning_log egy_map → 8 rows; query_projects (no filter) → 5 rows; query_projects (governorate="Port Said") → 1 row; estimate_steel_total returns expected dict shape; query_cbe_trend(usd_egp_rate, 2025-04..2026-03) → 12 rows; compare_cbe_periods returns expected dict; refresh/extract stubs return their run records; get_run_status → 7 rows (5 seeded + 2 from the stub calls just made).
  - **Step C commit:** `0ee06b3`.
- **What's mid-flight:** Five unpushed commits on `claude/ezz-steel-scraper-step1-yQejR`:
  - `b014654` get_dataset CBE branch fix
  - `b484995` round-trip pytest + G-B1 + pytest dep
  - `2f5629b` OBSERVATIONS Finding 2
  - `0ee06b3` Step C implementation (8 tools)
  - `<new>` this HANDOFF update (committing now)
  - Awaiting B on push (same fast-forward pattern as recovery + Step B). Then "go" for Appendix B done criterion #4 (HTTP test script) and criterion #5 (Streamlit chat UI) — separate authorization required per B's note.
- **Next concrete step on resume:** Push the 5 unpushed commits, then await B's "go" for criterion #4. Criterion #4 is a thin pytest or shell script that hits each of the 9 endpoints via HTTP (not TestClient) and asserts sensible responses — should be quick given the smoke test already passed via TestClient. Criterion #5 (Streamlit chat UI) is the larger remaining task.

---

## Verification status as of session end

- **Step A (G-A1–G-A7):** all PASS. Last run during env setup (2026-05-08). Schema and seed unchanged since. `system_prompt.txt` sha256 baseline unchanged.
- **Step B (G-B1 round-trip):** 9/9 PASS. Codified as `tests/test_round_trip.py`; runs in 0.67s.
- **Criterion #3 spot-check:** PASS — `query_projects` and `estimate_steel_total` filters all optional.
- **Failures:** None.
- **Drift signals:** `requirements.txt` 7 → 9 lines (added `python-dotenv==1.0.1` and `pytest==8.3.4`, both B-approved). `main.py` grew from 41 to 256 lines (8 new routes + helpers). `chat.py` grew from 33 to 44 lines (anyOf helper). Both expected for Step C scope.
- **Hashes pinned:**
  - `system_prompt.txt` (spec Appendix A): `7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01`
  - `GET_DATASET_DESCRIPTION` (spec §5 line 142, with trailing `\n` for diff alignment): `94228a7e5127b96b95149f27095b284623f64c607d8e89aea8f816a72ec8c8dc`
  - The remaining 8 §5 descriptions are pinned indirectly by their spec line numbers in the G-B1 test registry; any drift fails the pytest.

---

## Open questions for B

- **Push the 5 new commits.** Same fast-forward pattern (canonical + main).
- **"Go" for Appendix B criterion #4 (test script).** A pytest or shell script that exercises each of the 9 endpoints via real HTTP (uvicorn) and asserts a sensible response. The TestClient smoke test in this session is a cheap proxy; the criterion wants the live-HTTP form.
- **"Go" for Appendix B criterion #5 (Streamlit chat UI).** Standalone bot using `st.chat_input`, system prompt from `system_prompt.txt`, tool definitions auto-loaded from FastAPI's OpenAPI via the validated translator. Welcome message + four suggested-prompt buttons.
- **Spec v1.3 amendment for §3.1 wording** (OBSERVATIONS entry 2026-05-08). Flag-don't-act; awaiting B's call.
- **Demo target date and audience.** Still unset in `CLAUDE.md` §1.

---

## Things to NOT do next session

- Do not regenerate or rebuild any Step A scaffolding.
- Do not edit `db.py` seed data to satisfy any test failure.
- Do not commit `scraperbot.db`.
- Do not edit `system_prompt.txt` away from spec Appendix A. (sha256 baseline: `7bbf9e06…`.)
- Do not edit any `GET_<TOOL>_DESCRIPTION` constant away from spec §5. The G-B1 pytest will catch drift, but treat any FAIL there as "the spec changed or someone broke verbatim preservation" — not as "the test is wrong."
- Do not commit `.env`; do not echo `ANTHROPIC_API_KEY` to any committed file.
- Do not paraphrase, truncate, or auto-summarize any spec §5 tool description.
- Do not add new packages without B approval. Currently approved beyond the original 7: `python-dotenv==1.0.1`, `pytest==8.3.4`.
- Do not start Appendix B criterion #4 or #5 before B explicitly says "go" for each — they are separate gates.
- Do not push any branch without B's explicit authorization.

---

## Session history (last 5 sessions)

Most recent at top. Older entries get pruned to the last five — but never deleted entirely without B's say-so. If full history is needed, move pruned entries to `HANDOFF_ARCHIVE.md`.

| Session # | Date | What got done | What was mid-flight |
|-----------|------|---------------|---------------------|
| 4 | 2026-05-08 | Step B settle-up (CBE branch fix `b014654`, OBSERVATIONS Finding 2 `2f5629b`, round-trip pytest G-B1 `b484995`); Step C / Appendix B criterion #3 — all 8 remaining §5 tools implemented (`0ee06b3`), translator updated for Optional/`anyOf` params, all 9 tools PASS round-trip pytest, criterion #3 filter-optionality spot-check PASS, functional smoke test on all 9 endpoints PASS; pushed prior Step B commits to canonical + main | 5 unpushed commits; awaiting B on push and on "go" for criterion #4 (HTTP test script) and #5 (Streamlit UI) |
| 3 | 2026-05-08 | Step B / Appendix B criterion #2: `get_dataset` route, translator + `route_once` in `chat.py`, round-trip validation PASS (description byte-identical to spec §5, sha256 `94228a7e…`), live routing test PASS via `claude-haiku-4-5` | 4 unpushed commits; awaiting B on push and Step C / criterion #3 |
| 2 | 2026-05-08 | Step A recovery via merge (`641b8d3`); G-A1–G-A7 all PASS; VERIFICATION.md G-A7 SQL fix (`f53c1e1`); HANDOFF recovery update (`9206960`); push consolidation to `origin/main` and `origin/claude/ezz-steel-scraper-step1-yQejR` both at `9206960`; session branch retired; env setup with `python-dotenv==1.0.1` committed as `10ea7648`; `.env` created and gitignored; API key load + Anthropic ping PASS end-to-end | 2 unpushed commits; awaiting B on push and Step B "go" |
| 1 | 2026-04-30 | Step A scaffolding (6 files, 609 insertions, commit `e525c21`); v1.1 spec removed (`4fb559e`); 9 tables seeded | Step B paused awaiting "go" and API key |
