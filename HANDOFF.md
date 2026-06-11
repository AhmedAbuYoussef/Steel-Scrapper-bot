# HANDOFF.md — Session continuity log

This file is the bridge between Claude Code sessions. Updated at the end of every session (or when limits are about to hit). Read at the start of every session, before anything else.

If this file says one thing and the code says another, **the code is the truth** but the discrepancy is itself information — surface it to B.

---

## Last session summary

- **Session ended:** 2026-05-22, clean halt at B's review gate. All work pushed (push-before-halt held the entire session). Origin `claude/ezz-steel-scraper-step1-yQejR` at `57021ba`.
- **Why ended:** B requested session end + handoff. The remaining blocker — `ANTHROPIC_API_KEY` for the criterion #5 smoke — is a B-side decision (local-machine run vs. platform key injection), so nothing further was runnable in-container.
- **What got done this session (2026-05-21 → 2026-05-22, one container spanning both days):**
  - **Sessions 6 work (2026-05-21):** lost-work diagnosis, push-before-halt rule adoption, branch switch to canonical, pre-flight (G-A1..G-A7 PASS, round-trip 9/9 PASS), rebuild of doc alignment + criterion #5 code. Commits `b370539`, `c186ce6`, `cbcb706`, `61d0890` — see session history table for detail.
  - **Stale-branch OBSERVATIONS entry (`be308cd`).** `claude/verify-docs-alignment-eb34f` on origin is stale at `7894cb2`; B said note-don't-delete. Cleanup options recorded in OBSERVATIONS.
  - **Criterion #5 smoke harness (`4b30702`, tests/smoke_criterion_5.py).** Standalone script (not a pytest target): spawns uvicorn on a free port, drives `chat.agent_turn` once per §10 button (4 verbatim prompts), captures per-button tool sequence + final text (500 chars) + iteration count + duration + PASS/FAIL, writes timestamped transcript to repo root (gitignored), tears down uvicorn in a `finally`. Exit 0/1/2 semantics. **Committed under the `[awaiting B review]` prefix** — the stop hook forced commit-and-push of what B had asked to keep staged; B retroactively approved the disposition ("your commit-and-push decision over strict-stage-only was right").
  - **Auth surface investigation (reported in chat, twice).** No `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` in env; `ANTHROPIC_BASE_URL` is the real `https://api.anthropic.com` (not an auth-injecting proxy); no secret-store paths (`/run/secrets`, `~/.config/anthropic`, etc.); `/run/ccr/session_token` is harness-to-platform auth, regenerated per container. Container date rolled 05-21 → 05-22 mid-conversation, confirming reclaim cycles; persistence of any in-container secret across reclaim: effectively none observed, platform-side injection mechanisms unknown.
  - **Local-run runbook (`57021ba`, tests/smoke_criterion_5_LOCAL.md).** Human-driven 10-section runbook for B to run the smoke on a local machine with the key: fresh clone → venv → `db.py` → uvicorn → verify 9 OpenAPI paths + `/system_prompt` sha (`7bbf9e06…`, 6218 bytes) → run harness → teardown → commit transcript via copy-paste template. Per-step rollbacks and a §9 hash/count expectations table. Diagnostics B requested (requirements count, .env.example, system_prompt bytes) all matched the draft — zero content revisions needed.
  - **.gitignore pattern fix (also `57021ba`).** `smoke_criterion_5_*.md` → `smoke_criterion_5_[0-9]*.md`; the broad pattern was accidentally masking the `_LOCAL.md` runbook.
- **What's mid-flight:** Nothing in-flight in code. The criterion #5 smoke is ready to run the moment auth exists (in-container) or B runs it locally per the runbook. Criterion #6 not started, not authorized.
- **Next concrete step on resume:** B's auth-path decision executes first: **(path A)** B runs `tests/smoke_criterion_5_LOCAL.md` locally and pushes the transcript, then the next session verifies the pushed transcript and proceeds toward the criterion #6 gate; or **(path B)** B injects the key platform-side and the next session runs `python db.py && python tests/smoke_criterion_5.py` directly, commits + pushes the transcript. Either way, after the smoke is green and B reviews: criterion #6 (all seven §11 prompts via `chat.agent_turn`) awaits B's separate "go".

---

## Verification status as of session end

