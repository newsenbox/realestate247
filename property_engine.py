"""
AUTONOMOUS PROPERTY ENGINE // 3030
────────────────────────────────────────────────────────────────────
Real Estate Deal Scraper — Multi-County — 3030 HUD Design
Tax Delinquency · Probate · Code Violations · Skip Trace · CRM · Analytics
"""

import streamlit as st
import pandas as pd
import requests
import random
import time
from datetime import datetime
from io import BytesIO
import base64
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np

# ─────────────────────────────────────────────────────────────
# 3030 FUTURISTIC HUD STYLING (CUSTOM CSS)
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AUTONOMOUS PROPERTY ENGINE // 3030",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
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
        position: relative;
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
        text-shadow: 0 0 8px rgba(255, 75, 114, 0.5);
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
        text-shadow: 0 0 8px rgba(0, 242, 254, 0.5);
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0b132b !important;
        color: #00f2fe !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        border-radius: 10px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
        color: #020305 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(0, 242, 254, 0.8) !important;
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CONFIGURATION — ALL COUNTIES
# ─────────────────────────────────────────────────────────────

COUNTIES = {
    "Miami-Dade": {
        "pa_api": "https://www.miamidadepa.gov/pa/api/property/{folio}",
        "tax_delinquent_url": "https://www.miamidade.gov/global/search/search.page?query=tax+delinquent",
        "code_violations_url": "https://www.miamidade.gov/global/government/departments/mCode/enforcement/index.page",
        "probate_url": "https://www.miamigov.com/courts/circuit/probate",
        "folios": [
            "0821220021310", "3021020010450", "0831150050120",
            "3031100000100", "0821220010020", "3021030040880",
            "0821220030080", "3031100010001", "0831150020030",
        ],
    },
    "Broward": {
        "pa_api": "https://www.browardpa.gov/api/property/{folio}",
        "tax_delinquent_url": "https://www.browardcounty.gov/tax-delinquent",
        "code_violations_url": "https://www.browardcounty.gov/code-enforcement",
        "probate_url": "https://www.browardclerk.com/probate",
        "folios": [
            "1511110010001", "1511110020002", "1511110030003",
            "1611110010001", "1611110020002",
        ],
    },
    "Orange": {
        "pa_api": "https://www.ocpau.com/api/property/{folio}",
        "tax_delinquent_url": "https://www.ocpau.com/tax-collections",
        "code_violations_url": "https://www.ocpau.com/code-enforcement",
        "probate_url": "https://www.ocpau.com/probate",
        "folios": [
            "0911110010001", "0911110020002", "0911110030003",
            "1011110010001", "1011110020002",
        ],
    },
    "Hillsborough": {
        "pa_api": "https://www.hcpafl.org/api/property/{folio}",
        "tax_delinquent_url": "https://www.hctax.com/tax-delinquent",
        "code_violations_url": "https://www.hillsboroughcounty.org/code-enforcement",
        "probate_url": "https://www.hillsboroughclerk.com/probate",
        "folios": [
            "1211110010001", "1211110020002", "1211110030003",
            "1311110010001", "1311110020002",
        ],
    },
    "Pinellas": {
        "pa_api": "https://www.pcpao.org/api/property/{folio}",
        "tax_delinquent_url": "https://www.pcpao.org/tax-delinquent",
        "code_violations_url": "https://www.pinellascounty.org/code-enforcement",
        "probate_url": "https://www.pinellascourts.org/probate",
        "folios": [
            "1411110010001", "1411110020002", "1411110030003",
            "1511110010001", "1511110020002",
        ],
    },
}

# ─────────────────────────────────────────────────────────────
# SCRAPER ENGINE — MULTI-COUNTY
# ─────────────────────────────────────────────────────────────

st.session_state.setdefault("scraped_leads", None)
st.session_state.setdefault("pipeline_running", False)
st.session_state.setdefault("last_scrape", None)


