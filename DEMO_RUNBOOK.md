# DEMO_RUNBOOK.md — Demo survival template

**This file is a reusable template, not a one-shot.** The scraper bot is expected to be demoed multiple times to different audiences across different physical locations. For each scheduled demo, B copies §0 below into a new file at the repo root named `DEMO_<YYYY-MM-DD>_PREP.md`, fills in the specifics for that instance, and uses it for the pre-flight, T-7, T-3, T-1, T-0 checklists. The runbook itself stays generic.

Demo dates are gated on validation passing, not set in advance. See `CLAUDE.md` §1 (project completion gate).

---

## 0. Per-instance pre-flight metadata (template — copy to a new `DEMO_<DATE>_PREP.md` file per demo)

```
Demo date/time:        YYYY-MM-DD HH:MM Egypt time
Demo location:         <physical room, building, or virtual platform>
Audience:              <names and companies/roles — knowing this changes the script>
Demo duration:         <minutes — set after validation tells us what fits>
B's role:              <presenter / driver / both>
Backup driver:         <name or "none">
Validation status:     <which scope passed validation, on what commit, what's in/out for this audience>
Mode flag in CLAUDE.md: demo_prep
```

Once the values are written into a `DEMO_<DATE>_PREP.md` file, set the **Mode flag** in `CLAUDE.md` §1 to `demo_prep` to engage the operating-rule changes in `CLAUDE.md` §6.

---

## 1. The demo script

In sequence, what gets shown. The five locked prompts in spec §11 are the spine. Each step has: what B says, what B does, what should appear on screen, what could go wrong.

### Step 1 — Open the system, show the landing
- **B says:** Brief framing of what the bot does and what data it sees.
- **B does:** Launch the Streamlit UI from a terminal that's already cd'd into the repo and has the venv active.
- **Expected screen:** Streamlit landing page with the bot's intro and the prompt input.
- **Failure mode:** If Streamlit doesn't launch within 5 seconds, switch to a pre-recorded screen capture; do not debug live.
- **Time budget:** 30 seconds.

### Step 2 — Run prompt 1 (per spec §11)
- **B says:** What the prompt is asking and why this matters for EZZ Steel/CBE.
- **B does:** Paste prompt 1 from the spec into the input.
- **Expected screen:** Bot's response with citations to specific rows in `projects_clean` or `cleaning_log` as applicable.
- **Failure mode:** Anthropic API timeout — see Card 1. Wrong answer — see Card 2.
- **Time budget:** 60 seconds.

### Steps 3–6 — Run prompts 2 through 5
Same pattern. Prompt 5 specifically requires the 60 seeded rows in `cbe_metrics` to produce a 12-month trend. If that's been truncated to 12 rows, prompt 5 will fail — verify before demo.

### Closing
- **B says:** Summary of what the bot just demonstrated and what's coming in subsequent phases.
- **Time budget:** 60 seconds.

### Steps that should NEVER be in this demo:
- A live Anthropic API call without a pre-recorded fallback for each of the five prompts
- Any prompt that isn't one of the five locked prompts in §11 (the bot will fail to handle it gracefully unless explicitly tested)
- A piece of UI you finished writing in the last 24 hours
- Anything where you say "and now let me just quickly..."

---

## 2. T-7: One week out

- [ ] Full verification suite passes (every test in `VERIFICATION.md` §2 and §3, plus all canaries in §5)
- [ ] All five spec §11 prompts run end-to-end successfully against the live bot
- [ ] Demo script run end-to-end at least once, timed
- [ ] Demo script run end-to-end with one witness present
- [ ] Every "failure mode" entry below has an actual recovery, not aspirational
- [ ] Code freeze planned for T-3
- [ ] Pre-recorded screen captures of all five prompt responses (for fallback)
- [ ] Demo machine identified — same machine that will be used live
- [ ] Backup machine identified, repo cloned, dependencies installed, smoke test passes
- [ ] `ANTHROPIC_API_KEY` confirmed valid and in environment on both machines

---

## 3. T-3: Three days out

- [ ] No new features merged — confirm via `git log --since "3 days ago"`
- [ ] Demo script run end-to-end, timed, logged (date, time, duration, any anomalies)
- [ ] All canary tests in `VERIFICATION.md` §5 pass — no fabrications, no silent failures
- [ ] Demo machine: full restart, then full demo run from cold start
- [ ] Network plan confirmed (Wi-Fi, hotspot backup)
- [ ] Audience list confirmed; any pre-reads sent

---

## 4. T-1: Day before

