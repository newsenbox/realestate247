import streamlit as st
import pandas as pd
import json

# ==========================================
# PAGE CONFIG & "3030" FUTURISTIC STYLING
# ==========================================
st.set_page_config(
    page_title="3030 Real Estate Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode & neon accents
st.markdown("""
    <style>
    .main {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    .stSidebar {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    h1, h2, h3 {
        color: #00f0ff !important;
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(90deg, #00f0ff 0%, #7000ff 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
    }
    .legal-footer {
        font-size: 0.75rem;
        color: #6b7280;
        border-top: 1px solid #1f2937;
        padding-top: 10px;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR NAVIGATION & TOOLS
# ==========================================
st.sidebar.title("⚡ 3030 Engine")
st.sidebar.caption("Real Estate Acquisition & Analytics")

# 5-Page Navigation
page = st.sidebar.radio(
    "Navigation", 
    ["Dashboard", "Property Inspector", "ARV/MAO Calculator", "Contract Generator", "Settings / Admin"]
)

st.sidebar.markdown("---")

# SIDEBAR MODULE: Investment Calculator Quick-Access
st.sidebar.subheader("🧮 Quick MAO Estimate")
sb_arv = st.sidebar.number_input("After Repair Value (ARV)", min_value=0, max_value=1000000, value=250000, step=5000)
sb_repairs = st.sidebar.number_input("Est. Repair Costs", min_value=0, max_value=250000, value=35000, step=2500)
sb_fee = st.sidebar.number_input("Wholesale Fee", min_value=0, max_value=100000, value=10000, step=1000)

# MAO Formula: (ARV * 70%) - Repairs - Fee
sb_mao = (sb_arv * 0.70) - sb_repairs - sb_fee
st.sidebar.metric(label="Max Allowable Offer (MAO)", value=f"${sb_mao:,.2f}")

st.sidebar.markdown("---")

# SIDEBAR MODULE: Legal Compliance & Disclaimers
st.sidebar.subheader("⚖️ Legal Compliance")
st.sidebar.info("""
**Florida Wholesaling Notice:** 
Ensure all contract assignments comply with FL Statute § 475. Options/assignments must transfer equitable interest only.

**DNC / TCPA:** Verify phone numbers against Do Not Call registries prior to automated outreach.
""")

# ==========================================
# MAIN CONTENT AREA
# ==========================================

# PAGE 1: DASHBOARD
if page == "Dashboard":
    st.title("📊 Real Estate Lead Dashboard")
    st.write("Overview of recent lead ingestion, tax delinquencies, and deal status.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Leads", "142", "+12 today")
    col2.metric("Avg. Equity", "48%", "High distress")
    col3.metric("Pending Contracts", "4", "2 awaiting e-sign")
    
    st.subheader("Recent Property Activity")
    dummy_data = pd.DataFrame({
        "Address": ["123 NW 10th Ave", "456 SW 8th St", "789 NE 125th St"],
        "County": ["Miami-Dade", "Miami-Dade", "Miami-Dade"],
        "Est. ARV": ["$320,000", "$450,000", "$280,000"],
        "Status": ["Tax Delinquent", "Pre-Foreclosure", "Cold Lead"]
    })
    st.dataframe(dummy_data, use_container_width=True)

# PAGE 2: PROPERTY INSPECTOR
elif page == "Property Inspector":
    st.title("🔍 Property Inspector")
    st.write("Evaluate property details and location context.")
    
    prop_address = st.text_input("Enter Property Address", "123 NW 10th Ave, Miami, FL")
    
    if prop_address:
        st.subheader(f"Inspection Target: {prop_address}")
        # Google Maps embed block
        map_url = f"https://maps.google.com/maps?q={prop_address.replace(' ', '%20')}&t=&z=15&ie=UTF8&iwloc=&output=embed"
        st.components.v1.iframe(map_url, height=400)

# PAGE 3: FULL ARV/MAO CALCULATOR
elif page == "ARV/MAO Calculator":
    st.title("🧮 Comprehensive ARV / MAO Calculator")
    st.write("Deep-dive financial breakdown for wholesale and buy-and-hold strategies.")
    
    col1, col2 = st.columns(2)
    with col1:
        arv = st.number_input("After Repair Value (ARV)", min_value=0, max_value=1000000, value=sb_arv, step=5000)
        repairs = st.number_input("Estimated Repairs", min_value=0, max_value=250000, value=sb_repairs, step=1000)
        rule_pct = st.slider("Investor Rule Target (%)", min_value=50, max_value=85, value=70) / 100.0
    
    with col2:
        fee = st.number_input("Desired Assignment Fee", min_value=0, max_value=100000, value=sb_fee, step=1000)
        closing_costs = st.number_input("Est. Closing Costs", min_value=0, max_value=50000, value=5000, step=500)
    
    calculated_mao = (arv * rule_pct) - repairs - fee - closing_costs
    
    st.markdown("---")
    st.subheader(f"Calculated Max Allowable Offer: :green[${calculated_mao:,.2f}]")
    
    st.json({
        "ARV": arv,
        "Target Rule": f"{rule_pct * 100}%",
        "Less Repairs": repairs,
        "Less Fee": fee,
        "Less Closing Costs": closing_costs,
        "Net MAO": calculated_mao
    })

# PAGE 4: CONTRACT GENERATOR
elif page == "Contract Generator":
    st.title("📝 Contract Generator")
    st.write("Generate standardized assignment and purchase agreements.")
    
    with st.form("contract_form"):
        seller = st.text_input("Seller Legal Name")
        buyer = st.text_input("Buyer / Assignee Legal Name")
        address = st.text_input("Property Legal Address")
        price = st.number_input("Agreed Purchase Price", min_value=0, value=150000)
        
        submitted = st.form_submit_button("Generate Agreement Draft")
        if submitted:
            st.success("Draft generated successfully!")
            st.code(f"""
AGREEMENT FOR PURCHASE AND SALE
--------------------------------
Seller: {seller}
Buyer: {buyer}
Property: {address}
Purchase Price: ${price:,.2f}

This contract is subject to clear title and equitable interest assignment rights...
            """, language="markdown")

# PAGE 5: SETTINGS / ADMIN
elif page == "Settings / Admin":
    st.title("⚙️ System Admin & API Toggles")
    st.write("Manage secure keys and background integrations.")
    
    admin_toggle = st.toggle("Enable Admin Mode")
    if admin_toggle:
        st.text_input("Retell AI API Key", type="password")
        st.text_input("ElevenLabs Key", type="password")
        st.text_input("Database SFTP Port", value="22")
        st.success("Admin configurations active.")
    else:
        st.warning("Admin mode locked. Toggle above to edit credentials.")

# ==========================================
# GLOBAL FOOTER
# ==========================================
st.markdown("""
<div class="legal-footer">
    <p>© 2026 3030 Property Engine. All rights reserved. | Built with Streamlit</p>
    <p><b>Legal & Compliance Notice:</b> Electronic signatures executed via this platform conform to the ESIGN Act and UETA regulations. All data scrapers and automated communication tools must abide by local, state, and federal laws regarding outreach and property acquisitions.</p>
</div>
""", unsafe_allow_html=True)
