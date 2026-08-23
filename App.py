from datetime import datetime
import time
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="🏡 24_7 REAL ESTATE PROPERTY ENGINE ",
    page_icon="🏡 ",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# CORE ENGINE HELPER FUNCTIONS (SCORING & CONTRACT GENERATION)
# ==============================================================================
def calculate_deal_priority(df):
    """Calculate a deal priority score safely with type sanitization."""
    if df.empty:
        return df

    df = df.copy()

    # Ensure numeric types to prevent calculation runtime errors
    df["Market Value"] = pd.to_numeric(
        df.get("Market Value", 0), errors="coerce"
    ).fillna(0)
    df["Est. Repairs"] = pd.to_numeric(
        df.get("Est. Repairs", 0), errors="coerce"
    ).fillna(0)
    df["Days Delinquent"] = pd.to_numeric(
        df.get("Days Delinquent", 0), errors="coerce"
    ).fillna(0)
    df["MAO"] = pd.to_numeric(df.get("MAO", 0), errors="coerce").fillna(0)

    df["Delinquency Score"] = df["Days Delinquent"].apply(
        lambda x: min(100, x / 1825 * 100) if x > 0 else 0
    )
    return df


# ==============================================================================
# INITIALIZE SESSION STATE FOR DEAL PIPELINE
# ==============================================================================
if "pipeline_leads" not in st.session_state:
    st.session_state.pipeline_leads = pd.DataFrame([
        {
            "Property Address": "100 NW 1st Ave, Miami, FL",
            "Owner Name": "John Doe",
            "Market Value": 300000,
            "Est. Repairs": 40000,
            "MAO": 170000,
            "Status": "Active Prospect",
            "Days Delinquent": 730,
        }
    ])

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
st.sidebar.title("🏡 Engine Navigation")
section = st.sidebar.radio(
    "Go to Section:",
    [
        "Section 1: Scraper Control",
        "Section 2: Skip Trace Terminal",
        "Section 3: Deal Pipeline CRM",
        "Section 4: ARV & MAO Calculator",
        "Section 5: Property Inspector",
    ],
)

# ==============================================================================
# SECTION 1: MULTI-COUNTY SCRAPER CONTROL
# ==============================================================================
if section == "Section 1: Scraper Control":
    st.title("Section 1: Multi-County Scraper Control")
    st.markdown("Automated public record scrapers for South Florida counties.")

    col1, col2 = st.columns(2)
    with col1:
        county = st.selectbox(
            "Target County Target:",
            [
                "Miami-Dade County, FL",
                "Broward County, FL",
                "Palm Beach County, FL",
            ],
        )
    with col2:
        record_type = st.selectbox(
            "Record Type Scraping:",
            [
                "Delinquent Taxes / Tax Certificates",
                "Probate / Estate Filings",
                "Code Violations",
            ],
        )

    if st.button("🚀 Launch Scraper Engine", use_container_width=True):
        st.success(
            f"Autonomous scraper initiated for **{county}** on **{record_type}** records!"
        )

# ==============================================================================
# SECTION 2: SKIP TRACE LEAD TERMINAL
# ==============================================================================
elif section == "Section 2: Skip Trace Terminal":
    st.title("Section 2: Skip Trace Lead Terminal")
    st.markdown("Batch or single lookup for property owner phone and address.")

    search_term = st.text_input(
        "Input Target Address or Owner Name:",
        placeholder="e.g. John Doe, 123 NW 12th Ave, Miami, FL",
    )

    if st.button("🔍 Execute Skip Trace", use_container_width=True):
        if search_term:
            st.info(f"Running API skip trace for: **{search_term}**...")
            time.sleep(1)
            st.success("Skip trace completed! Phone numbers and email pulled.")
        else:
            st.warning("Please enter a valid search term.")

