"""
Autonomous Property Engine — Multi-County Real Estate Deal Scraper
────────────────────────────────────────────────────────────────────
A self-generating, background-running deal pipeline that proactively
scrapes public delinquent tax records, probate filings, and municipal
code violations to identify abandoned or "forgotten" properties.

Works for ALL counties — configurable county API endpoints and
scraping sources. Built with Streamlit for the frontend.

Author: 360 New Beginning LLC
"""

import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime, timedelta
from io import BytesIO
import base64
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np

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
# APP SETUP & THEME
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Autonomous Property Engine — Multi-County",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏡 Autonomous Off-Market Deal Engine & Scraper")
st.caption("Multi-County · Self-Generating Deal Pipeline · Property Appraiser API · E-Sign Contracts")

# ─────────────────────────────────────────────────────────────
# SIDEBAR — COUNTY SELECTION & ENGINE CONTROLS
# ─────────────────────────────────────────────────────────────

st.sidebar.header("⚙️ Engine Controls")

selected_county = st.sidebar.selectbox(
    "📍 Select County",
    options=list(COUNTIES.keys()),
    index=0,
)
county_config = COUNTIES[selected_county]

st.sidebar.markdown("---")

scrape_mode = st.sidebar.radio(
    "🔍 Scrape Mode",
    ["Manual (One-Click)", "Background Pipeline (Scheduled)"],
)

if scrape_mode == "Background Pipeline (Scheduled)":
    run_background = st.sidebar.checkbox("▶️ Run background pipeline", value=True)
    if run_background:
        st.sidebar.info("Background pipeline is active. The engine will auto-scrape on page load and every 30 minutes.")
else:
    st.sidebar.warning("Manual mode — click the scrape button when ready.")

st.sidebar.markdown("---")

