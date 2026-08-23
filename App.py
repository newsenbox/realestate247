import time
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="24_7 REAL ESTATE PROPERTY ENGINE ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# CORE ENGINE HELPER FUNCTIONS (SCORING & CALCULATIONS)
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

    # Delinquency Score Calculation
    df["Delinquency Score"] = df["Days Delinquent"].apply(
        lambda x: min(100, x / 1825 * 100) if x > 0 else 0
    )

    # Cleaned Absentee Score Logic
    if "Absentee Owner" in df.columns:
        df["Absentee Score"] = df["Absentee Owner"].apply(
            lambda x: 100 if bool(x) else 0
        )
    else:
        df["Absentee Score"] = 0

    return df


# ==============================================================================
# INITIALIZE SESSION STATE FOR DEAL PIPELINE
# ==============================================================================
if "pipeline_leads" not in st.session_state:
    st.session_state.pipeline_leads = pd.DataFrame([
        {
            "Property Address": "1245 NW 36th St, Miami, FL",
            "Owner Name": "Johnathan H. Doe",
            "Market Value": 300000,
            "Est. Repairs": 40000,
            "MAO": 170000,
            "Status": "Active Prospect",
            "Days Delinquent": 1095,
            "Absentee Owner": True,
        },
        {
            "Property Address": "7820 NW 12th Ave, Miami, FL",
            "Owner Name": "Apex Assets LLC",
            "Market Value": 250000,
            "Est. Repairs": 35000,
            "MAO": 140000,
            "Status": "Tax Lien Issued",
            "Days Delinquent": 730,
            "Absentee Owner": True,
        },
        {
            "Property Address": "3101 Opa-locka Blvd, Opa-locka, FL",
            "Owner Name": "Estate of Mary Johnson",
            "Market Value": 380000,
            "Est. Repairs": 60000,
            "MAO": 206000,
            "Status": "Probate / Distress",
            "Days Delinquent": 1460,
            "Absentee Owner": True,
        },
    ])

# ==============================================================================
# 3030 FUTURISTIC HUD STYLING (CUSTOM CSS)
# ==============================================================================
st.markdown(
    """
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
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
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
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# NAVIGATION SIDEBAR (THE 5 PAGES)
# ==============================================================================
st.sidebar.markdown(
    """
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='color:#00f2fe; font-size: 1.2rem; margin:0;'>AUTONOMOUS ENGINE</h2>
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
        "4. AI Market Analytics",
        "5. System & API Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='font-size:0.75rem; color:#64748b;'>
        <p>📡 <strong>System Status:</strong> <span style='color:#00ff88;'>ONLINE</span></p>
        <p>🎯 <strong>Active Counties:</strong> Miami-Dade, Broward, Palm Beach</p>
        <p>⚡ <strong>Scraper Core:</strong> Multi-Node Active</p>
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
    st.caption("Live Tax Delinquency, Probate & Distress Property Scanner")
    st.markdown("<br>", unsafe_allow_html=True)

    # Top HUD Stats
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            """
            <div class="hud-card">
                <div class="hud-title">Scrape Yield</div>
                <div class="hud-value">2,841</div>
                <span style="color:#00ff88; font-size:0.75rem;">+18.4% Live Feeds</span>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            """
            <div class="hud-card">
                <div class="hud-title">High Equity Deals</div>
                <div class="hud-value">849</div>
                <span style="color:#00f2fe; font-size:0.75rem;">>$150k Equity Target</span>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            """
            <div class="hud-card">
                <div class="hud-title">Avg Tax Debt</div>
                <div class="hud-value">$11,240</div>
                <span style="color:#ff4b72; font-size:0.75rem;">Critical Priority</span>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            """
            <div class="hud-card">
                <div class="hud-title">Automated Skip</div>
                <div class="hud-value">94.2%</div>
                <span style="color:#00ff88; font-size:0.75rem;">Contact Match Rate</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Search Control Panel
    st.subheader("⚡ Quantum Search & Multi-Filter Controls")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.text_input(
            "Target Query",
            placeholder="Address, Folio #, Zip, or Owner Name...",
        )
    with c2:
        st.selectbox(
            "County Zone",
            ["Miami-Dade Zone", "Broward Zone", "Palm Beach Zone"],
        )
    with c3:
        st.selectbox(
            "Delinquency Level",
            [
                "All Levels",
                "1+ Year",
                "2+ Years",
                "3+ Years / Deed Imminent",
            ],
        )
    with c4:
        st.selectbox(
            "Property Class",
            [
                "All Types",
                "Single Family",
                "Multi-Family",
                "Vacant Commercial",
            ],
        )

    sc_col1, sc_col2 = st.columns([1, 4])
    with sc_col1:
        if st.button("🚀 INITIATE SCRAPE"):
            st.session_state["last_scrape"] = time.strftime("%H:%M:%S EST")
            st.toast("Scraper activated! Scanning county public portals...")

    st.markdown("---")

    # High Impact Deal Cards
    st.subheader("🔥 Prioritized Target Cards")
    dc1, dc2, dc3 = st.columns(3)

    with dc1:
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )
        st.button("TRACE CONTACTS", key="c1_btn", use_container_width=True)

    with dc2:
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )
        st.button("TRACE CONTACTS", key="c2_btn", use_container_width=True)

    with dc3:
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )
        st.button("TRACE CONTACTS", key="c3_btn", use_container_width=True)


