"""
Database Module — SQLite Backend for Autonomous Property Engine 3030
────────────────────────────────────────────────────────────────────
Handles all CRUD operations for scraped leads, property data, scrape
history, and analytics caching. Uses SQLite for portability and zero
maintenance overhead.

Author: 360 New Beginning LLC
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# DATABASE PATH — stored alongside the app
# ─────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "property_engine.db"

# ─────────────────────────────────────────────────────────────
# SCHEMA — TABLES
# ─────────────────────────────────────────────────────────────

LEADS_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT UNIQUE NOT NULL,
    county TEXT NOT NULL,
    address TEXT NOT NULL,
    owner TEXT,
    zip_code TEXT,
    sqft REAL DEFAULT 0,
    market_value REAL DEFAULT 0,
    est_repairs REAL DEFAULT 0,
    mao REAL DEFAULT 0,
    last_sale_price REAL DEFAULT 0,
    distress_type TEXT DEFAULT 'Unknown',
    days_delinquent INTEGER DEFAULT 0,
    absentee_owner INTEGER DEFAULT 0,
    vacant_flag INTEGER DEFAULT 0,
    deal_priority_score REAL DEFAULT 0,
    tier TEXT DEFAULT 'Unknown',
    scraped_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

SCRAPE_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS scrape_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    county TEXT NOT NULL,
    mode TEXT NOT NULL,
    leads_found INTEGER DEFAULT 0,
    leads_scored INTEGER DEFAULT 0,
    hot_deals INTEGER DEFAULT 0,
    total_mao REAL DEFAULT 0,
    avg_market_value REAL DEFAULT 0,
    status TEXT DEFAULT 'completed',
    started_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT
);
"""

ANALYTICS_CACHE_SCHEMA = """
CREATE TABLE IF NOT EXISTS analytics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    county TEXT NOT NULL,
    filter_json TEXT,
    cached_at TEXT NOT NULL,
    total_leads INTEGER DEFAULT 0,
    total_mao REAL DEFAULT 0,
    avg_market_value REAL DEFAULT 0,
    avg_repairs REAL DEFAULT 0,
    best_mao REAL DEFAULT 0,
    tier_hot INTEGER DEFAULT 0,
    tier_good INTEGER DEFAULT 0,
    tier_review INTEGER DEFAULT 0,
    tier_cold INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL
);
"""

METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    key TEXT PRIMARY KEY,
    value REAL,
    updated_at TEXT NOT NULL
);
"""


# ─────────────────────────────────────────────────────────────
# CONNECTION POOL — thread-safe SQLite
# ─────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Get a thread-safe SQLite connection with WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database schema if tables don't exist."""
    conn = get_connection()
    try:
        for schema in [LEADS_SCHEMA, SCRAPE_HISTORY_SCHEMA, ANALYTICS_CACHE_SCHEMA, METRICS_SCHEMA]:
            conn.execute(schema)
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# LEADS CRUD
# ─────────────────────────────────────────────────────────────

def upsert_lead(
    folio: str,
    county: str,
    address: str,
    owner: str = "",
    zip_code: str = "",
    sqft: float = 0,
    market_value: float = 0,
    est_repairs: float = 0,
    mao: float = 0,
    last_sale_price: float = 0,
    distress_type: str = "Unknown",
    days_delinquent: int = 0,
    absentee_owner: bool = False,
    vacant_flag: bool = False,
    deal_priority_score: float = 0,
    tier: str = "Unknown",
) -> int:
    """
    Insert or update a lead record. Returns the row ID.
    Uses folio as unique key — new scrape overwrites stale data.
    """
    conn = get_connection()
    now = datetime.now().isoformat()
    try:
        conn.execute("""
            INSERT INTO leads (
                folio, county, address, owner, zip_code,
                sqft, market_value, est_repairs, mao, last_sale_price,
                distress_type, days_delinquent, absentee_owner, vacant_flag,
                deal_priority_score, tier, scraped_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(folio) DO UPDATE SET
                county=excluded.county, address=excluded.address,
                owner=excluded.owner, zip_code=excluded.zip_code,
                sqft=excluded.sqft, market_value=excluded.market_value,
                est_repairs=excluded.est_repairs, mao=excluded.mao,
                last_sale_price=excluded.last_sale_price,
                distress_type=excluded.distress_type,
                days_delinquent=excluded.days_delinquent,
                absentee_owner=excluded.absentee_owner,
                vacant_flag=excluded.vacant_flag,
                deal_priority_score=excluded.deal_priority_score,
                tier=excluded.tier,
                scraped_at=excluded.scraped_at,
                updated_at=excluded.updated_at
        """, (
            folio, county, address, owner, zip_code,
            sqft, market_value, est_repairs, mao, last_sale_price,
            distress_type, days_delinquent,
            int(absentee_owner), int(vacant_flag),
            deal_priority_score, tier,
            now, now,
        ))
        conn.commit()
        row_id = conn.execute("SELECT id FROM leads WHERE folio=?", (folio,)).fetchone()[0]
        return row_id
    finally:
        conn.close()


