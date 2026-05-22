# Criterion #5 smoke — local run instructions (for B)

This runbook is for B running `tests/smoke_criterion_5.py` on a local
machine where `ANTHROPIC_API_KEY` is in the environment, since the
remote-execution container that built the harness has no
key-injection path (see HANDOFF session 6 + OBSERVATIONS 2026-05-21).

The smoke is the criterion #5 verification gate: it drives the four
spec §10 suggested-prompt buttons through `chat.agent_turn` end-to-end
and captures per-button transcripts.

---

## 0. Preconditions

- Local machine with `python3.11+` available.
- `ANTHROPIC_API_KEY` either exported in the shell, or in a `.env`
  file you create at step 2 (the codebase calls `load_dotenv()` at
  the top of `chat.py` and `main.py`).
- Network access to `https://api.anthropic.com` (the FastAPI side is
  local, but `agent_turn` calls Claude).
- Roughly 5 minutes of human time + however long the four Claude
  turns take (typically 30–90 s total).

---

## 1. Clone the canonical branch fresh

Use a fresh directory so nothing from a prior local clone leaks in.

```bash
cd /tmp                                    # or wherever you keep scratch clones
rm -rf ezz-steel-scraper-step1-smoke       # in case a prior run left one
git clone --branch claude/ezz-steel-scraper-step1-yQejR \
          --single-branch \
          <REPO_URL_HERE> ezz-steel-scraper-step1-smoke
cd ezz-steel-scraper-step1-smoke
```

Expected: `git log --oneline -1` shows commit `4b30702` or later
(top of branch at the time of this runbook). If it's older,
something cached the clone — delete the directory and retry.

**Rollback if step fails:** `rm -rf /tmp/ezz-steel-scraper-step1-smoke`,
investigate clone error.

---

## 2. Python venv from requirements.txt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Expected: 9 packages installed (fastapi, uvicorn[standard], streamlit,
anthropic, requests, pydantic, httpx, python-dotenv, pytest). No
errors. Approximate size: ~300 MB in `.venv/`.

Drop the key in a `.env` if you haven't already exported it:

```bash
cp .env.example .env
# Then open .env in an editor and fill in ANTHROPIC_API_KEY=sk-ant-...
```

**Rollback:** `deactivate; rm -rf .venv`, investigate pip error.

---

## 3. Regenerate scraperbot.db

```bash
rm -f scraperbot.db
python db.py
```

Expected output (verbatim, modulo whitespace):

```
DB: <absolute_path>/scraperbot.db
Tables (9): cbe_metrics, cbe_raw_extractions, cleaning_log, conversations, projects_clean, projects_clean_currency_only, projects_raw, runs, steel_ratios

table                                 rows
--------------------------------------------
cbe_metrics                             60
cbe_raw_extractions                      5
cleaning_log                             8
conversations                            3
projects_clean                           5
projects_clean_currency_only             5
projects_raw                             5
runs                                     5
steel_ratios                            10
```

If row counts differ on any line, **stop** and surface — that's
either a db.py drift or a fixture corruption. Compare `db.py` sha256:

```bash
sha256sum db.py
# Expected: b0574b04060533861a39bf436977f179658fe86b65ffb4aa7d95792494884fa1
```

**Rollback:** `rm -f scraperbot.db`, re-pull, retry.

---

## 4. Launch uvicorn in background

```bash
PORT=8000
nohup python -m uvicorn main:app --host 127.0.0.1 --port "$PORT" \
     --log-level warning >/tmp/uvicorn-smoke.log 2>&1 &
UVICORN_PID=$!
echo "uvicorn PID=$UVICORN_PID port=$PORT"

# Wait up to 15s for it to come up
for i in $(seq 1 60); do
    curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null && break
    sleep 0.25
done
```

