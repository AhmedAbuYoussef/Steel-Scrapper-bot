# Scraper bot guardrails — integration guide

Five files for the `ezz-steel-scraper-step1` repo. Together with the existing `scraper_bot_demo_spec_v1_2.md`, `system_prompt.txt`, and `db.py`, they close the gaps that the cost engine bundle didn't have to worry about (session continuity, demo survival, formal verification, observation discipline).

## What's in this folder

| File | Status | Purpose |
|------|--------|---------|
| `CLAUDE.md` | Project-specific, ready to drop in | Read by Claude Code at every session start. Project identity, required reads, operating rules, forbidden behaviors, demo-proximity protocol. |
| `HANDOFF.md` | Pre-populated with Step A status | Session continuity. Already reflects the actual end-of-Step-A state from the Claude Code reply. |
| `VERIFICATION.md` | Pre-populated with Step A done-criteria | Golden tests. Step A tests (G-A1 through G-A7) currently passing; Step B test placeholders ready. |
| `DEMO_RUNBOOK.md` | Stack-specific, two fields to fill | Demo survival. Failure-mode cards specific to FastAPI + Streamlit + Anthropic + SQLite. Demo date and audience need to be filled. |
| `OBSERVATIONS.md` | Pre-populated with the 60-vs-12 deviation | Out-of-scope dump. Already records the cbe_metrics row-count issue you flagged in Step A. |

## What you do not need

Three of the nine generic templates I gave you earlier are redundant for this project because you already have equivalents:

- `PROJECT_BRIEF.md` and `RULEBOOK.md` → your `scraper_bot_demo_spec_v1_2.md` covers both
- `SYSTEM_PROMPT.md` → your `system_prompt.txt` is the canonical artifact
- `STATE.json` → your `db.py` + `scraperbot.db` is the canonical state

Don't duplicate them. The new `CLAUDE.md` points to the existing files as the sources of truth.

## Integration steps

### Step 1 — Drop the files into the repo

Place all five files at the root of `ezz-steel-scraper-step1`, alongside `scraper_bot_demo_spec_v1_2.md`. They do not replace anything — nothing in your existing repo gets deleted.

### Step 2 — Commit them

In the terminal, from the repo root:

```bash
git add CLAUDE.md HANDOFF.md VERIFICATION.md DEMO_RUNBOOK.md OBSERVATIONS.md
git commit -m "Add project guardrails (CLAUDE.md, HANDOFF, VERIFICATION, DEMO_RUNBOOK, OBSERVATIONS)"
git push
```

Don't `git add .` — stage by name, same discipline you used in Step A.

### Step 3 — Tell Claude Code about them

In your existing Claude Code session (the one paused awaiting "go" for Step B), paste this prompt:

> Five new files have been added to the repo: `CLAUDE.md`, `HANDOFF.md`, `VERIFICATION.md`, `DEMO_RUNBOOK.md`, `OBSERVATIONS.md`. Read all five carefully before doing anything else. From this point forward, follow `CLAUDE.md` §2 (required reads at session start), §3 (operating rules), §4 (forbidden behaviors), and §5 (session-end protocol) on every session. Do not start Step B yet — first confirm you have read the five new files, summarize what they require of you in five bullet points, and flag anything in them that contradicts the spec or your current understanding of the project state. Then stop and await my "go" for Step B.

This is one prompt. Claude Code will read the files, summarize, and pause — it will not start Step B until you say so explicitly.

### Step 4 — Mode flag stays at `build` for now

`CLAUDE.md` §1 has a **Mode flag** field set to `build`. That's correct — the project is not yet in demo-prep mode and won't be until validation passes on whatever scope you sign off as in-scope. There are no demo dates or audiences to fill in right now. When you eventually schedule a specific demo, you'll create a `DEMO_<YYYY-MM-DD>_PREP.md` file at the repo root from the template in `DEMO_RUNBOOK.md` §0, and flip the mode flag to `demo_prep`. Multiple demos to different audiences = multiple prep files. The runbook itself stays generic.

### Step 5 — Mirror to Claude.ai project files (optional but recommended)

If you have a Claude.ai project for this scraper bot, drop the same five files in its workspace. That way when you ask me a question about the project from inside it, I see the same files Claude Code is reading. Don't delete anything that's already in the project workspace — just add these alongside.

### Step 6 — Continue with Step B

Once Claude Code has confirmed it read the new files, give it the two things it's been waiting for: confirmation that `ANTHROPIC_API_KEY` is in the environment, and "go for Step B." From here on, it will follow the new operating rules.
