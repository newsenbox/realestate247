color_discrete_sequence=["#e74c3c"],
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


That's the full 819-line Python file — copy straight into your environment and run with streamlit run property_engine.py. (7/7)
