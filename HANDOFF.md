# HANDOFF.md — Session continuity log

This file is the bridge between Claude Code sessions. Updated at the end of every session (or when limits are about to hit). Read at the start of every session, before anything else.

If this file says one thing and the code says another, **the code is the truth** but the discrepancy is itself information — surface it to B.

---

## Last session summary

- **Session ended:** 2026-05-08, after Appendix B done criterion #4 complete (HTTP test script). Step C commits and the prior Step B settle-up commits have all been pushed to origin (canonical + main).
- **Why ended:** Criterion #4 done and verified: `scripts/test_endpoints.py` exercises all 9 §5 tools over real HTTP against a live uvicorn and reports per-endpoint PASS/FAIL with exit-code semantics. 16/16 cases PASS against a fresh DB. Awaiting B's "go" for criterion #5 (Streamlit chat UI) and criterion #6 (7 canned prompts), which are separate gates and the biggest remaining surface area.
- **What got done:**
  - **Push consolidations.** Two fast-forward pushes this session, same pattern as the recovery consolidation:
    - `9206960..b2c1274` (4 commits: env setup + Step B + HANDOFF round)
    - `b2c1274..4359c76` (5 commits: CBE fix + G-B1 pytest + Finding 2 OBSERVATIONS + Step C + HANDOFF round)
    - `origin/claude/ezz-steel-scraper-step1-yQejR` and `origin/main` both at `4359c76` after the second push.
  - **OBSERVATIONS entry — runs-table side effect from stub refresh endpoints.** `/refresh_egy_map` and `/extract_latest_cbe_bulletin` write a row to `runs` on every call, per the spec §6 architectural rule ("every action ends up in `cleaning_log` and `runs`"). This is correct behavior, not a bug — but it means G-A3's `runs == 5` baseline FAILs on any G-A3 run that happens after a smoke / criterion-#4 run without rebuilding the DB first. Documented the verification workflow: `python db.py` first, then any test that hits live endpoints. Codifying as a wrapper script is a flag-don't-act follow-up. Commit `7a4378d`.
  - **Criterion #4 — HTTP test script (`scripts/test_endpoints.py`).** Hits all 9 §5 tools over real HTTP at `http://127.0.0.1:8000` (assumes uvicorn already running; does not auto-start). Uses `httpx` (already in `requirements.txt` from Step A). 16 cases across 9 endpoints — `/get_dataset` has 6 variants (each valid `(source, version)` plus the 400 error path), the rest 1–2 each. Each case asserts both HTTP status and a shape predicate (row count or required dict keys). Prints PASS/FAIL per case with a one-line response shape summary, exits 0 if all pass else 1. Header docstring documents the run sequence per the OBSERVATIONS workflow note.
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
  - **Step C commit:** `0ee06b3`. **Criterion #4 commit:** `<new>` (this HANDOFF round + `scripts/test_endpoints.py`).
  - **Criterion #4 live run.** Sequence: `rm scraperbot.db && python db.py` (fresh `runs=5`), then `uvicorn main:app` on port 8000, then `python scripts/test_endpoints.py`. Result:
    ```
    Hitting http://127.0.0.1:8000
    ==========================================================================================
      PASS  get_dataset egy_map raw                 HTTP 200  list, rows=5
      PASS  get_dataset egy_map clean               HTTP 200  list, rows=5
      PASS  get_dataset egy_map currency            HTTP 200  list, rows=5
      PASS  get_dataset cbe raw                     HTTP 200  list, rows=5
      PASS  get_dataset cbe clean                   HTTP 200  list, rows=60
      PASS  get_dataset cbe currency (400)          HTTP 400  dict, keys=['detail']
      PASS  get_cleaning_log egy_map                HTTP 200  list, rows=8
      PASS  query_projects no filter                HTTP 200  list, rows=5
      PASS  query_projects Port Said                HTTP 200  list, rows=1
      PASS  estimate_steel_total no filter          HTTP 200  dict, keys=[total_tons_*, top_contributors, insufficient_data_count]
      PASS  estimate_steel_total energy             HTTP 200  dict, keys=[same]
      PASS  query_cbe_trend usd_egp_rate            HTTP 200  list, rows=12
      PASS  compare_cbe_periods usd_egp             HTTP 200  dict, keys=[metric, period_a, period_b, absolute_difference, percent_change]
      PASS  refresh_egy_map (stub)                  HTTP 200  dict, keys=[run_id, component, status, ...]
      PASS  extract_latest_cbe_bulletin             HTTP 200  dict, keys=[same]
      PASS  get_run_status                          HTTP 200  list, rows=7
    ==========================================================================================
    PASS — 16/16 cases
    ```
    Exit 0. Post-run `runs` count is 7 (5 seeded + 2 from the stub endpoints), expected per the OBSERVATIONS workflow note — rebuild the DB before re-running G-A3.
- **What's mid-flight:** Two unpushed commits on `claude/ezz-steel-scraper-step1-yQejR`:
  - `7a4378d` OBSERVATIONS workflow note
  - `<new>` criterion #4 script + HANDOFF update (committing now)
- **Next concrete step on resume:** Push the 2 commits (same FF pattern). Then await B's explicit "go" for criterion #5 (Streamlit chat UI) — the biggest surface-area task remaining and the gate B has flagged for separate review. Criterion #6 (the 7 canned demo prompts producing non-error responses) sits on top of criterion #5.

---

## Verification status as of session end

