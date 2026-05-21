from dotenv import load_dotenv
load_dotenv()

import os
import time

import requests
from anthropic import Anthropic


API_BASE = os.environ.get("SCRAPER_BOT_API_BASE", "http://127.0.0.1:8000")
DB_PATH = os.environ.get("SQLITE_PATH", "scraperbot.db")


def _param_type(schema):
    if "type" in schema:
        return schema["type"]
    for branch in schema.get("anyOf", []):
        if branch.get("type") != "null":
            return branch["type"]
    raise ValueError(f"cannot extract scalar type from schema: {schema!r}")


def openapi_to_anthropic_tool(openapi_doc, path, method="get"):
    operation = openapi_doc["paths"][path][method]
    properties = {}
    required = []
    for param in operation.get("parameters", []):
        if param.get("in") != "query":
            continue
        name = param["name"]
        properties[name] = {"type": _param_type(param["schema"])}
        if param.get("required", False):
            required.append(name)
    return {
        "name": path.lstrip("/"),
        "description": operation["description"],
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def fetch_system_prompt(base=None, timeout=10):
    base = base or API_BASE
    r = requests.get(f"{base}/system_prompt", timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_tools(base=None, timeout=10):
    base = base or API_BASE
    r = requests.get(f"{base}/openapi.json", timeout=timeout)
    r.raise_for_status()
    doc = r.json()
    return [openapi_to_anthropic_tool(doc, p) for p in doc["paths"].keys()]


def data_frozen_timestamp(path=None):
    # mtime of db.py — the seed-script source. Chosen over runs.finished_at
    # because that table mutates on every refresh-stub call (see
    # OBSERVATIONS 2026-05-08 runs-table side effect note); also chosen
    # over scraperbot.db mtime because db.py is the canonical source.
    path = path or os.path.join(os.path.dirname(__file__) or ".", "db.py")
    mtime = os.path.getmtime(path)
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(mtime))


def route_once(user_message, tools, system_prompt, model="claude-haiku-4-5-20251001", max_tokens=1024):
    client = Anthropic()
    return client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        tools=tools,
        messages=[{"role": "user", "content": user_message}],
    )


def _serialize_blocks(content):
    out = []
    for block in content:
        if block.type == "text":
            out.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            out.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
    return out


def _execute_tool(name, args, base, timeout=30):
    try:
        r = requests.get(f"{base}/{name}", params=args, timeout=timeout)
    except Exception as e:
        return f"HTTP request failed: {e}", True
    if r.status_code >= 400:
        return f"HTTP {r.status_code}: {r.text}", True
    return r.text, False


def agent_turn(
    user_message,
    history,
    tools,
    system_prompt,
    base=None,
    model="claude-haiku-4-5-20251001",
    max_tokens=2048,
    max_iters=10,
):
    """Run a Claude+tool dispatch loop until stop_reason != 'tool_use'.

    history is a list of message dicts in Anthropic format. Returns
    (final_text, updated_history, tool_calls_log)."""
    base = base or API_BASE
    client = Anthropic()
    messages = list(history) + [{"role": "user", "content": user_message}]
    tool_calls_log = []

    for _ in range(max_iters):
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": _serialize_blocks(resp.content)})

        if resp.stop_reason != "tool_use":
            final_text = "\n".join(b.text for b in resp.content if b.type == "text").strip()
            return final_text, messages, tool_calls_log

        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            tool_calls_log.append({"name": block.name, "input": dict(block.input)})
            content, is_error = _execute_tool(block.name, block.input, base)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
                "is_error": is_error,
            })
        messages.append({"role": "user", "content": tool_results})

    return (
        "[agent stopped: exceeded max_iters tool-use rounds without final text]",
        messages,
        tool_calls_log,
    )


# Streamlit UI — only runs under `streamlit run chat.py`. Guarded so pytest
# (which does `from chat import openapi_to_anthropic_tool`) doesn't trigger
# UI side effects.
if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(page_title="EZZ Steel Scraper Bot")
    st.title("EZZ Steel Scraper Bot")
    st.caption("Egyptian state projects + CBE monthly metrics.")

    if "history" not in st.session_state:
        try:
            st.session_state.system_prompt = fetch_system_prompt()
            st.session_state.tools = fetch_tools()
        except Exception as e:
            st.error(
                f"Failed to load system prompt or tools from FastAPI at {API_BASE}.\n\n"
                f"Is uvicorn running?  ({type(e).__name__}: {e})"
            )
            st.stop()
        st.session_state.frozen = data_frozen_timestamp()
        st.session_state.history = []
        st.session_state.transcript = []

    frozen = st.session_state.frozen
    welcome = (
        "I'm the EZZ Steel Scraper Bot. I cover 138 Egyptian state projects "
        "(from egy-map) and 12 months of selected CBE metrics. "
        f"Data was last refreshed {frozen}. "
        "Try one of the suggestions below or ask anything in scope."
    )
    st.info(welcome)

    SUGGESTIONS = [
        "Show me the scraped egy-map data",
        "What infrastructure projects in Port Said involve steel?",
        "Construction sector lending rate trend, last 12 months",
        "Compare industrial production this quarter vs last year",
    ]

    submitted_prompt = None
    cols = st.columns(2)
    for i, prompt in enumerate(SUGGESTIONS):
        if cols[i % 2].button(prompt, key=f"sugg_{i}", use_container_width=True):
            submitted_prompt = prompt

    if st.button("Reset conversation", key="reset"):
        st.session_state.history = []
        st.session_state.transcript = []
        st.rerun()

    for entry in st.session_state.transcript:
        role = entry["role"]
        with st.chat_message(role):
            if entry.get("tool_calls"):
                with st.expander(f"Tools called ({len(entry['tool_calls'])})"):
                    for tc in entry["tool_calls"]:
                        st.code(f"{tc['name']}({tc['input']})", language="python")
            st.markdown(entry["text"])

    typed = st.chat_input("Ask about projects, CBE metrics, or steel.")
    user_input = typed or submitted_prompt

    if user_input:
        st.session_state.transcript.append({"role": "user", "text": user_input, "tool_calls": []})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    text, history, tcs = agent_turn(
                        user_input,
                        st.session_state.history,
                        st.session_state.tools,
                        st.session_state.system_prompt,
                    )
                except Exception as e:
                    st.error(f"Agent turn failed: {type(e).__name__}: {e}")
                    text, history, tcs = (None, st.session_state.history, [])

            if text is not None:
                if tcs:
                    with st.expander(f"Tools called ({len(tcs)})"):
                        for tc in tcs:
                            st.code(f"{tc['name']}({tc['input']})", language="python")
                st.markdown(text)
                st.session_state.history = history
                st.session_state.transcript.append({"role": "assistant", "text": text, "tool_calls": tcs})

    st.divider()
    st.caption(f"Data frozen {frozen}. For live refresh, ask explicitly.")
