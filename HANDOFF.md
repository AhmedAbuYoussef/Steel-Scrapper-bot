# HANDOFF.md — Session continuity log

This file is the bridge between Claude Code sessions. Updated at the end of every session (or when limits are about to hit). Read at the start of every session, before anything else.

If this file says one thing and the code says another, **the code is the truth** but the discrepancy is itself information — surface it to B.

---

## Last session summary

- **Session ended:** 2026-05-21, mid-flight in step 6 of B's 2026-05-21 brief (criterion #5 verification smoke). Criterion #5 code is on origin; the 4-button smoke is the next runnable step, blocked on `ANTHROPIC_API_KEY` availability in this container.
- **Why ended:** Previous session (start of 2026-05-21) detected the lost-work event from the halt-before-push container reclaim — the prior session's criterion #5 + doc alignment + 3 commits (00f859c, 487a496, 0eceda3) were never on origin. This session rebuilt them under the new push-before-halt operating rule B set in the 2026-05-21 brief. Pushed in order: OBSERVATIONS entry on the lost work (`b370539`), doc alignment 5→7 (`c186ce6`), criterion #5 code (`cbcb706`). This HANDOFF round is `<new>`. Smoke still to run.
- **What got done this session (so far):**
  - **Pre-flight verification.** Fresh `python db.py`; G-A1..G-A7 all PASS; round-trip pytest 9/9 PASS in 0.80s. No drift since 2026-05-08.
  - **Branch decision.** B authorized switching off the task-runner's default branch `claude/verify-docs-alignment-eb34f` (which is what this container started on) to the canonical `claude/ezz-steel-scraper-step1-yQejR` named in CLAUDE.md §1. Both were at `7894cb2`. Fetched canonical from origin and checked out a local tracking branch. All work pushed to canonical.
  - **OBSERVATIONS entry — lost work from halt-before-push across container boundary (`b370539`).** Records what was lost (criterion #5 + doc alignment + 3 commits), the root cause (containers in this remote-execution environment are reclaimed after inactivity; unpushed commits are gone), and the new operating rule from B (**push-before-halt**: every commit lands on origin before any halt; if push fails, that's the halt point). Note: B is considering codifying this in CLAUDE.md §3.
  - **Doc alignment 5 → 7 (`c186ce6`).** CLAUDE.md §1 / §3: "five locked prompts" → "seven canned prompts (five rehearsed in the live demo)"; "do not add a sixth" → "do not add an eighth"; spec entry "11 (the five prompts)" → "11 (the seven canned prompts)". DEMO_RUNBOOK.md §1: rewritten to distinguish canonical (7) vs rehearsed (5 — prompts 1, 2, 4, 5, 6 per §12 stage script); Steps 3–6 now name prompts 2, 4, 5, 6 (Step 2 keeps prompt 1). DEMO_RUNBOOK.md §2 T-7: criterion #6 covers all 7; fallbacks cover the 5 rehearsed. DEMO_RUNBOOK.md Card 3 + §1 "NEVER" list: out-of-scope asks measured against canonical 7. VERIFICATION.md Canary C1: "seven canned prompts". Spec untouched (flag-don't-act). Aphorism at DEMO_RUNBOOK.md §8 ("four prompts that run vs. five where the fifth breaks") left intact — that's a reliability maxim about the rehearsed count, not canonical.
  - **Criterion #5 code (`cbcb706`).** `main.py`: new `/system_prompt` endpoint returns `system_prompt.txt` verbatim as `text/plain`; `include_in_schema=False` keeps it off `/openapi.json`. Validated byte-identical against `system_prompt.txt`; round-trip pytest still 9/9 PASS. `chat.py`: new helpers `fetch_system_prompt`, `fetch_tools`, `data_frozen_timestamp`, `agent_turn` (Claude+tool dispatch loop, bounded `max_iters=10`). `data_frozen_timestamp` uses `db.py` mtime (not `runs.finished_at` because that mutates on every refresh-stub call per OBSERVATIONS 2026-05-08; not `scraperbot.db` mtime because db.py is the canonical seed source). Streamlit UI guarded by `if __name__ == "__main__":` so pytest's `from chat import ...` does not trigger UI side effects. UI per spec §10: title + caption verbatim, welcome `st.info` with Appendix A WELCOME MESSAGE (timestamp substituted), four suggested-prompt buttons in 2-column grid (verbatim §10 copy), `st.chat_input`, reset button, footer caption with the same frozen timestamp.
- **What's mid-flight:** Step 6 of B's 2026-05-21 brief — the 4-button criterion #5 smoke test against fresh `db.py` + live uvicorn — has not run. The smoke requires `ANTHROPIC_API_KEY`, which is not present in this container's environment (no `.env`, no env var). Containers are ephemeral so the prior session's `.env` did not survive. **Halting at the smoke gate to ask B for the key (or for confirmation that the platform proxies via `ANTHROPIC_BASE_URL` alone)** before continuing.
- **Next concrete step on resume:** B provides `ANTHROPIC_API_KEY` (or confirms the platform proxy handles auth). Then: fresh `python db.py`; `uvicorn main:app` on port 8000; `streamlit run chat.py` on the side; click each of the 4 suggested-prompt buttons; capture per-button transcript (tools called + sequence + response shape + length + PASS/FAIL on non-error). Compare to the lost session's reported behavior (especially: button 3 date-window self-correct, button 4 clarification ask). Commit the smoke artifact, push, then halt for B's wrap-up review.

(Session 5's detailed bullets — Step B/C/criterion-#4 build-out — now live in the Session history table below; the full text is preserved in git history at commit `7894cb2`.)

---

## Verification status as of session end

- **Step A (G-A1–G-A7):** all PASS. Last run 2026-05-21 on fresh DB. Schema and seed unchanged since Step A. `system_prompt.txt` sha256 baseline unchanged (`7bbf9e06…`). **Workflow note:** re-run `python db.py` before re-running G-A3 — the `runs == 5` baseline is sensitive to any session that hit `/refresh_egy_map` or `/extract_latest_cbe_bulletin`.
- **Step B (G-B1 round-trip):** 9/9 PASS, last run 2026-05-21 in 0.80s (also re-run after `/system_prompt` added — confirmed unchanged because the test only iterates the 9 §5 tools).
- **Criterion #3 spot-check:** PASS — `query_projects` and `estimate_steel_total` filters all optional.
- **Criterion #4 (HTTP test script):** 16/16 cases PASS via `scripts/test_endpoints.py` against fresh DB + live uvicorn on port 8000 (last run 2026-05-08; not re-run this session because the criterion #5 changes don't touch the 9 §5 routes).
- **Criterion #5 (Streamlit chat UI + /system_prompt):** code on origin (`cbcb706`). Endpoint validated byte-identical to `system_prompt.txt` and confirmed absent from `/openapi.json`. **4-button live smoke NOT YET RUN** — blocked on `ANTHROPIC_API_KEY` availability in this container.
- **Criterion #6 (all seven §11 prompts non-error):** not started. Sits on top of criterion #5 smoke pass.
- **Failures:** None.
- **Drift signals:** `requirements.txt` 7 → 9 lines (added `python-dotenv==1.0.1` and `pytest==8.3.4`, both B-approved; B has noted the next dep gets the explicit-ask treatment regardless of how implicit the task directive seems). `main.py` ~256 lines (9 routes + helpers). `chat.py` ~44 lines (translator + anyOf helper + `route_once`).
- **Hashes pinned:**
  - `system_prompt.txt` (spec Appendix A): `7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01`
  - `GET_DATASET_DESCRIPTION` (spec §5 line 142, with trailing `\n` for diff alignment): `94228a7e5127b96b95149f27095b284623f64c607d8e89aea8f816a72ec8c8dc`
  - The remaining 8 §5 descriptions are pinned indirectly by their spec line numbers in the G-B1 test registry; any drift fails the pytest.

---

## Open questions for B

- **`ANTHROPIC_API_KEY` for this container.** The smoke gate at step 6 of the 2026-05-21 brief needs it. `.env` is gitignored and didn't survive the container reclaim; no key in the live env. `ANTHROPIC_BASE_URL` is set, suggesting platform proxying, but the SDK still wants `ANTHROPIC_API_KEY`. Either provide the key, or confirm I should use a different auth mechanism.
- **Codify push-before-halt in CLAUDE.md §3?** B flagged in the 2026-05-21 brief that this is under consideration. OBSERVATIONS entry recorded. Awaiting B's call.
- **Spec v1.3 amendments** (two OBSERVATIONS entries dated 2026-05-08). Flag-don't-act; awaiting B's call on (a) §3.1 docstring wording, (b) the runs-table side-effect workflow note (whether to codify as a wrapper script).
- **Criterion #6 ("go").** All seven §11 prompts must produce a non-error response on dummy data. B has said this is a separate gate that follows criterion #5 verification. Not authorized to start until B confirms criterion #5 is durably on origin and the smoke matches the lost-session behavior.
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
| 6 | 2026-05-21 | Diagnosed lost-work event from prior session's halt-before-push across container boundary (criterion #5 + doc alignment + 3 unpushed commits gone). B set new push-before-halt rule. Switched to canonical branch per B. Pre-flight: G-A1..G-A7 PASS, round-trip pytest 9/9 PASS. Rebuilt & pushed: OBSERVATIONS entry (`b370539`), doc alignment 5→7 (`c186ce6`), criterion #5 code (`cbcb706`), HANDOFF round (`<new>`). All on `origin/claude/ezz-steel-scraper-step1-yQejR`. | 4-button criterion #5 smoke not yet run — blocked on `ANTHROPIC_API_KEY` in this container. Awaiting B for the key (or auth-mechanism confirmation). |
| 5 | 2026-05-08 | Pushed Step C commits to canonical + main (`b2c1274..4359c76`); OBSERVATIONS entry on runs-table workflow (`7a4378d`); Appendix B criterion #4 — `scripts/test_endpoints.py` HTTP test runner against live uvicorn; 16/16 cases PASS against a fresh DB; criterion #4 commit + HANDOFF round | 2 unpushed commits; awaiting B on push and on "go" for criterion #5 (Streamlit UI) — flagged as the gate that needs its own kickoff review |
| 4 | 2026-05-08 | Step B settle-up (CBE branch fix `b014654`, OBSERVATIONS Finding 2 `2f5629b`, round-trip pytest G-B1 `b484995`); Step C / Appendix B criterion #3 — all 8 remaining §5 tools implemented (`0ee06b3`), translator updated for Optional/`anyOf` params, all 9 tools PASS round-trip pytest, criterion #3 filter-optionality spot-check PASS, functional smoke test on all 9 endpoints PASS; pushed prior Step B commits to canonical + main | 5 unpushed commits; awaiting B on push and on "go" for criterion #4 (HTTP test script) and #5 (Streamlit UI) |
| 3 | 2026-05-08 | Step B / Appendix B criterion #2: `get_dataset` route, translator + `route_once` in `chat.py`, round-trip validation PASS (description byte-identical to spec §5, sha256 `94228a7e…`), live routing test PASS via `claude-haiku-4-5` | 4 unpushed commits; awaiting B on push and Step C / criterion #3 |
| 2 | 2026-05-08 | Step A recovery via merge (`641b8d3`); G-A1–G-A7 all PASS; VERIFICATION.md G-A7 SQL fix (`f53c1e1`); HANDOFF recovery update (`9206960`); push consolidation to `origin/main` and `origin/claude/ezz-steel-scraper-step1-yQejR` both at `9206960`; session branch retired; env setup with `python-dotenv==1.0.1` committed as `10ea7648`; `.env` created and gitignored; API key load + Anthropic ping PASS end-to-end | 2 unpushed commits; awaiting B on push and Step B "go" |
| 1 | 2026-04-30 | Step A scaffolding (6 files, 609 insertions, commit `e525c21`); v1.1 spec removed (`4fb559e`); 9 tables seeded | Step B paused awaiting "go" and API key |