# ==============================================================================
# PAGE 2: SKIP TRACE & CONTACT TERMINAL (WITH SATELLITE & COUNTY RECON)
# ==============================================================================
elif page == "2. Skip Trace & Contact Terminal":
    st.markdown(
        '<div class="glow-title">SKIP TRACE TERMINAL // 3030</div>',
        unsafe_allow_html=True,
    )
    st.caption("Deep-Search Owner Intelligence & Phone/Email Matrix")
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
        with st.spinner(
            "Extracting phone numbers, emails, relative ties, and LLC structures..."
        ):
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

    # PROPERTY INSPECTOR SATELLITE MAP & COUNTY SALES RECON
    st.subheader("🛰️ Property Optical Recon & Sales History")
    recon_col1, recon_col2 = st.columns([1.2, 1])

    with recon_col1:
        st.markdown("**Satellite Optical Map**")
        encoded_address = urllib.parse.quote(
            target_address if target_address else "Miami Dade County FL"
        )
        map_url = f"https://maps.google.com/maps?q={encoded_address}&t=k&z=19&ie=UTF8&iwloc=&output=embed"
        st.components.v1.iframe(map_url, height=320, scrolling=False)

    with recon_col2:
        st.markdown("**Last Sale & County Records**")
        st.info("""
        **Last Purchase Price:** $185,000.00  
        **Last Sale Date:** 04/12/2018  
        **Owner of Record:** Johnathan H. Doe  
        **Folio / Parcel ID:** 30-3115-002  
        **Status:** Active Deal Lead
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📞 Instant AI Voice Agent Trigger")
    v1, v2 = st.columns(2)
    with v1:
        if st.button("🎙️ Trigger AI Voice Agent Call", use_container_width=True):
            st.success("AI Voice Agent triggered and dispatched!")
    with v2:
        if st.button(
            "💬 Send Automated SMS Offer Script", use_container_width=True
        ):
            st.success("SMS Offer Script transmitted!")


# ==============================================================================
# PAGE 3: DEAL PIPELINE & CRM
# ==============================================================================
elif page == "3. Deal Pipeline & CRM":
    st.markdown(
        '<div class="glow-title">DEAL PIPELINE CRM // 3030</div>',
        unsafe_allow_html=True,
    )
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Lead Matrix Data & Priority Scoring")
    processed_df = calculate_deal_priority(st.session_state.pipeline_leads)
    st.dataframe(processed_df, use_container_width=True)


# ==============================================================================
# PAGE 4: AI MARKET ANALYTICS (WITH ARV & MAO CALCULATOR)
# ==============================================================================
elif page == "4. AI Market Analytics":
    st.markdown(
        '<div class="glow-title">QUANTUM MARKET ANALYTICS</div>',
        unsafe_allow_html=True,
    )
    st.caption("Predictive Distress Trends & County Volume Analysis")
    st.markdown("<br>", unsafe_allow_html=True)

    chart_data = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "Miami-Dade Leads": [320, 450, 510, 680, 890, 1120],
        "Broward Leads": [210, 290, 340, 410, 520, 690],
    }).set_index("Month")

    st.line_chart(chart_data)

    st.markdown("<br>", unsafe_allow_html=True)

    # ARV & MAO INVESTMENT CALCULATOR
    st.subheader("🧮 ARV & MAO Investment Deal Calculator")
    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
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

    with calc_col2:
        investor_rule = st.number_input(
            "Investor Rule (%)", min_value=50, max_value=90, value=70, step=1
        )

        rule_pct = investor_rule / 100.0
        calculated_mao = (market_value * rule_pct) - est_repairs
        estimated_profit = market_value * 0.15

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
# PAGE 5: SYSTEM & API MATRIX
# ==============================================================================
elif page == "5. System & API Matrix":
    st.markdown(
        '<div class="glow-title">SYSTEM MATRIX & API KEYS</div>',
        unsafe_allow_html=True,
    )
    st.caption("Configure Scraping Nodes, Webhooks, and AI Integrations")
    st.markdown("<br>", unsafe_allow_html=True)

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

    if st.button("SAVE SYSTEM CONFIGURATION"):
        st.success("Configuration updated and deployed across all nodes!")


# ==============================================================================
# FOOTER & LEGAL COMPLIANCE
# ==============================================================================
st.markdown("---")
st.caption(
    f"🏡 24_7 Real Estate Property Engine · Multi-County · "
    f"Last scrape: {st.session_state.get('last_scrape', 'Never')} · "
    f"© WALTONEXLLC & 360 NEW BEGINNING LLC"
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
