"""Criterion #5 smoke harness — drives the four §10 suggested-prompt buttons
end-to-end against a freshly-built DB and a locally-spawned uvicorn.

NOT a pytest target. Run directly:

    python tests/smoke_criterion_5.py

Outputs a single transcript artifact at the repo root named
`smoke_criterion_5_<ISO_UTC>.md`. Per-button report contains:

  - tool-call sequence (tool name + arguments, in order)
  - full final response text
  - iteration count (number of assistant turns in agent_turn's loop)
  - duration in seconds
  - PASS / FAIL on "non-error response"

Requirements:
  - `python db.py` already run (or scraperbot.db already at the canonical
    seed state). Per OBSERVATIONS 2026-05-08, the harness does NOT
    regenerate the DB — that's the caller's responsibility, so this script
    can also be re-run quickly without flushing other test artifacts.
  - `ANTHROPIC_API_KEY` (or platform-provided equivalent) in the
    environment — `agent_turn` hits Claude via the Anthropic SDK.

Exit code: 0 if all 4 buttons PASS, 1 otherwise. Cleans up uvicorn on exit
in both success and failure paths.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# Spec §10 verbatim — the four suggested-prompt button labels. These are
# the strings the Streamlit UI submits on click; the harness drives the
# same strings so the smoke matches user-visible behavior.
BUTTONS = [
    "Show me the scraped egy-map data",
    "What infrastructure projects in Port Said involve steel?",
    "Construction sector lending rate trend, last 12 months",
    "Compare industrial production this quarter vs last year",
]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_uvicorn(base: str, proc: subprocess.Popen, timeout: float = 20.0) -> None:
    import requests
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out = (proc.stdout.read() or b"").decode("utf-8", "replace")
            raise RuntimeError(
                f"uvicorn exited early with code {proc.returncode}:\n{out}"
            )
        try:
            r = requests.get(f"{base}/openapi.json", timeout=2)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError(f"uvicorn at {base} did not become ready within {timeout}s")


def _drive_one(prompt: str, tools, system_prompt: str, base: str) -> dict:
    from chat import agent_turn
    t0 = time.monotonic()
    try:
        text, messages, tool_calls = agent_turn(
            prompt,
            history=[],
            tools=tools,
            system_prompt=system_prompt,
            base=base,
        )
        iter_count = sum(1 for m in messages if m.get("role") == "assistant")
        return {
            "prompt": prompt,
            "ok": True,
            "iter_count": iter_count,
            "duration_s": round(time.monotonic() - t0, 2),
            "tool_calls": tool_calls,
            "final_text": text or "",
            "error": None,
        }
    except Exception as e:
        return {
            "prompt": prompt,
            "ok": False,
            "iter_count": None,
            "duration_s": round(time.monotonic() - t0, 2),
            "tool_calls": [],
            "final_text": "",
            "error": f"{type(e).__name__}: {e}",
        }


def _format_artifact(
    results: list[dict],
    base: str,
    t_start: datetime,
    t_end: datetime,
    db_mtime_iso: str,
) -> str:
    passes = sum(1 for r in results if r["ok"])
    fails = len(results) - passes
    out: list[str] = []
    out.append("# Criterion #5 smoke transcript — 4 §10 suggested-prompt buttons")
    out.append("")
    out.append(f"- **Started (UTC):** `{t_start.isoformat()}`")
    out.append(f"- **Finished (UTC):** `{t_end.isoformat()}`")
    out.append(f"- **Total wall time:** {(t_end - t_start).total_seconds():.2f} s")
    out.append(f"- **API base:** `{base}`")
    out.append(f"- **DB mtime (UTC):** `{db_mtime_iso}`")
    out.append(f"- **Buttons exercised:** {len(results)}")
    out.append(f"- **Result:** **{passes} PASS / {fails} FAIL**")
    out.append("")
    out.append("---")
    out.append("")
    for i, r in enumerate(results, 1):
        out.append(f"## Button {i} — \"{r['prompt']}\"")
        out.append("")
        out.append(f"- **Status:** **{'PASS' if r['ok'] else 'FAIL'}**")
        out.append(f"- **Iterations (assistant turns):** {r['iter_count']}")
        out.append(f"- **Duration:** {r['duration_s']} s")
        if r["error"]:
            out.append(f"- **Error:** `{r['error']}`")
        out.append(f"- **Tool calls ({len(r['tool_calls'])}):**")
        if r["tool_calls"]:
            for j, tc in enumerate(r["tool_calls"], 1):
                out.append(f"  {j}. `{tc['name']}({tc['input']})`")
        else:
            out.append("  _(none)_")
        out.append("")
        out.append("**Final response (full):**")
        out.append("")
        out.append("```")
        out.append(r["final_text"])
        out.append("```")
        out.append("")
        out.append("---")
        out.append("")
    return "\n".join(out)


def main() -> int:
    if not (ROOT / "scraperbot.db").exists():
        print("ERROR: scraperbot.db not found. Run `python db.py` first.", file=sys.stderr)
        return 2

    port = _free_port()
    base = f"http://127.0.0.1:{port}"

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--log-level", "warning",
        ],
        cwd=str(ROOT),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_uvicorn(base, proc)

        from chat import fetch_system_prompt, fetch_tools
        system_prompt = fetch_system_prompt(base=base)
        tools = fetch_tools(base=base)

        db_mtime = datetime.fromtimestamp(
            (ROOT / "scraperbot.db").stat().st_mtime, tz=timezone.utc,
        ).isoformat()

        t_start = datetime.now(timezone.utc)
        results = [_drive_one(p, tools, system_prompt, base) for p in BUTTONS]
        t_end = datetime.now(timezone.utc)

        artifact = _format_artifact(results, base, t_start, t_end, db_mtime)
        iso = t_start.strftime("%Y%m%dT%H%M%SZ")
        out_path = ROOT / f"smoke_criterion_5_{iso}.md"
        out_path.write_text(artifact, encoding="utf-8")

        print(artifact)
        print()
        print(f"Wrote: {out_path}")

        passes = sum(1 for r in results if r["ok"])
        return 0 if passes == len(results) else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
