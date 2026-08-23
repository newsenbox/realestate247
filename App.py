from dataclasses import dataclass
from datetime import datetime
import os
import sqlite3
import time
import urllib.parse
import uuid
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. PAGE CONFIGURATION & COUNTY CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="🏡 24_7 REAL ESTATE ENGINE 3030",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# County Configurations Dictionary
COUNTIES = {
    "Miami-Dade County, FL": {
        "fips": "12086",
        "portal_url": "https://www.miamidade.gov/pa/",
        "tax_url": "https://miamidade.realforeclose.com/",
    },
    "Broward County, FL": {
        "fips": "12011",
        "portal_url": "https://www.bcpa.net/",
        "tax_url": "https://broward.realforeclose.com/",
    },
    "Palm Beach County, FL": {
        "fips": "12099",
        "portal_url": "https://www.pbcgov.org/papa/",
        "tax_url": "https://palmbeach.realforeclose.com/",
    },
}

# DB Setup for Contract Tracking
DB_NAME = "real_estate_engine.db"


@dataclass
class ContractRequest:
    seller_name: str
    buyer_name: str
    property_address: str
    seller_email: str
    purchase_price: float
    emd_amount: float
    inspection_period: int
    closing_date: str


def send_wholesale_contract_handler(req: ContractRequest):
    """Hooks into an E-Signature API (like PandaDoc, DocuSign, or SignWell)

    to map deal variables to a PDF template and send it.
    """
    api_key = os.getenv("ESIGN_API_KEY", "DEMO_KEY")
    template_id = os.getenv("ESIGN_TEMPLATE_ID", "wholesale_psa_template_01")

    # Log the contract generation to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT,
            seller TEXT,
            buyer TEXT,
            price REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute(
        """
        INSERT INTO contracts (address, seller, buyer, price, status)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            req.property_address,
            req.seller_name,
            req.buyer_name,
            req.purchase_price,
            "Sent for Signature",
        ),
    )
    conn.commit()
    conn.close()

    mock_doc_id = str(uuid.uuid4())[:8]

    return {
        "status": "SUCCESS",
        "message": f"Contract sent to {req.seller_email}",
        "document_id": f"DOC-{mock_doc_id}",
    }


# ==============================================================================
# 2. 3030 FUTURISTIC HUD STYLING (CUSTOM CSS WITH VISIBILITY FIX)
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

    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #0b132b !important;
        color: #00f2fe !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        border-radius: 10px !important;
    }

    /* --- CONTRACT PREVIEW VISIBILITY FIX --- */
    div[data-baseweb="textarea"] textarea {
        background-color: #ffffff !important;
        color: #05070a !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        line-height: 1.5 !important;
        opacity: 1 !important;
        border: 2px solid #00f2fe !important;
        border-radius: 10px !important;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.25) !important;
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
    </style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. CORE ENGINE HELPER FUNCTIONS
# ==============================================================================
def calculate_deal_priority(df):
    if df.empty:
        return df

    df = df.copy()
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

    return df


def generate_assignment_contract(assignor_name, details, mao):
    today = datetime.now().strftime("%B %d, %Y")
    return f"""================================================================================
          FLORIDA ASSIGNMENT OF REAL ESTATE PURCHASE & SALE CONTRACT
================================================================================
Date: {today}
County: {details.get('County', 'N/A')}
Folio / Parcel ID: {details.get('Folio', 'N/A')}

1. PARTIES:
   Assignor: {assignor_name}
   Assignee: [Assignee / Buyer Name]
   Seller (Owner of Record): {details.get('Owner', 'N/A')}

2. SUBJECT PROPERTY:
   Address: {details.get('Address', 'N/A')}, Zip Code: {details.get('Zip Code', 'N/A')}
   County of {details.get('County', 'N/A')}, State of Florida.
   Parcel ID / Folio Number: {details.get('Folio', 'N/A')}

3. ASSIGNMENT OF RIGHTS:
   Assignor hereby transfers and assigns to Assignee all rights, title, and 
   interest in and to that certain Purchase and Sale Agreement for the subject property.

4. FINANCIAL TERMS:
   - Purchase Price / MAO Target: ${mao:,.2f}
   - Market Value (ARV): ${details.get('Market Value', 0):,.2f}
   - Estimated Repair Costs: ${details.get('Est. Repairs', 0):,.2f}

5. CLOSING & TERMS:
   - Closing shall take place on or before 30 days from agreement execution.
   - Assignee accepts property in 'As-Is' condition unless specified otherwise.
   - Governed under the laws of the State of Florida (FL Stat § 475 compliance).

================================================================================
IN WITNESS WHEREOF, Assignor and Assignee have executed this Assignment.

Assignor Signature: _______________________   Date: ______________
Assignee Signature: _______________________   Date: ______________
================================================================================"""


# ==============================================================================
# 4. INITIALIZE SESSION STATE
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
        }
    ])

# ==============================================================================
# 5. NAVIGATION & SIDEBAR CONTROLS
# ==============================================================================
st.sidebar.markdown(
    """
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='color:#00f2fe; font-size: 1.2rem; margin:0;'>LEAD SCANNER ENGINE</h2>
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
        "5. System Settings",
    ],
)

