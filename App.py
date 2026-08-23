import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# CONFIG & SETUP
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="24_7 Real Estate Property Engine",
    page_icon="🏡",
    layout="wide"
)

# Dummy county dictionary for reference setup
COUNTIES = {
    "Miami-Dade": {"appraiser_url": "https://www.miamidade.gov/pa/"},
    "Broward": {"appraiser_url": "https://bcpa.net/"},
    "Palm Beach": {"appraiser_url": "https://www.pbcgov.org/papa/"}
}


# ─────────────────────────────────────────────────────────────
# FEATURE 1: EQUITY & NEGLECT MULTIPLIER
# ─────────────────────────────────────────────────────────────

def calculate_deal_priority(df):
    """
    Calculate a deal priority score safely with type sanitization.
    """
    if df.empty:
        return df

    df = df.copy()

    # Ensure numeric types to prevent calculation runtime errors
    df["Market Value"] = pd.to_numeric(df["Market Value"], errors="coerce").fillna(0)
    df["Est. Repairs"] = pd.to_numeric(df["Est. Repairs"], errors="coerce").fillna(0)
    df["Days Delinquent"] = pd.to_numeric(df["Days Delinquent"], errors="coerce").fillna(0)
    df["MAO"] = pd.to_numeric(df["MAO"], errors="coerce").fillna(0)

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
# FEATURE 2: CONTRACT GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_contract_text(details, buyer_name):
    """Generates a Florida Assignment of Real Estate Purchase & Sale Contract."""
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
# FEATURE 3: SIDEBAR — COUNTY SELECTION & ENGINE CONTROLS
# ─────────────────────────────────────────────────────────────

st.sidebar.header("⚙️ Engine Controls")

selected_county = st.sidebar.selectbox(
    "📍 Select County",
    options=list(COUNTIES.keys()),
    index=0,
)
county_config = COUNTIES[selected_county]

# Automatically clear cache if county selection changes
st.session_state.setdefault("current_county", selected_county)
if st.session_state["current_county"] != selected_county:
    st.session_state["scraped_leads"] = None
    st.session_state["current_county"] = selected_county

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
# MAIN DASHBOARD AREA
# ─────────────────────────────────────────────────────────────

st.title("🏡 24/7 Real Estate Property Engine")
st.write(f"Targeting County: **{selected_county}**")


# ─────────────────────────────────────────────────────────────
# FEATURE 4: FOOTER & LEGAL COMPLIANCE
# ─────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    f"🏡 24_7 Real Estate Property Engine · Multi-County · "
    f"Last scrape: {st.session_state.get('last_scrape', 'Never')} · "
    f"© WALTONEXLLC"
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
