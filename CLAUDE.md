# CLAUDE.md — Read this first, every session

This file is the contract between B and Claude Code for the ezz-steel-scraper-step1 demo project. Read it at the start of every session before touching any other file. If anything below conflicts with a user instruction, the user wins — but flag the conflict before complying.

---

## 1. Project identity

- **Project name:** ezz-steel-scraper-step1
- **One-sentence purpose:** A demo scraper bot for EZZ Steel + CBE data, with five locked prompts the audience can run against a SQLite store of cleaned project data, CBE metrics, and steel ratios.
- **Spec (single source of truth for scope and behavior):** `scraper_bot_demo_spec_v1_2.md` — sections 4 (tables), 6 (cleaning log), 8 (locked metrics), 10, 11 (the five prompts), Appendix A (system prompt), Appendix B (data fixtures). v1.1 was deleted in commit `4fb559e` and is no longer authoritative.
- **Branch:** `claude/ezz-steel-scraper-step1-yQejR`
- **Time budget remaining:** roughly 5.5–7.5 hours of the original 6–8h budget as of end of Step A.
- **Phase status:** Step A complete (commit `e525c21`). Step B paused awaiting B's "go" and `ANTHROPIC_API_KEY` confirmation.
- **Project completion gate:** the project is "done" when `VERIFICATION.md` reports a full-suite pass on whatever scope B has signed off as in-scope. Demo dates are NOT set before this gate.
- **Demo schedule:** `not yet scheduled`. The project is expected to be demoed multiple times to different audiences in different physical locations. Each demo instance gets its own prep file (`DEMO_<YYYY-MM-DD>_PREP.md`) created from the template in `DEMO_RUNBOOK.md` §0. Multiple demo prep files can coexist.
- **Mode flag:** `BUILD_MODE` (one of: `build`, `demo_prep`, `frozen`). Currently: `build`. See §6 for transition rules.

---

## 2. Required reads at session start

In this exact order, every session, before any code execution:

1. `CLAUDE.md` (this file)
2. `HANDOFF.md` — what the previous session ended on
3. `scraper_bot_demo_spec_v1_2.md` — the spec is the brief and the rulebook combined
4. `VERIFICATION.md` — golden tests and Step A done-criteria
5. `DEMO_RUNBOOK.md` — only required reading once the demo is within 7 days, otherwise reference-only

If any of these files are missing, malformed, or contradict each other, **halt and ask** rather than guess.

---

## 3. Operating rules (non-negotiable)

**On scope.** Do exactly what B asks for the current Step. Steps are defined in the spec — do not advance to Step B before B says "go," do not partially start Step C while finishing B, do not "improve" code outside the current step's scope. If you see something that needs fixing in another area, write it to `OBSERVATIONS.md` for B to triage later.

**On the spec.** `scraper_bot_demo_spec_v1_2.md` is locked. Only B edits it. If the spec is wrong or contradicts itself, surface it and ask — do not patch it inline. The 60-rows-vs-12-rows discrepancy you flagged in Step A is exactly the right behavior: deliberate deviation, surfaced explicitly with reasoning, awaiting sign-off.

**On data.** `db.py` + `scraperbot.db` is the canonical state. Never edit fixtures to make a test pass — that is the highest-severity violation in this project. If a test fails, the formula or the test is wrong, not the fixture. `scraperbot.db` is a build artifact (excluded via `.gitignore`); regenerate by running `db.py`. Do not commit it.

**On Appendix A (the system prompt).** `system_prompt.txt` must remain byte-identical to Appendix A of the spec, with the one Arabic-script correction you already caught and fixed. Re-verify with a diff before any commit that touches it. A silent system prompt edit is a drift event.

**On formulas and prompt logic.** The five locked prompts in spec §11 are the only behaviors the bot supports for this demo. Do not extend them, do not add a sixth, do not silently change what one of them returns. Each prompt has criteria #1–#6 in the spec — those are the acceptance tests.

**On uncertainty.** If you are not 70%+ confident in something, say so. Use phrases like "I think" or "based on what I read." Never fabricate a number, a citation, a function signature, or a library API. The Step A reply where you flagged the row-count discrepancy is the model — that's what surfacing uncertainty looks like.

**On dependencies.** `requirements.txt` is pinned at 7 packages (fastapi, uvicorn, streamlit, anthropic, requests, pydantic, httpx). Do not add new packages without asking. Do not bump versions without asking.

**On commits.** Before any commit, run the verification suite from `VERIFICATION.md`. If it fails, do not commit. Stage by name, not `git add .` — the same discipline you used in Step A. Always confirm `scraperbot.db` is excluded.

---

## 4. Forbidden behaviors

These are violations regardless of how reasonable they sound in the moment:

- Editing `db.py` seed data to make a test pass
- Editing `VERIFICATION.md` golden values without explicit user approval
- Patching `scraper_bot_demo_spec_v1_2.md` to resolve a contradiction (surface it instead)
- Editing `system_prompt.txt` away from spec Appendix A
- Advancing past the current Step without B's explicit "go"
- Adding a feature, prompt, route, or table the spec doesn't define
- Calling APIs, libraries, or functions you are not certain exist
- Committing `scraperbot.db`
- Continuing past an error you don't understand — stop and ask
- Deleting or compressing `HANDOFF.md` history without asking

---

## 5. Session-end protocol

Before you end a session (because B said so, or because limits are approaching), update `HANDOFF.md` with:

- What got completed in this session (one paragraph)
- What is in progress and where exactly to resume (file paths, function names, line numbers if relevant)
- Anything blocked or unclear, and what you'd ask B
- Verification status: which tests pass, which fail, which weren't run
- Time spent in this session, and approximate budget remaining

This is how the next session starts cleanly. Treat this as part of the work, not optional cleanup.

---

## 6. Mode transitions

The project lives in one of three modes, set by the **Mode flag** in §1. Each mode has different operating rules.

### `build` (current)
Standard rules apply. New code, new tests, new structure are all allowed within the current Step's scope. The full operating rules in §3 are in force.

### `demo_prep`
Triggered when B sets the mode flag to `demo_prep` AND a `DEMO_<YYYY-MM-DD>_PREP.md` file exists in the repo root with a date within 7 days. While in this mode:

- No new features. Bug fixes and verification only.
- No dependency changes of any kind.
- Every change must pass full verification before commit, no exceptions.
- Read the relevant `DEMO_<YYYY-MM-DD>_PREP.md` at session start in addition to the standard reads.
- If multiple `DEMO_*_PREP.md` files exist (multiple demos scheduled), the soonest one drives the rules — but any change must not break the others.

### `frozen`
Triggered when B sets the mode flag to `frozen`, typically within 24 hours of any demo. While in this mode:

- The repo is read-only except for explicit, surgical bug fixes B authorizes one by one.
- Any other request gets deferred to post-demo.
- After the demo, B sets the mode back to `build` (or `demo_prep` if another demo is imminent) and a `DEMO_<YYYY-MM-DD>_RETRO.md` is created.

### Transition discipline
Mode transitions happen by B editing the flag in §1. Claude Code does not change the mode autonomously. If Claude Code thinks a transition is needed (e.g., a demo is two days away and the mode is still `build`), it surfaces this in `OBSERVATIONS.md` and asks — it does not flip the flag itself.

---

## 7. When in doubt

Ask. Always cheaper than the cost of a wrong assumption that ships into the demo. The Step A handoff with explicit "Stopping. Awaiting 'go'" is the right pattern — keep doing that.