def insert_leads_batch(leads: list[dict]) -> int:
    """
    Bulk insert/update a list of lead dicts.
    Returns count of records affected.
    """
    count = 0
    for lead in leads:
        upsert_lead(
            folio=lead.get("Folio", ""),
            county=lead.get("County", ""),
            address=lead.get("Address", ""),
            owner=lead.get("Owner", ""),
            zip_code=lead.get("Zip Code", ""),
            sqft=float(lead.get("SqFt", 0) or 0),
            market_value=float(lead.get("Market Value", 0) or 0),
            est_repairs=float(lead.get("Est. Repairs", 0) or 0),
            mao=float(lead.get("MAO", 0) or 0),
            last_sale_price=float(lead.get("Last Sale Price", 0) or 0),
            distress_type=lead.get("Distress Type", "Unknown"),
            days_delinquent=int(lead.get("Days Delinquent", 0) or 0),
            absentee_owner=bool(lead.get("Absentee Owner", False)),
            vacant_flag=bool(lead.get("Vacant Flag", False)),
            deal_priority_score=float(lead.get("Deal Priority Score", 0) or 0),
            tier=lead.get("Tier", "Unknown"),
        )
        count += 1
    return count


def get_leads(
    county: Optional[str] = None,
    min_market_value: float = 0,
    max_market_value: float = float("inf"),
    min_mao: float = 0,
    tier_filter: Optional[list[str]] = None,
    distress_filter: Optional[list[str]] = None,
    limit: Optional[int] = None,
    order_by: str = "deal_priority_score DESC",
) -> pd.DataFrame:
    """
    Query leads from the database with optional filters.
    Returns a pandas DataFrame of matching records.
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM leads WHERE 1=1"
        params = []

        if county:
            query += " AND county = ?"
            params.append(county)

        query += " AND market_value >= ? AND market_value <= ?"
        params.extend([min_market_value, max_market_value])

        query += " AND mao >= ?"
        params.append(min_mao)

        if tier_filter:
            placeholders = ",".join("?" * len(tier_filter))
            query += f" AND tier IN ({placeholders})"
            params.extend(tier_filter)

        if distress_filter:
            placeholders = ",".join("?" * len(distress_filter))
            query += f" AND distress_type IN ({placeholders})"
            params.extend(distress_filter)

        query += f" ORDER BY {order_by}"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        df = pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame()

        # Convert integer columns
        if not df.empty:
            df["absentee_owner"] = df["absentee_owner"].astype(bool)
            df["vacant_flag"] = df["vacant_flag"].astype(bool)

        return df
    finally:
        conn.close()


def get_lead_by_folio(folio: str) -> Optional[pd.DataFrame]:
    """Get a single lead by folio number."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM leads WHERE folio = ?", (folio,))
        row = cursor.fetchone()
        if row:
            columns = [col[0] for col in cursor.description]
            df = pd.DataFrame([row], columns=columns)
            df["absentee_owner"] = df["absentee_owner"].astype(bool)
            df["vacant_flag"] = df["vacant_flag"].astype(bool)
            return df
        return None
    finally:
        conn.close()


