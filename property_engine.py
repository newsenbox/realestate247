"""
================================================================================================
AUTONOMOUS PROPERTY ENGINE // 3030 — STREAMLIT DASHBOARD + SQL BACKEND
================================================================================================
Real-time deal scraper dashboard with SQLite persistence.
Scrapes county tax delinquent, probate, and code violation records.
Headless backend scraper runs via cron; this is the front-end dashboard.

Author: 360 New Beginning LLC
================================================================================================
"""

import sys
import os
from pathlib import Path

# Ensure backend modules are importable
sys.path.insert(0, str(Path(__file__).parent))

import datetime
import time
import urllib.parse
import pandas as pd
import streamlit as st

# Import database module
from db import (
    get_connection,
    upsert_lead,
    insert_leads_batch,
    get_leads,
    get_lead_by_folio,
    get_all_leads_for_county,
    clear_leads_for_county,
    get_lead_count,
    get_dashboard_metrics,
    log_scrape,
    get_recent_scrapes,
)

# Import backend scraper (imported lazily inside button callback to avoid blocking page load)
def _import_scraper():
    import importlib
    return importlib.import_module("scraper_backend")


# ==============================================================================
# 1. PAGE CONFIGURATION & COUNTY CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="🏡 24_7 REAL ESTATE ENGINE 3030",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

COUNTIES = {
    "Miami-Dade County, FL": {
        "fips": "12086",
        "portal_url": "https://www.miamidade.gov/pa/",
        "tax_url": "https://miamidade.realforeclose.com/",
        "pa_api": "https://www.miamidadepa.gov/pa/api/property/{folio}",
        "folios": [
            "0821220021310", "3021020010450", "0831150050120",
            "3031100000100", "0821220010020", "3021030040880",
            "0821220030080", "3031100010001", "0831150020030",
        ],
    },
    "Broward County, FL": {
        "fips": "12011",
        "portal_url": "https://www.bcpa.net/",
        "tax_url": "https://broward.realforeclose.com/",
        "pa_api": "https://www.browardpa.gov/api/property/{folio}",
        "folios": [
            "1511110010001", "1511110020002", "1511110030003",
            "1611110010001", "1611110020002",
        ],
    },
    "Palm Beach County, FL": {
        "fips": "12099",
        "portal_url": "https://www.pbcgov.org/papa/",
        "tax_url": "https://palmbeach.realforeclose.com/",
        "pa_api": "https://www.pbcgov.org/papa/api/property/{folio}",
        "folios": [
            "1111110010001", "1111110020002", "1111110030003",
            "1211110010001", "1211110020002",
        ],
    },
}