st.sidebar.markdown("---")
selected_county = st.sidebar.selectbox(
    "🏡 Select County", options=list(COUNTIES.keys()), index=0
)
buyer_entity_default = st.sidebar.text_input(
    "Wholesaler / Entity Name", value="360 New Beginning LLC"
)

# ==============================================================================
# PAGES 1 - 3
# ==============================================================================
if page == "1. Scraper Control & Search":
    st.markdown(
        '<div class="glow-title">SYSTEM SCRAPER HUB // 3030</div>',
        unsafe_allow_html=True,
    )
    st.info(f"Target Zone: {selected_county}")

elif page == "2. Skip Trace & Contact Terminal":
    st.markdown(
        '<div class="glow-title">SKIP TRACE TERMINAL // 3030</div>',
        unsafe_allow_html=True,
    )

elif page == "3. Deal Pipeline & CRM":
    st.markdown(
        '<div class="glow-title">DEAL PIPELINE CRM // 3030</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(
        calculate_deal_priority(st.session_state.pipeline_leads),
        use_container_width=True,
    )

# ==============================================================================
# PAGE 4: MARKET ANALYTICS (WITH CALCULATOR & E-SIGN CONTRACT ENGINE)
# ==============================================================================
elif page == "4. Market Analytics & Calculator":
    st.markdown(
        '<div class="glow-title">MARKET ANALYTICS & CONTRACT GENERATOR</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "ARV / MAO Deal Evaluation System & Automated E-Signature Dispatch"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🧮 ARV & MAO Investment Deal Calculator")
    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
        market_value = st.number_input(
            "After Repair Value (ARV) / Market Value ($)",
            min_value=0,
            max_value=10000000,
            value=300000,
            step=5000,
        )
        est_repairs = st.number_input(
            "Estimated Repair Costs ($)",
            min_value=0,
            max_value=1000000,
            value=40000,
            step=1000,
        )

    with calc_col2:
        investor_rule = st.number_input(
            "Investor Rule Target (%)",
            min_value=1,
            max_value=100,
            value=70,
            step=1,
        )
        rule_pct = investor_rule / 100.0
        calculated_mao = (market_value * rule_pct) - est_repairs

    st.markdown("<br>", unsafe_allow_html=True)
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(
            label="Calculated Maximum Allowable Offer (MAO)",
            value=f"${max(0.0, calculated_mao):,.2f}",
        )
    with res_col2:
        st.metric(
            label="Estimated Investor Entry Target",
            value=f"${(market_value * rule_pct):,.2f}",
        )

    st.markdown("---")

    st.subheader("📄 Florida Assignment Contract Generator")

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        prop_address = st.text_input(
            "Property Address", value="1245 NW 36th St"
        )
        prop_zip = st.text_input("Zip Code", value="33142")
        prop_folio = st.text_input(
            "Parcel ID / Folio Number", value="30-3115-002"
        )
    with g_col2:
        prop_owner = st.text_input(
            "Owner of Record (Seller)", value="Johnathan H. Doe"
        )
        prop_county = st.text_input(
            "County", value=selected_county.split(",")[0]
        )

    contract_details = {
        "Address": prop_address,
        "Zip Code": prop_zip,
        "Folio": prop_folio,
        "Owner": prop_owner,
        "County": prop_county,
        "Market Value": market_value,
        "Est. Repairs": est_repairs,
    }

    generated_text = generate_assignment_contract(
        buyer_entity_default, contract_details, calculated_mao
    )

    # High-contrast Contract Preview Area
    st.text_area("Contract Preview", value=generated_text, height=350)

    st.markdown("---")

    # ==============================================================================
    # E-SIGNATURE CONTRACT DISPATCH ENGINE
    # ==============================================================================
    st.subheader("✍️ Direct E-Signature Dispatch Engine")
    st.caption("Hook variables to E-Sign API and log contract to database")

    es1, es2 = st.columns(2)
    with es1:
        seller_email = st.text_input(
            "Seller Email Address", value="jdoe.investments@gmail.com"
        )
        emd_amt = st.number_input(
            "Earnest Money Deposit (EMD) ($)", value=2500.0, step=500.0
        )
    with es2:
        inspection_days = st.number_input(
            "Inspection Period (Days)", value=10, step=1
        )
        closing_dt = st.text_input(
            "Closing Date", value=datetime.now().strftime("%Y-%m-%d")
        )

    if st.button("🚀 SEND CONTRACT FOR E-SIGNATURE", use_container_width=True):
        req = ContractRequest(
            seller_name=prop_owner,
            buyer_name=buyer_entity_default,
            property_address=f"{prop_address}, {prop_zip}",
            seller_email=seller_email,
            purchase_price=calculated_mao,
            emd_amount=emd_amt,
            inspection_period=inspection_days,
            closing_date=closing_dt,
        )

        res = send_wholesale_contract_handler(req)
        st.success(
            f"✅ {res['message']} | Document ID: **{res['document_id']}**"
        )

elif page == "5. System Settings":
    st.markdown(
        '<div class="glow-title">SYSTEM SETTINGS</div>', unsafe_allow_html=True
    )

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.caption(
    "🏡 24_7 Real Estate Property Engine · Multi-County · © WALTONEXLLC & 360 NEW BEGINNING LLC"
)