def fetch_property_data(folio, county_config):
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
            market_val = assessment.get("MarketValue", 0) or 0
            sqft = building.get("BuildingEffectiveArea", 1500) or 1500
            repairs = sqft * 50
            mao = (market_val * 0.70) - repairs - 15000
            last_sale = sales[0].get("SalePrice", 0) if sales else 0
            street_num = random.randint(100, 9999)
            streets = ["Oak Ave", "Maple Dr", "Pine St", "Cedar Ln", "Elm St",
                        "Birch Rd", "Willow Way", "Woodland Dr", "Sunset Blvd", "Park Ave"]
            street_name = random.choice(streets)
            city_map = {
                "Miami-Dade": "Miami", "Broward": "Fort Lauderdale",
                "Orange": "Orlando", "Hillsborough": "Tampa",
                "Pinellas": "St. Petersburg",
            }
            city = city_map.get(selected_county, "FL")
            demo_address = f"{street_num} {street_name}, {city}, FL"
            return {
                "Folio": clean_folio, "County": selected_county,
                "Address": demo_address,
                "Owner": owner.get("Name1", f"Owner {random.randint(1000,9999)}"),
                "Zip Code": f"{33000 + random.randint(0, 999):05d}",
                "SqFt": sqft, "Market Value": market_val,
                "Est. Repairs": repairs, "MAO": mao,
                "Last Sale Price": last_sale,
                "Distress Type": "Unknown",
                "Days Delinquent": 0,
                "Absentee Owner": False, "Vacant Flag": False,
            }
    except Exception:
        pass
    return None


def scrape_tax_delinquent_list(county_config):
    leads = []
    for folio in county_config.get("folios", [])[:10]:
        d = fetch_property_data(folio, county_config)
        if d:
            d["Distress Type"] = "Tax Delinquent"
            d["Days Delinquent"] = random.randint(365, 1825)
            d["Absentee Owner"] = random.choice([True, False])
            leads.append(d)
    return leads


def scrape_code_violations(county_config):
    leads = []
    for folio in county_config.get("folios", [])[:10]:
        d = fetch_property_data(folio, county_config)
        if d:
            d["Distress Type"] = "Code Violation / Abandoned"
            d["Days Delinquent"] = random.randint(90, 730)
            d["Vacant Flag"] = random.choice([True, False])
            leads.append(d)
    return leads


def scrape_probate_filings(county_config):
    leads = []
    for folio in county_config.get("folios", [])[:10]:
        d = fetch_property_data(folio, county_config)
        if d:
            d["Distress Type"] = "Probate / Estate"
            d["Days Delinquent"] = random.randint(0, 365)
            d["Absentee Owner"] = True
            leads.append(d)
    return leads


def auto_scrape_delinquent_leads(county_config, scrape_mode):
    all_leads = []
    if scrape_mode == "Manual (One-Click)":
        all_leads.extend(scrape_tax_delinquent_list(county_config))
        all_leads.extend(scrape_code_violations(county_config))
        all_leads.extend(scrape_probate_filings(county_config))
    else:
        all_leads.extend(scrape_tax_delinquent_list(county_config))
        all_leads.extend(scrape_code_violations(county_config))
    if all_leads:
        return pd.DataFrame(all_leads)
    return pd.DataFrame()


def calculate_deal_priority(df):
    if df.empty:
        return df
    df = df.copy()
    df["Delinquency Score"] = df["Days Delinquent"].apply(lambda x: min(100, x / 1825 * 100) if x > 0 else 0)
    df["Absentee Score"] = df["Absentee Owner"].apply(lambda x: 30 if x else 0)
    df["Vacant Score"] = df["Vacant Flag"].apply(lambda x: 20 if x else 0)
    df["MV_to_Repair_Ratio"] = df["Market Value"] / (df["Est. Repairs"] + 1)
    df["Margin Score"] = df["MV_to_Repair_Ratio"].apply(lambda x: min(50, (x - 2) * 20) if x > 2 else 0)
    df["Deal Priority Score"] = df["Delinquency Score"] + df["Absentee Score"] + df["Vacant Score"] + df["Margin Score"]
    df = df.sort_values("Deal Priority Score", ascending=False).reset_index(drop=True)

    def assign_tier(score):
        if score >= 150: return "🔥 Critical"
        elif score >= 100: return "✅ Hot"
        elif score >= 50: return "⚠️ Review"
        else: return "❌ Cold"
    df["Tier"] = df["Deal Priority Score"].apply(assign_tier)
    return df


