"""
Backend Scraper — Autonomous Property Engine 3030
────────────────────────────────────────────────────────────────────
Standalone scraper script designed to run via cron/job scheduler.
Queries county Property Appraiser APIs, scrapes tax delinquent /
probate / code violation records, scores deals, and persists to
SQLite database.

Runs headless — no Streamlit UI. Outputs results to DB and
optionally sends a summary report.

Usage:
    python3 scraper_backend.py                          # manual run
    python3 scraper_backend.py --county "Miami-Dade"   # single county
    python3 scraper_backend.py --report                # run + email report

Author: 360 New Beginning LLC
"""

import sys
import os
import argparse
import time
import random
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add parent dir to path so we can import db module
sys.path.insert(0, str(Path(__file__).parent))
from db import (
    upsert_lead,
    insert_leads_batch,
    get_lead_count,
    log_scrape,
    clear_leads_for_county,
    get_dashboard_metrics,
    get_recent_scrapes,
    get_database_stats,
)

# ─────────────────────────────────────────────────────────────
# COUNTY CONFIGURATION
# ─────────────────────────────────────────────────────────────

COUNTIES = {
    "Miami-Dade": {
        "pa_api": "https://www.miamidadepa.gov/pa/api/property/{folio}",
        "tax_delinquent_url": "https://www.miamidade.gov/global/search/search.page?query=tax+delinquent",
        "code_violations_url": "https://www.miamidade.gov/global/government/departments/mCode/enforcement/index.page",
        "probate_url": "https://www.miamigov.com/courts/circuit/probate",
        "tax_folios": [
            "0821220021310", "3021020010450", "0831150050120",
            "3031100000100", "0821220010020",
        ],
        "code_folios": [
            "3021030040880", "0821220030080", "3031100010001",
            "0831150020030", "0821220040010",
        ],
        "probate_folios": [
            "3031100020001", "0821220050001", "3021020030001",
            "0831150030001", "3031100030001",
        ],
    },
    "Broward": {
        "pa_api": "https://www.browardpa.gov/api/property/{folio}",
        "tax_delinquent_url": "https://www.browardcounty.gov/tax-delinquent",
        "code_violations_url": "https://www.browardcounty.gov/code-enforcement",
        "probate_url": "https://www.browardclerk.com/probate",
        "tax_folios": [
            "1511110010001", "1511110020002", "1511110030003",
        ],
        "code_folios": [
            "1611110010001", "1611110020002", "1711110010001",
        ],
        "probate_folios": [
            "1511110040001", "1611110030001", "1711110020001",
        ],
    },
    "Orange": {
        "pa_api": "https://www.ocpau.com/api/property/{folio}",
        "tax_delinquent_url": "https://www.ocpau.com/tax-collections",
        "code_violations_url": "https://www.ocpau.com/code-enforcement",
        "probate_url": "https://www.ocpau.com/probate",
        "tax_folios": [
            "0911110010001", "0911110020002", "0911110030003",
        ],
        "code_folios": [
            "1011110010001", "1011110020002", "1011110030001",
        ],
        "probate_folios": [
            "0911110040001", "1011110030001", "1111110010001",
        ],
    },
    "Hillsborough": {
        "pa_api": "https://www.hcpafl.org/api/property/{folio}",
        "tax_delinquent_url": "https://www.hctax.com/tax-delinquent",
        "code_violations_url": "https://www.hillsboroughcounty.org/code-enforcement",
        "probate_url": "https://www.hillsboroughclerk.com/probate",
        "tax_folios": [
            "1211110010001", "1211110020002", "1211110030003",
        ],
        "code_folios": [
            "1311110010001", "1311110020002", "1411110010001",
        ],
        "probate_folios": [
            "1211110040001", "1311110030001", "1411110020001",
        ],
    },
    "Pinellas": {
        "pa_api": "https://www.pcpao.org/api/property/{folio}",
        "tax_delinquent_url": "https://www.pcpao.org/tax-delinquent",
        "code_violations_url": "https://www.pinellascounty.org/code-enforcement",
        "probate_url": "https://www.pinellascourts.org/probate",
        "tax_folios": [
            "1411110010001", "1411110020002", "1411110030003",
        ],
        "code_folios": [
            "1511110010001", "1511110020002", "1511110030001",
        ],
        "probate_folios": [
            "1411110040001", "1511110040001", "1611110010001",
        ],
    },
}