def get_all_leads_for_county(county: str) -> pd.DataFrame:
    """Get all leads for a specific county, sorted by priority."""
    return get_leads(county=county, order_by="deal_priority_score DESC")


def clear_leads_for_county(county: str) -> int:
    """Remove all leads for a county before re-scraping."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM leads WHERE county = ?", (county,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_lead_count(county: Optional[str] = None) -> int:
    """Get total lead count, optionally filtered by county."""
    conn = get_connection()
    try:
        if county:
            cursor = conn.execute("SELECT COUNT(*) FROM leads WHERE county = ?", (county,))
        else:
            cursor = conn.execute("SELECT COUNT(*) FROM leads")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def get_dashboard_metrics(county: Optional[str] = None) -> dict:
    """
    Get dashboard KPI metrics from the database.
    Returns dict with: total_leads, hot_deals, good_deals, review_deals,
    cold_deals, avg_mao, avg_market_value.
    """
    conn = get_connection()
    try:
        where = "WHERE county = ?" if county else ""
        param = (county,) if county else ()

        total = conn.execute(f"SELECT COUNT(*) FROM leads {where}", param).fetchone()[0]

        hot = conn.execute(
            f"SELECT COUNT(*) FROM leads {where} AND tier IN ('🔥 Hot Deal', '🔥 Critical')"
            if where else f"SELECT COUNT(*) FROM leads WHERE tier IN ('🔥 Hot Deal', '🔥 Critical')",
            param,
        ).fetchone()[0]

        good = conn.execute(
            f"SELECT COUNT(*) FROM leads {where} AND tier IN ('✅ Good Deal', '✅ Hot')"
            if where else f"SELECT COUNT(*) FROM leads WHERE tier IN ('✅ Good Deal', '✅ Hot')",
            param,
        ).fetchone()[0]

        review = conn.execute(
            f"SELECT COUNT(*) FROM leads {where} AND tier IN ('⚠️ Worth Reviewing', '⚠️ Review')"
            if where else f"SELECT COUNT(*) FROM leads WHERE tier IN ('⚠️ Worth Reviewing', '⚠️ Review')",
            param,
        ).fetchone()[0]

        cold = conn.execute(
            f"SELECT COUNT(*) FROM leads {where} AND tier IN ('❌ Low Priority', '❌ Cold')"
            if where else f"SELECT COUNT(*) FROM leads WHERE tier IN ('❌ Low Priority', '❌ Cold')",
            param,
        ).fetchone()[0]

        avg_mao = conn.execute(
            f"SELECT COALESCE(AVG(mao), 0) FROM leads {where}", param
        ).fetchone()[0]

        avg_mv = conn.execute(
            f"SELECT COALESCE(AVG(market_value), 0) FROM leads {where}", param
        ).fetchone()[0]

        return {
            "total_leads": total,
            "hot_deals": hot,
            "good_deals": good,
            "review_deals": review,
            "cold_deals": cold,
            "avg_mao": avg_mao,
            "avg_market_value": avg_mv,
        }
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# SCRAPE HISTORY
# ─────────────────────────────────────────────────────────────

def log_scrape(
    county: str,
    mode: str,
    leads_found: int,
    leads_scored: int,
    hot_deals: int,
    total_mao: float,
    avg_market_value: float,
    started_at: str,
    completed_at: Optional[str] = None,
    status: str = "completed",
    error_message: Optional[str] = None,
) -> int:
    """Log a scrape run to the history table."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO scrape_history (
                county, mode, leads_found, leads_scored, hot_deals,
                total_mao, avg_market_value, status, started_at, completed_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            county, mode, leads_found, leads_scored, hot_deals,
            total_mao, avg_market_value, status, started_at,
            completed_at or datetime.now().isoformat(), error_message,
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_recent_scrapes(county: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
    """Get recent scrape history entries."""
    conn = get_connection()
    try:
        where = "WHERE county = ?" if county else ""
        param = (county,) if county else ()
        cursor = conn.execute(
            f"SELECT * FROM scrape_history {where} ORDER BY id DESC LIMIT ?",
            (*param, limit),
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# ANALYTICS CACHE
# ─────────────────────────────────────────────────────────────

def update_analytics_cache(
    county: str,
    filter_json: str,
    total_leads: int,
    total_mao: float,
    avg_market_value: float,
    avg_repairs: float,
    best_mao: float,
    tier_hot: int,
    tier_good: int,
    tier_review: int,
    tier_cold: int,
) -> None:
    """Upsert analytics cache for a county+filter combo."""
    conn = get_connection()
    now = datetime.now().isoformat()
    try:
        conn.execute("""
            INSERT INTO analytics_cache (
                county, filter_json, cached_at,
                total_leads, total_mao, avg_market_value,
                avg_repairs, best_mao,
                tier_hot, tier_good, tier_review, tier_cold,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(county, filter_json) DO UPDATE SET
                total_leads=excluded.total_leads,
                total_mao=excluded.total_mao,
                avg_market_value=excluded.avg_market_value,
                avg_repairs=excluded.avg_repairs,
                best_mao=excluded.best_mao,
                tier_hot=excluded.tier_hot,
                tier_good=excluded.tier_good,
                tier_review=excluded.tier_review,
                tier_cold=excluded.tier_cold,
                cached_at=excluded.cached_at,
                updated_at=excluded.updated_at
        """, (
            county, filter_json, now,
            total_leads, total_mao, avg_market_value,
            avg_repairs, best_mao,
            tier_hot, tier_good, tier_review, tier_cold,
            now,
        ))
        conn.commit()
    finally:
        conn.close()


def get_cached_analytics(county: str, filter_json: str) -> Optional[dict]:
    """Get cached analytics if available (within 1 hour)."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """SELECT * FROM analytics_cache
               WHERE county = ? AND filter_json = ?
               ORDER BY cached_at DESC LIMIT 1""",
            (county, filter_json),
        )
        row = cursor.fetchone()
        if row:
            cached_at = datetime.fromisoformat(row["cached_at"])
            age = (datetime.now() - cached_at).total_seconds()
            if age < 3600:  # 1 hour cache
                return {
                    "total_leads": row["total_leads"],
                    "total_mao": row["total_mao"],
                    "avg_market_value": row["avg_market_value"],
                    "avg_repairs": row["avg_repairs"],
                    "best_mao": row["best_mao"],
                    "tier_hot": row["tier_hot"],
                    "tier_good": row["tier_good"],
                    "tier_review": row["tier_review"],
                    "tier_cold": row["tier_cold"],
                }
        return None
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# METRICS (simple key-value store for counters)
# ─────────────────────────────────────────────────────────────

def update_metric(key: str, value: float) -> None:
    """Set a metric value."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO metrics (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (key, value, datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def get_metric(key: str) -> Optional[float]:
    """Get a metric value."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT value FROM metrics WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# MAINTENANCE
# ─────────────────────────────────────────────────────────────

def cleanup_old_leads(max_age_days: int = 90) -> int:
    """Remove leads older than max_age_days. Returns count deleted."""
    conn = get_connection()
    try:
        cutoff = (datetime.now() - __import__("datetime").timedelta(days=max_age_days)).isoformat()
        cursor = conn.execute(
            "DELETE FROM leads WHERE scraped_at < ?", (cutoff,)
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_database_stats() -> dict:
    """Get overall database statistics."""
    conn = get_connection()
    try:
        total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        total_scrapes = conn.execute("SELECT COUNT(*) FROM scrape_history").fetchone()[0]
        counties = conn.execute(
            "SELECT COUNT(DISTINCT county) FROM leads"
        ).fetchone()[0]
        db_size = Path(DB_PATH).stat().st_size if DB_PATH.exists() else 0
        return {
            "total_leads": total_leads,
            "total_scrapes": total_scrapes,
            "counties_indexed": counties,
            "db_size_bytes": db_size,
            "db_size_mb": round(db_size / (1024 * 1024), 2),
        }
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# INITIALIZE ON IMPORT
# ─────────────────────────────────────────────────────────────

init_db()
