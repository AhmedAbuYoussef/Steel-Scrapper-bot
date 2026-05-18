from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
from fastapi import FastAPI, HTTPException

app = FastAPI(title="EZZ Steel Scraper Bot")

# Verbatim from scraper_bot_demo_spec_v1_2.md §5 line 142.
# Per spec §3 "Single source of truth": this string must survive the
# OpenAPI -> Anthropic translation byte-identical. Any drift breaks
# routing. Verified by Appendix B done criterion #2 (round-trip diff).
GET_DATASET_DESCRIPTION = """Retrieves a dataset by source and processing stage. `source`: `egy_map` for Egyptian state projects (138 rows) or `cbe` for Central Bank of Egypt monthly metrics. `version`: `raw` for the original scraped data with messy formatting; `clean` for the normalized, processed version; `currency_only` for partially-cleaned (currencies normalized, rest raw). Use `raw` when user asks for "scraped", "original", or wants to see what came directly from the source. Use `clean` when user asks for the data to be processed, fixed, normalized, or analyzed. Use `currency_only` when user explicitly wants only currency normalization."""

_TABLE_MAP = {
    ("egy_map", "raw"): "projects_raw",
    ("egy_map", "clean"): "projects_clean",
    ("egy_map", "currency_only"): "projects_clean_currency_only",
}


@app.get("/get_dataset", description=GET_DATASET_DESCRIPTION)
def get_dataset(source: str, version: str):
    if source == "cbe":
        table = "cbe_metrics"
    elif (source, version) in _TABLE_MAP:
        table = _TABLE_MAP[(source, version)]
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown (source, version) combination: ({source!r}, {version!r}). "
                   f"Valid: source=egy_map with version in {{raw, clean, currency_only}}, "
                   f"or source=cbe with any version.",
        )
    db_path = os.environ.get("SQLITE_PATH", "scraperbot.db")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(f"SELECT * FROM {table}").fetchall()]
    con.close()
    return rows
