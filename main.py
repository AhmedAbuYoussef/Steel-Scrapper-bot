from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

app = FastAPI(title="EZZ Steel Scraper Bot")

# Spec §3 "Single source of truth": the system prompt lives in one file
# inside the FastAPI service; both clients (standalone bot, Fantomaas) load
# it from here. include_in_schema=False keeps this off /openapi.json so it
# does NOT appear in the Anthropic tool registry — it's a config endpoint,
# not a tool. The round-trip pytest (G-B1) only iterates the 9 §5 tools,
# so this addition does not affect it.
_SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")


@app.get("/system_prompt", include_in_schema=False, response_class=PlainTextResponse)
def system_prompt():
    with open(_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


# Each description below is verbatim from scraper_bot_demo_spec_v1_3.md §5.
# Per spec §3.1 the strings must survive OpenAPI -> Anthropic translation
# byte-identical. Stored as module constants and passed via `description=`
# on each route decorator (NOT as docstrings — FastAPI splits docstrings
# on first newline into summary/description, which would silently truncate).
# Round-trip tests in tests/test_round_trip.py enforce byte-identicality
# against spec line numbers (see VERIFICATION.md G-B1).

GET_DATASET_DESCRIPTION = """Retrieves a dataset by source and processing stage. `source`: `egy_map` for Egyptian state projects (138 rows) or `cbe` for Central Bank of Egypt monthly metrics. `version`: `raw` for the original scraped data with messy formatting; `clean` for the normalized, processed version; `currency_only` for partially-cleaned (currencies normalized, rest raw). Use `raw` when user asks for "scraped", "original", or wants to see what came directly from the source. Use `clean` when user asks for the data to be processed, fixed, normalized, or analyzed. Use `currency_only` when user explicitly wants only currency normalization."""

GET_CLEANING_LOG_DESCRIPTION = """Returns the audit log of cleaning actions taken on a source's data. Eight category-level rows for egy-map describing each issue found and the action taken. Use this when narrating what was cleaned, when user asks "what did you fix?" or "walk me through the cleaning," or whenever explaining the difference between raw and clean data."""

QUERY_PROJECTS_DESCRIPTION = """Filters the cleaned Egyptian projects table by any combination of governorate name, category, expected completion year range, and project cost range in EGP. All six parameters are optional — calling with no arguments returns all projects. Returns matching projects with all clean fields. Use for any question about specific projects, locations, categories, or completion timelines. Do NOT use for CBE economic indicators."""

ESTIMATE_STEEL_TOTAL_DESCRIPTION = """Aggregates steel estimates across a filtered set of projects. Filter signature is identical to `query_projects` — same six optional parameters (governorate, category, completion year range in `eta_year_min`/`eta_year_max`, cost range in EGP via `cost_min_egp`/`cost_max_egp`). Calling with no arguments aggregates across all projects. Returns total tons (typical), low/high band, count of projects with insufficient data excluded, and the top 3 contributors by tonnage. Use for "how much steel" questions across multiple projects. For single-project estimates, use `query_projects` and read the tons columns directly."""

QUERY_CBE_TREND_DESCRIPTION = """Time-series for a specific CBE metric over a date range. Available metrics: `construction_lending_rate`, `industrial_production_index`, `construction_sector_activity`, `usd_egp_rate`, `eur_egp_rate`. Periods are YYYY-MM format. Use for trend questions, "show me X over time," or "how has Y changed.\""""

COMPARE_CBE_PERIODS_DESCRIPTION = """Compares one CBE metric between two specific periods. Returns both values, absolute difference, and percentage change. Use for "compare X this quarter vs last year" questions."""

REFRESH_EGY_MAP_DESCRIPTION = """Triggers a live scrape of egy-map.com. Takes 30–60 seconds. ONLY call if the user explicitly asks for fresh data, a live scrape, or "refresh." Do not call automatically."""

EXTRACT_LATEST_CBE_BULLETIN_DESCRIPTION = """Triggers a live extraction of the most recent CBE PDF bulletin. Takes 1–3 minutes. ONLY call if user explicitly requests a fresh extraction."""

GET_RUN_STATUS_DESCRIPTION = """Returns timestamps and status of the last scrape, cleaning, and extraction runs. Use when user asks "is this fresh?" or any data-freshness question."""


_TABLE_MAP = {
    ("egy_map", "raw"): "projects_raw",
    ("egy_map", "clean"): "projects_clean",
    ("egy_map", "currency_only"): "projects_clean_currency_only",
    ("cbe", "raw"): "cbe_raw_extractions",
    ("cbe", "clean"): "cbe_metrics",
}


def _connect() -> sqlite3.Connection:
    db_path = os.environ.get("SQLITE_PATH", "scraperbot.db")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def _rows(cur) -> list:
    return [dict(r) for r in cur.fetchall()]


@app.get("/get_dataset", description=GET_DATASET_DESCRIPTION)
def get_dataset(source: str, version: str):
    if (source, version) not in _TABLE_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown (source, version) combination: ({source!r}, {version!r}). "
                   f"Valid: source=egy_map with version in {{raw, clean, currency_only}}, "
                   f"or source=cbe with version in {{raw, clean}} "
                   f"(currency_only is not meaningful for CBE metrics).",
        )
    table = _TABLE_MAP[(source, version)]
    con = _connect()
    try:
        return _rows(con.execute(f"SELECT * FROM {table}"))
    finally:
        con.close()