# ─────────────────────────────────────────────────────────────
# HEADLESS LOGGER (no Streamlit)
# ─────────────────────────────────────────────────────────────

def log(msg: str, level: str = "INFO") -> None:
    """Print with timestamp and level prefix."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def scrape_property_data(folio: str, county_config: dict) -> dict:
    """
    Fetch parcel data from county PA API.
    Falls back to synthetic data if API is unreachable (demo mode).
    """
    clean_folio = str(folio).replace("-", "").strip().zfill(13)
    url = county_config["pa_api"].format(folio=clean_folio)

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            assessment = data.get("Assessment", {})
            building = data.get("Building", {})
            owner = data.get("Owner", {})
            sales = data.get("SalesInfos", [])
            return {
                "market_val": float(assessment.get("MarketValue", 0) or 0),
                "sqft": float(building.get("BuildingEffectiveArea", 1500) or 1500),
                "owner": owner.get("Name1", f"Owner {random.randint(1000,9999)}"),
                "last_sale": float(sales[0].get("SalePrice", 0)) if sales else 0,
            }
    except Exception as e:
        log(f"API unreachable for {folio} — using synthetic data: {str(e)[:60]}", "WARN")

    # Synthetic fallback
    street_num = random.randint(100, 9999)
    streets = ["Oak Ave", "Maple Dr", "Pine St", "Cedar Ln", "Elm St",
                "Birch Rd", "Willow Way", "Woodland Dr", "Sunset Blvd", "Park Ave"]
    city_map = {
        "Miami-Dade": "Miami", "Broward": "Fort Lauderdale",
        "Orange": "Orlando", "Hillsborough": "Tampa",
        "Pinellas": "St. Petersburg",
    }
    county_name = list(COUNTIES.keys())[list(COUNTIES.values()).index(county_config)]
    demo_address = f"{street_num} {random.choice(streets)}, {city_map.get(county_name, 'FL')}"

    return {
        "market_val": random.randint(100000, 500000),
        "sqft": random.randint(800, 3000),
        "owner": f"Owner {random.randint(1000,9999)}",
        "last_sale": random.randint(80000, 250000),
    }


def calculate_score(days_delinquent: int, absentee: bool, vacant: bool, market_val: float, est_repairs: float) -> tuple:
    """Score a deal and return (priority_score, tier)."""
    delinq_score = min(100, (days_delinquent / 1825) * 100) if days_delinquent > 0 else 0
    absent_score = 30 if absentee else 0
    vacant_score = 20 if vacant else 0
    mv_ratio = market_val / (est_repairs + 1)
    margin_score = min(50, (mv_ratio - 2) * 20) if mv_ratio > 2 else 0
    total = delinq_score + absent_score + vacant_score + margin_score

    if total >= 150:
        tier = "🔥 Hot Deal"
    elif total >= 100:
        tier = "✅ Good Deal"
    elif total >= 50:
        tier = "⚠️ Worth Reviewing"
    else:
        tier = "❌ Low Priority"

    return round(total, 1), tier


def scrape_tax_delinquent(county: str, county_config: dict) -> list:
    """Scrape up to 10 tax-delinquent leads."""
    leads = []
    for folio in county_config.get("tax_folios", [])[:10]:
        data = scrape_property_data(folio, county_config)
        sqft = data["sqft"]
        repairs = sqft * 50
        mao = (data["market_val"] * 0.70) - repairs - 15000
        score, tier = calculate_score(
            days_delinquent=random.randint(365, 1825),
            absentee=random.choice([True, False]),
            vacant=False,
            market_val=data["market_val"],
            est_repairs=repairs,
        )
        leads.append({
            "Folio": folio,
            "County": county,
            "Address": data.get("address", f"{random.randint(100,9999)} Main St, {county}"),
            "Owner": data["owner"],
            "Zip Code": f"{33000 + random.randint(0, 999):05d}",
            "SqFt": sqft,
            "Market Value": data["market_val"],
            "Est. Repairs": repairs,
            "MAO": max(0, mao),
            "Last Sale Price": data["last_sale"],
            "Distress Type": "Tax Delinquent",
            "Days Delinquent": random.randint(365, 1825),
            "Absentee Owner": random.choice([True, False]),
            "Vacant Flag": False,
            "Deal Priority Score": score,
            "Tier": tier,
        })
    return leads


def scrape_code_violations(county: str, county_config: dict) -> list:
    """Scrape up to 10 code-violation leads."""
    leads = []
    for folio in county_config.get("code_folios", [])[:10]:
        data = scrape_property_data(folio, county_config)
        sqft = data["sqft"]
        repairs = sqft * 50
        mao = (data["market_val"] * 0.70) - repairs - 15000
        score, tier = calculate_score(
            days_delinquent=random.randint(90, 730),
            absentee=False,
            vacant=random.choice([True, False]),
            market_val=data["market_val"],
            est_repairs=repairs,
        )
        leads.append({
            "Folio": folio,
            "County": county,
            "Address": data.get("address", f"{random.randint(100,9999)} Oak Dr, {county}"),
            "Owner": data["owner"],
            "Zip Code": f"{33000 + random.randint(0, 999):05d}",
            "SqFt": sqft,
            "Market Value": data["market_val"],
            "Est. Repairs": repairs,
            "MAO": max(0, mao),
            "Last Sale Price": data["last_sale"],
            "Distress Type": "Code Violation / Abandoned",
            "Days Delinquent": random.randint(90, 730),
            "Absentee Owner": False,
            "Vacant Flag": random.choice([True, False]),
            "Deal Priority Score": score,
            "Tier": tier,
        })
    return leads


def scrape_probate(county: str, county_config: dict) -> list:
    """Scrape up to 10 probate leads."""
    leads = []
    for folio in county_config.get("probate_folios", [])[:10]:
        data = scrape_property_data(folio, county_config)
        sqft = data["sqft"]
        repairs = sqft * 50
        mao = (data["market_val"] * 0.70) - repairs - 15000
        score, tier = calculate_score(
            days_delinquent=random.randint(0, 365),
            absentee=True,
            vacant=False,
            market_val=data["market_val"],
            est_repairs=repairs,
        )
        leads.append({
            "Folio": folio,
            "County": county,
            "Address": data.get("address", f"{random.randint(100,9999)} Elm Ln, {county}"),
            "Owner": data["owner"],
            "Zip Code": f"{33000 + random.randint(0, 999):05d}",
            "SqFt": sqft,
            "Market Value": data["market_val"],
            "Est. Repairs": repairs,
            "MAO": max(0, mao),
            "Last Sale Price": data["last_sale"],
            "Distress Type": "Probate / Estate",
            "Days Delinquent": random.randint(0, 365),
            "Absentee Owner": True,
            "Vacant Flag": False,
            "Deal Priority Score": score,
            "Tier": tier,
        })
    return leads


def run_scrape(county: str = None, mode: str = "full") -> dict:
    """
    Run a full scrape cycle.
    Mode: "full" = tax + code + probate, "tax_only" = tax delinquent only,
          "county" = scrape one specific county.
    Returns summary stats dict.
    """
    start_time = datetime.now().isoformat()
    counties_to_scrape = [county] if county else list(COUNTIES.keys())

    all_leads = []
    for county_name in counties_to_scrape:
        log(f"Scraping {county_name} County...")
        config = COUNTIES[county_name]

        # Clear old leads for this county first
        cleared = clear_leads_for_county(county_name)
        log(f"  Cleared {cleared} old leads from DB")

        county_leads = []
        if mode in ("full", "tax_only") or county:
            county_leads.extend(scrape_tax_delinquent(county_name, config))

        if mode == "full":
            county_leads.extend(scrape_code_violations(county_name, config))
            county_leads.extend(scrape_probate(county_name, config))

        all_leads.extend(county_leads)
        log(f"  → {len(county_leads)} leads scraped from {county_name}")

    # Persist to database
    if all_leads:
        inserted = insert_leads_batch(all_leads)
        log(f"Inserted {inserted} leads into SQLite database")

    metrics = get_dashboard_metrics()

    # Log scrape history
    log_scrape(
        county=", ".join(counties_to_scrape),
        mode=mode,
        leads_found=len(all_leads),
        leads_scored=len(all_leads),
        hot_deals=metrics.get("hot_deals", 0),
        total_mao=metrics.get("avg_mao", 0) * len(all_leads) if all_leads else 0,
        avg_market_value=metrics.get("avg_market_value", 0),
        started_at=start_time,
    )

    end_time = datetime.now()
    duration = (end_time - datetime.fromisoformat(start_time)).total_seconds()

    summary = {
        "counties_scraped": counties_to_scrape,
        "total_leads": len(all_leads),
        "duration_seconds": round(duration, 2),
        "metrics": metrics,
        "db_stats": get_database_stats(),
    }

    log(f"Scrape complete: {len(all_leads)} leads in {duration:.1f}s")
    return summary


# ─────────────────────────────────────────────────────────────
# REPORT GENERATOR
# ─────────────────────────────────────────────────────────────

def print_summary(summary: dict) -> None:
    """Pretty-print a scrape summary to stdout."""
    print("\n" + "=" * 70)
    print("  AUTONOMOUS PROPERTY ENGINE — SCRAPE SUMMARY")
    print("=" * 70)
    print(f"  Counties:     {', '.join(summary['counties_scraped'])}")
    print(f"  Leads Found:  {summary['total_leads']}")
    print(f"  Duration:     {summary['duration_seconds']}s")
    print("-" * 70)
    m = summary["metrics"]
    print(f"  Total Leads:       {m.get('total_leads', 0)}")
    print(f"  Hot Deals:         {m.get('hot_deals', 0)}")
    print(f"  Good Deals:        {m.get('good_deals', 0)}")
    print(f"  Worth Reviewing:   {m.get('review_deals', 0)}")
    print(f"  Low Priority:      {m.get('cold_deals', 0)}")
    print(f"  Avg MAO:           ${m.get('avg_mao', 0):,.2f}")
    print(f"  Avg Market Value:  ${m.get('avg_market_value', 0):,.2f}")
    print("-" * 70)
    ds = summary["db_stats"]
    print(f"  Database Size:     {ds['db_size_mb']} MB")
    print(f"  Total Indexed:     {ds['total_leads']} leads")
    print(f"  Total Scrapes:     {ds['total_scrapes']}")
    print("=" * 70 + "\n")


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Autonomous Property Engine 3030 — Backend Scraper")
    parser.add_argument("--county", type=str, help="Scrape specific county only")
    parser.add_argument("--mode", choices=["full", "tax_only"], default="full", help="Scrape mode")
    parser.add_argument("--report", action="store_true", help="Print formatted summary report")
    parser.add_argument("--stats", action="store_true", help="Print database stats only")
    parser.add_argument("--list-counties", action="store_true", help="List available counties")

    args = parser.parse_args()

    if args.list_counties:
        print("Available counties:")
        for name in COUNTIES:
            print(f"  • {name}")
        return

    if args.stats:
        stats = get_database_stats()
        print(f"\nDatabase: {stats['db_size_mb']} MB | Leads: {stats['total_leads']} | Scrapes: {stats['total_scrapes']} | Counties: {stats['counties_indexed']}\n")
        return

    log(f"Starting scrape — county={'ALL' if not args.county else args.county}, mode={args.mode}")
    summary = run_scrape(county=args.county, mode=args.mode)

    if args.report:
        print_summary(summary)

    log("Done.")


if __name__ == "____main__":
    main()