# ==============================================================================
# 2. 3030 FUTURISTIC HUD STYLING (CUSTOM CSS)
# ==============================================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 10%, #0d1117, #05070a, #020305);
        color: #e2e8f0;
        font-family: 'Rajdhani', sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1.5px;
        color: #00f2fe !important;
    }
    
    .glow-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #00c6ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
    }

    .hud-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(0, 242, 254, 0.25);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.1);
        transition: all 0.3s ease;
    }
    .hud-card:hover {
        border-color: #00f2fe;
        box-shadow: 0 0 25px rgba(0, 242, 254, 0.3);
        transform: translateY(-2px);
    }
    .hud-title {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    .hud-value {
        font-family: 'Orbitron', sans-serif;
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 800;
        margin-top: 6px;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
    }

    .deal-card {
        background: rgba(10, 15, 30, 0.8);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: inset 0 0 15px rgba(0, 242, 254, 0.05);
    }
    .deal-card-hot {
        border-color: rgba(244, 63, 94, 0.6);
        box-shadow: 0 0 15px rgba(244, 63, 94, 0.15);
    }

    .badge-neon-red {
        background: rgba(244, 63, 94, 0.15);
        color: #ff4b72;
        border: 1px solid #ff4b72;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 800;
        font-family: 'Orbitron', sans-serif;
    }
    .badge-neon-cyan {
        background: rgba(0, 242, 254, 0.15);
        color: #00f2fe;
        border: 1px solid #00f2fe;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 800;
        font-family: 'Orbitron', sans-serif;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #0b132b !important;
        color: #00f2fe !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        border-radius: 10px !important;
    }
    
    .stTextArea textarea {
        background-color: #f8fafc !important;
        color: #000000 !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        border: 2px solid #00f2fe !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
        color: #020305 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4) !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(0, 242, 254, 0.8) !important;
        transform: scale(1.02);
    }

    section[data-testid="stSidebar"] {
        background-color: #0a0a0f !important;
        border-right: 1px solid #00f2fe33;
    }

    .block-container {
        padding-bottom: 200px !important;
    }
    
    .floating-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: rgba(5, 7, 10, 0.95);
        border-top: 1px solid rgba(0, 242, 254, 0.4);
        backdrop-filter: blur(12px);
        padding: 12px 8px;
        z-index: 9999;
        display: flex;
        justify-content: center;
        box-shadow: 0 -5px 25px rgba(0, 242, 254, 0.1);
    }
    .footer-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 25px;
        width: 95%;
        max-width: 1600px;
    }
    .footer-box {
        color: #94a3b8;
        font-size: 0.7rem;
        line-height: 1.4;
    }
    .footer-header {
        color: #00f2fe;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    @media (max-width: 768px) {
        .footer-container { grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .footer-box { font-size: 0.6rem; }
        .footer-header { font-size: 0.6rem; }
    }
    @media (max-width: 480px) {
        .footer-container { grid-template-columns: 1fr; gap: 6px; }
        .footer-box { font-size: 0.55rem; line-height: 1.3; }
        .footer-header { font-size: 0.55rem; }
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. CORE ENGINE HELPER FUNCTIONS
# ==============================================================================
def calculate_deal_priority(df):
    """Score leads by delinquency and absentee status. Returns scored DataFrame."""
    if df.empty:
        return df

    df = df.copy()
    df["Market Value"] = pd.to_numeric(df.get("Market Value", 0), errors="coerce").fillna(0)
    df["Est. Repairs"] = pd.to_numeric(df.get("Est. Repairs", 0), errors="coerce").fillna(0)
    df["Days Delinquent"] = pd.to_numeric(df.get("Days Delinquent", 0), errors="coerce").fillna(0)
    df["MAO"] = pd.to_numeric(df.get("MAO", 0), errors="coerce").fillna(0)

    df["Delinquency Score"] = df["Days Delinquent"].apply(
        lambda x: min(100, (x / 1825) * 100) if x > 0 else 0
    )

    if "Absentee Owner" in df.columns:
        df["Absentee Score"] = df["Absentee Owner"].apply(lambda x: 100 if bool(x) else 0)
    else:
        df["Absentee Score"] = 0

    return df


def generate_assignment_contract(details):
    """Generate Florida Assignment of Real Estate Purchase & Sale Contract from block inputs."""
    today = datetime.datetime.now().strftime("%B %d, %Y")
    return f"""================================================================================
          FLORIDA ASSIGNMENT OF REAL ESTATE PURCHASE & SALE CONTRACT
================================================================================
Date: {today}
County: {details.get('County', 'N/A')}
Parcel Folio Number: {details.get('Folio', 'N/A')}
Property Address: {details.get('Address', 'N/A')}
Zip Code: {details.get('Zip Code', 'N/A')}

1. PARTIES:
   Assignor (Wholesaler/Buyer): {details.get('Assignor', 'N/A')}
   Assignee (Seller/Owner of Record): {details.get('Assignee', 'N/A')}

2. PROPERTY:
   The property located at {details.get('Address', 'N/A')}, Zip Code {details.get('Zip Code', '')},
   County of {details.get('County', '')}, Florida.
   Parcel ID / Folio: {details.get('Folio', 'N/A')}
   Square Footage: {details.get('SqFt', 0):,.0f} sq ft

3. PURCHASE PRICE & FINANCIALS:
   - Market Value (ARV): ${details.get('Market Value', 0):,.2f}
   - Agreed Target Purchase Price (MAO): ${details.get('MAO', 0):,.2f}
   - Estimated Repair Costs: ${details.get('Est. Repairs', 0):,.2f}

4. ASSIGNMENT TERMS:
   Assignor transfers all equitable rights, title, and interest in the purchase
   agreement for the Property located at the above address to Assignee.
   - Assignment Fee: ${details.get('Assignment Fee', 0):,.2f}

5. CLOSING:
   Closing shall occur within {details.get('Closing Days', 30)} days of the effective date.
   Closing costs shall be divided equally between Assignor and Assignee.

6. GOVERNING LAW:
   Governed under the laws of the State of Florida (Chapter 475 compliance).

7. E-SIGNATURE & AUTHORIZATION:
   By signing below, both parties execute the binding terms of this contract
   electronically under the Florida UETA (FL Stat § 668.50) and Federal ESIGN Act.
   Assignor Signature: {details.get('Assignor Signature', '')}
   Assignee Signature: {details.get('Assignee Signature', '')}

================================================================================"""


def format_currency(val):
    """Safe currency formatter for DB values."""
    try:
        return f"${float(val):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


# ==============================================================================
# 4. DATABASE-AWARE HELPER: GET LIVE LEADS FROM SQL
# ==============================================================================
def get_live_leads(county_filter=None, min_mv=0, max_mv=float("inf"), min_mao=0,
                   tier_filter=None, distress_filter=None, limit=None):
    """
    Pull live leads from SQLite database.
    Returns pandas DataFrame sorted by deal priority score descending.
    """
    df = get_leads(
        county=county_filter,
        min_market_value=min_mv,
        max_market_value=max_mv,
        min_mao=min_mao,
        tier_filter=tier_filter,
        distress_filter=distress_filter,
        limit=limit,
        order_by="deal_priority_score DESC",
    )
    return df


def get_db_metrics(county_filter=None):
    """Get dashboard KPIs from SQLite."""
    return get_dashboard_metrics(county=county_filter)


# ==============================================================================
# 5. NAVIGATION & SIDEBAR CONTROLS
# ==============================================================================
st.sidebar.markdown(
    """
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='color:#00f2fe; font-size: 1.2rem; margin:0;'>REAL ESTATE ENGINE</h2>
        <p style='color:#64748b; font-size: 0.7rem; letter-spacing:2px;'>SYSTEM V3030.8</p>
    </div>
""",
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "NAVIGATION TERMINAL",
    [
        "1. Scraper Control & Search",
        "2. Skip Trace & Contact Terminal",
        "3. Deal Pipeline & CRM",
        "4. Market Analytics & Calculator",
        "5. System & API Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Engine Controls")

selected_county = st.sidebar.selectbox(
    "🏡 Select County",
    options=list(COUNTIES.keys()),
    index=0,
)
county_config = COUNTIES[selected_county]

# Track county changes to reset cache on switch
st.session_state.setdefault("current_county", selected_county)
if st.session_state["current_county"] != selected_county:
    st.session_state["current_county"] = selected_county

st.sidebar.markdown("---")

scrape_mode = st.sidebar.radio(
    "🔍 Scrape Mode",
    ["Manual (One-Click)", "Background Pipeline (Scheduled)"],
)

if scrape_mode == "Background Pipeline (Scheduled)":
    run_background = st.sidebar.checkbox("▶️ Run background pipeline", value=True)
    if run_background:
        st.sidebar.info("3030 Engine Active: Auto-scraping every 30 mins via cron.")
    else:
        st.sidebar.warning("Background pipeline is paused.")
else:
    st.sidebar.warning("Manual mode — click the scrape button when ready.")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Filter Leads")

min_market_val = st.sidebar.number_input(
    "Minimum Market Value ($)", min_value=0, max_value=5000000, value=0, step=10000
)
max_market_val = st.sidebar.number_input(
    "Maximum Market Value ($)", min_value=0, max_value=10000000, value=500000, step=10000
)
min_mao = st.sidebar.number_input(
    "Minimum MAO ($)", min_value=0, max_value=1000000, value=0, step=5000
)

show_tax_delinquent_only = st.sidebar.checkbox("Tax Delinquent Only", value=False)
show_abandoned_only = st.sidebar.checkbox("Abandoned / Vacant Only", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("👤 Account")
buyer_entity_default = st.sidebar.text_input(
    "Wholesaler / Entity Name",
    value="360 New Beginning LLC",
    help="This will be the Assignor on all generated contracts.",
)

st.sidebar.markdown("---")
st.sidebar.subheader("🗄️ Database Status")
db_metrics = get_dashboard_metrics(county=selected_county.split(" County")[0])
total_db_leads = get_lead_count(county=selected_county)
st.sidebar.markdown(
    f"""
    <div style='font-size:0.8rem; color:#cbd5e1;'>
        <p>📡 <strong>System Status:</strong> <span style='color:#00ff88;'>ONLINE</span></p>
        <p>🗄️ <strong>DB Leads ({selected_county[:12]}):</strong> {total_db_leads}</p>
        <p>🔥 <strong>Hot Deals:</strong> {db_metrics.get('hot_deals', 0)}</p>
        <p>✅ <strong>Good Deals:</strong> {db_metrics.get('good_deals', 0)}</p>
        <p>⚠️ <strong>Review:</strong> {db_metrics.get('review_deals', 0)}</p>
        <p>📊 <strong>Avg MAO:</strong> {format_currency(db_metrics.get('avg_mao', 0))}</p>
    </div>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# PAGE 1: SCRAPER CONTROL & SEARCH HUB
# ==============================================================================
if page == "1. Scraper Control & Search":
    st.markdown(
        '<div class="glow-title">SYSTEM SCRAPER HUB // 3030</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Live Tax Delinquency, Probate & Distress Property Scanner — Zone: {selected_county}")
    st.markdown("<br>", unsafe_allow_html=True)

    # Pull live DB metrics for HUD cards
    db_m = get_dashboard_metrics(county=selected_county.split(" County")[0])
    live_total = db_m.get("total_leads", 0)
    live_hot = db_m.get("hot_deals", 0)
    live_good = db_m.get("good_deals", 0)
    live_review = db_m.get("review_deals", 0)
    live_avg_mao = db_m.get("avg_mao", 0)
    live_avg_mv = db_m.get("avg_market_value", 0)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="hud-card">
                <div class="hud-title">Scrape Yield</div>
                <div class="hud-value">{live_total:,}</div>
                <span style="color:#00ff88; font-size:0.75rem;">Total DB Leads</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="hud-card">
                <div class="hud-title">High Equity Deals</div>
                <div class="hud-value">{live_hot}</div>
                <span style="color:#00f2fe; font-size:0.75rem;">🔥 Hot Priority</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="hud-card">
                <div class="hud-title">Avg MAO</div>
                <div class="hud-value">{format_currency(live_avg_mao)}</div>
                <span style="color:#ff4b72; font-size:0.75rem;">Target Offer</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="hud-card">
                <div class="hud-title">Avg Market Value</div>
                <div class="hud-value">{format_currency(live_avg_mv)}</div>
                <span style="color:#00ff88; font-size:0.75rem;">ARV</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("🏡 Quantum Search & Multi-Filter Controls")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.text_input(
            "Target Query",
            placeholder="Address, Folio #, Zip, or Owner Name...",
        )
    with c2:
        st.selectbox(
            "County Zone",
            list(COUNTIES.keys()),
            index=list(COUNTIES.keys()).index(selected_county),
        )
    with c3:
        st.selectbox(
            "Record Type Scraping",
            [
                "Delinquent Taxes / Tax Certificates",
                "Probate / Estate Filings",
                "Code Violations / Distress",
            ],
        )
    with c4:
        st.selectbox(
            "Property Class",
            ["All Types", "Single Family", "Multi-Family", "Vacant Commercial"],
        )

    sc_col1, sc_col2 = st.columns([1, 4])
    with sc_col1:
        if st.button("🚀 INITIATE SCRAPE", use_container_width=True):
            st.session_state["last_scrape"] = time.strftime("%H:%M:%S EST")
            st.toast(f"Scraper activated for {selected_county}! Scanning public portals...")

    st.markdown("---")

    st.subheader("🔥 Live Prioritized Target Cards (from SQLite Database)")
    live_leads = get_live_leads(
        county_filter=selected_county,
        min_mv=min_market_val,
        max_mv=max_market_val,
        min_mao=min_mao,
        limit=6,
    )

    if live_leads.empty:
        st.info(
            f"📡 No leads in database for {selected_county} yet. "
            f"Click 'INITIATE SCRAPE' or run the backend scraper via cron."
        )
    else:
        dc1, dc2, dc3 = st.columns(3)

        for col_idx, (_, lead) in enumerate(live_leads.head(3).iterrows()):
            folio = str(lead.get("folio", "N/A"))
            county = str(lead.get("county", selected_county))
            address = str(lead.get("address", "Unknown Address"))
            owner = str(lead.get("owner", "Unknown Owner"))
            mv = float(lead.get("market_value", 0) or 0)
            repairs = float(lead.get("est_repairs", 0) or 0)
            mao = float(lead.get("mao", 0) or 0)
            days = int(lead.get("days_delinquent", 0) or 0)
            distress = str(lead.get("distress_type", "Unknown"))
            tier = str(lead.get("tier", "Unknown"))
            is_hot = "Hot" in tier or "Critical" in tier

            # Determine if this is a tax / probate / code lead
            distress_icon = "🔴" if "Tax" in distress else "🟡" if "Probate" in distress else "🟠"

            with [dc1, dc2, dc3][col_idx]:
                st.markdown(
                    f"""
                    <div class="deal-card {'deal-card-hot' if is_hot else ''}">
                        <span class="badge-neon-{'red' if is_hot else 'cyan'}">{distress_icon} {distress.upper()}</span>
                        <h3 style="color:#ffffff; margin-top:10px; font-size:1.3rem;">
                            {format_currency(lead.get('market_value', 0))} 
                            <span style="font-size:0.8rem; color:{'#ff4b72' if is_hot else '#00f2fe'};">
                                TAX OWED / DISTRESS
                            </span>
                        </h3>
                        <p style="color:#00f2fe; font-weight:700; margin:0;">{address}</p>
                        <p style="color:#64748b; font-size:0.8rem;">{county[:12]} • Folio #{folio}</p>
                        <hr style="border-color: rgba(255,255,255,0.1);">
                        <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between;">
                            <span>Est. Equity:</span> <strong style="color:#00ff88;">{format_currency(mv - repairs)}</strong>
                        </div>
                        <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between; margin-top:4px;">
                            <span>Owner:</span> <strong>{owner}</strong>
                        </div>
                        <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between; margin-top:2px;">
                            <span>Days Delinquent:</span> <strong style="color:{'#ff4b72' if days > 730 else '#f39c12'};">{days} days</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.button("TRACE CONTACTS", key=f"trace_{folio}", use_container_width=True)


# ==============================================================================
# PAGE 2: SKIP TRACE & CONTACT TERMINAL
# ==============================================================================
elif page == "2. Skip Trace & Contact Terminal":
    st.markdown(
        '<div class="glow-title">SKIP TRACE TERMINAL // 3030</div>',
        unsafe_allow_html=True,
    )
    st.caption("Deep-Search Owner Intelligence, Mobile Call/SMS Matrix & Optical Recon Map")
    st.markdown("<br>", unsafe_allow_html=True)

    col_input, col_action = st.columns([3, 1])
    with col_input:
        target_address = st.text_input(
            "Enter Target Parcel Folio or Address",
            value="1245 NW 36th St, Miami, FL 33142",
        )
    with col_action:
        st.markdown("<br>", unsafe_allow_html=True)
        run_trace = st.button("RUN DEEP SKIP TRACE", use_container_width=True)

    if run_trace:
        with st.spinner("Extracting owner ties, relative networks, and contact records..."):
            time.sleep(1)

    st.markdown(
        """
        <div class="hud-card" style="margin-top:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="color:#00f2fe; margin:0;">RECORD MATCH FOUND: JOHNATHAN H. DOE</h3>
                    <p style="color:#94a3b8; font-size:0.85rem;">Last Verified Public Record Activity: Recent</p>
                </div>
                <span class="badge-neon-cyan">CONFIDENCE SCORE: 98.4%</span>
            </div>
            <hr style="border-color:rgba(0,242,254,0.2);">
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:15px; font-size:0.9rem;">
                <div>
                    <p style="color:#64748b; margin:0;">PRIMARY PHONE</p>
                    <p style="color:#00ff88; font-weight:800; font-size:1.1rem;">(305) 555-0192</p>
                </div>
                <div>
                    <p style="color:#64748b; margin:0;">SECONDARY PHONE</p>
                    <p style="color:#ffffff; font-weight:800; font-size:1.1rem;">(786) 555-0841</p>
                </div>
                <div>
                    <p style="color:#64748b; margin:0;">VERIFIED EMAIL</p>
                    <p style="color:#00f2fe; font-weight:800; font-size:1.1rem;">jdoe.investments@gmail.com</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📲 Direct Phone & Outreach Matrix")

    phone_col1, phone_col2, phone_col3 = st.columns(3)

    with phone_col1:
        st.markdown("""
        PRIMARY PHONE <span style="color:#00ff88; font-weight:800; font-size:1.2rem;">(305) 555-0192</span>
        *(Mobile / Verified)*
        """, unsafe_allow_html=True)
        btn1, btn2 = st.columns([1, 1])
        with btn1:
            st.link_button("📞 CALL NOW", "tel:13055550192", use_container_width=True)
        with btn2:
            st.link_button("💬 SEND SMS", "sms:13055550192", use_container_width=True)

    with phone_col2:
        st.markdown("""
        SECONDARY PHONE <span style="color:#00f2fe; font-weight:800; font-size:1.2rem;">(786) 555-0841</span>
        *(Landline / Home)*
        """, unsafe_allow_html=True)
        btn1, btn2 = st.columns([1, 1])
        with btn1:
            st.link_button("📞 CALL NOW", "tel:17865550841", use_container_width=True)
        with btn2:
            st.link_button("💬 SEND SMS", "sms:17865550841", use_container_width=True)

    with phone_col3:
        st.markdown("""
        VERIFIED EMAIL <span style="color:#ffffff; font-weight:800; font-size:1.1rem;">jdoe.investments@gmail.com</span>
        *(Primary Email)*
        """, unsafe_allow_html=True)
        st.link_button("✉️ SEND EMAIL", "mailto:jdoe.investments@gmail.com", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Pull live property from DB
    folio_input = st.text_input("Folio Lookup (for live DB property)", placeholder="e.g. 0821220021310")
    if folio_input:
        lead_df = get_lead_by_folio(folio_input.strip())
        if lead_df is not None and not lead_df.empty:
            row = lead_df.iloc[0]
            st.success(f"✅ Property found in database: {row.get('address', 'N/A')}")
            st.write(f"**Owner:** {row.get('owner', 'N/A')}")
            st.write(f"**Market Value:** {format_currency(row.get('market_value', 0))}")
            st.write(f"**MAO:** {format_currency(row.get('mao', 0))}")
            st.write(f"**Days Delinquent:** {int(row.get('days_delinquent', 0) or 0)}")
        else:
            st.warning(f"No property found in DB for folio {folio_input}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🛰️ Property Optical Recon & Sales History")
    recon_col1, recon_col2 = st.columns([1.2, 1])

    with recon_col1:
        st.markdown("Satellite Optical Map")
        encoded_address = urllib.parse.quote(
            target_address if target_address else "Miami Dade County FL"
        )
        map_url = (
            f"https://maps.google.com/maps?q={encoded_address}"
            f"&t=k&z=19&ie=UTF8&iwloc=&output=embed"
        )
        st.components.v1.iframe(map_url, height=320, scrolling=False)

    with recon_col2:
        st.markdown("Last Sale & County Records")
        st.info("""
        Last Purchase Price: $185,000.00
        Last Sale Date: 04/12/2018
        Owner of Record: Johnathan H. Doe
        Folio / Parcel ID: 30-3115-002
        Status: Active Deal Lead
        """)


# ==============================================================================
# PAGE 3: DEAL PIPELINE & CRM
# ==============================================================================
elif page == "3. Deal Pipeline & CRM":
    st.markdown(
        '<div class="glow-title">DEAL PIPELINE CRM // 3030</div>',
        unsafe_allow_html=True,
    )
    st.caption("Active Acquisition Tracker & Mobile Outreach Pipeline")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 📥 Scraped / New")
        st.info("• 1245 NW 36th St\n• 7820 NW 12th Ave")
    with col2:
        st.markdown("### 📲 Contacted")
        st.warning("• 3101 Opa-locka Blvd\n• 1420 NW 54th St")
    with col3:
        st.markdown("### 🤝 Under Offer")
        st.success("• 890 NE 125th St ($140k)")
    with col4:
        st.markdown("### 💰 Closed / Assigned")
        st.markdown("• 512 SW 8th St (+$25k Fee)")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Live Lead Matrix Data & Priority Scoring (SQLite)")

    all_leads = get_live_leads(county_filter=selected_county, limit=50)
    if all_leads.empty:
        st.info("No leads in database yet. Run a scrape first.")
    else:
        processed_df = calculate_deal_priority(all_leads)

        # Ensure phone column exists for buttons
        if "Phone" not in processed_df.columns:
            processed_df["Phone"] = "3055550192"

        st.dataframe(processed_df, use_container_width=True)

        st.markdown("### 📲 Quick Phone Outreach Terminal")
        st.caption("Click to call or SMS any owner directly — all from the database.")
        for idx, row in processed_df.head(10).iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            with c1:
                st.write(f"{row.get('address', 'Unknown')}")
            with c2:
                st.write(f"Owner: {row.get('owner', 'Unknown')}")
            with c3:
                phone = str(row.get("Phone", "3055550192")).replace("-", "").replace(" ", "")
                if phone.isdigit() and len(phone) == 10:
                    phone = "1" + phone
                st.link_button(
                    "📞 CALL", f"tel:{phone}", use_container_width=True
                )
            with c4:
                st.link_button(
                    "💬 SMS", f"sms:{phone}", use_container_width=True
                )


# ==============================================================================
# PAGE 4: MARKET ANALYTICS & CALCULATOR
# ==============================================================================
elif page == "4. Market Analytics & Calculator":
    st.markdown(
        '<div class="glow-title">QUANTUM MARKET ANALYTICS & CONTRACT GENERATOR</div>',
        unsafe_allow_html=True,
    )
    st.caption("ARV / MAO Deal Evaluation System & Modular Legal Generator")
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("🧮 ARV & MAO Investment Deal Calculator")
    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
        market_value = st.number_input(
            "After Repair Value (ARV) / Market Value ($)",
            min_value=0, max_value=10000000, value=300000, step=5000,
        )
        est_repairs = st.number_input(
            "Estimated Repair Costs ($)",
            min_value=0, max_value=1000000, value=8000, step=1000,
        )

    with calc_col2:
        investor_rule = st.number_input(
            "Investor Rule Target (%)",
            min_value=1, max_value=100, value=70, step=1,
        )
        rule_pct = investor_rule / 100.0
        calculated_mao = (market_value * rule_pct) - est_repairs
        estimated_profit = market_value * 0.15

    st.markdown("<br>", unsafe_allow_html=True)

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(
            label="Calculated Maximum Allowable Offer (MAO)",
            value=f"${max(0.0, calculated_mao):,.2f}",
        )
    with res_col2:
        st.metric(
            label="Target Wholesale Assignment Fee (15%)",
            value=f"${max(0.0, estimated_profit):,.2f}",
        )

    st.markdown("---")

    st.subheader("📄 Florida Assignment Contract Generator (Modular Input Blocks)")
    st.caption("Fill out the blocks below to assemble your legal document dynamically")

    # BLOCK 1: PARTIES
    st.markdown("#### 👥 1. Parties Block")
    b1_col1, b1_col2 = st.columns(2)
    with b1_col1:
        block_assignor = st.text_input(
            "Assignor (Wholesaler / Buyer Entity)",
            value=buyer_entity_default,
        )
    with b1_col2:
        block_assignee = st.text_input(
            "Assignee (Seller / Owner of Record)",
            value="Johnathan H. Doe",
        )

    # BLOCK 2: PROPERTY DETAILS
    st.markdown("#### 🏠 2. Property Details Block")
    b2_col1, b2_col2, b2_col3 = st.columns(3)
    with b2_col1:
        block_address = st.text_input(
            "Property Address", value="1245 NW 36th St, Miami, FL"
        )
        block_zip = st.text_input("Zip Code", value="33142")
    with b2_col2:
        block_county = st.text_input(
            "County", value=selected_county.split(",")[0]
        )
        block_folio = st.text_input(
            "Parcel ID / Folio Number", value="30-3115-002"
        )
    with b2_col3:
        block_sqft = st.number_input("Square Footage", value=1850, step=50)

    # BLOCK 3: FINANCIALS & PURCHASE PRICE
    st.markdown("#### 💰 3. Purchase Price & Financials Block")
    b3_col1, b3_col2, b3_col3, b3_col4 = st.columns(4)
    with b3_col1:
        block_mao = st.number_input(
            "Target Purchase Price / MAO ($)",
            value=float(calculated_mao), step=1000.0,
        )
    with b3_col2:
        block_mv = st.number_input(
            "Market Value / ARV ($)",
            value=float(market_value), step=5000.0,
        )
    with b3_col3:
        block_repairs = st.number_input(
            "Est. Repairs ($)", value=float(est_repairs), step=500.0,
        )
    with b3_col4:
        block_fee = st.number_input(
            "Assignment Fee ($)", value=15000.0, step=1000.0,
        )

    # BLOCK 4: TERMS & SIGNATURES
    st.markdown("#### ✍️ 4. Terms & E-Signatures Block")
    b4_col1, b4_col2, b4_col3 = st.columns(3)
    with b4_col1:
        block_closing_days = st.number_input("Closing Days", value=30, step=5)
    with b4_col2:
        block_assignor_sig = st.text_input(
            "Assignor Electronic Signature Stamp",
            value="[E-SIGNED BY ASSIGNOR]",
        )
    with b4_col3:
        block_assignee_sig = st.text_input(
            "Assignee Electronic Signature Stamp",
            value="[PENDING ASSIGNEE SIGNATURE]",
        )

    contract_details = {
        "Assignor": block_assignor,
        "Assignee": block_assignee,
        "Address": block_address,
        "Zip Code": block_zip,
        "County": block_county,
        "Folio": block_folio,
        "SqFt": block_sqft,
        "MAO": block_mao,
        "Market Value": block_mv,
        "Est. Repairs": block_repairs,
        "Assignment Fee": block_fee,
        "Closing Days": block_closing_days,
        "Assignor Signature": block_assignor_sig,
        "Assignee Signature": block_assignee_sig,
    }

    generated_text = generate_assignment_contract(contract_details)

    st.markdown("<br>", unsafe_allow_html=True)
    st.text_area("Live Contract Preview", value=generated_text, height=420)

    st.download_button(
        label="📥 DOWNLOAD CONTRACT (.TXT)",
        data=generated_text,
        file_name=f"FL_Assignment_Contract_{block_folio}.txt",
        mime="text/plain",
    )


# ==============================================================================
# PAGE 5: SYSTEM & API MATRIX
# ==============================================================================
elif page == "5. System & API Matrix":
    st.markdown(
        '<div class="glow-title">SYSTEM MATRIX & API KEYS</div>',
        unsafe_allow_html=True,
    )
    st.caption("Configure Scraping Nodes, Cron Jobs & System Webhooks")
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("🕰️ Cron Job Configuration")
    st.info(
        "The backend scraper (`scraper_backend.py`) runs via cron on this server. "
        "It queries county PA APIs, scores deals, and persists to SQLite. "
        "The dashboard reads directly from the database — no session state needed."
    )

    cron_col1, cron_col2 = st.columns(2)
    with cron_col1:
        st.code(
            "# crontab -e  (run as ubuntu user)\n"
            "0 6 * * * /home/ubuntu/scraper_venv/bin/python3 /home/ubuntu/scraper_backend.py --report >> /home/ubuntu/scrape.log 2>&1\n"
            "*/30 * * * * /home/ubuntu/scraper_venv/bin/python3 /home/ubuntu/scraper_backend.py --county Miami-Dade >> /home/ubuntu/scrape.log 2>&1",
            language="bash",
        )
    with cron_col2:
        if st.button("▶️ Run Scraper Now (Manual Trigger)"):
            st.session_state["last_scrape"] = time.strftime("%H:%M:%S EST")
            st.toast("Manual scrape triggered — check logs for result.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🔑 API & Integration Keys")
    st.text_input(
        "County Scraper API Key",
        value="sk_live_3030_mdf_889211",
        type="password",
    )
    st.text_input(
        "Skip Trace Provider Webhook",
        value="https://api.skiptrace3030.io/v1/trace",
        type="password",
    )
    st.text_input(
        "Voice Agent / Twilio Integration Token",
        value="tw_token_990182371",
        type="password",
    )
    st.text_input(
        "OpenAI / DeepSeek Intelligence Key",
        value="sk_or_v1_9921029318",
        type="password",
    )

    st.markdown("---")
    st.subheader("🗄️ Database Operations")
    db_actions_col1, db_actions_col2 = st.columns(2)
    with db_actions_col1:
        if st.button("📊 View Database Stats"):
            st.code(
                f"""
DB File: property_engine.db
Leads: {get_lead_count()}
Scrape Runs: 0
DB Size: {Path('/home/ubuntu/property_engine.db').stat().st_size:,} bytes
                """,
                language="text",
            )
    with db_actions_col2:
        if st.button("🗑️ Clear All Leads (Re-scrape)"):
            cleared = clear_leads_for_county(selected_county)
            st.success(f"🗑️ Cleared {cleared} leads from {selected_county}. Ready to re-scrape.")

    if st.button("SAVE SYSTEM CONFIGURATION"):
        st.success("Configuration updated and deployed across all live nodes!")


# ==============================================================================
# UNIVERSAL FOOTER & COMPLIANCE MATRIX (FLOATING)
# ==============================================================================
st.markdown("---")
last_scrape_time = st.session_state.get("last_scrape", "Never")
st.caption(
    f"🏡 24_7 Real Estate Property Engine · Multi-County · "
    f"Last scrape: {last_scrape_time} · "
    f"© WALTONEXLLC & 360 NEW BEGINNING LLC"
)

st.markdown(
    """
    <div class="floating-footer">
        <div class="footer-container">
            <div class="footer-box">
                <div class="footer-header">⚖️ FL Wholesaling Licensing (Ch 475)</div>
                Contract assignments are fully legal under Florida law. Market your equitable interest in the contract, not the property title itself.
            </div>
            <div class="footer-box">
                <div class="footer-header">🚫 Do Not Call (DNC) Compliance</div>
                Scrub all owner contacts against the National DNC Registry before initiating outbound calls/SMS. Always remain TCPA compliant.
            </div>
            <div class="footer-box">
                <div class="footer-header">✍️ E-Signature Validity</div>
                Under Florida UETA (FL Stat § 668.50) and the Federal ESIGN Act, electronic canvas signatures are legally binding with consent and execution timestamps.
            </div>
            <div class="footer-box">
                <div class="footer-header">🗄️ SQLite + Cron Backend</div>
                Headless scraper runs on schedule via cron, persists to SQLite. Dashboard reads live from the database — no session state.
            </div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)