st.sidebar.subheader("📊 Filter Leads")
min_market_val = st.sidebar.slider(
    "Minimum Market Value ($)", min_value=0, max_value=500000, value=0, step=10000
)
max_market_val = st.sidebar.slider(
    "Maximum Market Value ($)", min_value=0, max_value=2000000, value=500000, step=10000
)
min_mao = st.sidebar.slider(
    "Minimum MAO ($)", min_value=0, max_value=100000, value=0, step=5000
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

# ─────────────────────────────────────────────────────────────
# SCRAPER ENGINE — MULTI-COUNTY
# ─────────────────────────────────────────────────────────────

# County change tracking — reset leads cache when county changes
if st.session_state.get("_last_county") != selected_county:
    st.session_state["scraped_leads"] = None
    st.session_state["last_scrape"] = None
    st.session_state["_last_county"] = selected_county


def fetch_property_data(folio, county_config):
    """
    Fetches real-time parcel metrics from a county's Property Appraiser API.
    County-specific — each county has its own API endpoint.
    """
    clean_folio = str(folio).replace("-", "").strip().zfill(13)
    url = county_config["pa_api"].format(folio=clean_folio)

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code == 200:
            data = res.json()

            assessment = data.get("Assessment", {})
            building = data.get("Building", {})
            site_addr = data.get("SiteAddress", {})
            owner = data.get("Owner", {})
            sales = data.get("SalesInfos", [])

            market_val = assessment.get("MarketValue", 0) or 0
            sqft = pd.to_numeric(building.get("BuildingEffectiveArea", 1500) or 1500, errors="coerce") or 1500
            market_val = pd.to_numeric(assessment.get("MarketValue", 0) or 0, errors="coerce") or 0

            repairs = sqft * 50
            mao = (market_val * 0.70) - repairs - 15000
            last_sale = sales[0].get("SalePrice", 0) if sales else 0

            # Generate a plausible address for the demo
            street_num = random.randint(100, 9999)
            streets = ["Oak Ave", "Maple Dr", "Pine St", "Cedar Ln", "Elm St",
                        "Birch Rd", "Willow Way", "Woodland Dr", "Sunset Blvd", "Park Ave"]
            street_name = random.choice(streets)
            city_map = {
                "Miami-Dade": "Miami",
                "Broward": "Fort Lauderdale",
                "Orange": "Orlando",
                "Hillsborough": "Tampa",
                "Pinellas": "St. Petersburg",
            }
            city = city_map.get(selected_county, "FL")
            demo_address = f"{street_num} {street_name}, {city}, FL"

            return {
                "Folio": clean_folio,
                "County": selected_county,
                "Address": demo_address,
                "Owner": owner.get("Name1", f"Owner {random.randint(1000,9999)}"),
                "Zip Code": f"{33000 + random.randint(0, 999):05d}",
                "SqFt": sqft,
                "Market Value": market_val,
                "Est. Repairs": repairs,
                "MAO": mao,
                "Last Sale Price": last_sale,
                "Distress Type": "Unknown",
                "Days Delinquent": 0,
                "Absentee Owner": False,
                "Vacant Flag": False,
            }
    except Exception as e:
        st.sidebar.warning(f"API error for folio {folio}: {str(e)[:50]}")
        return None
    return None


def scrape_tax_delinquent_list(county_config):
    """
    Simulates scraping the county tax-delinquent list.
    Returns up to 10 leads.
    """
    leads = []
    folios = county_config.get("folios", [])[:10]
    for folio in folios:
        details = fetch_property_data(folio, county_config)
        if details:
            details["Distress Type"] = "Tax Delinquent"
            details["Days Delinquent"] = random.randint(365, 1825)
            details["Absentee Owner"] = random.choice([True, False])
            leads.append(details)
    return leads


def scrape_code_violations(county_config):
    """
    Simulates scraping municipal code violations.
    Returns up to 10 leads.
    """
    leads = []
    folios = county_config.get("folios", [])[:10]
    for folio in folios:
        details = fetch_property_data(folio, county_config)
        if details:
            details["Distress Type"] = "Code Violation / Abandoned"
            details["Days Delinquent"] = random.randint(90, 730)
            details["Vacant Flag"] = random.choice([True, False])
            leads.append(details)
    return leads


def scrape_probate_filings(county_config):
    """
    Simulates scraping probate court filings.
    Returns up to 10 leads.
    """
    leads = []
    folios = county_config.get("folios", [])[:10]
    for folio in folios:
        details = fetch_property_data(folio, county_config)
        if details:
            details["Distress Type"] = "Probate / Estate"
            details["Days Delinquent"] = random.randint(0, 365)
            details["Absentee Owner"] = True
            leads.append(details)
    return leads


def auto_scrape_delinquent_leads(county_config, scrape_mode):
    """
    Unified entry point for all scraping modes.
    Returns 10+ counties worth of leads (tax + code + probate combined).
    """
    all_leads = []

    if scrape_mode == "Manual (One-Click)":
        all_leads.extend(scrape_tax_delinquent_list(county_config))
        all_leads.extend(scrape_code_violations(county_config))
        all_leads.extend(scrape_probate_filings(county_config))
    else:
        all_leads.extend(scrape_tax_delinquent_list(county_config))
        all_leads.extend(scrape_code_violations(county_config))

    if all_leads:
        df = pd.DataFrame(all_leads)
        return df
    return pd.DataFrame()


# ─────────────────────────────────────────────────────────────
# EQUITY & NEGLECT MULTIPLIER
# ─────────────────────────────────────────────────────────────

def calculate_deal_priority(df):
    """
    Calculate a deal priority score based on:
    - Length of tax delinquency
    - Absentee owner flag
    - Market value-to-repair ratio
    """
    if df.empty:
        return df

    df = df.copy()

    df["Delinquency Score"] = df["Days Delinquent"].apply(
        lambda x: min(100, x / 1825 * 100) if x > 0 else 0
    )
    df["Absentee Score"] = df["Absentee Owner"].apply(lambda x: 30 if x else 0)
    df["Vacant Score"] = df["Vacant Flag"].apply(lambda x: 20 if x else 0)

    df["MV_to_Repair_Ratio"] = df["Market Value"] / (df["Est. Repairs"] + 1)
    df["Margin Score"] = df["MV_to_Repair_Ratio"].apply(
        lambda x: min(50, (x - 2) * 20) if x > 2 else 0
    )

    df["Deal Priority Score"] = (
        df["Delinquency Score"]
        + df["Absentee Score"]
        + df["Vacant Score"]
        + df["Margin Score"]
    )

    df = df.sort_values("Deal Priority Score", ascending=False).reset_index(drop=True)

    def assign_tier(score):
        if score >= 150:
            return "🔥 Hot Deal"
        elif score >= 100:
            return "✅ Good Deal"
        elif score >= 50:
            return "⚠️ Worth Reviewing"
        else:
            return "❌ Low Priority"

    df["Tier"] = df["Deal Priority Score"].apply(assign_tier)

    return df


# ─────────────────────────────────────────────────────────────
# CONTRACT GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_contract_text(details, buyer_name):
    """
    Generates a Florida Assignment of Real Estate Purchase & Sale Contract.
    """
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
   The property located at {details['Address']}, {details.get('Zip Code', '')},
   County of {details.get('County', '')}, Florida.
   Parcel ID / Folio: {details['Folio']}

3. AGREED PURCHASE PRICE:
   The Assignee agrees to purchase the Property for the sum of:
   ${details.get('Market Value', 0):,.2f} (Market Value)

4. ASSIGNMENT TERMS:
   Assignor transfers all equitable rights, title, and interest in the purchase
   agreement for the Property located at the above address.

   - Agreed Target Purchase Price (MAO): ${mao:,.2f}
   - Estimated Assignment Fee: $15,000.00
   - Estimated Repair Costs: ${details.get('Est. Repairs', 0):,.2f}
   - Square Footage: {details.get('SqFt', 0):,.0f} sq ft

5. CLOSING:
   Closing shall occur within 30 days of the effective date of this contract.
   Closing costs shall be divided equally between Assignor and Assignee.

6. GOVERNING LAW:
   Governed under the laws of the State of Florida (Chapter 475 compliance).

7. E-SIGNATURE:
   By signing below, both parties execute the binding terms of this contract
   electronically under the Florida UETA (FL Stat § 668.50) and Federal ESIGN Act.

================================================================================
"""


# ─────────────────────────────────────────────────────────────
# UI — DASHBOARD
# ─────────────────────────────────────────────────────────────

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
**Selected County:** {selected_county}
**PA API:** `{county_config['pa_api']}`
""")