@app.get("/get_cleaning_log", description=GET_CLEANING_LOG_DESCRIPTION)
def get_cleaning_log(source: str):
    con = _connect()
    try:
        return _rows(con.execute(
            "SELECT id, source, issue_category, rows_affected, action_taken, applied_at "
            "FROM cleaning_log WHERE source = ? ORDER BY id",
            (source,),
        ))
    finally:
        con.close()


def _projects_filter(
    governorate: Optional[str],
    category: Optional[str],
    eta_year_min: Optional[int],
    eta_year_max: Optional[int],
    cost_min_egp: Optional[float],
    cost_max_egp: Optional[float],
) -> tuple[str, list]:
    clauses = []
    params: list = []
    if governorate is not None:
        clauses.append("governorate = ?")
        params.append(governorate)
    if category is not None:
        clauses.append("category = ?")
        params.append(category)
    if eta_year_min is not None:
        clauses.append("eta_year >= ?")
        params.append(eta_year_min)
    if eta_year_max is not None:
        clauses.append("eta_year <= ?")
        params.append(eta_year_max)
    if cost_min_egp is not None:
        clauses.append("cost_egp >= ?")
        params.append(cost_min_egp)
    if cost_max_egp is not None:
        clauses.append("cost_egp <= ?")
        params.append(cost_max_egp)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


@app.get("/query_projects", description=QUERY_PROJECTS_DESCRIPTION)
def query_projects(
    governorate: Optional[str] = None,
    category: Optional[str] = None,
    eta_year_min: Optional[int] = None,
    eta_year_max: Optional[int] = None,
    cost_min_egp: Optional[float] = None,
    cost_max_egp: Optional[float] = None,
):
    where, params = _projects_filter(
        governorate, category, eta_year_min, eta_year_max, cost_min_egp, cost_max_egp,
    )
    con = _connect()
    try:
        return _rows(con.execute(f"SELECT * FROM projects_clean{where} ORDER BY id", params))
    finally:
        con.close()


@app.get("/estimate_steel_total", description=ESTIMATE_STEEL_TOTAL_DESCRIPTION)
def estimate_steel_total(
    governorate: Optional[str] = None,
    category: Optional[str] = None,
    eta_year_min: Optional[int] = None,
    eta_year_max: Optional[int] = None,
    cost_min_egp: Optional[float] = None,
    cost_max_egp: Optional[float] = None,
):
    where, params = _projects_filter(
        governorate, category, eta_year_min, eta_year_max, cost_min_egp, cost_max_egp,
    )
    top_where = (where + " AND tons_estimated IS NOT NULL") if where \
        else " WHERE tons_estimated IS NOT NULL"

    con = _connect()
    try:
        agg = con.execute(
            f"SELECT "
            f"  COALESCE(SUM(tons_estimated), 0) AS total_typical, "
            f"  COALESCE(SUM(tons_low), 0)       AS total_low, "
            f"  COALESCE(SUM(tons_high), 0)      AS total_high, "
            f"  SUM(CASE WHEN tons_estimated IS NULL OR confidence = 'insufficient_data' "
            f"           THEN 1 ELSE 0 END) AS insufficient_data_count "
            f"FROM projects_clean{where}",
            params,
        ).fetchone()
        top_rows = _rows(con.execute(
            f"SELECT id, name_en, governorate, category, tons_estimated "
            f"FROM projects_clean{top_where} "
            f"ORDER BY tons_estimated DESC LIMIT 3",
            params,
        ))
    finally:
        con.close()

    return {
        "total_tons_typical": agg["total_typical"],
        "total_tons_low":     agg["total_low"],
        "total_tons_high":    agg["total_high"],
        "insufficient_data_count": agg["insufficient_data_count"],
        "top_contributors": top_rows,
    }