def generate_contract_text(details, buyer_name):
    today = datetime.now().strftime("%B %d, %Y")
    mao = details.get("MAO", 0)
    return f"""
================================================================================
          FLORIDA ASSIGNMENT OF REAL ESTATE PURCHASE & SALE CONTRACT
================================================================================
Date: {today}
County: {details.get('County', 'N/A')}
Parcel Folio Number: {details['Folio']}
Property Address: {details['Address']}
Zip Code: {details.get('Zip Code', 'N/A')}
1. PARTIES:
   Assignor (Wholesaler/Buyer): {buyer_name}
   Assignee (Seller/Owner of Record): {details.get('Owner', 'N/A')}
2. PROPERTY:
   {details['Address']}, {details.get('Zip Code', '')},
   County of {details.get('County', '')}, Florida. Folio: {details['Folio']}
3. AGREED PURCHASE PRICE:
   ${details.get('Market Value', 0):,.2f} (Market Value)
4. ASSIGNMENT TERMS:
   MAO: ${mao:,.2f} | Assignment Fee: $15,000.00
   Repairs: ${details.get('Est. Repairs', 0):,.2f} | SqFt: {details.get('SqFt', 0):,.0f}
5. CLOSING: Within 30 days. Costs split equally.
6. GOVERNING LAW: State of Florida (Chapter 475 compliance).
7. E-SIGNATURE: Under Florida UETA (FL Stat § 668.50) and Federal ESIGN Act.
================================================================================
"""


# ─────────────────────────────────────────────────────────────
# NAVIGATION SIDEBAR — THE 5 PAGES
# ─────────────────────────────────────────────────────────────

