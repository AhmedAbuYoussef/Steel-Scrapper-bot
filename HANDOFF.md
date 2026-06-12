# HANDOFF.md — Session continuity log

This file is the bridge between Claude Code sessions. Updated at the end of every session (or when limits are about to hit). Read at the start of every session, before anything else.

If this file says one thing and the code says another, **the code is the truth** but the discrepancy is itself information — surface it to B.

---

## Last session summary

- **Session ended:** 2026-06-12 (session 10), clean halt at B's review gate after the spec v1.3 batch. All work pushed per push-before-halt.
- **Why ended:** B's 2026-06-12 brief was a fixed 8-task batch ending in a mandated halt. Tasks complete; criterion #6 remains gated on B's explicit "go", and the criterion #5 re-smoke (against the new seed + full-text harness) is B's local task.
- **What got done this session (one container, ~1.5 h):**
  - **Spec v1.3 applied (B-authored, executed verbatim through Claude Code per B's brief — this is B's edit, consistent with the only-B-edits-the-spec rule).** `scraper_bot_demo_spec_v1_3.md` created from v1.2 with exactly B's 8-item edit list: 24-month CBE window (§8, Appendix A DOMAIN + WELCOME, Appendix B → 120 rows), deterministic §10 button 3/4 and §11 prompt 5/6 wording (prompt 6 now "Q1 2026 vs Q1 2025" with a quarter-label re-validation note), §12 script lines, §14 T-24h checklist line, and a new Appendix A NEVER rule forbidding partial-window approximation/substitution. v1.2 deleted (precedent `4fb559e`). Filename refs updated in CLAUDE.md, README.md, `main.py` comment, and `tests/test_round_trip.py`.
  - **Root cause being fixed:** session 9's button-4 FAIL — the bot fabricated a "Q1 2025" baseline because a year-over-year quarterly comparison needs ≥15 months and the seed had 12. §11 prompt 6 was structurally unanswerable; v1.3 makes the data sufficient AND pins the prompt wording to explicit quarters.
  - **`tests/test_round_trip.py` registry consequence:** the v1.3 header block is 2 lines longer than v1.2's, shifting §5 — all 9 `spec_line` pins moved +2 (get_dataset 142→144 … get_run_status 166→168). Description bytes themselves are untouched by v1.3; the golden values (verbatim §5 text) did not change.
  - **`system_prompt.txt` regenerated** byte-identical to v1.3 Appendix A (exact string equality verified). New sha256 `4f1b64d15059e48fd5a43136f8049f3caad461b3e61b24e5d2cdeaa0f987d837`, 6404 bytes (was `7bbf9e06…`, 6218).
  - **`db.py` reseeded:** `cbe_metrics` extended backward 12 months (2024-04 → 2025-03, all 5 metrics, 60 new rows → 120 total). Original 60 rows verified byte-identical (the criterion #5 smoke validated those exact values). All 5 series monotonic across the seam; generation rule documented in a `db.py` comment (backward continuation of each series' average month-over-month delta, hand-typed literals). Q1 2025 avg (102.7) and Q1 2026 avg (111.63) for `industrial_production_index` both computable from seed. `scripts/test_endpoints.py` cbe-clean expectation 60→120.
  - **VERIFICATION.md updates (all B-approved in the brief):** G-A3 `cbe_metrics` 120; G-A4 sha pin added (`4f1b64d1…`, 6404 bytes) + line ref now "lines 526–639 in v1.3"; §6 drift baseline `requirements.txt` 7→9 with the approved note; §7 last-full-verification log refreshed.
  - **DEMO_RUNBOOK.md:** prompt 5/6 wording to v1.3; 60-row references → 120 (§1 step 3–6 note, §8).
  - **Smoke harness:** 500-char response cap removed — transcripts now capture full final response text (the cap hid exactly where hedges/disclosures live; session-9 button-4 audit was nearly blinded by it). `tests/smoke_criterion_5_LOCAL.md` pins refreshed: db.py sha `b4141efb…`, system_prompt sha `4f1b64d1…`/6404 bytes, cbe_metrics 120.
  - **OBSERVATIONS:** 60-vs-12 entry resolved (v1.3 sets 120); two new flag-don't-act entries — `runs` fixture row 3 `rows_out=60` now narratively inconsistent with the 120-row seed; G-A1's "~57 KB" stale (DB now ~72 KB).
- **What's mid-flight:** Nothing in code. The criterion #5 re-smoke against the new seed + full-text harness is B's local run (per the brief: not run in-container).
- **Next concrete step on resume:** B re-runs the smoke locally per `tests/smoke_criterion_5_LOCAL.md` and pushes the transcript; next session verifies it (per-button tool sequence, response shape, button 3 window handling, button 4 explicit-quarter handling — now with full response text available). Then B's separate "go" gates criterion #6 (all seven §11 prompts).

---

## Verification status as of session end

- **Full suite run 2026-06-12 on the v1.3 tree (pre-commit):**
  - Step A G-A1–G-A7: all PASS (G-A3 at the new `cbe_metrics = 120` baseline; G-A4 zero diff vs v1.3 Appendix A, sha `4f1b64d1…`).
  - RT1, RT2: PASS.
  - G-B1 round-trip (`tests/test_round_trip.py`): 9/9 PASS with the +2 line pins against v1.3.
  - Criterion #4 (`scripts/test_endpoints.py`, live uvicorn): 16/16 PASS, including cbe clean = 120 rows.
  - DB rebuilt to `runs = 5` baseline after the live-endpoint run.
- **Criterion #5:** code unchanged this session (`cbcb706`); previous 4-button smoke (2026-06-12, transcript `669ba46`) is now STALE — it validated the 12-month seed and prompt wording v1.2, and its button 4 FAILed session 9's content audit (fabricated out-of-window baseline; root cause now fixed by v1.3). Re-smoke pending on B's machine.
- **Criterion #6:** not started, not authorized.
- **Failures:** none in the suite. The stale smoke is superseded, not a suite failure.
- **Hashes pinned:**
  - `system_prompt.txt` (spec v1.3 Appendix A): `4f1b64d15059e48fd5a43136f8049f3caad461b3e61b24e5d2cdeaa0f987d837` (6404 bytes)
  - `db.py`: `b4141efb3b408bcb87f6ae6be9840e4d858bc5db694f067fa31d5fed2527dabf`
  - `GET_DATASET_DESCRIPTION` (spec v1.3 §5 line 144): sha unchanged `94228a7e5127b96b95149f27095b284623f64c607d8e89aea8f816a72ec8c8dc` — v1.3 did not touch §5 text, only its line position (+2).
  - The remaining 8 §5 descriptions pinned via the G-B1 registry line numbers (now 147–168); drift fails the pytest.

---

## Open questions for B

- **Criterion #5 re-smoke** against the new seed + full-text harness (B's local run per the runbook), then transcript verification next session.
- **Criterion #6 "go"** — separate gate after the re-smoke is green and reviewed. Not authorized.
- **Two new flag-don't-act items (2026-06-12):** `runs` fixture `rows_out=60` narrative inconsistency; G-A1 "~57 KB" → ~72 KB update needs approval.
- **CLAUDE.md §3 "On the spec" still narrates the 60-vs-12 deviation as "awaiting sign-off"** — now resolved by v1.3; sentence is stale but wasn't in the authorized edit list. B's call on a wording refresh.
- **Spec v1.3 leftover from the v1.2 amendment queue:** the §3.1 "docstring" wording observation (2026-05-08) was NOT addressed in v1.3 — still open in OBSERVATIONS.
- **Stale branch `claude/verify-docs-alignment-eb34f`:** B's call recorded 2026-06-12 — leave it; post-criterion-#6 housekeeping.
- **Demo target date and audience:** still unset in `CLAUDE.md` §1.
- **Session-history pruning:** table below now holds 10 rows; B's standing instruction (2026-05-21) was don't-prune until it adds noise, revisit ~session 8. Revisit is due.

---

## Things to NOT do next session

- Do not regenerate or rebuild any Step A scaffolding.
- Do not edit `db.py` seed data to satisfy any test failure. The 2025-04 → 2026-03 sub-window of `cbe_metrics` is smoke-validated — byte-identical preservation is load-bearing.
- Do not commit `scraperbot.db`.
- Do not edit `system_prompt.txt` away from spec v1.3 Appendix A. (sha256 baseline: `4f1b64d1…`, 6404 bytes.)
- Do not edit any `GET_<TOOL>_DESCRIPTION` constant away from spec §5. The G-B1 pytest will catch drift; treat any FAIL there as "the spec changed or verbatim preservation broke," not "the test is wrong."
- Do not commit `.env`; do not echo `ANTHROPIC_API_KEY` to any committed file.
- Do not paraphrase, truncate, or auto-summarize any spec §5 tool description.
- Do not add new packages without an explicit ask (B's NOTE 1, 2026-05-08). Approved beyond the original 7: `python-dotenv==1.0.1`, `pytest==8.3.4`.
- Do not run live-endpoint tests without rebuilding `scraperbot.db` from `db.py` first (runs-table side effect; G-A3 baseline `runs == 5`).
- Do not start criterion #6 before B explicitly authorizes it after the criterion #5 re-smoke review.
- Do not run the button smoke in-container (B runs it locally; standing instruction 2026-06-12).
- Do not halt with unpushed commits (push-before-halt, now codified in CLAUDE.md §3).
- Do not push any branch other than canonical `claude/ezz-steel-scraper-step1-yQejR`.

---

## Session history (last 5 sessions)

Most recent at top. Older entries get pruned to the last five — but never deleted entirely without B's say-so. If full history is needed, move pruned entries to `HANDOFF_ARCHIVE.md`. (Currently 10 rows; B's don't-prune-yet instruction stands, revisit due.)

| Session # | Date | What got done | What was mid-flight |
|-----------|------|---------------|---------------------|
| 10 | 2026-06-12 | Spec v1.3 applied verbatim per B's brief (24-month CBE window, deterministic prompt 5/6 wording, new Appendix A NEVER rule); v1.2 deleted; `system_prompt.txt` regenerated (sha `4f1b64d1…`); `db.py` reseeded to 120 `cbe_metrics` rows with original 60 byte-identical, Q1 2025 + Q1 2026 averages computable; VERIFICATION baselines updated (B-approved); DEMO_RUNBOOK aligned; smoke harness 500-char cap removed + runbook pins refreshed; full suite PASS (G-A 7/7, RT 2/2, G-B1 9/9, criterion #4 16/16); 28cc2b1 self-audit (10ea764 + b484995 verified) | Criterion #5 re-smoke on B's machine against new seed; criterion #6 not authorized |
| 9 | 2026-06-12 | Transcript `669ba46` content-audited: buttons 1–3 PASS (button 3 window-recovery exemplary), button 4 FAIL — fabricated "Q1 2025 (Jan–Mar) = 104.7" baseline (no rows before 2025-04 in seed; value = avg of 2025-04/05 mislabeled). Halted per B's instruction; Tasks 2–3 of that brief not started | B's triage of button 4; root cause later confirmed: 12-month seed cannot answer a YoY quarterly comparison |
| 8 | 2026-06-12 | Session-start verification suite full PASS (16-vs-9 explained: 16/16 = `scripts/test_endpoints.py` cases, 9/9 = round-trip pytest — two different suites, both correct); CLAUDE.md §3 package count 7→9 + push-before-halt codified (`28cc2b1`); OBSERVATIONS stale-branch call + push-before-halt resolution (`8163d7d`); halted on missing smoke transcript (origin had no commit past `8163d7d`) | B to push the smoke transcript; criterion #6 gate untouched |
| 7 | 2026-05-21→22 | Same container as session 6, continued after B's review. Stale-branch OBSERVATIONS (`be308cd`); smoke harness `tests/smoke_criterion_5.py` (`4b30702`, hook-forced commit under `[awaiting B review]`, disposition approved by B); auth surface investigation ×2 (no key, no secret store, no proxy auth, no persistence — full probe output in 2026-05-22 chat); local-run runbook `tests/smoke_criterion_5_LOCAL.md` + .gitignore pattern fix (`57021ba`); diagnostics confirmed requirements=9 / .env.example exists / system_prompt=6218 bytes; HANDOFF session-end round (`dcd071b`) | Criterion #5 smoke ready but not run — awaiting B's auth-path decision (local run per runbook vs. platform key injection). Criterion #6 not authorized. |
| 6 | 2026-05-21 | Diagnosed lost-work event from prior session's halt-before-push across container boundary (criterion #5 + doc alignment + 3 unpushed commits gone). B set new push-before-halt rule. Switched to canonical branch per B. Pre-flight: G-A1..G-A7 PASS, round-trip pytest 9/9 PASS. Rebuilt & pushed: OBSERVATIONS entry (`b370539`), doc alignment 5→7 (`c186ce6`), criterion #5 code (`cbcb706`), HANDOFF round (`61d0890`). All on `origin/claude/ezz-steel-scraper-step1-yQejR`. | 4-button criterion #5 smoke not yet run — blocked on `ANTHROPIC_API_KEY` in this container. Awaiting B for the key (or auth-mechanism confirmation). |
| 5 | 2026-05-08 | Pushed Step C commits to canonical + main (`b2c1274..4359c76`); OBSERVATIONS entry on runs-table workflow (`7a4378d`); Appendix B criterion #4 — `scripts/test_endpoints.py` HTTP test runner against live uvicorn; 16/16 cases PASS against a fresh DB; criterion #4 commit + HANDOFF round | 2 unpushed commits; awaiting B on push and on "go" for criterion #5 (Streamlit UI) — flagged as the gate that needs its own kickoff review |
| 4 | 2026-05-08 | Step B settle-up (CBE branch fix `b014654`, OBSERVATIONS Finding 2 `2f5629b`, round-trip pytest G-B1 `b484995`); Step C / Appendix B criterion #3 — all 8 remaining §5 tools implemented (`0ee06b3`), translator updated for Optional/`anyOf` params, all 9 tools PASS round-trip pytest, criterion #3 filter-optionality spot-check PASS, functional smoke test on all 9 endpoints PASS; pushed prior Step B commits to canonical + main | 5 unpushed commits; awaiting B on push and on "go" for criterion #4 (HTTP test script) and #5 (Streamlit UI) |
| 3 | 2026-05-08 | Step B / Appendix B criterion #2: `get_dataset` route, translator + `route_once` in `chat.py`, round-trip validation PASS (description byte-identical to spec §5, sha256 `94228a7e…`), live routing test PASS via `claude-haiku-4-5` | 4 unpushed commits; awaiting B on push and Step C / criterion #3 |
| 2 | 2026-05-08 | Step A recovery via merge (`641b8d3`); G-A1–G-A7 all PASS; VERIFICATION.md G-A7 SQL fix (`f53c1e1`); HANDOFF recovery update (`9206960`); push consolidation to `origin/main` and `origin/claude/ezz-steel-scraper-step1-yQejR` both at `9206960`; session branch retired; env setup with `python-dotenv==1.0.1` committed as `10ea7648`; `.env` created and gitignored; API key load + Anthropic ping PASS end-to-end | 2 unpushed commits; awaiting B on push and Step B "go" |
| 1 | 2026-04-30 | Step A scaffolding (6 files, 609 insertions, commit `e525c21`); v1.1 spec removed (`4fb559e`); 9 tables seeded | Step B paused awaiting "go" and API key |