@app.get("/query_cbe_trend", description=QUERY_CBE_TREND_DESCRIPTION)
def query_cbe_trend(metric: str, period_start: str, period_end: str):
    con = _connect()
    try:
        return _rows(con.execute(
            "SELECT metric, period, value, unit, source_pdf, extracted_at "
            "FROM cbe_metrics WHERE metric = ? AND period >= ? AND period <= ? "
            "ORDER BY period",
            (metric, period_start, period_end),
        ))
    finally:
        con.close()


@app.get("/compare_cbe_periods", description=COMPARE_CBE_PERIODS_DESCRIPTION)
def compare_cbe_periods(metric: str, period_a: str, period_b: str):
    con = _connect()
    try:
        rows = _rows(con.execute(
            "SELECT period, value, unit FROM cbe_metrics "
            "WHERE metric = ? AND period IN (?, ?)",
            (metric, period_a, period_b),
        ))
    finally:
        con.close()
    by_period = {r["period"]: r for r in rows}
    a = by_period.get(period_a)
    b = by_period.get(period_b)
    if a is None or b is None:
        missing = [p for p, v in [(period_a, a), (period_b, b)] if v is None]
        raise HTTPException(
            status_code=404,
            detail=f"No data for metric={metric!r} at period(s) {missing!r}.",
        )
    diff = b["value"] - a["value"]
    pct = (diff / a["value"] * 100.0) if a["value"] else None
    return {
        "metric": metric,
        "period_a": {"period": period_a, "value": a["value"], "unit": a["unit"]},
        "period_b": {"period": period_b, "value": b["value"], "unit": b["unit"]},
        "absolute_difference": diff,
        "percent_change": pct,
    }


def _record_run(component: str, status: str, note: str) -> dict:
    """Insert a stub runs row for refresh/extract endpoints in Step 1."""
    now = datetime.now(timezone.utc).isoformat()
    con = _connect()
    try:
        cur = con.execute(
            "INSERT INTO runs (component, started_at, finished_at, rows_in, rows_out, status, error) "
            "VALUES (?, ?, ?, NULL, NULL, ?, ?)",
            (component, now, now, status, note),
        )
        con.commit()
        run_id = cur.lastrowid
    finally:
        con.close()
    return {
        "run_id": run_id,
        "component": component,
        "status": status,
        "note": note,
        "started_at": now,
    }


@app.get("/refresh_egy_map", description=REFRESH_EGY_MAP_DESCRIPTION)
def refresh_egy_map():
    return _record_run(
        component="egy_map_scraper",
        status="step_1_stub",
        note="Live scraping not enabled in Step 1; demo runs on frozen dummy data per spec §17.",
    )


@app.get("/extract_latest_cbe_bulletin", description=EXTRACT_LATEST_CBE_BULLETIN_DESCRIPTION)
def extract_latest_cbe_bulletin():
    return _record_run(
        component="cbe_pdf_extractor",
        status="step_1_stub",
        note="Live extraction not enabled in Step 1; demo runs on frozen dummy data per spec §17.",
    )


@app.get("/get_run_status", description=GET_RUN_STATUS_DESCRIPTION)
def get_run_status():
    con = _connect()
    try:
        return _rows(con.execute(
            "SELECT id, component, started_at, finished_at, rows_in, rows_out, status, error "
            "FROM runs ORDER BY started_at DESC"
        ))
    finally:
        con.close()