# ==============================================================================
# SECTION 3: DEAL PIPELINE CRM
# ==============================================================================
elif section == "Section 3: Deal Pipeline CRM":
    st.title("Section 3: Deal Pipeline CRM")
    st.markdown("Manage incoming leads and trigger automated voice/SMS outreach.")

    # Calculate Priority Scores
    processed_df = calculate_deal_priority(st.session_state.pipeline_leads)

    st.dataframe(processed_df, use_container_width=True)

    if st.button("📞 Trigger AI Voice Call to Selected Leads"):
        st.success("AI Voice Agent dispatched to target lead batch!")

# ==============================================================================
# SECTION 4: DEAL CALCULATOR (ARV & MAO)
# ==============================================================================
elif section == "Section 4: ARV & MAO Calculator":
    st.title("Section 4: ARV & MAO Investment Calculator")
    st.markdown(
        "Evaluate property profitability using market value, repair estimates, and investor margin rules."
    )

    col1, col2 = st.columns(2)

    with col1:
        # Single Market Value slider/input from $0 to $1,000,000 in $1,000 increments
        market_value = st.number_input(
            "Market Value / ARV ($0 - $1,000,000)",
            min_value=0,
            max_value=1000000,
            value=300000,
            step=1000,
        )

        est_repairs = st.number_input(
            "Estimated Repair Costs ($)",
            min_value=0,
            max_value=500000,
            value=40000,
            step=500,
        )

    with col2:
        investor_rule = st.number_input(
            "Investor Rule (%)", min_value=50, max_value=90, value=70, step=1
        )

        # Calculation Logic: (ARV * Margin %) - Repairs
        rule_pct = investor_rule / 100.0
        calculated_mao = (market_value * rule_pct) - est_repairs
        estimated_profit = market_value * 0.15  # 15% net profit target

    st.divider()

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(
            label="Calculated Maximum Allowable Offer (MAO)",
            value=f"${max(0.0, calculated_mao):,.2f}",
        )
    with res_col2:
        st.metric(
            label="Estimated Profit Target (15%)",
            value=f"${max(0.0, estimated_profit):,.2f}",
        )

# ==============================================================================
# SECTION 5: PROPERTY INSPECTOR & HISTORY (WITH HIDDEN SYSTEM MATRIX)
# ==============================================================================
elif section == "Section 5: Property Inspector":
    st.title("Section 5: Property Inspector & Sale History")
    st.markdown("Visual property verification via satellite maps and county sales history.")

    address_input = st.text_input(
        "Property Address Search:",
        value="100 NW 1st Ave, Miami, FL",
        placeholder="Enter property address...",
    )

    st.divider()

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("Satellite View")
        encoded_address = urllib.parse.quote(
            address_input if address_input else "Miami Dade County FL"
        )
        map_url = f"https://maps.google.com/maps?q={encoded_address}&t=k&z=19&ie=UTF8&iwloc=&output=embed"

        st.components.v1.iframe(map_url, height=380, scrolling=False)

    with col2:
        st.subheader("Last Sale & County Records")
        st.info("""
        **Last Purchase Price:** $185,000.00  
        **Last Sale Date:** 04/12/2018  
        **Owner of Record:** John Doe  
        **Folio / Parcel ID:** 01-3136-000-0100  
        **Status:** Active Deal Lead
        """)

    st.divider()

    # HIDDEN ACCORDION FOR SYSTEM API MATRIX ADMIN SETTINGS
    with st.expander("⚙️ System API Matrix (Backend Admin Configuration)"):
        st.caption(
            "Keys are hidden from the primary view to prevent exposure."
        )
        st.text_input(
            "Scraper Node Webhook URL:",
            value="https://api.yourvps.com/scraper/v1",
            type="password",
        )
        st.text_input(
            "Skip Trace API Key:",
            value="sk_live_123456789abcdef",
            type="password",
        )
        st.text_input(
            "Telegram Bot Token:",
            value="123456789:ABCdefGHIjklMNOpqrs",
            type="password",
        )    df["Absentee Score"] = df.get("Absentee Owner", pd.Series([False]*len(df))).apply(lambda x: 30 if x else 0)
    df["Vacant Score"] = df.get("Vacant Flag", pd.Series([False]*len(df))).apply(lambda x: 20 if x else 0)

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