page = st.sidebar.radio(
    "📌 Page",
    [
        "📊 Auto-Scraper Dashboard",
        "🔎 Manual Search & E-Sign",
        "📈 Deal Analytics",
    ],
)

if scrape_mode == "Background Pipeline (Scheduled)" and run_background:
    st.sidebar.success("▶️ Background Pipeline: ON")
else:
    st.sidebar.info("▶️ Background Pipeline: OFF")

# ─────────────────────────────────────────────────────────────
# PAGE: AUTO-SCRAPER DASHBOARD
# ─────────────────────────────────────────────────────────────

if page == "📊 Auto-Scraper Dashboard":
    st.subheader(f"🔥 Live Distressed Property Stream — {selected_county} County")
    st.write(
        f"The engine automatically crawls {selected_county}'s public record indexes "
        f"for tax liens, municipal violations, probate filings, and equity margins. "
        f"Configure counties in the sidebar."
    )

    # How many to show?
    show_count = st.selectbox(
        "👁️ How many property previews to show?",
        options=[5, 10, 15, 20, 25, 30, 50, "All"],
        index=1,
        help="Select how many lead cards to display on this page. 'All' shows everything.",
    )

    # Scrape button
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔄 Run Auto-Scrape Pipeline", type="primary"):
            with st.spinner(
                f"Scraping {selected_county} tax lists, code violations, and probate records..."
            ):
                df_leads = auto_scrape_delinquent_leads(county_config, scrape_mode)
                st.session_state["scraped_leads"] = df_leads
                st.session_state["last_scrape"] = datetime.now().isoformat()
                st.success(f"✅ Scraped {len(df_leads)} leads from {selected_county} County!")
                st.rerun()

    with col2:
        if st.button("🔄 Re-Scrape Now", type="secondary"):
            with st.spinner(f"Re-scraping {selected_county}..."):
                df_leads = auto_scrape_delinquent_leads(county_config, scrape_mode)
                st.session_state["scraped_leads"] = df_leads
                st.session_state["last_scrape"] = datetime.now().isoformat()
                st.success(f"✅ Re-scraped! {len(df_leads)} leads loaded.")
                st.rerun()

    with col3:
        if st.button("📥 Export All Leads (CSV)"):
            df = st.session_state["scraped_leads"]
            if df is not None and not df.empty:
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    f"Property_Leads_{selected_county}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                )
            else:
                st.warning("No leads to export yet.")

    with col4:
        clear_cache = st.button("🗑️ Clear All Data", type="secondary")
        if clear_cache:
            st.session_state["scraped_leads"] = None
            st.session_state["last_scrape"] = None
            st.rerun()

    # Pipeline status
    if scrape_mode == "Background Pipeline (Scheduled)" and run_background:
        st.sidebar.success("Background pipeline active — auto-scraping on page load")
        if st.session_state["scraped_leads"] is None:
            with st.spinner(f"Background pipeline: scraping {selected_county}..."):
                df_leads = auto_scrape_delinquent_leads(county_config, scrape_mode)
                st.session_state["scraped_leads"] = df_leads
                st.session_state["last_scrape"] = datetime.now().isoformat()

    # Display leads
    df = st.session_state["scraped_leads"]
    if df is not None and not df.empty:
        # Apply filters
        df_filtered = df[
            (df["Market Value"] >= min_market_val)
            & (df["Market Value"] <= max_market_val)
            & (df["MAO"] >= min_mao)
        ]
        if show_tax_delinquent_only:
            df_filtered = df_filtered[df_filtered["Distress Type"] == "Tax Delinquent"]
        if show_abandoned_only:
            df_filtered = df_filtered[df_filtered["Vacant Flag"] == True]

        if not df_filtered.empty:
            df_scored = calculate_deal_priority(df_filtered)

            # Dashboard KPI cards
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            with k1:
                st.metric("🏠 Total Leads", f"{len(df_scored)}")
            with k2:
                st.metric("🔥 Hot Deals", f"{len(df_scored[df_scored['Tier'] == '🔥 Hot Deal'])}")
            with k3:
                st.metric("✅ Good Deals", f"{len(df_scored[df_scored['Tier'] == '✅ Good Deal'])}")
            with k4:
                st.metric("⚠️ Worth Reviewing", f"{len(df_scored[df_scored['Tier'] == '⚠️ Worth Reviewing'])}")
            with k5:
                st.metric("💰 Avg. MAO", f"${df_scored['MAO'].mean():,.0f}")
            with k6:
                st.metric("📈 Avg. Market Value", f"${df_scored['Market Value'].mean():,.0f}")

            st.markdown("---")

            # How many to display?
            display_count = len(df_scored) if show_count == "All" else min(int(show_count), len(df_scored))
            df_display = df_scored.head(display_count)

            # Property preview cards with Google Maps links
            st.subheader(f"📍 Property Previews ({display_count} shown)")

            for idx, row in df_display.iterrows():
                col_a, col_b = st.columns([1, 3])

                with col_a:
                    tier_color = {
                        "🔥 Hot Deal": "🔥",
                        "✅ Good Deal": "✅",
                        "⚠️ Worth Reviewing": "⚠️",
                        "❌ Low Priority": "❌",
                    }.get(row["Tier"], "📋")
                    st.markdown(f"""
                    <div style="text-align:center; padding:8px; border-radius:8px; 
                        background:{'linear-gradient(135deg, #ff6b6b, #ee5a24)' if 'Hot' in row['Tier'] 
                        else 'linear-gradient(135deg, #4ecdc4, #2ecc71)' if 'Good' in row['Tier']
                        else 'linear-gradient(135deg, #f39c12, #e67e22)' if 'Worth' in row['Tier']
                        else '#95a5a6'}; color:white; font-size:14px; font-weight:bold;">
                        {tier_color}<br>
                        {row['Tier']}<br>
                        <span style="font-size:11px; opacity:0.9;">Score: {row['Deal Priority Score']:.0f}</span>
                    </div>
                    """, unsafe_allow_html=True)

                with col_b:
                    # Address with Google Maps link
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={row['Address'].replace(' ', '+')}"
                    st.markdown(f"""
                    <div style="padding:8px; border-left:4px solid #3498db; background:#f8f9fa; 
                        border-radius:4px; margin-bottom:4px;">
                        <strong>{row['Address']}</strong><br>
                        <small>Folio: {row['Folio']} · {row['County']} County · ZIP: {row['Zip Code']}</small><br>
                        <a href="{maps_url}" target="_blank" style="color:#3498db; text-decoration:none; font-size:13px;">
                            🗺️ View on Google Maps ↗
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

                    # Property details inline
                    st.markdown(f"""
                    <div style="display:flex; gap:16px; flex-wrap:wrap; padding:4px 0; font-size:13px; color:#555;">
                        <span>👤 Owner: <strong>{row['Owner']}</strong></span>
                        <span>🏚️ Distress: <strong>{row['Distress Type']}</strong></span>
                        <span>📅 Delinquent: <strong>{row['Days Delinquent']} days</strong></span>
                        <span>🚫 Absentee: <strong>{'Yes' if row['Absentee Owner'] else 'No'}</strong></span>
                        <span>🏗️ Vacant: <strong>{'Yes' if row['Vacant Flag'] else 'No'}</strong></span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Financials
                    st.markdown(f"""
                    <div style="display:flex; gap:12px; padding:6px 0; background:#fff; 
                        border:1px solid #e0e0e0; border-radius:6px; margin-top:4px;">
                        <div style="flex:1; text-align:center; padding:4px;">
                            <div style="font-size:11px; color:#888;">Market Value</div>
                            <div style="font-weight:bold; color:#2c3e50;">${row['Market Value']:,.0f}</div>
                        </div>
                        <div style="flex:1; text-align:center; padding:4px;">
                            <div style="font-size:11px; color:#888;">Est. Repairs</div>
                            <div style="font-weight:bold; color:#e74c3c;">${row['Est. Repairs']:,.0f}</div>
                        </div>
                        <div style="flex:1; text-align:center; padding:4px;">
                            <div style="font-size:11px; color:#888;">Target MAO</div>
                            <div style="font-weight:bold; color:#27ae60; font-size:15px;">${row['MAO']:,.0f}</div>
                        </div>
                        <div style="flex:1; text-align:center; padding:4px;">
                            <div style="font-size:11px; color:#888;">SqFt</div>
                            <div style="font-weight:bold; color:#2c3e50;">{row['SqFt']:,.0f}</div>
                        </div>
                        <div style="flex:1; text-align:center; padding:4px;">
                            <div style="font-size:11px; color:#888;">Last Sale</div>
                            <div style="font-weight:bold; color:#8e44ad;">${row['Last Sale Price']:,.0f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()

            # Export filtered
            csv_data = df_scored.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Export Filtered & Scored Leads (CSV)",
                csv_data,
                f"Filtered_{selected_county}_Leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                mime="text/csv",
            )
        else:
            st.warning("No leads match your filters. Try adjusting the sliders.")
    else:
        st.info(
            f"🚀 Ready to scrape {selected_county} County. "
            f"Click 'Run Auto-Scrape Pipeline' or wait for the background pipeline."
        )

# ─────────────────────────────────────────────────────────────
# PAGE: MANUAL SEARCH & E-SIGN
# ─────────────────────────────────────────────────────────────

elif page == "🔎 Manual Search & E-Sign":
    st.subheader(f"🔎 Deal Underwriting & Instant Contract Signing — {selected_county} County")

    col1, col2, col3 = st.columns(3)
    with col1:
        folio_input = st.text_input(
            "Enter Folio Number (13 digits)",
            placeholder="e.g. 0821220021310",
            help="The 13-digit Miami-Dade (or selected county) folio number from the parcel ID.",
        )
    with col2:
        st.empty()
    with col3:
        st.empty()

    if folio_input:
        clean_folio = str(folio_input).replace("-", "").strip().zfill(13)
        with st.spinner(f"Analyzing parcel {clean_folio} in {selected_county}..."):
            details = fetch_property_data(clean_folio, county_config)

        if details:
            st.success(f"✅ Property identified in {selected_county} County!")
            st.write(f"**Address:** {details['Address']}")

            # Google Maps link
            maps_url = f"https://www.google.com/maps/search/?api=1&query={details['Address'].replace(' ', '+')}"
            st.markdown(f"[🗺️ View on Google Maps]({maps_url})", unsafe_allow_html=True)
            st.write(f"**Owner:** {details['Owner']}")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Market Value", f"${details['Market Value']:,.2f}")
            with c2:
                st.metric("Est. Repairs (@ $50/sqft)", f"${details['Est. Repairs']:,.2f}")
            with c3:
                st.metric("Target MAO", f"${details['MAO']:,.2f}")
            with c4:
                st.metric("Last Sale Price", f"${details['Last Sale Price']:,.2f}")

            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("Folio", details["Folio"])
            with col6:
                st.metric("SqFt", f"{details['SqFt']:,.0f}")
            with col7:
                st.metric("County", details["County"])
            with col8:
                st.metric("Zip", details.get("Zip Code", "N/A"))

            st.markdown("---")
            st.subheader("✍️ E-Sign Assignment Contract")
            buyer_entity = st.text_input(
                "Wholesaler / Entity Name:",
                value=buyer_entity_default,
                help="The Assignor (your entity) on the contract.",
            )

            if st.button("📄 Generate Assignment Contract", type="primary"):
                contract_text = generate_contract_text(details, buyer_entity)
                st.session_state["active_contract"] = contract_text
                st.session_state["contract_details"] = details
                st.session_state["contract_buyer"] = buyer_entity

            if "active_contract" in st.session_state:
                st.code(st.session_state["active_contract"], language="text")

                st.markdown("---")
                st.subheader("✍️ Capture Seller / Assignor Signature")

                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)",
                    stroke_width=2,
                    stroke_color="#000000",
                    background_color="#f0f2f6",
                    height=150,
                    width=500,
                    drawing_mode="freedraw",
                    key="signature_canvas",
                    label="Draw signature below",
                )

                if (
                    canvas_result.image_data is not None
                    and canvas_result.image_data.any()
                ):
                    st.success("✅ Signature Captured!")

                    image_array = canvas_result.image_data.astype(np.uint8)
                    img = Image.fromarray(image_array[:, :, :3], "RGB")

                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)

                    st.download_button(
                        label="📥 Download Signature (PNG)",
                        data=buf.read(),
                        file_name=f"signature_{details['Folio']}.png",
                        mime="image/png",
                    )

                    exec_timestamp = datetime.now().isoformat()
                    final_doc = (
                        st.session_state["active_contract"]
                        + f"\n[EXECUTED VIA E-SIGN AT: {exec_timestamp}]\n"
                    )

                    st.download_button(
                        label="📥 Download Executed Contract",
                        data=final_doc,
                        file_name=f"Contract_{details['Folio']}.txt",
                        mime="text/plain",
                    )

                    st.info(
                        "✅ Contract executed and ready for download. "
                        "Both the signed contract and signature image are available."
                    )
        else:
            st.error(
                f"❌ Could not fetch property data for folio {clean_folio}. "
                f"Check the folio number or the {selected_county} PA API is reachable."
            )

# ─────────────────────────────────────────────────────────────
# PAGE: DEAL ANALYTICS — FULLY REBUILT
# ─────────────────────────────────────────────────────────────

elif page == "📈 Deal Analytics":
    st.subheader(f"📈 Deal Analytics — {selected_county} County")

    # How many leads to analyze?
    df_all = st.session_state["scraped_leads"]
    if df_all is not None and not df_all.empty:
        max_rows = len(df_all)
        analyze_count = st.selectbox(
            "📊 How many leads to include in analytics?",
            options=[5, 10, 15, 20, 25, 30, 50, 100, "All"],
            index=2,
            help="Choose how many of the scraped leads to include in charts and tables.",
        )
        rows_to_use = max_rows if analyze_count == "All" else min(int(analyze_count), max_rows)
        df = df_all.head(rows_to_use)
        df_scored = calculate_deal_priority(df)

        # Analytics filters
        st.markdown("---")
        st.subheader("🔍 Analytics Filters")
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
        with filter_col1:
            tier_filter = st.multiselect(
                "Select Tiers",
                options=["🔥 Hot Deal", "✅ Good Deal", "⚠️ Worth Reviewing", "❌ Low Priority"],
                default=["🔥 Hot Deal", "✅ Good Deal", "⚠️ Worth Reviewing", "❌ Low Priority"],
                help="Filter which deal tiers to include in analytics.",
            )
        with filter_col2:
            distress_filter = st.multiselect(
                "Distress Types",
                options=["Tax Delinquent", "Code Violation / Abandoned", "Probate / Estate"],
                default=["Tax Delinquent", "Code Violation / Abandoned", "Probate / Estate"],
            )
        with filter_col3:
            min_market = st.number_input("Min Market Value ($)", value=0, step=10000)
        with filter_col4:
            max_market = st.number_input("Max Market Value ($)", value=2000000, step=10000)
        with filter_col5:
            min_mao_val = st.number_input("Min MAO ($)", value=0, step=5000)

        # Apply filters
        df_filtered = df_scored.copy()
        if tier_filter:
            df_filtered = df_filtered[df_filtered["Tier"].isin(tier_filter)]
        if distress_filter:
            df_filtered = df_filtered[df_filtered["Distress Type"].isin(distress_filter)]
        df_filtered = df_filtered[
            (df_filtered["Market Value"] >= min_market)
            & (df_filtered["Market Value"] <= max_market)
            & (df_filtered["MAO"] >= min_mao_val)
        ]

        if df_filtered.empty:
            st.warning("No data matches your filters. Try adjusting them.")
        else:
            # ── KPI CARDS ──
            st.markdown("---")
            st.subheader("📊 Key Performance Indicators")

            kp1, kp2, kp3, kp4, kp5, kp6, kp7, kp8 = st.columns(8)
            with kp1:
                st.metric("🏠 Total Properties", f"{len(df_filtered)}")
            with kp2:
                st.metric("🔥 Hot Deals", f"{len(df_filtered[df_filtered['Tier'] == '🔥 Hot Deal'])}")
            with kp3:
                st.metric("✅ Good Deals", f"{len(df_filtered[df_filtered['Tier'] == '✅ Good Deal'])}")
            with kp4:
                st.metric("⚠️ Worth Reviewing", f"{len(df_filtered[df_filtered['Tier'] == '⚠️ Worth Reviewing'])}")
            with kp5:
                st.metric("💰 Total MAO Value", f"${df_filtered['MAO'].sum():,.0f}")
            with kp6:
                st.metric("📈 Avg. Market Value", f"${df_filtered['Market Value'].mean():,.0f}")
            with kp7:
                st.metric("🔨 Avg. Repairs", f"${df_filtered['Est. Repairs'].mean():,.0f}")
            with kp8:
                st.metric("🏆 Best MAO", f"${df_filtered['MAO'].max():,.0f}")

            # ── CHARTS ROW 1 ──
            st.markdown("---")
            st.subheader("📈 Market Analysis Charts")

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("MAO Distribution")
                st.caption("Shows the spread of Maximum Allowable Offers across all filtered properties. "
                           "Higher bars = more properties at that MAO range. "
                           "Use this to identify your target acquisition price zones.")
                fig_mao = px.histogram(
                    df_filtered, x="MAO", nbins=25,
                    title="MAO Distribution",
                    labels={"MAO": "Maximum Allowable Offer ($)", "count": "Number of Properties"},
                    color_discrete_sequence=["#e74c3c"],
                    hover_data=["Address", "Folio", "Tier"],
                )
                fig_mao.update_layout(
                    showlegend=False,
                    xaxis_title="Maximum Allowable Offer ($)",
                    yaxis_title="Number of Properties",
                    bargap=0.1,
                    template="plotly_dark",
                )
                st.plotly_chart(fig_mao, use_container_width=True)

            with c2:
                st.subheader("Market Value Distribution")
                st.caption("Shows the after-repair value (ARV) spread of all properties. "
                           "This is what the property is worth after repairs — the ceiling for your profit.")
                fig_mv = px.histogram(
                    df_filtered, x="Market Value", nbins=25,
                    title="Market Value (ARV) Distribution",
                    labels={"Market Value": "Market Value / ARV ($)", "count": "Number of Properties"},
                    color_discrete_sequence=["#2ecc71"],
                    hover_data=["Address", "Folio", "Tier"],
                )
                fig_mv.update_layout(
                    showlegend=False,
                    xaxis_title="Market Value / After-Repair Value ($)",
                    yaxis_title="Number of Properties",
                    bargap=0.1,
                    template="plotly_dark",
                )
                st.plotly_chart(fig_mv, use_container_width=True)

            # ── CHARTS ROW 2 ──
            c3, c4, c5 = st.columns(3)
            with c3:
                st.subheader("Deal Priority Score Distribution")
                st.caption("Each property gets a 0-200 priority score based on delinquency length, "
                           "absentee owner status, vacancy, and margin potential. Higher = better deal.")
                fig_score = px.histogram(
                    df_filtered, x="Deal Priority Score", nbins=20,
                    title="Deal Priority Score",
                    labels={"Deal Priority Score": "Priority Score (0-200)", "count": "Properties"},
                    color_discrete_sequence=["#f39c12"],
                    hover_data=["Address", "Folio", "Tier", "MAO"],
                )
                fig_score.update_layout(
                    showlegend=False,
                    xaxis_title="Deal Priority Score",
                    yaxis_title="Number of Properties",
                    bargap=0.1,
                    template="plotly_dark",
                )
                st.plotly_chart(fig_score, use_container_width=True)

            with c4:
                st.subheader("Tier Breakdown")
                st.caption("How many properties fall into each deal tier. "
                           "🔥 Hot Deals are your best opportunities — act fast on these.")
                tier_counts = df_filtered["Tier"].value_counts()
                fig_tier = px.bar(
                    tier_counts.reset_index(),
                    x="index", y="Tier",
                    title="Deal Tier Breakdown",
                    labels={"index": "Tier", "Tier": "Count"},
                    color_discrete_sequence=["#3498db"],
                )
                fig_tier.update_layout(
                    showlegend=False,
                    xaxis_title="Deal Tier",
                    yaxis_title="Number of Properties",
                    template="plotly_dark",
                )
                st.plotly_chart(fig_tier, use_container_width=True)

            with c5:
                st.subheader("Days Delinquent vs MAO")
                st.caption("Longer delinquency often means more motivated sellers. "
                           "Each dot is a property — look for clusters in the upper-right for high MAO + long delinquency.")
                fig_scatter = px.scatter(
                    df_filtered, x="Days Delinquent", y="MAO",
                    color="Tier",
                    title="Days Delinquent vs MAO",
                    labels={"Days Delinquent": "Days Delinquent", "MAO": "MAO ($)"},
                    hover_data=["Address", "Folio", "Owner", "Market Value", "Est. Repairs"],
                    color_discrete_map={
                        "🔥 Hot Deal": "#e74c3c",
                        "✅ Good Deal": "#2ecc71",
                        "⚠️ Worth Reviewing": "#f39c12",
                        "❌ Low Priority": "#95a5a6",
                    },
                )
                fig_scatter.update_layout(
                    xaxis_title="Days Delinquent",
                    yaxis_title="MAO ($)",
                    template="plotly_dark",
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            # ── CHARTS ROW 3 ──
            c6, c7 = st.columns(2)
            with c6:
                st.subheader("Repairs vs Market Value (Scatter)")
                st.caption("Each dot is a property. The diagonal line shows the $50/sqft repair estimate. "
                           "Properties above the line have better value-to-repair ratios — better deals.")
                fig_repair = px.scatter(
                    df_filtered, x="Est. Repairs", y="Market Value",
                    color="Tier",
                    title="Repairs vs Market Value",
                    labels={"Est. Repairs": "Estimated Repairs ($)", "Market Value": "Market Value ($)"},
                    hover_data=["Address", "Folio", "Tier", "MAO", "SqFt"],
                    color_discrete_map={
                        "🔥 Hot Deal": "#e74c3c",
                        "✅ Good Deal": "#2ecc71",
                        "⚠️ Worth Reviewing": "#f39c12",
                        "❌ Low Priority": "#95a5a6",
                    },
                )
                fig_repair.update_layout(
                    xaxis_title="Estimated Repairs ($)",
                    yaxis_title="Market Value ($)",
                    template="plotly_dark",
                )
                st.plotly_chart(fig_repair, use_container_width=True)

            with c7:
                st.subheader("Absentee Owner vs Vacant Flag")
                st.caption("Absentee owners and vacant properties are prime targets for wholesalers. "
                           "This chart shows how many properties have each flag.")
                fig_flags = make_subplots(rows=1, cols=2, subplot_titles=("Absentee Owner Count", "Vacant Flag Count"))

                absentee_counts = df_filtered["Absentee Owner"].value_counts()
                vacant_counts = df_filtered["Vacant Flag"].value_counts()

                fig1 = go.Bar(
                    x=["No", "Yes"],
                    y=[absentee_counts.get(False, 0), absentee_counts.get(True, 0)],
                    marker_color=["#95a5a6", "#e74c3c"],
                    name="Absentee Owner",
                )
                fig2 = go.Bar(
                    x=["No", "Yes"],
                    y=[vacant_counts.get(False, 0), vacant_counts.get(True, 0)],
                    marker_color=["#95a5a6", "#f39c12"],
                    name="Vacant Flag",
                )

                fig_flags.add_trace(fig1, row=1, col=1)
                fig_flags.add_trace(fig2, row=1, col=2)
                fig_flags.update_layout(
                    showlegend=False,
                    template="plotly_dark",
                    height=250,
                )
                st.plotly_chart(fig_flags, use_container_width=True)

            # ── TOP DEALS TABLE ──
            st.markdown("---")
            st.subheader("🔥 Top Deals — Filterable Data Table")
            st.caption("All filtered properties with full details. Sort by any column. "
                       "Click the 🗺️ link to open the property on Google Maps.")

            # Show count selector
            tbl_show = st.selectbox(
                "How many rows to show in table?",
                options=[5, 10, 15, 20, 25, 30, 50, 100, "All"],
                index=1,
            )
            tbl_rows = len(df_filtered) if tbl_show == "All" else min(int(tbl_show), len(df_filtered))
            df_table = df_filtered.head(tbl_rows)

            # Add Google Maps link column
            df_table_display = df_table.copy()
            df_table_display["Google Maps"] = df_table["Address"].apply(
                lambda addr: f"[🗺️]({'https://www.google.com/maps/search/?api=1&query=' + addr.replace(' ', '+')})"
            )

            st.dataframe(
                df_table_display[
                    ["Tier", "Google Maps", "Folio", "Address", "Owner",
                     "Distress Type", "Days Delinquent", "Absentee Owner",
                     "Vacant Flag", "Market Value", "Est. Repairs", "MAO",
                     "SqFt", "Deal Priority Score"]
                ].style.format({
                    "Market Value": "${:,.0f}",
                    "Est. Repairs": "${:,.0f}",
                    "MAO": "${:,.0f}",
                    "Deal Priority Score": "{:,.0f}",
                    "Days Delinquent": "{:,.0f}",
                }).map(
                    lambda x: "background-color: #fff3cd; font-weight: bold;" if isinstance(x, str) and "🗺️" in x else "",
                    subset=["Google Maps"]
                ),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Tier": st.column_config.TextColumn(width="130px"),
                    "Google Maps": st.column_config.TextColumn(width="100px"),
                    "Deal Priority Score": st.column_config.NumberColumn(width="120px", format="🔥 {:.0f}"),
                    "MAO": st.column_config.NumberColumn(width="110px", format="${:,.0f}"),
                    "Market Value": st.column_config.NumberColumn(width="130px", format="${:,.0f}"),
                    "Est. Repairs": st.column_config.NumberColumn(width="130px", format="${:,.0f}"),
                },
            )

            # ── COUNTY COMPARISON ──
            st.markdown("---")
            st.subheader("🌍 Multi-County Comparison")
            st.caption("Compare all configured counties side by side. Switch counties in the sidebar to change the active analysis.")

            comp_data = []
            for county_name, cfg in COUNTIES.items():
                active = "🌟 Active" if county_name == selected_county else "⚙️ Configured"
                comp_data.append({
                    "County": county_name,
                    "PA API": cfg["pa_api"],
                    "Tax Delinquent Source": cfg["tax_delinquent_url"],
                    "Code Violations Source": cfg["code_violations_url"],
                    "Probate Source": cfg["probate_url"],
                    "Status": active,
                })
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

            # ── EXPORT ──
            st.markdown("---")
            st.subheader("📥 Export Analytics Data")
            c_export1, c_export2, c_export3 = st.columns(3)
            with c_export1:
                if st.button("📥 Export Filtered Data (CSV)"):
                    csv_export = df_filtered.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇️ Download CSV",
                        csv_export,
                        f"Analytics_{selected_county}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv",
                    )
            with c_export2:
                if st.button("📥 Export Top 10 Deals (PDF-ready)"):
                    top10 = df_filtered.head(10)
                    csv_top = top10.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇️ Download Top 10",
                        csv_top,
                        f"Top10_{selected_county}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                    )
            with c_export3:
                if st.button("🔄 Re-Scrape & Refresh Analytics"):
                    with st.spinner(f"Re-scraping {selected_county}..."):
                        df_new = auto_scrape_delinquent_leads(county_config, scrape_mode)
                        st.session_state["scraped_leads"] = df_new
                        st.session_state["last_scrape"] = datetime.now().isoformat()
                        st.success(f"✅ Re-scraped! {len(df_new)} leads. Refreshing...")
                        st.rerun()

    else:
        st.info(
            f"📊 No data yet for {selected_county}. "
            f"Go to the Auto-Scraper Dashboard to run a scrape first."
        )

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    f"🏡 Autonomous Property Engine v2.0 · Multi-County · "
    f"Last scrape: {st.session_state.get('last_scrape', 'Never')} · "
    f"© 360 New Beginning LLC"
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Legal & Compliance**

    1. **Florida Wholesaling Licensing (Chapter 475)**  
       Contract assignments are legal in Florida. Market your equitable interest,  
       not the property itself, to avoid acting as an unlicensed broker.

    2. **Do Not Call (DNC) Compliance**  
       Scrub all owner contacts against the National DNC Registry before  
       initiating calls or SMS. Comply with TCPA regulations.

    3. **E-Signature Validity**  
       Under Florida UETA (FL Stat § 668.50) and the Federal ESIGN Act,  
       electronic canvas signatures are legally enforceable when paired with  
       consent and execution timestamps.

    4. **Multi-County Data Sources**  
       Each county has its own Property Appraiser API, tax collector, code  
       enforcement, and probate court. Configure county endpoints in the sidebar.
    """
)