- **Step A (G-A1–G-A7):** all PASS. Last run 2026-05-21 on fresh DB. Schema and seed unchanged since Step A. `system_prompt.txt` sha256 baseline unchanged (`7bbf9e06…`). **Workflow note:** re-run `python db.py` before re-running G-A3 — the `runs == 5` baseline is sensitive to any session that hit `/refresh_egy_map` or `/extract_latest_cbe_bulletin`.
- **Step B (G-B1 round-trip):** 9/9 PASS, last run 2026-05-21 in 0.80s (also re-run after `/system_prompt` added — confirmed unchanged because the test only iterates the 9 §5 tools).
- **Criterion #3 spot-check:** PASS — `query_projects` and `estimate_steel_total` filters all optional.
- **Criterion #4 (HTTP test script):** 16/16 cases PASS via `scripts/test_endpoints.py` against fresh DB + live uvicorn on port 8000 (last run 2026-05-08; not re-run this session because the criterion #5 changes don't touch the 9 §5 routes).
- **Criterion #5 (Streamlit chat UI + /system_prompt):** code on origin (`cbcb706`). Endpoint validated byte-identical to `system_prompt.txt` (sha `7bbf9e06…`, 6218 bytes) and confirmed absent from `/openapi.json` (9 paths). Smoke harness (`tests/smoke_criterion_5.py`, `4b30702`) and local runbook (`tests/smoke_criterion_5_LOCAL.md`, `57021ba`) both on origin. **4-button live smoke NOT YET RUN** — blocked on auth-path decision (B local-run vs. platform key injection).
- **Criterion #6 (all seven §11 prompts non-error):** not started. Sits on top of criterion #5 smoke pass + B's "go".
- **Failures:** None.
- **Drift signals:** `requirements.txt` 7 → 9 lines (added `python-dotenv==1.0.1` and `pytest==8.3.4`, both B-approved; B has noted the next dep gets the explicit-ask treatment regardless of how implicit the task directive seems). **CLAUDE.md §3 still says "pinned at 7 packages" — B has seen the 9-package fact and is deciding which doc is source of truth; do not edit CLAUDE.md §3 without B's call.** `main.py` ~298 lines (9 routes + `/system_prompt` + helpers). `chat.py` ~251 lines (translator + helpers + `agent_turn` + guarded Streamlit UI).
- **Hashes pinned:**
  - `system_prompt.txt` (spec Appendix A): `7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01`
  - `GET_DATASET_DESCRIPTION` (spec §5 line 142, with trailing `\n` for diff alignment): `94228a7e5127b96b95149f27095b284623f64c607d8e89aea8f816a72ec8c8dc`
  - The remaining 8 §5 descriptions are pinned indirectly by their spec line numbers in the G-B1 test registry; any drift fails the pytest.

---

## Open questions for B

- **Auth path for the criterion #5 smoke (the gating decision).** Auth surface investigation complete (2026-05-22, reported in chat): no key in container env, no secret store, no auth-injecting proxy, no observed persistence across reclaim. Path A: B runs `tests/smoke_criterion_5_LOCAL.md` on a local machine and pushes the transcript. Path B: B finds a platform-side injection mechanism (session env / SessionStart hook) and the next session runs the smoke in-container.
- **Approve or revert the two `[awaiting B review]` commits** — `4b30702` (smoke harness) and `57021ba` (local runbook + .gitignore tighten). `4b30702`'s disposition was retroactively approved by B in chat ("commit-and-push decision … was right; stays as historical record"); `57021ba` followed the same pattern and awaits the same explicit call on contents.
- **CLAUDE.md §3 "7 packages" vs requirements.txt 9 packages.** Both extras (`python-dotenv`, `pytest`) were B-approved historically (commits `10ea764`, `b484995`). B has the verbatim diagnostic facts (2026-05-22 chat) and is deciding which doc gets corrected. Do not edit either without the call.
- **Codify push-before-halt in CLAUDE.md §3?** Under consideration since the 2026-05-21 brief. OBSERVATIONS entry recorded. Related friction: the stop hook (`~/.claude/stop-hook-git-check.sh`) forces commit-and-push of work B asked to keep staged — twice this session. B has kept hook modification off the table; the `[awaiting B review]` commit-prefix pattern is the working compromise.
- **Stale branch `claude/verify-docs-alignment-eb34f`** on origin at `7894cb2` (OBSERVATIONS 2026-05-21). Options: FF to canonical HEAD, delete, or leave. Don't-delete stands until B says otherwise.
- **Spec v1.3 amendments** (two OBSERVATIONS entries dated 2026-05-08). Flag-don't-act; awaiting B's call on (a) §3.1 docstring wording, (b) the runs-table side-effect workflow note (whether to codify as a wrapper script).
- **Criterion #6 ("go").** All seven §11 prompts must produce a non-error response on dummy data. Separate gate after the criterion #5 smoke is green and reviewed. Not authorized.
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
- Do not start criterion #6 before B explicitly authorizes it after reviewing the criterion #5 smoke results — criterion #6 is a separate gate per B (2026-05-21 brief).
- **Do not halt with unpushed commits in this container** (push-before-halt rule, B 2026-05-21). Containers are reclaimed after inactivity and unpushed work is gone. If push fails, that's the halt point — investigate, don't keep working on top of unpushed commits.
- Do not push any branch other than the one B has authorized for the session. B authorized canonical `claude/ezz-steel-scraper-step1-yQejR` for the 2026-05-21 session (not the task-runner default `claude/verify-docs-alignment-eb34f`).

