"""Appendix B done criterion #4 — HTTP test script for all nine §5 tools.

Calls each FastAPI tool over real HTTP against a live uvicorn (not via
TestClient) and asserts a sensible response shape. The pytest in
tests/test_round_trip.py covers OpenAPI -> Anthropic translation
correctness; this script covers the live-HTTP path end-to-end.

Run sequence:
    (a) python db.py                          # rebuild scraperbot.db from spec §4/§6 seed
    (b) uvicorn main:app                      # in another terminal (defaults to 127.0.0.1:8000)
    (c) python scripts/test_endpoints.py      # this script

Exits 0 if every endpoint passes; exits 1 with a per-endpoint PASS/FAIL
table if any fails. Designed to be run after `db.py` rebuilds the DB —
`/refresh_egy_map` and `/extract_latest_cbe_bulletin` write to `runs`,
so running this script changes the `runs` row count (see OBSERVATIONS
2026-05-08 on the runs-table side effect).
"""

import sys
from typing import Any, Callable

import httpx


BASE_URL = "http://127.0.0.1:8000"


def _is_nonempty_list(body: Any) -> bool:
    return isinstance(body, list) and len(body) > 0


def _is_list_of_len(n: int) -> Callable[[Any], bool]:
    return lambda body: isinstance(body, list) and len(body) == n


def _dict_with_keys(*keys: str) -> Callable[[Any], bool]:
    needed = set(keys)
    return lambda body: isinstance(body, dict) and needed.issubset(body.keys())


def _summary(body: Any) -> str:
    if isinstance(body, list):
        return f"list, rows={len(body)}"
    if isinstance(body, dict):
        return f"dict, keys={sorted(body.keys())}"
    return f"scalar={body!r}"


# Each case: (label, method, path, params, expected_status, shape_predicate)
# shape_predicate runs on the JSON body when status matches expected_status.
CASES = [
    ("get_dataset egy_map raw",         "GET", "/get_dataset",                  {"source": "egy_map", "version": "raw"},          200, _is_list_of_len(5)),
    ("get_dataset egy_map clean",       "GET", "/get_dataset",                  {"source": "egy_map", "version": "clean"},        200, _is_list_of_len(5)),
    ("get_dataset egy_map currency",    "GET", "/get_dataset",                  {"source": "egy_map", "version": "currency_only"},200, _is_list_of_len(5)),
    ("get_dataset cbe raw",             "GET", "/get_dataset",                  {"source": "cbe",     "version": "raw"},          200, _is_list_of_len(5)),
    ("get_dataset cbe clean",           "GET", "/get_dataset",                  {"source": "cbe",     "version": "clean"},        200, _is_list_of_len(60)),
    ("get_dataset cbe currency (400)",  "GET", "/get_dataset",                  {"source": "cbe",     "version": "currency_only"},400, lambda b: "detail" in b and "currency_only" in b["detail"]),
    ("get_cleaning_log egy_map",        "GET", "/get_cleaning_log",             {"source": "egy_map"},                            200, _is_list_of_len(8)),
    ("query_projects no filter",        "GET", "/query_projects",               {},                                               200, _is_list_of_len(5)),
    ("query_projects Port Said",        "GET", "/query_projects",               {"governorate": "Port Said"},                     200, _is_list_of_len(1)),
    ("estimate_steel_total no filter",  "GET", "/estimate_steel_total",         {},                                               200, _dict_with_keys("total_tons_typical", "total_tons_low", "total_tons_high", "insufficient_data_count", "top_contributors")),
    ("estimate_steel_total energy",     "GET", "/estimate_steel_total",         {"category": "energy"},                           200, _dict_with_keys("total_tons_typical", "top_contributors")),
    ("query_cbe_trend usd_egp_rate",    "GET", "/query_cbe_trend",              {"metric": "usd_egp_rate", "period_start": "2025-04", "period_end": "2026-03"}, 200, _is_list_of_len(12)),
    ("compare_cbe_periods usd_egp",     "GET", "/compare_cbe_periods",          {"metric": "usd_egp_rate", "period_a": "2025-04", "period_b": "2026-03"},      200, _dict_with_keys("metric", "period_a", "period_b", "absolute_difference", "percent_change")),
    ("refresh_egy_map (stub)",          "GET", "/refresh_egy_map",              {},                                               200, _dict_with_keys("run_id", "component", "status")),
    ("extract_latest_cbe_bulletin",     "GET", "/extract_latest_cbe_bulletin",  {},                                               200, _dict_with_keys("run_id", "component", "status")),
    ("get_run_status",                  "GET", "/get_run_status",               {},                                               200, _is_nonempty_list),
]


def main() -> int:
    print(f"Hitting {BASE_URL}")
    print("=" * 90)
    fails: list[tuple[str, str]] = []
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        for label, method, path, params, expected_status, shape_ok in CASES:
            try:
                resp = client.request(method, path, params=params)
                got_status = resp.status_code
                body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            except Exception as e:
                print(f"  FAIL  {label:38s}  EXCEPTION: {type(e).__name__}: {e}")
                fails.append((label, f"exception {type(e).__name__}"))
                continue
            status_ok = got_status == expected_status
            shape_pass = False
            try:
                shape_pass = bool(shape_ok(body)) if status_ok else False
            except Exception as e:
                shape_pass = False
            verdict = "PASS" if (status_ok and shape_pass) else "FAIL"
            print(f"  {verdict}  {label:38s}  HTTP {got_status}  {_summary(body)}")
            if verdict == "FAIL":
                reason = (
                    f"expected status {expected_status} got {got_status}"
                    if not status_ok
                    else "shape predicate failed"
                )
                fails.append((label, reason))
    print("=" * 90)
    if fails:
        print(f"FAIL — {len(fails)} of {len(CASES)} cases failed:")
        for label, reason in fails:
            print(f"  - {label}: {reason}")
        return 1
    print(f"PASS — {len(CASES)}/{len(CASES)} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
