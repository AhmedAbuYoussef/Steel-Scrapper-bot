# HANDOFF.md — Session continuity log

This file is the bridge between Claude Code sessions. Updated at the end of every session (or when limits are about to hit). Read at the start of every session, before anything else.

If this file says one thing and the code says another, **the code is the truth** but the discrepancy is itself information — surface it to B.

---

## Last session summary

- **Session ended:** 2026-05-08, after Step A recovery
- **Why ended:** Step A artifacts successfully recovered onto the current session branch via merge; verification re-run from a clean `db.py` rebuild and all G-A1 through G-A7 PASS; awaiting B's decisions on push strategy, branch reconciliation, and Step B "go" (environment setup queued first).
- **What got done:**
  - **Forensics.** Discovered the repo had split into two lineages at common ancestor `5c3ed9e`. The docs lineage (tip `02a3958`, also `main`/`origin/main`) carried `CLAUDE.md`, `HANDOFF.md`, `VERIFICATION.md`, `OBSERVATIONS.md`, `README.md`, `DEMO_RUNBOOK.md`, plus an inadvertent re-introduction of the v1.1 spec. The code lineage (`origin/claude/ezz-steel-scraper-step1-yQejR`, tip `e525c21`, parent `4fb559e`) carried the Step A scaffold (`db.py`, `system_prompt.txt`, `requirements.txt`, `main.py`, `chat.py`, `.gitignore`) plus v1.2 spec only, with v1.1 deleted. Both `e525c21` and `4fb559e` were intact on origin, neither GC'd. The two lineages had never been merged, which is why the working tree on the docs side carried zero code despite HANDOFF describing Step A as "complete."
  - **Recovery.** Merged `origin/claude/ezz-steel-scraper-step1-yQejR` onto `claude/check-status-continue-QT5cm` with `--no-ff`. Strategy `ort`, zero conflicts. Merge commit `641b8d3`. The v1.1 spec deletion was folded into the merge automatically by clean three-way resolution (recovered branch's `4fb559e` deletion vs docs branch unchanged on v1.1 since the common ancestor). The original plan called for a standalone deletion commit, but Option 1 was chosen — the merge diff already records the deletion, and a re-add-then-delete sequence would obscure history more than it clarifies. None of the recovered files were regenerated; the blobs in the merged tree are byte-identical to the originals at `e525c21`.
  - **Verification.** Rebuilt `scraperbot.db` from `db.py` and executed VERIFICATION.md §1 manual procedure plus G-A4 (system-prompt diff). All seven golden tests PASS against the merged tree:
    - **G-A1: PASS** — `python db.py` produces `scraperbot.db` (57344 bytes, ~56 KB; spec said "~57 KB").
    - **G-A2: PASS** — exactly 9 Section 4 tables present, names match.
    - **G-A3: PASS** — row counts match baseline (cbe_metrics 60, cbe_raw_extractions 5, cleaning_log 8, conversations 3, projects_clean 5, projects_clean_currency_only 5, projects_raw 5, runs 5, steel_ratios 10).
    - **G-A4: PASS** — `system_prompt.txt` byte-identical to spec v1.2 Appendix A (extracted between the ``` fences at lines 522–633 of `scraper_bot_demo_spec_v1_2.md`). `diff -u system_prompt.txt /tmp/appendix_a_extracted.txt` returned exit 0. Both files sha256 = `7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01`. 112 lines, 6218 bytes each. This is the strongest possible evidence of byte-identicality.
    - **G-A5: PASS** — `steel_ratios` columns match spec §4 line 126 exactly: `category, subcategory, scale_variable, low_ratio, typical_ratio, high_ratio, confidence, egypt_factor, assumptions, sources`.
    - **G-A6: PASS** — `projects_clean` 5 rows match Appendix B: Dabaa Nuclear Plant, 6th October Monorail, 13K Housing Units Kafr El Sheikh, East Port Said Logistics Zone, Red Sea Solar Plant.
    - **G-A7: PASS** — `cleaning_log` 8 rows verbatim against spec §6 lines 176–183 (issue text, rows_affected, action text all match). The "312 cells" / INTEGER 312 nuance loss is the existing flagged observation in `OBSERVATIONS.md`, not a regression.
  - **Documentation bug fix.** VERIFICATION.md §2 G-A7's "Inputs:" line referenced columns `issue` and `action`, which do not exist in the schema (`db.py` and spec §4 use `issue_category` and `action_taken`). The literal SQL would have errored with `no such column: issue` if anyone had run it. This was a residue of the two-lineage split — VERIFICATION.md was authored on the docs side without ever being run against the actual code from `e525c21`. Fixed in commit `f53c1e1`: input SQL only, golden expected values untouched. Documentation bug surfaced by recovery verification, fixed in scope per Option B.
- **What's mid-flight:** Nothing in code. Awaiting B's decisions on:
  - Push strategy — which branch(es) to push to (current session branch, canonical branch, main, or some combination).
  - Whether to retire `claude/check-status-continue-QT5cm` post-push.
  - Whether to update `CLAUDE.md` §1's branch field to match whichever branch is chosen canonical post-recovery.
  - Step B "go" — still NOT YET; `ANTHROPIC_API_KEY` environment setup queued first.
- **Next concrete step on resume:** Get B's decision on push strategy and branch reconciliation; arrange `ANTHROPIC_API_KEY` to be set in the environment; only then begin Step B work per spec §11 routing criterion.

---

## Verification status as of session end

- **Last full run:** 2026-05-08, end of recovery session.
- **Result:** G-A1 through G-A7 all PASS against the post-merge tree, against a freshly rebuilt `scraperbot.db`. Hallucination canaries C1–C5 not yet runnable (require Step B routing). Round-trip tests RT1/RT2 not run this session.
- **Per-table row counts at end of recovery:**

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

- **Failures:** None.
- **Mid-session VERIFICATION.md edit:** G-A7's input SQL was fixed (commit `f53c1e1`) — column names corrected to match schema. Golden expected values were not modified. Authorized by B as Option B with strict scope control.

---

## Open questions for B

- **Push strategy.** Which branch(es) should the recovered state be pushed to? Options include the current session branch (`claude/check-status-continue-QT5cm`), the canonical branch (`claude/ezz-steel-scraper-step1-yQejR`), `main`, or a combination. No push has happened in this session.
- **Branch reconciliation.** Session is on `claude/check-status-continue-QT5cm`; `CLAUDE.md` §1 names `claude/ezz-steel-scraper-step1-yQejR` as canonical. After push strategy is decided, `CLAUDE.md` §1's branch field may need updating to match the chosen canonical branch. Flag for B's decision; do not edit `CLAUDE.md` autonomously.
- **`ANTHROPIC_API_KEY`.** Currently `unset` in this session's environment (informational check at session start). Step B blocked until it's set; environment setup is queued before Step B "go."
- **Demo target date and audience.** Still unset in `CLAUDE.md` §1. Set them so the demo-proximity protocol can engage at the right time.

**(Resolved this session)** 60-vs-12 `cbe_metrics`: KEEP 60. Confirmed by B during recovery session. The 12 monthly values × 5 metrics reading is correct; Appendix B's "12" is a wording slip in the spec, to be fixed in v1.3 of the spec when it lands. The seed count stays at 60 in `db.py`.

---

## Things to NOT do next session

- Do not regenerate or rebuild any Step A scaffolding — it's recovered, verified, and committed. The blobs are originals from `e525c21`.
- Do not edit `db.py` seed data to satisfy any future test failure — flag the test instead.
- Do not commit `scraperbot.db` — it's a build artifact excluded by `.gitignore`.
- Do not edit `system_prompt.txt` away from spec Appendix A. (sha256 baseline: `7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01`.)
- Do not push any branch or commit without B's explicit authorization — push strategy is still pending.
- Do not edit `CLAUDE.md` §1's branch field until B decides which branch is canonical post-recovery.
- Do not start Step B logic before B explicitly says "go" and `ANTHROPIC_API_KEY` is confirmed set.

---

## Session history (last 5 sessions)

Most recent at top. Older entries get pruned to the last five — but never deleted entirely without B's say-so. If full history is needed, move pruned entries to `HANDOFF_ARCHIVE.md`.

| Session # | Date | What got done | What was mid-flight |
|-----------|------|---------------|---------------------|
| 2 | 2026-05-08 | Step A recovery via merge of `origin/claude/ezz-steel-scraper-step1-yQejR` (merge commit `641b8d3`); G-A1–G-A7 all PASS against rebuilt `scraperbot.db`; VERIFICATION.md G-A7 SQL fix (commit `f53c1e1`, column names only); 60-vs-12 `cbe_metrics` resolved (keep 60) | Awaiting B on push strategy, branch reconciliation, `ANTHROPIC_API_KEY` env setup, Step B "go" |
| 1 | 2026-04-30 | Step A scaffolding (6 files, 609 insertions, commit `e525c21`); v1.1 spec removed (`4fb559e`); 9 tables seeded | Step B paused awaiting "go" and API key |