# ==============================================================================
# 3030 FUTURISTIC HUD STYLING (CUSTOM CSS)
# ==============================================================================
st.markdown("""
    <style>
    /* Import Futuristic Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

    /* Global Dark Cyber Theme */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #0d1117, #05070a, #020305);
        color: #e2e8f0;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Neon Titles & Headings */
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

    /* Futuristic HUD Metric Cards */
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

    /* Neon Property Deal Cards */
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

    /* Badges */
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

    /* Custom Input and Select Box Tweaks */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0b132b !important;
        color: #00f2fe !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        border-radius: 10px !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
        color: #020305 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(0, 242, 254, 0.8) !important;
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# NAVIGATION SIDEBAR (THE 5 PAGES + NEW CONTROLS)
# ==============================================================================
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
        "5. System & API Matrix"
    ]
)

st.sidebar.markdown("---")

# NEW FEATURE: ENGINE CONTROLS & FILTERS
st.sidebar.subheader("⚙️ Engine Controls")

selected_county = st.sidebar.selectbox(
    "📍 Target County",
    options=["Miami-Dade", "Broward", "Palm Beach"],
    index=0,
)

scrape_mode = st.sidebar.radio(
    "🔍 Scrape Mode",
    ["Manual (One-Click)", "Background Pipeline (Scheduled)"],
)

if scrape_mode == "Background Pipeline (Scheduled)":
    run_background = st.sidebar.checkbox("▶️ Run background pipeline", value=True)
    if run_background:
        st.sidebar.info("Background pipeline active: Scanning county public portals...")

st.sidebar.subheader("📊 Filter Leads")
min_market_val = st.sidebar.slider(
    "Min Market Value ($)", min_value=0, max_value=500000, value=0, step=10000
)
max_market_val = st.sidebar.slider(
    "Max Market Value ($)", min_value=0, max_value=2000000, value=500000, step=10000
)
show_tax_delinquent_only = st.sidebar.checkbox("Tax Delinquent Only", value=True)

st.sidebar.subheader("👤 Account / Entity")
buyer_entity_default = st.sidebar.text_input(
    "Wholesaler / Entity Name",
    value="360 New Beginning LLC",
    help="Assignor name on generated contracts.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='font-size:0.75rem; color:#64748b;'>
        <p>📡 <strong>System Status:</strong> <span style='color:#00ff88;'>ONLINE</span></p>
        <p>🎯 <strong>Active Counties:</strong> Miami-Dade, Broward, Palm Beach</p>
        <p>🏡 <strong>Scraper Core:</strong> Multi-Node Active</p>
    </div>
""", unsafe_allow_html=True)