- [ ] Code freeze: nothing merges. CLAUDE.md §6 in force.
- [ ] Final verification run, full result captured to `HANDOFF.md`
- [ ] Demo script run end-to-end in the actual room/setup that will be used
- [ ] All cables, adapters, dongles in the bag
- [ ] Phone charged, laptop charged, backup battery if applicable
- [ ] One person (other than B) knows where the laptop and the bag are
- [ ] B sleeps. No more code.

---

## 5. T-0: Day of

### Two hours before
- [ ] Cold start: power off laptop, power on, run the full demo end-to-end one final time
- [ ] Close every browser tab not needed for the demo
- [ ] Disable notifications (Slack, email, system, calendar pop-ups)
- [ ] Set Do Not Disturb / Focus mode
- [ ] Check battery, network, projector cable
- [ ] `ANTHROPIC_API_KEY` confirmed in environment one final time

### Thirty minutes before
- [ ] Open Streamlit to its starting state. Leave it there. Do not "test it again."
- [ ] Pre-recorded fallbacks open in a second browser tab, ready to swap to
- [ ] Water and a working pen
- [ ] Phone on silent, in pocket — not on the table next to the laptop

### Two minutes before
- Breathe. The work is done. The work doesn't change in the next two minutes.

---

## 6. During the demo: failure mode cards

Each card is designed to be readable in three seconds while a room of people watches. **Print these and put them next to the laptop.**

### Card 1 — Anthropic API timeout / 5xx error
- **Symptom:** Streamlit hangs or shows an error after submitting a prompt
- **Don't:** retry, debug, or apologize at length
- **Do:** "Let me show you what this looks like with the cached version" → switch to pre-recorded fallback for that prompt
- **Then:** narrate the result as if it had run live

### Card 2 — Wrong number / clearly bad output
- **Symptom:** the bot returns something that's obviously wrong
- **Don't:** apologize, deflect, or try to correct it live
- **Do:** "That's not the verified output — let me show you the verified version" → switch to fallback
- **Then:** make a private note. Do not debug live. Move on.

### Card 3 — Audience asks something outside the five prompts
- **Symptom:** "Can it also do X?" where X isn't in spec §11
- **Don't:** improvise — the bot wasn't designed for X
- **Do:** "This demo covers five locked use cases. X is exactly the kind of expansion that comes in the next phase. Let me note it." → write it visibly. Move on.

### Card 4 — Network fails
- **Symptom:** no Wi-Fi, hotspot fails, or API unreachable
- **Don't:** keep retrying
- **Do:** flip to pre-recorded mode. Narrate what would have happened.
- **Then:** "I'll show you the live version after the session if you'd like."

### Card 5 — Hostile question / "this won't scale" / "this isn't real production"
- **Don't:** defend the demo as if it's production
- **Do:** "You're right that this version doesn't handle X. The next phase covers it — here's the plan." Stay specific. Stay short.

### Card 6 — Hardware fails (laptop crashes, projector cuts, cable dies)
- **Don't:** lose the room
- **Do:** "Let me switch to the backup" — do it without commentary, keep talking through what they would have seen
- **Then:** if the backup also fails: switch to a pure narration mode. Describe what the demo would have shown.

### Card 7 — Streamlit hangs or crashes
- **Symptom:** UI frozen, can't submit prompts
- **Don't:** keep clicking
- **Do:** "Let me restart this — give me 15 seconds" → quit and relaunch from terminal. If it doesn't come back in 15s, switch to fallbacks.
- **Then:** finish the demo on fallbacks. Investigate after.

### Card 8 — You forget what comes next
- **Don't:** show it
- **Do:** "Let me skip to the part that matters most for this audience" → jump to the prompt most relevant to their domain
- **Then:** finish that step, return to the rest if time allows

---

## 7. Post-demo capture (within 24 hours)

Save as `DEMO_<YYYY-MM-DD>_RETRO.md`. The retros accumulate. Reading the last three before the next demo prep is the most underrated practice.

- [ ] What worked
- [ ] What broke or almost broke
- [ ] Audience reactions and what surprised B
- [ ] Questions that didn't have good answers — these go into the next phase brief as scope
- [ ] Recovery cards that got used — were they good enough? edit them
- [ ] Anything in the system that needs immediate fixing (not for this audience, for the next one)

---

## 8. The single most important thing

A demo with four prompts that reliably runs end-to-end will land better than a demo with five prompts where the fifth breaks in front of the audience. **Cut features before the demo, not during it.** Anything you're not 95% sure of by T-3 — cut it. The demo is not the place to test things.

For this specific project: prompt 5 (the 12-month trend) depends on the 60 rows in `cbe_metrics` surviving B's sign-off. If B truncates to 12 rows before T-3, prompt 5 must be cut from the demo or rebuilt. Decide early.
