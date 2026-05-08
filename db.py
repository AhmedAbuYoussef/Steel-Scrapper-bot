"""
Build scraperbot.db: schema for all Section 4 tables + Step 1 dummy seed data.

Run: python db.py
Idempotent — drops and recreates the file each run.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraperbot.db")

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")
FROZEN_REFRESH = "2026-04-29T22:00:00+00:00"

SCHEMA = """
CREATE TABLE projects_raw (
    id INTEGER PRIMARY KEY,
    scraped_at TEXT NOT NULL,
    name TEXT,
    category_raw TEXT,
    location_raw TEXT,
    eta_raw TEXT,
    area_raw TEXT,
    cost_raw TEXT,
    source_url TEXT
);

CREATE TABLE projects_clean (
    id INTEGER PRIMARY KEY,
    name_ar TEXT,
    name_en TEXT,
    category TEXT,
    governorate TEXT,
    eta_year INTEGER,
    eta_month INTEGER,
    area_m2 REAL,
    area_km REAL,
    cost_egp REAL,
    cost_currency_original TEXT,
    tons_estimated REAL,
    tons_low REAL,
    tons_high REAL,
    confidence TEXT,
    method TEXT,
    notes TEXT,
    FOREIGN KEY (id) REFERENCES projects_raw(id)
);

CREATE TABLE projects_clean_currency_only (
    id INTEGER PRIMARY KEY,
    name TEXT,
    category_raw TEXT,
    location_raw TEXT,
    eta_raw TEXT,
    area_raw TEXT,
    cost_egp REAL,
    cost_currency_original TEXT,
    source_url TEXT
);

CREATE TABLE cleaning_log (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    issue_category TEXT NOT NULL,
    rows_affected INTEGER NOT NULL,
    action_taken TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE cbe_raw_extractions (
    id INTEGER PRIMARY KEY,
    bulletin_period TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    extracted_json TEXT NOT NULL,
    extracted_at TEXT NOT NULL
);

CREATE TABLE cbe_metrics (
    metric TEXT NOT NULL,
    period TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    source_pdf TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    PRIMARY KEY (metric, period)
);

CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    component TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    rows_in INTEGER,
    rows_out INTEGER,
    status TEXT NOT NULL,
    error TEXT
);