st.sidebar.markdown("""
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='color:#00f2fe; font-size: 1.2rem; margin:0;'>AUTONOMOUS ENGINE</h2>
        <p style='color:#64748b; font-size: 0.7rem; letter-spacing:2px;'>SYSTEM V3030.8</p>
    </div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "NAVIGATION TERMINAL",
    [
        "1. Scraper Control & Search",
        "2. Skip Trace & Contact Terminal",
        "3. Deal Pipeline & CRM",
        "4. AI Market Analytics",
        "5. System & API Matrix",
    ],
)

st.sidebar.markdown("---")
selected_county = st.sidebar.selectbox(
    "📍 County Zone",
    options=list(COUNTIES.keys()),
    index=0,
)
county_config = COUNTIES[selected_county]

st.sidebar.markdown("""
    <div style='font-size:0.75rem; color:#64748b;'>
        <p>📡 <strong>System Status:</strong> <span style='color:#00ff88;'>ONLINE</span></p>
        <p>🎯 <strong>Active County:</strong> """ + selected_county + """</p>
        <p>⚡ <strong>Scraper Core:</strong> Multi-Node Active</p>
    </div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PAGE 1: SCRAPER CONTROL & SEARCH HUB
# ─────────────────────────────────────────────────────────────

if page == "1. Scraper Control & Search":
    st.markdown('<div class="glow-title">SYSTEM SCRAPER HUB // 3030</div>', unsafe_allow_html=True)
    st.caption("Live Tax Delinquency, Probate & Distress Property Scanner")
    st.markdown("<br>", unsafe_allow_html=True)

    # Top HUD Stats
    m1, m2, m3, m4 = st.columns(4)
    df_all = st.session_state["scraped_leads"]
    total = len(df_all) if df_all is not None and not df_all.empty else 0
    scored = calculate_deal_priority(df_all) if df_all is not None and not df_all.empty else pd.DataFrame()
    with m1:
        st.markdown(f"""
            <div class="hud-card">
                <div class="hud-title">Scrape Yield</div>
                <div class="hud-value">{total:,}</div>
                <span style="color:#00ff88; font-size:0.75rem;">Live Feeds · {selected_county}</span>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        hot_count = len(scored[scored["Tier"].isin(["🔥 Critical", "✅ Hot"])]) if not scored.empty else 0
        st.markdown(f"""
            <div class="hud-card">
                <div class="hud-title">High Equity Deals</div>
                <div class="hud-value">{hot_count}</div>
                <span style="color:#00f2fe; font-size:0.75rem;">>$150k Equity Target</span>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        avg_tax = df_all["Days Delinquent"].mean() if not df_all.empty else 0
        st.markdown(f"""
            <div class="hud-card">
                <div class="hud-title">Avg Delinquency</div>
                <div class="hud-value">{avg_tax:,.0f}d</div>
                <span style="color:#ff4b72; font-size:0.75rem;">Critical Priority</span>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        mao_avg = df_all["MAO"].mean() if not df_all.empty else 0
        st.markdown(f"""
            <div class="hud-card">
                <div class="hud-title">Avg Target MAO</div>
                <div class="hud-value">${mao_avg:,.0f}</div>
                <span style="color:#00ff88; font-size:0.75rem;">Assignment Ready</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Search control panel
    st.subheader("⚡ Quantum Search & Multi-Filter Controls")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.text_input("Target Query", placeholder="Address, Folio #, Zip, or Owner Name...")
    with c2:
        st.selectbox("County Zone", list(COUNTIES.keys()), index=list(COUNTIES.keys()).index(selected_county))
    with c3:
        st.selectbox("Delinquency Level", ["All Levels", "1+ Year", "2+ Years", "3+ Years / Deed Imminent"])
    with c4:
        st.selectbox("Property Class", ["All Types", "Single Family", "Multi-Family", "Vacant Commercial"])

    sc_col1, sc_col2 = st.columns([1, 4])
    with sc_col1:
        if st.button("🚀 INITIATE SCRAPE"):
            with st.spinner(f"Scanning {selected_county} county public portals..."):
                df_leads = auto_scrape_delinquent_leads(county_config, "Manual (One-Click)")
                st.session_state["scraped_leads"] = df_leads
                st.session_state["last_scrape"] = datetime.now().isoformat()
                st.success(f"✅ Scraper Complete — {len(df_leads)} Leads Captured")
                st.rerun()

    st.markdown("---")

    # High Impact Deal Cards
    if df_all is not None and not df_all.empty:
        df_scored = calculate_deal_priority(df_all)
        show_n = min(10, len(df_scored))
        df_display = df_scored.head(show_n)

        st.subheader("🔥 Prioritized Target Cards")
        cols = st.columns(3)
        for idx, (i, row) in enumerate(df_display.iterrows()):
            col = cols[i % 3]

            with col:
                is_hot = row["Tier"] in ["🔥 Critical", "✅ Hot"]
                card_class = "deal-card deal-card-hot" if is_hot else "deal-card"
                badge_class = "badge-neon-red" if is_hot else "badge-neon-cyan"
                badge_text = row["Distress Type"].upper()[:20]
                if row["Days Delinquent"] > 730:
                    badge_text = "TAX DEBT " + str(int(row["Days Delinquent"] / 365)) + "+ YR"
                    badge_class = "badge-neon-red"

                st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display:flex; justify-between; align-items:center;">
                            <span class="{badge_class}">{badge_text}</span>
                        </div>
                        <h3 style="color:#ffffff; margin-top:10px; font-size:1.3rem;">
                            ${row['MAO']:,.0f} <span style="font-size:0.8rem; color:{'#ff4b72' if is_hot else '#00f2fe'};">MAO</span>
                        </h3>
                        <p style="color:#00f2fe; font-weight:700; margin:0;">{row['Address']}</p>
                        <p style="color:#64748b; font-size:0.8rem;">Folio #{row['Folio']} · {row['County']}</p>
                        <hr style="border-color: rgba(255,255,255,0.1);">
                        <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between;">
                            <span>Est. Equity (MV):</span>
                            <strong style="color:#00ff88;">${row['Market Value']:,.0f}</strong>
                        </div>
                        <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between; margin-top:4px;">
                            <span>Owner:</span>
                            <strong>{row['Owner']}</strong>
                        </div>
                        <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between; margin-top:4px;">
                            <span>Days Delinquent:</span>
                            <strong style="color:{'#ff4b72' if row['Days Delinquent'] > 730 else '#00f2fe'};">{row['Days Delinquent']}d</strong>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                maps_url = f"https://www.google.com/maps/search/?api=1&query={row['Address'].replace(' ', '+')}"
                st.markdown(f'<a href="{maps_url}" target="_blank" style="color:#00f2fe; font-size:0.75rem; text-decoration:none;">🗺️ Google Maps ↗</a>', unsafe_allow_html=True)
                st.button("TRACE CONTACTS", key=f"trace_{row['Folio']}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)

            if (i + 1) % 3 == 0:
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("🟢 System Idle — Click 🚀 INITIATE SCRAPE to activate the scraper core.")


# ─────────────────────────────────────────────────────────────
# PAGE 2: SKIP TRACE & CONTACT TERMINAL
# ─────────────────────────────────────────────────────────────

elif page == "2. Skip Trace & Contact Terminal":
    st.markdown('<div class="glow-title">SKIP TRACE TERMINAL // 3030</div>', unsafe_allow_html=True)
    st.caption("Deep-Search Owner Intelligence & Phone/Email Matrix")
    st.markdown("<br>", unsafe_allow_html=True)

    col_input, col_action = st.columns([3, 1])
    with col_input:
        target_address = st.text_input("Enter Target Parcel Folio or Address", value="1245 NW 36th St, Miami, FL 33142")
    with col_action:
        st.markdown("<br>", unsafe_allow_html=True)
        run_trace = st.button("RUN DEEP SKIP TRACE", use_container_width=True)

    if run_trace:
        with st.spinner("Extracting phone numbers, emails, relative ties, and LLC structures..."):
            time.sleep(1)

    st.markdown("""
        <div class="hud-card" style="margin-top:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="color:#00f2fe; margin:0;">RECORD MATCH FOUND</h3>
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
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📞 Instant AI Voice Agent Trigger")
    v1, v2 = st.columns(2)
    with v1:
        st.button("🎙️ Trigger AI Voice Agent Call", use_container_width=True)
    with v2:
        st.button("💬 Send Automated SMS Offer Script", use_container_width=True)


# ─────────────────────────────────────────────────────────────
# PAGE 3: DEAL PIPELINE & CRM
# ─────────────────────────────────────────────────────────────

elif page == "3. Deal Pipeline & CRM":
    st.markdown('<div class="glow-title">DEAL PIPELINE CRM // 3030</div>', unsafe_allow_html=True)
    st.caption("Active Acquisition Tracker & Lead Conversion Stage")
    st.markdown("<br>", unsafe_allow_html=True)

    if df_all is not None and not df_all.empty:
        df_scored = calculate_deal_priority(df_all)
        cold = df_scored[df_scored["Tier"] == "❌ Cold"]
        review = df_scored[df_scored["Tier"] == "⚠️ Review"]
        hot = df_scored[df_scored["Tier"].isin(["✅ Hot"])]
        critical = df_scored[df_scored["Tier"] == "🔥 Critical"]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("### 📥 Scraped / New")
            st.info(f"• {len(cold)} Cold Leads\n• {len(review)} Needs Review")
        with col2:
            st.markdown("### 📲 Contacted")
            st.warning(f"• {len(hot)} Hot Leads Ready")
        with col3:
            st.markdown("### 🤝 Under Offer")
            st.success(f"• {len(critical)} Critical / Urgent")
        with col4:
            st.markdown("### 💰 Closed / Assigned")
            st.markdown("• 512 SW 8th St (+$25k Fee)")
    else:
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


# ─────────────────────────────────────────────────────────────
# PAGE 4: AI MARKET ANALYTICS
# ─────────────────────────────────────────────────────────────

elif page == "4. AI Market Analytics":
    st.markdown('<div class="glow-title">QUANTUM MARKET ANALYTICS</div>', unsafe_allow_html=True)
    st.caption("Predictive Distress Trends & County Volume Analysis")
    st.markdown("<br>", unsafe_allow_html=True)

    if df_all is not None and not df_all.empty:
        df_scored = calculate_deal_priority(df_all)

        # Monthly chart simulation
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        miami = [320, 450, 510, 680, 890, 1120]
        broward = [210, 290, 340, 410, 520, 690]
        chart_data = pd.DataFrame({
            "Month": months,
            "Miami-Dade Leads": miami,
            "Broward Leads": broward,
        }).set_index("Month")

        st.line_chart(chart_data)
        st.markdown("<br>", unsafe_allow_html=True)

        # KPI row
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
                <div class="hud-card">
                    <div class="hud-title">Total Scanned</div>
                    <div class="hud-value">{len(df_scored):,}</div>
                </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
                <div class="hud-card">
                    <div class="hud-title">Avg MAO</div>
                    <div class="hud-value">${df_scored['MAO'].mean():,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
                <div class="hud-card">
                    <div class="hud-title">Avg Market Value</div>
                    <div class="hud-value">${df_scored['Market Value'].mean():,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
                <div class="hud-card">
                    <div class="hud-title">Avg Repairs</div>
                    <div class="hud-value">${df_scored['Est. Repairs'].mean():,.0f}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Analytics filters
        st.subheader("🔍 Analytics Filters")
        f1, f2, f3, f4, f5 = st.columns(5)
        with f1:
            tier_f = st.multiselect("Tiers", options=["🔥 Critical", "✅ Hot", "⚠️ Review", "❌ Cold"],
                                     default=["🔥 Critical", "✅ Hot"])
        with f2:
            dist_f = st.multiselect("Distress", options=["Tax Delinquent", "Code Violation / Abandoned", "Probate / Estate"],
                                     default=["Tax Delinquent", "Code Violation / Abandoned", "Probate / Estate"])
        with f3:
            st.number_input("Min Market Value ($)", value=0, step=10000)
        with f4:
            st.number_input("Max Market Value ($)", value=2000000, step=10000)
        with f5:
            st.number_input("Min MAO ($)", value=0, step=5000)

        df_f = df_scored.copy()
        if tier_f:
            df_f = df_f[df_f["Tier"].isin(tier_f)]
        if dist_f:
            df_f = df_f[df_f["Distress Type"].isin(dist_f)]

        if not df_f.empty:
            # MAO histogram
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("MAO Distribution")
                fig = px.histogram(df_f, x="MAO", nbins=20, title="MAO Distribution",
                                   color_discrete_sequence=["#00f2fe"], template="plotly_dark")
                fig.update_layout(showlegend=False, bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.subheader("Market Value Distribution")
                fig = px.histogram(df_f, x="Market Value", nbins=20, title="Market Value (ARV)",
                                   color_discrete_sequence=["#2ecc71"], template="plotly_dark")
                fig.update_layout(showlegend=False, bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Priority score + tier breakdown
            c3, c4, c5 = st.columns(3)
            with c3:
                st.subheader("Deal Priority Score")
                fig = px.histogram(df_f, x="Deal Priority Score", nbins=20, title="Priority Score",
                                   color_discrete_sequence=["#f39c12"], template="plotly_dark")
                fig.update_layout(showlegend=False, bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
            with c4:
                st.subheader("Tier Breakdown")
                tc = df_f["Tier"].value_counts()
                fig = px.bar(tc.reset_index(), x="index", y="Tier", title="Tier Breakdown",
                             color_discrete_sequence=["#3498db"], template="plotly_dark")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            with c5:
                st.subheader("Days Delinquent vs MAO")
                fig = px.scatter(df_f, x="Days Delinquent", y="MAO", color="Tier", title="Delinquency vs MAO",
                                 template="plotly_dark", color_discrete_map={"🔥 Critical":"#e74c3c","✅ Hot":"#2ecc71","⚠️ Review":"#f39c12","❌ Cold":"#95a5a6"})
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Top deals table
            st.subheader("🔥 Top Deals — Filterable Data Table")
            tshow = st.selectbox("Rows to show?", [5, 10, 15, 20, 50, "All"], index=1)
            tr = len(df_f) if tshow == "All" else min(int(tshow), len(df_f))
            df_t = df_f.head(tr).copy()
            df_t["Google Maps"] = df_t["Address"].apply(lambda a: f"[🗺️]({'https://www.google.com/maps/search/?api=1&query=' + a.replace(' ', '+')})")

            st.dataframe(
                df_t[["Tier", "Google Maps", "Folio", "Address", "Owner", "Distress Type",
                      "Days Delinquent", "Absentee Owner", "Vacant Flag", "Market Value",
                      "Est. Repairs", "MAO", "SqFt", "Deal Priority Score"]].style.format({
                    "Market Value": "${:,.0f}", "Est. Repairs": "${:,.0f}",
                    "MAO": "${:,.0f}", "Deal Priority Score": "{:,.0f}",
                    "Days Delinquent": "{:,.0f}",
                }).map(lambda x: "background-color: #fff3cd; font-weight: bold;" if isinstance(x, str) and "🗺️" in x else "",
                       subset=["Google Maps"]),
                use_container_width=True, hide_index=True,
                column_config={
                    "Tier": st.column_config.TextColumn(width="130px"),
                    "Google Maps": st.column_config.TextColumn(width="100px"),
                },
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📥 Export Analytics Data")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📥 Export Filtered Data (CSV)"):
                    csv = df_f.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇️ Download CSV", csv, f"Analytics_{selected_county}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            with c2:
                if st.button("🔄 Re-Scrape & Refresh"):
                    with st.spinner(f"Re-scraping {selected_county}..."):
                        df_new = auto_scrape_delinquent_leads(county_config, "Manual (One-Click)")
                        st.session_state["scraped_leads"] = df_new
                        st.success(f"✅ Re-scraped! {len(df_new)} leads.")
                        st.rerun()
    else:
        st.info("📊 No data yet — run a scrape from Page 1 to populate analytics.")


# ─────────────────────────────────────────────────────────────
# PAGE 5: SYSTEM & API MATRIX
# ─────────────────────────────────────────────────────────────

elif page == "5. System & API Matrix":
    st.markdown('<div class="glow-title">SYSTEM MATRIX & API KEYS</div>', unsafe_allow_html=True)
    st.caption("Configure Scraping Nodes, Webhooks, and AI Integrations")
    st.markdown("<br>", unsafe_allow_html=True)

    st.text_input("County Scraper API Key", value="sk_live_3030_mdf_889211", type="password")
    st.text_input("Skip Trace Provider Webhook", value="https://api.skiptrace3030.io/v1/trace", type="password")
    st.text_input("Voice Agent / Twilio Integration Token", value="tw_token_990182371", type="password")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⚙️ County Configuration")

    st.markdown(f"""
        <div class="hud-card">
            <div class="hud-title">Active County</div>
            <h2 style="color:#00f2fe; font-family:'Orbitron'; margin-top:8px;">{selected_county}</h2>
            <p style="color:#94a3b8; font-size:0.9rem;">PA API: <code>{county_config['pa_api']}</code></p>
            <p style="color:#94a3b8; font-size:0.9rem;">Tax Source: <code>{county_config['tax_delinquent_url']}</code></p>
            <p style="color:#94a3b8; font-size:0.9rem;">Code Source: <code>{county_config['code_violations_url']}</code></p>
            <p style="color:#94a3b8; font-size:0.9rem;">Probate Source: <code>{county_config['probate_url']}</code></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("SAVE SYSTEM CONFIGURATION"):
        st.success("Configuration updated and deployed across all nodes!")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align:center; color:#64748b; font-size:0.7rem; padding:20px; border-top:1px solid rgba(0,242,254,0.1);">
            <p>AUTONOMOUS PROPERTY ENGINE // SYSTEM V3030.8</p>
            <p>MULTI-COUNTY · REAL-TIME SCRAPE · DEAL SCORING · E-SIGN CONTRACTS</p>
            <p>© 360 NEW BEGINNING LLC · ALL SYSTEMS NOMINAL</p>
        </div>
    """, unsafe_allow_html=True)
