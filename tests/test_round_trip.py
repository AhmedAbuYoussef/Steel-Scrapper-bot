"""Codified round-trip validation of OpenAPI -> Anthropic tool schema translation.

Permanent regression net for Appendix B done criterion #2 (and #3's
spot-check on optional vs required parameters). For each FastAPI route
listed in TOOLS, this asserts:

  (a) The translator's tool.description is byte-identical to the
      corresponding spec section 5 paragraph (extracted from
      scraper_bot_demo_spec_v1_2.md by line number, with the leading
      `> ` markdown blockquote prefix stripped).
  (b) Parameter types in input_schema.properties match the expected
      mapping for that tool.
  (c) Required parameters match the route signature exactly — no
      defaulted params end up in required[], no required params get
      dropped.

The tool registry below is the source of truth for what is in scope.
Add a row when a new tool lands. Failure of any check halts the suite.
"""

import hashlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chat import openapi_to_anthropic_tool  # noqa: E402
from main import app  # noqa: E402


SPEC_PATH = ROOT / "scraper_bot_demo_spec_v1_2.md"


_PROJECTS_FILTER_PROPS = {
    "governorate":  "string",
    "category":     "string",
    "eta_year_min": "integer",
    "eta_year_max": "integer",
    "cost_min_egp": "number",
    "cost_max_egp": "number",
}

TOOLS = [
    # (path, spec_line, props, required)
    # spec_line is 1-indexed; points to the "> ..." blockquote in spec section 5.
    ("/get_dataset",                  142, {"source": "string", "version": "string"}, ["source", "version"]),
    ("/get_cleaning_log",             145, {"source": "string"},                       ["source"]),
    ("/query_projects",               148, _PROJECTS_FILTER_PROPS,                     []),
    ("/estimate_steel_total",         151, _PROJECTS_FILTER_PROPS,                     []),
    ("/query_cbe_trend",              154, {"metric": "string", "period_start": "string", "period_end": "string"}, ["metric", "period_start", "period_end"]),
    ("/compare_cbe_periods",          157, {"metric": "string", "period_a":     "string", "period_b":   "string"}, ["metric", "period_a",     "period_b"]),
    ("/refresh_egy_map",              160, {}, []),
    ("/extract_latest_cbe_bulletin",  163, {}, []),
    ("/get_run_status",               166, {}, []),
]


def _spec_description(line_number: int) -> str:
    line = SPEC_PATH.read_text().splitlines()[line_number - 1]
    assert line.startswith("> "), f"spec line {line_number} is not a `> ...` blockquote"
    return line[2:]


@pytest.fixture(scope="module")
def openapi_doc():
    return TestClient(app).get("/openapi.json").json()


@pytest.mark.parametrize(
    "path,spec_line,expected_props,expected_required",
    TOOLS,
    ids=[t[0] for t in TOOLS],
)
def test_round_trip(openapi_doc, path, spec_line, expected_props, expected_required):
    tool = openapi_to_anthropic_tool(openapi_doc, path)

    spec_desc = _spec_description(spec_line)
    assert tool["description"] == spec_desc, (
        f"{path}: description does not match spec line {spec_line} byte-for-byte"
    )
    h_tool = hashlib.sha256(tool["description"].encode()).hexdigest()
    h_spec = hashlib.sha256(spec_desc.encode()).hexdigest()
    assert h_tool == h_spec, f"{path}: sha256 mismatch (tool={h_tool}, spec={h_spec})"

    props = tool["input_schema"]["properties"]
    actual_props = {k: v["type"] for k, v in props.items()}
    assert actual_props == expected_props, (
        f"{path}: properties mismatch (got {actual_props}, expected {expected_props})"
    )
    for name, schema in props.items():
        assert set(schema.keys()) == {"type"}, (
            f"{path}: property {name!r} has unexpected keys {set(schema.keys())}"
        )

    assert sorted(tool["input_schema"]["required"]) == sorted(expected_required), (
        f"{path}: required mismatch (got {tool['input_schema']['required']}, "
        f"expected {expected_required})"
    )
