import streamlit as st
import pandas as pd
import plotly.express as px

# Page Setup
st.set_page_config(page_title="Autonomous Property Engine", layout="wide")

st.title("🏠 Autonomous Property Engine v2.0")

# Demo Counties Config
COUNTIES = {
    "Miami-Dade": {
        "pa_api": "https://api.miamidade.gov",
        "tax_delinquent_url": "https://miamidade.realforeclose.com",
        "code_violations_url": "https://miamidade.gov/code",
        "probate_url": "https://miamidade.clerk.org",
    },
    "Broward": {
        "pa_api": "https://api.bcpa.net",
        "tax_delinquent_url": "https://broward.realforeclose.com",
        "code_violations_url": "https://broward.org/code",
        "probate_url": "https://browardclerk.org",
    }
}

# Sidebar Selection
selected_county = st.sidebar.selectbox("Select County", list(COUNTIES.keys()))

# Demo Data
data = {
    "Tier": ["Tier 1", "Tier 1", "Tier 2"],
    "Folio": ["30-2131-001-0010", "30-2131-001-0020", "30-2131-001-0030"],
    "Address": ["123 Main St", "456 Ocean Dr", "789 Palm Ave"],
    "Owner": ["John Doe", "Jane Smith", "Estate of Bob Johnson"],
    "Distress Type": ["Tax Delinquent", "Probate", "Code Violation"],
    "Market Value": [350000.00, 520000.00, 280000.00],
    "MAO": [210000.00, 312000.00, 168000.00],
    "Est. Repairs": [45000.00, 60000.00, 35000.00],
    "Deal Priority Score": [92, 88, 75],
}

df_scored = pd.DataFrame(data)

# Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["📊 Analytics", "🔥 Top Deals", "⚙️ County Setup"])

with tab1:
    st.subheader("Maximum Allowable Offer (MAO) Distribution")
    fig_mao = px.histogram(
        df_scored, 
        x="MAO", 
        nbins=10, 
        color_discrete_sequence=["#e74c3c"]
    )
    fig_mao.update_layout(showlegend=False, xaxis_title="MAO ($)", yaxis_title="Count")
    st.plotly_chart(fig_mao, use_container_width=True)

with tab2:
    st.subheader("🔥 Top Deals by Priority Score")
    st.dataframe(
        df_scored.head(10)[
            ["Tier", "Folio", "Address", "Owner", "Distress Type",
             "Market Value", "MAO", "Deal Priority Score"]
        ].style.format({
            "Market Value": "${:,.2f}",
            "MAO": "${:,.2f}",
            "Deal Priority Score": "{:,.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

with tab3:
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Market Value", f"${df_scored['Market Value'].sum():,.2f}")
    with m2:
        st.metric("Avg. Market Value", f"${df_scored['Market Value'].mean():,.2f}")
    with m3:
        st.metric("Avg. MAO", f"${df_scored['MAO'].mean():,.2f}")
    with m4:
        st.metric("Avg. Repairs", f"${df_scored['Est. Repairs'].mean():,.2f}")
    with m5:
        st.metric("Total Leads", len(df_scored))

    st.markdown("---")
    st.subheader("County Comparison")

    county_data = []
    for county, config in COUNTIES.items():
        county_data.append({
            "County": county,
            "PA API": config["pa_api"],
            "Tax Delinquent Source": config["tax_delinquent_url"],
            "Code Violations Source": config["code_violations_url"],
            "Probate Source": config["probate_url"],
            "Status": "📡 Active" if county == selected_county else "⚙️ Configured",
        })
    st.dataframe(pd.DataFrame(county_data), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    f"Autonomous Property Engine v2.0 · Multi-County · {selected_county} · "
    f"Last scrape: {st.session_state.get('last_scrape', 'Never')} · "
    f"© 360 New Beginning LLC"
)

# ─────────────────────────────────────────────────────────────
# COMPLIANCE NOTES (sidebar)
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("---")
    st.subheader("⚖️ Legal & Compliance")
    st.caption("""
1. **Florida Wholesaling Licensing**: Contract assignments are legal in Florida under Chapter 475. 
   Ensure you market your equitable interest in the contract rather than acting as an unlicensed broker.

2. **DNC & TCPA Compliance**: Ensure all owner contacts scrub against National Do Not Call (DNC) lists 
   and comply with Telephone Consumer Protection Act (TCPA) regulations before initiating bulk calls/SMS.

3. **E-Signature Validity**: Under the Florida UETA (FL Stat § 668.50) and Federal ESIGN Act, 
   electronic canvas signatures hold full legal enforceability when paired with consent and execution timestamps.

4. **Multi-County Data Sources**: This engine pulls from county-specific Property Appraiser APIs, 
   tax delinquent lists, code enforcement databases, and probate court records. 
   Each county's data sources are configured in the COUNTIES dictionary at the top of this file.
    """)