---

## Session history (last 5 sessions)

Most recent at top. Older entries get pruned to the last five — but never deleted entirely without B's say-so. If full history is needed, move pruned entries to `HANDOFF_ARCHIVE.md`.

| Session # | Date | What got done | What was mid-flight |
|-----------|------|---------------|---------------------|
| 7 | 2026-05-21→22 | Same container as session 6, continued after B's review. Stale-branch OBSERVATIONS (`be308cd`); smoke harness `tests/smoke_criterion_5.py` (`4b30702`, hook-forced commit under `[awaiting B review]`, disposition approved by B); auth surface investigation ×2 (no key, no secret store, no proxy auth, no persistence — full probe output in 2026-05-22 chat); local-run runbook `tests/smoke_criterion_5_LOCAL.md` + .gitignore pattern fix (`57021ba`); diagnostics confirmed requirements=9 / .env.example exists / system_prompt=6218 bytes; HANDOFF session-end round (`<new>`) | Criterion #5 smoke ready but not run — awaiting B's auth-path decision (local run per runbook vs. platform key injection). Criterion #6 not authorized. |
| 6 | 2026-05-21 | Diagnosed lost-work event from prior session's halt-before-push across container boundary (criterion #5 + doc alignment + 3 unpushed commits gone). B set new push-before-halt rule. Switched to canonical branch per B. Pre-flight: G-A1..G-A7 PASS, round-trip pytest 9/9 PASS. Rebuilt & pushed: OBSERVATIONS entry (`b370539`), doc alignment 5→7 (`c186ce6`), criterion #5 code (`cbcb706`), HANDOFF round (`61d0890`). All on `origin/claude/ezz-steel-scraper-step1-yQejR`. | 4-button criterion #5 smoke not yet run — blocked on `ANTHROPIC_API_KEY` in this container. Awaiting B for the key (or auth-mechanism confirmation). |
| 5 | 2026-05-08 | Pushed Step C commits to canonical + main (`b2c1274..4359c76`); OBSERVATIONS entry on runs-table workflow (`7a4378d`); Appendix B criterion #4 — `scripts/test_endpoints.py` HTTP test runner against live uvicorn; 16/16 cases PASS against a fresh DB; criterion #4 commit + HANDOFF round | 2 unpushed commits; awaiting B on push and on "go" for criterion #5 (Streamlit UI) — flagged as the gate that needs its own kickoff review |
| 4 | 2026-05-08 | Step B settle-up (CBE branch fix `b014654`, OBSERVATIONS Finding 2 `2f5629b`, round-trip pytest G-B1 `b484995`); Step C / Appendix B criterion #3 — all 8 remaining §5 tools implemented (`0ee06b3`), translator updated for Optional/`anyOf` params, all 9 tools PASS round-trip pytest, criterion #3 filter-optionality spot-check PASS, functional smoke test on all 9 endpoints PASS; pushed prior Step B commits to canonical + main | 5 unpushed commits; awaiting B on push and on "go" for criterion #4 (HTTP test script) and #5 (Streamlit UI) |
| 3 | 2026-05-08 | Step B / Appendix B criterion #2: `get_dataset` route, translator + `route_once` in `chat.py`, round-trip validation PASS (description byte-identical to spec §5, sha256 `94228a7e…`), live routing test PASS via `claude-haiku-4-5` | 4 unpushed commits; awaiting B on push and Step C / criterion #3 |
| 2 | 2026-05-08 | Step A recovery via merge (`641b8d3`); G-A1–G-A7 all PASS; VERIFICATION.md G-A7 SQL fix (`f53c1e1`); HANDOFF recovery update (`9206960`); push consolidation to `origin/main` and `origin/claude/ezz-steel-scraper-step1-yQejR` both at `9206960`; session branch retired; env setup with `python-dotenv==1.0.1` committed as `10ea7648`; `.env` created and gitignored; API key load + Anthropic ping PASS end-to-end | 2 unpushed commits; awaiting B on push and Step B "go" |
| 1 | 2026-04-30 | Step A scaffolding (6 files, 609 insertions, commit `e525c21`); v1.1 spec removed (`4fb559e`); 9 tables seeded | Step B paused awaiting "go" and API key |