CREATE TABLE steel_ratios (
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    scale_variable TEXT NOT NULL,
    low_ratio REAL NOT NULL,
    typical_ratio REAL NOT NULL,
    high_ratio REAL NOT NULL,
    confidence TEXT NOT NULL,
    egypt_factor REAL NOT NULL,
    assumptions TEXT,
    sources TEXT,
    PRIMARY KEY (category, subcategory)
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    client TEXT NOT NULL,
    user_message TEXT NOT NULL,
    tool_calls_json TEXT,
    bot_response TEXT,
    timestamp TEXT NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

# 5 projects, ids 1..5, matching Appendix B sample table verbatim.
PROJECTS_CLEAN = [
    (1, "محطة الضبعة النووية", "Dabaa Nuclear Plant", "energy", "Matrouh",
     2030, None, None, None, 870_000_000_000, "EGP",
     240_000, 200_000, 320_000, "medium",
     "nuclear × 4 reactors × 60,000 t/reactor", None),
    (2, "مونوريل 6 أكتوبر", "6th October Monorail", "transport", "Giza",
     2024, None, None, None, 137_000_000_000, "EGP",
     50_000, 33_000, 63_000, "medium",
     "elevated_metro × 42 km × 1,100 t/km", None),
    (3, "إنشاء 13 ألف وحدة سكنية بكفر الشيخ", "13K Housing Units Kafr El Sheikh",
     "housing", "Kafr El Sheikh",
     2024, None, None, None, None, "EGP",
     52_000, 39_000, 65_000, "high",
     "residential × 13,000 units × 4 t/unit", None),
    (4, "المناطق اللوجستية شرق بورسعيد", "East Port Said Logistics Zone",
     "logistics", "Port Said",
     2030, None, None, None, None, "EGP",
     None, None, None, "insufficient_data", None,
     "scale data missing"),
    (5, "محطة خلايا شمسية البحر الأحمر", "Red Sea Solar Plant",
     "energy", "Red Sea",
     2025, None, None, None, 700_000_000, "EGP",
     1_750, 1_500, 2_500, "high",
     "solar_pv × 50 MW × 35 t/MW", None),
]

# Raw versions of the same 5 projects: messy formatting before cleaning.
PROJECTS_RAW = [
    (1, FROZEN_REFRESH,
     "اسم المشروع: محطة الضبعة النووية",
     "قطاع الطاقة",
     "محافظة مطروح",
     "٢٠٣٠",
     "0",
     "٨٧٠ مليار جنيه",
     "https://egy-map.com/projects/dabaa"),
    (2, FROZEN_REFRESH,
     "اسم المشروع: مونوريل 6 أكتوبر",
     "قطاع النقل",
     "محافظة الجيزة",
     "٢٠٢٤",
     "42 km",
     "$2,800,000,000",
     "https://egy-map.com/projects/october-monorail"),
    (3, FROZEN_REFRESH,
     "اسم المشروع: إنشاء 13 ألف وحدة سكنية بكفر الشيخ",
     "قطاع الإسكان",
     "محافظة كفر الشيخ",
     "٢٠٢٤",
     "0",
     "0",
     "https://egy-map.com/projects/kafr-el-sheikh-housing"),
    (4, FROZEN_REFRESH,
     "اسم المشروع: المناطق اللوجستية شرق بورسعيد",
     "قطاع الخدمات اللوجستية",
     "محافظة بورسعيد",
     "٢٠٣٠",
     "0",
     "0",
     "https://egy-map.com/projects/east-port-said-logistics"),
    (5, FROZEN_REFRESH,
     "اسم المشروع: محطة خلايا شمسية البحر الأحمر",
     "قطاع الطاقة",
     "محافظة البحر الأحمر",
     "٢٠٢٥",
     "0",
     "€13,400,000",
     "https://egy-map.com/projects/red-sea-solar"),
]

# Currency-only partial cleaning: same five projects, currencies normalized to
# EGP at frozen rate; everything else still raw. Used for the
# "just fix the currencies, leave the rest" demo prompt.
PROJECTS_CLEAN_CURRENCY_ONLY = [
    (1,
     "اسم المشروع: محطة الضبعة النووية",
     "قطاع الطاقة",
     "محافظة مطروح",
     "٢٠٣٠",
     "0",
     870_000_000_000.0, "EGP",
     "https://egy-map.com/projects/dabaa"),
    (2,
     "اسم المشروع: مونوريل 6 أكتوبر",
     "قطاع النقل",
     "محافظة الجيزة",
     "٢٠٢٤",
     "42 km",
     137_200_000_000.0, "USD",
     "https://egy-map.com/projects/october-monorail"),
    (3,
     "اسم المشروع: إنشاء 13 ألف وحدة سكنية بكفر الشيخ",
     "قطاع الإسكان",
     "محافظة كفر الشيخ",
     "٢٠٢٤",
     "0",
     None, "EGP",
     "https://egy-map.com/projects/kafr-el-sheikh-housing"),
    (4,
     "اسم المشروع: المناطق اللوجستية شرق بورسعيد",
     "قطاع الخدمات اللوجستية",
     "محافظة بورسعيد",
     "٢٠٣٠",
     "0",
     None, "EGP",
     "https://egy-map.com/projects/east-port-said-logistics"),
    (5,
     "اسم المشروع: محطة خلايا شمسية البحر الأحمر",
     "قطاع الطاقة",
     "محافظة البحر الأحمر",
     "٢٠٢٥",
     "0",
     700_000_000.0, "EUR",
     "https://egy-map.com/projects/red-sea-solar"),
]

# Section 6 cleaning log table, eight rows, verbatim.
CLEANING_LOG = [
    (1, "egy_map", "Arabic label prefix in every field", 138,
     "Strip prefix", FROZEN_REFRESH),
    (2, "egy_map", "Placeholder \"0\" for missing values", 312,
     "Convert to NULL", FROZEN_REFRESH),
    (3, "egy_map", "Arabic-Indic numerals in dates and amounts", 89,
     "Normalize to Western digits", FROZEN_REFRESH),
    (4, "egy_map", "Missing cost data", 47,
     "Mark NULL, flag for review", FROZEN_REFRESH),
    (5, "egy_map", "Mixed currencies (USD/EUR/EGP)", 91,
     "Normalize to EGP at frozen CBE rate", FROZEN_REFRESH),
    (6, "egy_map", "Scale words (\"مليار\", \"مليون\") embedded in cost", 91,
     "Parse to numeric multiplier", FROZEN_REFRESH),
    (7, "egy_map", "Mixed area units (m², km, feddan)", 64,
     "Normalize to m² where applicable; linear units to area_km column",
     FROZEN_REFRESH),
    (8, "egy_map", "Unparseable ETAs", 12,
     "Flag for manual review", FROZEN_REFRESH),
]

# Five page-level Claude-vision extractions for the most recent bulletin.
CBE_RAW_EXTRACTIONS = [
    (1, "2026-03", 12,
     json.dumps({"table": "construction_lending_rate",
                 "rows": [{"period": "2026-03", "value": 24.5, "unit": "percent"}]}),
     FROZEN_REFRESH),
    (2, "2026-03", 18,
     json.dumps({"table": "industrial_production_index",
                 "rows": [{"period": "2026-03", "value": 112.4, "unit": "index_2018=100"}]}),
     FROZEN_REFRESH),
    (3, "2026-03", 22,
     json.dumps({"table": "construction_sector_activity",
                 "rows": [{"period": "2026-03", "value": 105.7, "unit": "index_2018=100"}]}),
     FROZEN_REFRESH),
    (4, "2026-03", 31,
     json.dumps({"table": "fx_rates",
                 "rows": [{"metric": "usd_egp_rate", "period": "2026-03", "value": 49.8, "unit": "EGP_per_USD"}]}),
     FROZEN_REFRESH),
    (5, "2026-03", 31,
     json.dumps({"table": "fx_rates",
                 "rows": [{"metric": "eur_egp_rate", "period": "2026-03", "value": 53.6, "unit": "EGP_per_EUR"}]}),
     FROZEN_REFRESH),
]

# 12 monthly rows for each of the five locked metrics (Section 8).
# Window: 2025-04 through 2026-03 inclusive.
PERIODS = [
    "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
    "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03",
]

CBE_METRIC_SERIES = {
    "construction_lending_rate": (
        [27.5, 27.5, 27.0, 26.5, 26.5, 26.0, 25.5, 25.5, 25.0, 25.0, 24.75, 24.5],
        "percent",
    ),
    "industrial_production_index": (
        [104.1, 105.3, 106.0, 106.8, 107.5, 108.2, 109.0, 109.7, 110.3, 110.9, 111.6, 112.4],
        "index_2018=100",
    ),
    "construction_sector_activity": (
        [98.2, 98.9, 99.5, 100.1, 100.8, 101.4, 102.0, 102.7, 103.4, 104.1, 104.9, 105.7],
        "index_2018=100",
    ),
    "usd_egp_rate": (
        [48.6, 48.7, 48.9, 49.0, 49.1, 49.2, 49.3, 49.4, 49.5, 49.6, 49.7, 49.8],
        "EGP_per_USD",
    ),
    "eur_egp_rate": (
        [52.4, 52.5, 52.7, 52.8, 52.9, 53.0, 53.1, 53.2, 53.3, 53.4, 53.5, 53.6],
        "EGP_per_EUR",
    ),
}

CBE_METRICS = []
for metric, (values, unit) in CBE_METRIC_SERIES.items():
    for period, value in zip(PERIODS, values):
        CBE_METRICS.append((metric, period, value, unit,
                            "cbe_monthly_bulletin_2026_03.pdf", FROZEN_REFRESH))

# Audit log of recent pipeline runs.
RUNS = [
    (1, "egy_map_scraper", "2026-04-29T20:00:00+00:00",
     "2026-04-29T20:04:12+00:00", None, 138, "ok", None),
    (2, "egy_map_cleaner", "2026-04-29T20:05:00+00:00",
     "2026-04-29T20:05:38+00:00", 138, 138, "ok", None),
    (3, "cbe_extractor", "2026-04-29T21:30:00+00:00",
     "2026-04-29T21:32:17+00:00", 1, 60, "ok", None),
    (4, "steel_estimator", "2026-04-29T21:40:00+00:00",
     "2026-04-29T21:40:51+00:00", 138, 137, "ok",
     "1 project marked insufficient_data"),
    (5, "egy_map_scraper", "2026-04-22T20:00:00+00:00",
     "2026-04-22T20:03:45+00:00", None, 138, "ok", None),
]

# Steel ratios: Section 4 column order. ~10 rows.
STEEL_RATIOS = [
    ("housing", "residential_apartment", "units_count",
     3.2, 4.0, 5.0, "high", 0.95,
     "Reinforced concrete frame, mid-rise.",
     "Worldsteel residential factsheet 2023; Egyptian construction handbook."),
    ("housing", "social_housing", "units_count",
     2.4, 3.0, 3.8, "high", 0.90,
     "Lower-spec finishes, smaller floor plates.",
     "MoH&UD design briefs."),
    ("transport", "elevated_metro", "route_km",
     900.0, 1100.0, 1400.0, "medium", 1.00,
     "Viaduct + stations averaged per km.",
     "UITP urban-rail benchmarks; Cairo Metro Line 3 data."),
    ("transport", "highway", "route_km",
     180.0, 250.0, 340.0, "medium", 1.05,
     "Asphalt highway with bridges; reinforcement only.",
     "FHWA pavement guides; NUCA road specs."),
    ("energy", "nuclear_reactor", "reactor_count",
     50000.0, 60000.0, 75000.0, "medium", 1.00,
     "VVER-1200 class reactor; per-unit steel including containment.",
     "Rosatom technical briefs; IAEA-TECDOC-1382."),
    ("energy", "solar_pv", "capacity_mw",
     28.0, 35.0, 45.0, "high", 1.00,
     "Utility-scale fixed-tilt; mounting + inverter station structures.",
     "IRENA cost benchmarks; Benban site data."),
    ("energy", "wind_onshore", "capacity_mw",
     110.0, 140.0, 180.0, "medium", 1.00,
     "Tower + nacelle internals + foundation rebar.",
     "GWEC reports; Ras Ghareb wind farm BoQ."),
    ("logistics", "industrial_zone", "area_m2",
     0.05, 0.08, 0.12, "low", 1.00,
     "Mixed warehouse, internal roads, perimeter; very wide range.",
     "GAFI master plan templates."),
    ("infrastructure", "water_treatment_plant", "capacity_m3_per_day",
     0.0008, 0.0012, 0.0018, "medium", 1.00,
     "Concrete-heavy with rebar; per m³/day capacity.",
     "AWWA design manuals."),
    ("infrastructure", "bridge", "deck_area_m2",
     0.18, 0.25, 0.34, "medium", 1.00,
     "Composite steel-concrete deck; rebar plus structural steel.",
     "AASHTO LRFD; Egyptian bridge code."),
]

# A few sample logged conversations.
CONVERSATIONS = [
    (1, "sess-001", "standalone",
     "Show me the scraped egy-map data.",
     json.dumps([{"name": "get_dataset",
                  "input": {"source": "egy_map", "version": "raw"}}]),
     "Returned 138-row raw projects table.",
     "2026-04-29T22:15:01+00:00"),
    (2, "sess-001", "standalone",
     "Clean this dataset.",
     json.dumps([{"name": "get_cleaning_log", "input": {"source": "egy_map"}},
                 {"name": "get_dataset",
                  "input": {"source": "egy_map", "version": "clean"}}]),
     "Narrated 8-row cleaning log, returned clean projects.",
     "2026-04-29T22:16:30+00:00"),
    (3, "sess-002", "fantomaas",
     "Steel demand for Port Said infrastructure?",
     json.dumps([{"name": "estimate_steel_total",
                  "input": {"governorate": "Port Said"}}]),
     "1 project, insufficient_data — total 0 with caveat.",
     "2026-04-29T23:01:44+00:00"),
]


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    conn.executemany(
        "INSERT INTO projects_raw VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        PROJECTS_RAW,
    )
    conn.executemany(
        "INSERT INTO projects_clean VALUES "
        "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        PROJECTS_CLEAN,
    )
    conn.executemany(
        "INSERT INTO projects_clean_currency_only VALUES "
        "(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        PROJECTS_CLEAN_CURRENCY_ONLY,
    )
    conn.executemany(
        "INSERT INTO cleaning_log VALUES (?, ?, ?, ?, ?, ?)",
        CLEANING_LOG,
    )
    conn.executemany(
        "INSERT INTO cbe_raw_extractions VALUES (?, ?, ?, ?, ?)",
        CBE_RAW_EXTRACTIONS,
    )
    conn.executemany(
        "INSERT INTO cbe_metrics VALUES (?, ?, ?, ?, ?, ?)",
        CBE_METRICS,
    )
    conn.executemany(
        "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        RUNS,
    )
    conn.executemany(
        "INSERT INTO steel_ratios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        STEEL_RATIOS,
    )
    conn.executemany(
        "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?, ?)",
        CONVERSATIONS,
    )

    conn.commit()
    return conn


def report(conn):
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    print(f"DB: {DB_PATH}")
    print(f"Tables ({len(tables)}): {', '.join(tables)}")
    print()
    print(f"{'table':<35} {'rows':>6}")
    print("-" * 44)
    for t in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t:<35} {n:>6}")


if __name__ == "__main__":
    conn = build()
    report(conn)
    conn.close()
