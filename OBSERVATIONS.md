# OBSERVATIONS.md — Things noticed, not acted on

`CLAUDE.md` requires Claude Code to write here whenever it spots something outside the current scope (a refactor opportunity, an inconsistency, a probable bug in unrelated code, a potential improvement). The point is: **don't lose the observation, but also don't act on it without B's say-so.**

B reviews this file periodically and decides which observations become tasks (move them to the spec or to the next step's brief), which get archived, and which get killed.

---

## Open observations

Most recent at top.

### 2026-06-12 — `runs` fixture row 3 (`cbe_extractor`) says `rows_out=60`, now inconsistent with the 120-row `cbe_metrics` seed

- **What I noticed:** While reseeding `cbe_metrics` to 120 rows per spec v1.3 (Task 3 of B's 2026-06-12 brief), the `RUNS` fixture row 3 in `db.py` (`cbe_extractor`, `rows_out=60`) kept its old value. A 24-month frozen window implies the extraction run would have written 120 rows.
- **Why I didn't act:** Changing it alters a `runs` fixture value B didn't authorize in the Task 3 scope (which was cbe_metrics only). Cosmetic narrative inconsistency in dummy data; no test reads `rows_out`.
- **Awaiting:** B's call — update `rows_out` to 120 in a future approved pass, or leave as-is.

### 2026-06-12 — G-A1's "~57 KB" descriptive size is stale after the 120-row reseed

- **What I noticed:** `scraperbot.db` is now 73,728 bytes (~72 KB) after the v1.3 reseed; VERIFICATION.md G-A1 still says "~57 KB". Tolerance there is "file size approximate," but +28% stretches "approximate."
- **Why I didn't act:** B's Task 4 list explicitly named the only VERIFICATION.md edits authorized ("No other golden values change"); the size figure wasn't on it.
- **Awaiting:** B's approval to update G-A1's expected size to ~72 KB.

### 2026-05-21 — Stale branch on origin: `claude/verify-docs-alignment-eb34f`

- **What I noticed:** Session 6 (2026-05-21) was started by the task-runner on branch `claude/verify-docs-alignment-eb34f`. B authorized switching to canonical `claude/ezz-steel-scraper-step1-yQejR` for the actual work; both branches were at `7894cb2` at the time of the switch, and all session 6 commits went to canonical (now at `61d0890`). The verify-docs branch on origin is still at `7894cb2` — unchanged, just unused. Local copy of that branch also still exists.
- **Where:** `refs/heads/claude/verify-docs-alignment-eb34f` on origin; local `claude/verify-docs-alignment-eb34f` tracking it. Confirmed via `git ls-remote origin` at session 6 end.
- **Why it might matter:** The task-runner uses this branch name as the default development target for sessions invoked with that branch slug; leaving it stale at `7894cb2` while canonical advances will cause future task-runner-launched sessions to start on stale state. Eventually the branch will need to be either (a) fast-forwarded to track canonical, (b) deleted on origin if the task-runner can be reconfigured to use canonical, or (c) left alone if the slug is one-shot anyway.
- **Why I didn't act:** B explicitly instructed "Don't delete it this session" in the 2026-05-21 follow-up brief. Cleanup is a flag-don't-act item.
- **Awaiting:** B's call on how to retire it. Possibilities (in order of safety): FF the branch on origin to current canonical HEAD; delete the branch on origin; leave it as a historical marker.
- **B's call (2026-06-12):** leave it. Retirement is post-criterion-#6 housekeeping — revisit after criterion #6 is signed off. (Note: `git ls-remote origin` from the 2026-06-12 container shows only `claude/ezz-steel-scraper-step1-yQejR` and `main`; the remote-proxy in this environment may be filtering refs, so this is not confirmation the stale branch was deleted.)

### 2026-05-21 — Lost work from prior session: halt-before-push across container boundary

- **What I noticed:** A prior session built Appendix B criterion #5 (Streamlit chat UI + `/system_prompt` endpoint), did the CLAUDE.md/DEMO_RUNBOOK doc alignment from "five locked prompts" → "seven canned (five rehearsed)", and committed three commits on top of `7894cb2` (reported by B as `00f859c`, `487a496`, `0eceda3`). That session halted for B review with the commits unpushed. The container was then reclaimed before B could push. When this session started in a fresh container, none of that work was on origin — `git ls-remote` shows `claude/ezz-steel-scraper-step1-yQejR` and `main` both still at `7894cb2`, and the alleged commits don't exist on any branch. Lost work: criterion #5 build + the doc-alignment commit + the HANDOFF that documented them.
- **Where:** entire repo state as of session start 2026-05-21. CLAUDE.md and DEMO_RUNBOOK.md still read "five locked prompts" throughout; no `streamlit_app.py` or equivalent UI file; no `/system_prompt` route in `main.py`; HANDOFF.md still ends at criterion #4.
- **Why it might matter:** The previous protocol was "halt at logical checkpoints with unpushed commits, await B's review, then push." That protocol is **unsafe across container boundaries** — the remote-execution environment B is using reclaims containers after inactivity, and anything not on origin is gone when the next session starts. This will keep happening as long as the protocol stays "halt with unpushed work."
- **New operating rule (from B, 2026-05-21):** **push-before-halt.** Every commit lands on origin before any halt for B review. Halt for review at the end of logical chunks, but never halt with unpushed commits in the container. If push fails for any reason, that's the halt point — don't continue working with unpushed commits on top of an unpushed commit.
- **Awaiting:** ~~B is considering whether to codify this in `CLAUDE.md` §3 (Operating rules). Until then, this OBSERVATIONS entry + the explicit instruction in B's 2026-05-21 task brief carry the rule.~~ **Resolved 2026-06-12:** B approved codification; the rule now lives in `CLAUDE.md` §3 as "On push-before-halt."
- **What I did:** Logged it here and switched the operating discipline for this session to push-before-halt. Step 4 (redo doc alignment) and step 5 (rebuild criterion #5) of B's 2026-05-21 brief each terminate with a push before any halt point.

### 2026-05-08 — `runs`-table side effect from stub refresh endpoints constrains verification workflow

- **What I noticed:** `/refresh_egy_map` and `/extract_latest_cbe_bulletin` insert one row each into the `runs` table on every call, even in their Step 1 stub form. This is the correct behavior — the spec's "every action ends up in `cleaning_log` and `runs`" rule from §6 applies to scrape/extract triggers too. But it means that any test or smoke run that hits those endpoints leaves `runs` at >5 rows, which causes G-A3's `runs == 5` baseline to FAIL on the next G-A3 run if `db.py` hasn't been re-run in between.
- **Where:** `main.py` (`refresh_egy_map`, `extract_latest_cbe_bulletin`, both use `_record_run()`); `VERIFICATION.md` §2 G-A3; this session's smoke test left `runs` at 7 rows after Step C.
- **Why it might matter:** A future session that runs verification without rebuilding the DB first will see G-A3 FAIL on the `runs` count and may mistake it for a regression. The fix is workflow discipline, not code change — the endpoint behavior is correct.
- **What I did:** Documented the verification workflow: `python db.py` first (rebuilds `scraperbot.db` from scratch), then run tests / smoke / criterion #4. Every time. This needs to be the standard order whenever G-A3 is in scope. Recommend codifying in a `Makefile` target or a short `scripts/verify.sh` wrapper at some later cleanup step — flag-don't-act.
- **Awaiting:** B's call on whether to add a thin wrapper script that enforces the order. Not blocking; documenting the ordering rule alongside this observation is enough for now.

### 2026-05-08 — Spec §3.1 "docstring" wording diverges from implementation reality

- **What I noticed:** Spec §3.1 says "Implementation rule: put each Section 5 description verbatim into the FastAPI route docstring; the translator copies that string into the Anthropic schema with no transformation." Using a Python docstring directly is unsafe: FastAPI splits a docstring on the first newline into `summary` (first line) and `description` (rest). The §5 descriptions are long single-line paragraphs; line-wrapping them in source for readability would silently change the OpenAPI output, breaking the verbatim-preservation guarantee §3.1 itself depends on.
- **Where:** spec §3.1 (implementation-rule sentence); `main.py` (`GET_DATASET_DESCRIPTION` constant + `description=` decorator parameter).
- **What I did:** Stored each §5 description as a module-level constant and passed it via `description=` on the route decorator. The constant value goes verbatim into `operation.description` in OpenAPI, then verbatim into the Anthropic tool dict. Verified four-way byte-identical hash (`94228a7e…`): constant ≡ FastAPI OpenAPI ≡ Anthropic tool dict ≡ spec line 142. Flagged in source comment.
- **Why it might matter:** The pattern is about to be replicated for the other 8 tools in Step C. Doing this 8 more times without spec acknowledgement risks a future reader assuming the docstring wording in §3.1 is authoritative and "correcting" the code back to a broken state.
- **Recommendation:** Spec v1.3 should amend §3.1 to say "the FastAPI route's OpenAPI `description` field (via `description=` parameter on the route decorator OR a single-line docstring)" — wording that admits both mechanisms but explicitly excludes multi-line docstrings.
- **Awaiting:** B's call on whether to amend the spec. Flag-don't-act per CLAUDE.md §3 ("on the spec").

### 2026-04-30 — `cbe_metrics` row-count discrepancy: 60 rows seeded, Appendix B says "12"

- **What I noticed:** Appendix B's "Not in Step 1" note says "Hand-type 12 dummy `cbe_metrics` rows," but spec §4 (`"last 12 months"`), §8 (5 locked metrics), and §11 prompt 5 ("trend over past 12 months") all require 12 monthly values **per metric**. 12 rows total cannot satisfy criterion #6 for prompt 5.
- **Where:** `db.py` seed for `cbe_metrics` table; spec Appendix B + §11.
- **Why it might matter:** If B reads Appendix B as a hard 12-row cap, prompt 5 cannot meet criterion #6 with the current data. If 60 rows is correct, Appendix B should be edited in v1.3 of the spec to say "12 months × 5 metrics = 60 rows."
- **What I did:** Seeded 60 rows (12 months × 5 metrics, window 2025-04 → 2026-03, plausible monotonic series) and explicitly flagged the deviation in the Step A handoff for B's sign-off.
- **Awaiting:** ~~B's call — keep 60, or truncate to 12.~~ **Resolved 2026-06-12:** spec v1.3 (B-authored) sets the window to 24 months × 5 metrics = 120 rows after the session-9 button-4 FAIL showed a year-over-year quarterly comparison needs 15+ months. `db.py` reseeded accordingly; the original 60 rows kept byte-identical, 12 months extended backward (2024-04 → 2025-03).

### 2026-04-30 — `cleaning_log.rows_affected` column type loses cells-vs-rows nuance

- **What I noticed:** Spec §6 lists "312 cells" for one of the cleaning issues, but `cleaning_log.rows_affected` is an INTEGER column — the cells-vs-rows distinction is lost when stored as `312`.
- **Where:** `db.py` schema for `cleaning_log`; spec §6.
- **Why it might matter:** For the demo this is acceptable (it's dummy data), but if a future version reuses this schema for real cleaning runs, the unit ambiguity could cause silent reporting errors.
- **Why I didn't act:** Out of scope for Step A; flagged for Step B or later.

---

## Resolved / archived

(None yet.)