Expected: `uvicorn PID=<n> port=8000` printed, no errors in
`/tmp/uvicorn-smoke.log`, the curl loop exits cleanly (the next
verification step will fail loudly if uvicorn didn't actually come up).

**Rollback if step fails:** `kill $UVICORN_PID 2>/dev/null; cat /tmp/uvicorn-smoke.log`.
Common cause: port 8000 already in use. Set `PORT=8765` (or any free
port) and retry.

---

## 5. Verify /openapi.json and /system_prompt

```bash
# /openapi.json should expose exactly 9 paths (the 9 §5 tools).
# /system_prompt should NOT appear (include_in_schema=False).
PATHS_COUNT=$(curl -s "http://127.0.0.1:$PORT/openapi.json" \
    | python -c "import json,sys; d=json.load(sys.stdin); print(len(d['paths']))")
echo "openapi paths: $PATHS_COUNT (expected: 9)"
[ "$PATHS_COUNT" = "9" ] || { echo "FAIL: openapi path count wrong"; kill $UVICORN_PID; exit 1; }

curl -s "http://127.0.0.1:$PORT/openapi.json" \
    | python -c "import json,sys; d=json.load(sys.stdin); assert '/system_prompt' not in d['paths'], 'system_prompt leaked into openapi'; print('system_prompt off the schema: OK')"

# /system_prompt body must be byte-identical to system_prompt.txt.
EXPECTED_SHA=7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01
RESP_SHA=$(curl -s "http://127.0.0.1:$PORT/system_prompt" | sha256sum | awk '{print $1}')
FILE_SHA=$(sha256sum system_prompt.txt | awk '{print $1}')
echo "expected sha: $EXPECTED_SHA"
echo "/system_prompt sha: $RESP_SHA"
echo "system_prompt.txt sha: $FILE_SHA"
[ "$RESP_SHA" = "$EXPECTED_SHA" ] && [ "$FILE_SHA" = "$EXPECTED_SHA" ] \
    || { echo "FAIL: system_prompt sha drift"; kill $UVICORN_PID; exit 1; }
echo "verify step: PASS"
```

**Expected stable sha256 (system_prompt.txt and /system_prompt body):**
`7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01`
(6218 bytes)

If either sha differs from expected: **stop**, tear down uvicorn, and
surface — `system_prompt.txt` was supposed to be byte-identical to
spec Appendix A and that's a CLAUDE.md §4 forbidden drift if it
moved.

**Rollback:** `kill $UVICORN_PID`, investigate `git diff system_prompt.txt`.

---

## 6. Run the smoke harness

```bash
python tests/smoke_criterion_5.py
SMOKE_EXIT=$?
echo "smoke exit code: $SMOKE_EXIT  (0=all PASS, 1=any FAIL, 2=db missing)"
```

The harness:
- Spawns its own uvicorn on a different free port (so you can leave
  the one from step 4 running for inspection if you like, or skip
  step 4 entirely if you trust the harness to manage uvicorn).
- Drives `chat.agent_turn(prompt, history=[], tools, system_prompt, base)`
  once per §10 button (4 buttons, verbatim prompt strings).
- Writes a transcript file `smoke_criterion_5_<YYYYMMDDTHHMMSSZ>.md`
  to repo root. **Already gitignored**, so it won't accidentally
  get committed.

Look at the transcript:
```bash
ls -la smoke_criterion_5_*.md
TRANSCRIPT=$(ls -t smoke_criterion_5_*.md | head -1)
echo "Transcript file: $TRANSCRIPT"
head -30 "$TRANSCRIPT"
```

**Rollback / debugging if smoke fails:**
- Exit code 2 → `scraperbot.db` missing; re-run step 3.
- Exit code 1 → at least one button FAILed. Open the transcript;
  the failing button's "Error:" line + stack trace tell you which
  layer broke. Common causes: ANTHROPIC_API_KEY invalid (401 from
  Anthropic), tool-routing produced a bad request (400 from one of
  the FastAPI routes), iteration cap hit (max_iters=10 in
  `chat.agent_turn`).
- Process management: `pkill -f "uvicorn main:app"` if any stray
  uvicorn was left behind.

---

## 7. Tear down uvicorn (the one from step 4)

The smoke harness manages its own uvicorn subprocess and cleans up
on exit. The one you started in step 4 is independent.

```bash
kill $UVICORN_PID
wait $UVICORN_PID 2>/dev/null
echo "uvicorn $UVICORN_PID terminated"
```

If `kill` returned non-zero (process already gone), no action.
Belt-and-braces:

```bash
pkill -f "uvicorn main:app --host 127.0.0.1 --port $PORT" 2>/dev/null
```

---

## 8. Commit the transcript (only if smoke PASSed 4/4)

The transcript file is gitignored by default. To capture this run as
an artifact on the canonical branch, force-add and commit with the
template below. If the smoke had any FAILs, do not commit — surface
the failure to me (in chat) instead, and we triage before recording
the run.

```bash
git add -f smoke_criterion_5_<YYYYMMDDTHHMMSSZ>.md   # replace with actual filename
git commit -m "$(cat <<'EOF'
criterion #5 smoke: 4/4 §10 buttons PASS — transcript captured

Live run of tests/smoke_criterion_5.py against fresh db.py + uvicorn
on a local machine (B's, since the remote-execution container has no
Anthropic API key path). All four §10 suggested-prompt buttons
returned a non-error response.

Per-button: see transcript file for tool sequence + arguments + first
500 chars of final response + iteration count + duration.

Smoke harness: tests/smoke_criterion_5.py (4b30702).
DB seed sha: <sha256sum scraperbot.db output>
system_prompt.txt sha: 7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01
EOF
)"
git push origin claude/ezz-steel-scraper-step1-yQejR
```

**Rollback if commit was a mistake:**
- Not pushed yet: `git reset --soft HEAD~1; git rm --cached smoke_criterion_5_*.md`
- Already pushed: `git revert <sha>` and push the revert.

---

## 9. Hash & artifact expectations summary

| Artifact | Expected sha256 | Size |
|----------|----------------|------|
| `system_prompt.txt` | `7bbf9e06181160bf9907c1d1f6f535ee6bd2265e1590d0c9f654cb0f56b07d01` | 6218 bytes |
| `GET /system_prompt` response body | (same as above) | 6218 bytes |
| `db.py` | `b0574b04060533861a39bf436977f179658fe86b65ffb4aa7d95792494884fa1` | (current) |

| Artifact | Expected count |
|----------|---------------|
| `/openapi.json` `paths` keys | 9 |
| `/system_prompt` in `/openapi.json` | absent |
| `scraperbot.db` tables | 9 |
| `cbe_metrics` rows | 60 |
| `projects_clean` rows | 5 |
| `cleaning_log` rows | 8 |
| `runs` rows (post-db.py, pre-smoke) | 5 |
| §10 buttons smoke-tested | 4 |
| Smoke harness exit code (all PASS) | 0 |

If any hash or count differs from expected, **stop and surface**
before committing anything — divergence here means either a drift
event in canonical state or something wrong with this runbook.

---

## 10. Total time budget

- Steps 1–5 (clone + venv + DB + uvicorn + verify): ~2–3 minutes.
- Step 6 (smoke): 30 s – 2 min depending on Claude latency.
- Step 7 (teardown): seconds.
- Step 8 (commit + push): ~30 s.

Budget about 5 minutes including buffer. If it takes more than 15,
something structural is wrong — stop and tell me what you saw.