# ==============================================================================
# PAGE 1: SCRAPER CONTROL & SEARCH HUB
# ==============================================================================
if page == "1. Scraper Control & Search":
    st.markdown('<div class="glow-title">SYSTEM SCRAPER HUB // 3030</div>', unsafe_allow_html=True)
    st.caption("Live Tax Delinquency, Probate & Distress Property Scanner")
    st.markdown("<br>", unsafe_allow_html=True)

    # Top HUD Stats
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("""
            <div class="hud-card">
                <div class="hud-title">Scrape Yield</div>
                <div class="hud-value">2,841</div>
                <span style="color:#00ff88; font-size:0.75rem;">+18.4% Live Feeds</span>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
            <div class="hud-card">
                <div class="hud-title">High Equity Deals</div>
                <div class="hud-value">849</div>
                <span style="color:#00f2fe; font-size:0.75rem;">>$150k Equity Target</span>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
            <div class="hud-card">
                <div class="hud-title">Avg Tax Debt</div>
                <div class="hud-value">$11,240</div>
                <span style="color:#ff4b72; font-size:0.75rem;">Critical Priority</span>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
            <div class="hud-card">
                <div class="hud-title">Automated Skip</div>
                <div class="hud-value">94.2%</div>
                <span style="color:#00ff88; font-size:0.75rem;">Contact Match Rate</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Search Control Panel
    st.subheader("🏡 Quantum Search & Multi-Filter Controls")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.text_input("Target Query", placeholder="Address, Folio #, Zip, or Owner Name...")
    with c2:
        st.selectbox("County Zone", ["Miami-Dade Zone", "Broward Zone", "Palm Beach Zone"])
    with c3:
        st.selectbox("Delinquency Level", ["All Levels", "1+ Year", "2+ Years", "3+ Years / Deed Imminent"])
    with c4:
        st.selectbox("Property Class", ["All Types", "Single Family", "Multi-Family", "Vacant Commercial"])

    sc_col1, sc_col2 = st.columns([1, 4])
    with sc_col1:
        if st.button("🚀 INITIATE SCRAPE"):
            st.toast("Scraper activated! Scanning county public portals...")

    st.markdown("---")

    # High Impact Deal Cards
    st.subheader("🔥 Prioritized Target Cards")
    dc1, dc2, dc3 = st.columns(3)

    with dc1:
        st.markdown("""
            <div class="deal-card deal-card-hot">
                <div style="display:flex; justify-between; align-items:center;">
                    <span class="badge-neon-red">CRITICAL • 3+ YR TAX DEBT</span>
                </div>
                <h3 style="color:#ffffff; margin-top:10px; font-size:1.3rem;">$24,800 <span style="font-size:0.8rem; color:#ff4b72;">TAX OWED</span></h3>
                <p style="color:#00f2fe; font-weight:700; margin:0;">1245 NW 36th St</p>
                <p style="color:#64748b; font-size:0.8rem;">Miami, FL 33142 • Folio #30-3115-002</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between;">
                    <span>Est. Equity:</span> <strong style="color:#00ff88;">$215,000</strong>
                </div>
                <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between; margin-top:4px;">
                    <span>Owner Status:</span> <strong>Absentee / Heir</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.button("TRACE CONTACTS", key="c1_btn", use_container_width=True)

    with dc2:
        st.markdown("""
            <div class="deal-card">
                <span class="badge-neon-cyan">TAX LIEN ISSUED</span>
                <h3 style="color:#ffffff; margin-top:10px; font-size:1.3rem;">$12,150 <span style="font-size:0.8rem; color:#00f2fe;">TAX OWED</span></h3>
                <p style="color:#00f2fe; font-weight:700; margin:0;">7820 NW 12th Ave</p>
                <p style="color:#64748b; font-size:0.8rem;">Miami, FL 33150 • Folio #30-2208-014</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between;">
                    <span>Est. Equity:</span> <strong style="color:#00ff88;">$190,000</strong>
                </div>
                <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between; margin-top:4px;">
                    <span>Owner Status:</span> <strong>Corporate / LLC</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.button("TRACE CONTACTS", key="c2_btn", use_container_width=True)

    with dc3:
        st.markdown("""
            <div class="deal-card deal-card-hot">
                <span class="badge-neon-red">PROBATE / DISTRESS</span>
                <h3 style="color:#ffffff; margin-top:10px; font-size:1.3rem;">$31,400 <span style="font-size:0.8rem; color:#ff4b72;">TAX OWED</span></h3>
                <p style="color:#00f2fe; font-weight:700; margin:0;">3101 Opa-locka Blvd</p>
                <p style="color:#64748b; font-size:0.8rem;">Opa-locka, FL 33054 • Folio #30-1102-088</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between;">
                    <span>Est. Equity:</span> <strong style="color:#00ff88;">$275,000</strong>
                </div>
                <div style="font-size:0.85rem; color:#cbd5e1; display:flex; justify-content:space-between; margin-top:4px;">
                    <span>Owner Status:</span> <strong>Estate / Deceased</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.button("TRACE CONTACTS", key="c3_btn", use_container_width=True)


# ==============================================================================
# PAGE 2: SKIP TRACE & CONTACT TERMINAL
# ==============================================================================
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
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📞 Instant AI Voice Agent Trigger")
    v1, v2 = st.columns(2)
    with v1:
        st.button("🎙️ Trigger AI Voice Agent Call", use_container_width=True)
    with v2:
        st.button("💬 Send Automated SMS Offer Script", use_container_width=True)


# ==============================================================================
# PAGE 3: DEAL PIPELINE & CRM
# ==============================================================================
elif page == "3. Deal Pipeline & CRM":
    st.markdown('<div class="glow-title">DEAL PIPELINE CRM // 3030</div>', unsafe_allow_html=True)
    st.caption("Active Acquisition Tracker & Lead Conversion Stage")
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
        st.markdown("• 512 SW 8th St (**+$25k Fee**)")

    st.markdown("---")

    # NEW FEATURE: CONTRACT GENERATOR
    st.subheader("📄 Automated Florida Assignment Contract Generator")
    with st.expander("📝 Generate Assignment Contract for Lead", expanded=False):
        c_fol = st.text_input("Folio Number", "30-3115-002")
        c_addr = st.text_input("Property Address", "1245 NW 36th St, Miami, FL 33142")
        c_own = st.text_input("Owner of Record", "Johnathan H. Doe")
        c_mv = st.number_input("Market Value ($)", value=315000)
        c_mao = st.number_input("Maximum Allowable Offer (MAO) ($)", value=185000)
        c_rep = st.number_input("Estimated Repairs ($)", value=45000)

        if st.button("🏡 GENERATE CONTRACT"):
            sample_details = {
                "Folio": c_fol,
                "Address": c_addr,
                "Owner": c_own,
                "Market Value": c_mv,
                "MAO": c_mao,
                "Est. Repairs": c_rep,
                "County": selected_county,
                "Zip Code": "33142",
                "SqFt": 1850,
            }
            contract = generate_contract_text(sample_details, buyer_entity_default)
            st.code(contract, language="text")
            st.download_button(
                label="📥 Download Contract Text",
                data=contract,
                file_name=f"Assignment_Contract_{c_fol}.txt",
                mime="text/plain",
            )


# ==============================================================================
# PAGE 4: AI MARKET ANALYTICS
# ==============================================================================
elif page == "4. AI Market Analytics":
    st.markdown('<div class="glow-title">QUANTUM MARKET ANALYTICS</div>', unsafe_allow_html=True)
    st.caption("Predictive Distress Trends & County Volume Analysis")
    st.markdown("<br>", unsafe_allow_html=True)

    chart_data = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "Miami-Dade Leads": [320, 450, 510, 680, 890, 1120],
        "Broward Leads": [210, 290, 340, 410, 520, 690]
    }).set_index("Month")

    st.line_chart(chart_data)


# ==============================================================================
# PAGE 5: SYSTEM & API MATRIX
# ==============================================================================
elif page == "5. System & API Matrix":
    st.markdown('<div class="glow-title">SYSTEM MATRIX & API KEYS</div>', unsafe_allow_html=True)
    st.caption("Configure Scraping Nodes, Webhooks, and AI Integrations")
    st.markdown("<br>", unsafe_allow_html=True)

    st.text_input("County Scraper API Key", value="sk_live_3030_mdf_889211", type="password")
    st.text_input("Skip Trace Provider Webhook", value="https://api.skiptrace3030.io/v1/trace", type="password")
    st.text_input("Voice Agent / Twilio Integration Token", value="tw_token_990182371", type="password")

    if st.button("SAVE SYSTEM CONFIGURATION"):
        st.success("Configuration updated and deployed across all nodes!")


# ==============================================================================
# FOOTER & LEGAL COMPLIANCE
# ==============================================================================
st.markdown("---")
st.caption(
    f"🏡 24_7 Real Estate Property Engine 3030 · Multi-County · "
    f"Last scrape: {st.session_state.get('last_scrape', 'Live Feed Active')} · "
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