- **Step A (G-A1–G-A7):** all PASS. Last run during env setup (2026-05-08). Schema and seed unchanged since. `system_prompt.txt` sha256 baseline unchanged. **Workflow note:** re-run `python db.py` before re-running G-A3 — the `runs == 5` baseline is sensitive to any session that hit `/refresh_egy_map` or `/extract_latest_cbe_bulletin`.
- **Step B (G-B1 round-trip):** 9/9 PASS. Codified as `tests/test_round_trip.py`; runs in 0.67s.
- **Criterion #3 spot-check:** PASS — `query_projects` and `estimate_steel_total` filters all optional.
- **Criterion #4 (HTTP test script):** 16/16 cases PASS via `scripts/test_endpoints.py` against fresh DB + live uvicorn on port 8000.
- **Failures:** None.
- **Drift signals:** `requirements.txt` 7 → 9 lines (added `python-dotenv==1.0.1` and `pytest==8.3.4`, both B-approved; B has noted the next dep gets the explicit-ask treatment regardless of how implicit the task directive seems). `main.py` ~256 lines (9 routes + helpers). `chat.py` ~44 lines (translator + anyOf helper + `route_once`).
- **Hashes pinned:**
  - `system_prompt.txt` (spec Appendix A): `7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01`
  - `GET_DATASET_DESCRIPTION` (spec §5 line 142, with trailing `\n` for diff alignment): `94228a7e5127b96b95149f27095b284623f64c607d8e89aea8f816a72ec8c8dc`
  - The remaining 8 §5 descriptions are pinned indirectly by their spec line numbers in the G-B1 test registry; any drift fails the pytest.

---

## Open questions for B

- **Push the 2 new commits.** `7a4378d` (OBSERVATIONS workflow note) + criterion #4 commit. Same FF pattern (canonical + main).
- **"Go" for Appendix B criterion #5 (Streamlit chat UI).** Standalone bot using `st.chat_input`, system prompt from `system_prompt.txt`, tool definitions auto-loaded from FastAPI's OpenAPI via the validated translator. Welcome message + four suggested-prompt buttons. B flagged this as the largest surface-area task remaining and the gate that needs its own review checkpoint before kickoff.
- **"Go" for criterion #6 (canned prompts).** All seven §11 prompts must produce a non-error response on dummy data. Sits on top of #5; can't run until the UI is wired.
- **Spec v1.3 amendments** (two OBSERVATIONS entries dated 2026-05-08). Flag-don't-act; awaiting B's call on (a) §3.1 docstring wording, (b) the runs-table side-effect workflow note (whether to codify as a wrapper script).
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
- **Do not add new packages without an explicit ask, even when the task directive obviously implies one** (B's NOTE 1 on 2026-05-08; the inference path is closed). Currently approved beyond the original 7: `python-dotenv==1.0.1`, `pytest==8.3.4`.
- Do not run live-endpoint tests (criterion #4 script, smoke tests, anything hitting `/refresh_egy_map` or `/extract_latest_cbe_bulletin`) without rebuilding `scraperbot.db` from `db.py` first. The stub endpoints write to `runs` and the G-A3 baseline (`runs == 5`) will FAIL otherwise.
- Do not start Appendix B criterion #5 or #6 before B explicitly says "go" — they are separate gates and #5 needs a kickoff review per B.
- Do not push any branch without B's explicit authorization.

---

## Session history (last 5 sessions)

Most recent at top. Older entries get pruned to the last five — but never deleted entirely without B's say-so. If full history is needed, move pruned entries to `HANDOFF_ARCHIVE.md`.

| Session # | Date | What got done | What was mid-flight |
|-----------|------|---------------|---------------------|
| 5 | 2026-05-08 | Pushed Step C commits to canonical + main (`b2c1274..4359c76`); OBSERVATIONS entry on runs-table workflow (`7a4378d`); Appendix B criterion #4 — `scripts/test_endpoints.py` HTTP test runner against live uvicorn; 16/16 cases PASS against a fresh DB; criterion #4 commit + HANDOFF round | 2 unpushed commits; awaiting B on push and on "go" for criterion #5 (Streamlit UI) — flagged as the gate that needs its own kickoff review |
| 4 | 2026-05-08 | Step B settle-up (CBE branch fix `b014654`, OBSERVATIONS Finding 2 `2f5629b`, round-trip pytest G-B1 `b484995`); Step C / Appendix B criterion #3 — all 8 remaining §5 tools implemented (`0ee06b3`), translator updated for Optional/`anyOf` params, all 9 tools PASS round-trip pytest, criterion #3 filter-optionality spot-check PASS, functional smoke test on all 9 endpoints PASS; pushed prior Step B commits to canonical + main | 5 unpushed commits; awaiting B on push and on "go" for criterion #4 (HTTP test script) and #5 (Streamlit UI) |
| 3 | 2026-05-08 | Step B / Appendix B criterion #2: `get_dataset` route, translator + `route_once` in `chat.py`, round-trip validation PASS (description byte-identical to spec §5, sha256 `94228a7e…`), live routing test PASS via `claude-haiku-4-5` | 4 unpushed commits; awaiting B on push and Step C / criterion #3 |
| 2 | 2026-05-08 | Step A recovery via merge (`641b8d3`); G-A1–G-A7 all PASS; VERIFICATION.md G-A7 SQL fix (`f53c1e1`); HANDOFF recovery update (`9206960`); push consolidation to `origin/main` and `origin/claude/ezz-steel-scraper-step1-yQejR` both at `9206960`; session branch retired; env setup with `python-dotenv==1.0.1` committed as `10ea7648`; `.env` created and gitignored; API key load + Anthropic ping PASS end-to-end | 2 unpushed commits; awaiting B on push and Step B "go" |
| 1 | 2026-04-30 | Step A scaffolding (6 files, 609 insertions, commit `e525c21`); v1.1 spec removed (`4fb559e`); 9 tables seeded | Step B paused awaiting "go" and API key |
