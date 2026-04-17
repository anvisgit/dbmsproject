import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from app.db_connect import (
    get_customer, get_customer_credit_scores, get_latest_credit_score,
    get_loans_for_customer, insert_customer, get_all_customers
)

st.set_page_config(page_title="Customer Management — LoanIQ", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"] { font-family:'Inter',sans-serif; }
.stApp { background:#0d1117; color:#e6edf3; }
[data-testid="stSidebar"] { background:#161b22; border-right:1px solid #30363d; }
[data-testid="stSidebar"] * { color:#e6edf3 !important; }
.block-container { padding-top:2rem; }
h1,h2,h3 { color:#e6edf3; font-weight:600; }
.section-head { font-size:0.72rem; font-weight:600; color:#7d8590; text-transform:uppercase;
                letter-spacing:0.08em; border-bottom:1px solid #30363d; padding-bottom:0.5rem;
                margin:1.75rem 0 1rem; }
.profile { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:1.25rem 1.5rem; margin-bottom:1rem; }
.profile-name { font-size:1.3rem; font-weight:700; color:#e6edf3; }
.profile-sub  { font-size:0.82rem; color:#7d8590; margin-top:0.2rem; }
.meta-grid { display:flex; flex-wrap:wrap; gap:1.25rem; margin-top:1rem; }
.meta-item { min-width:130px; }
.meta-lbl  { font-size:0.68rem; color:#7d8590; text-transform:uppercase; letter-spacing:0.05em; }
.meta-val  { font-size:0.9rem;  color:#e6edf3; font-weight:500; margin-top:0.15rem; }
.score-chip { display:inline-block; font-size:0.75rem; font-weight:600; padding:3px 10px; border-radius:4px; margin-top:0.4rem; }
.chip-low  { background:#1a3326; color:#3fb950; }
.chip-med  { background:#2d1e0f; color:#d29922; }
.chip-high { background:#2a1215; color:#f85149; }
.stButton > button { background:#238636 !important; color:#fff !important; border:1px solid #2ea043 !important;
                     border-radius:6px !important; font-weight:500 !important; }
.stButton > button:hover { background:#2ea043 !important; }
.stTextInput input, .stNumberInput input, .stSelectbox select { background:#161b22 !important; color:#e6edf3 !important; border-color:#30363d !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### LoanIQ")
    st.markdown("---")
    st.markdown("**Customer Management**")
    st.caption("Search profiles, view credit history, register new customers.")

st.markdown("# Customer Management")

tab_search, tab_register, tab_all = st.tabs(["Search by ID", "Register New Customer", "All Customers"])

with tab_search:
    cust_id = st.number_input("Customer ID", min_value=1, step=1, value=1)
    if st.button("Search"):
        customer = get_customer(int(cust_id))
        if customer is None:
            st.error(f"No customer found with ID {cust_id}.")
        else:
            latest = get_latest_credit_score(int(cust_id))
            score  = latest["score_value"] if latest else "N/A"
            risk   = latest["risk_level"]  if latest else "Unknown"
            chip   = f'chip-{"low" if risk=="Low" else "med" if risk=="Medium" else "high"}'

            st.markdown(f"""
            <div class="profile">
              <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
                <div>
                  <div class="profile-name">{customer['name']}</div>
                  <div class="profile-sub">ID #{customer['customer_id']} &nbsp;|&nbsp; {customer.get('email','—')}</div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:0.68rem;color:#7d8590;text-transform:uppercase;">Credit Score</div>
                  <div style="font-size:1.8rem;font-weight:700;color:#2f81f7;">{score}</div>
                  <span class="score-chip {chip}">{risk} Risk</span>
                </div>
              </div>
              <div class="meta-grid">
                <div class="meta-item"><div class="meta-lbl">Date of Birth</div><div class="meta-val">{customer.get('dob','—')}</div></div>
                <div class="meta-item"><div class="meta-lbl">Phone</div><div class="meta-val">{customer.get('phone','—')}</div></div>
                <div class="meta-item"><div class="meta-lbl">Monthly Income</div><div class="meta-val">Rs.{float(customer.get('monthly_income',0)):,.0f}</div></div>
                <div class="meta-item"><div class="meta-lbl">Employment</div><div class="meta-val">{customer.get('employment_type','—')}</div></div>
                <div class="meta-item"><div class="meta-lbl">Company</div><div class="meta-val">{customer.get('company_name','—')}</div></div>
                <div class="meta-item"><div class="meta-lbl">City</div><div class="meta-val">{customer.get('city','—')} {customer.get('zip_code','')}</div></div>
                <div class="meta-item"><div class="meta-lbl">Total Loans</div><div class="meta-val">{customer.get('total_loans',0)}</div></div>
                <div class="meta-item"><div class="meta-lbl">Total Defaults</div><div class="meta-val">{customer.get('total_defaults',0)}</div></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-head">Credit Score History</div>', unsafe_allow_html=True)
            hist = get_customer_credit_scores(int(cust_id))
            if not hist.empty:
                cmap = {"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"}
                fig = go.Figure()
                fig.add_scatter(
                    x=hist["score_date"], y=hist["score_value"],
                    mode="lines+markers",
                    line=dict(color="#2f81f7", width=2),
                    marker=dict(size=8, color=[cmap.get(r,"#2f81f7") for r in hist["risk_level"]],
                                line=dict(width=1.5, color="#0d1117")),
                    hovertemplate="<b>%{x}</b><br>Score: %{y}<extra></extra>"
                )
                fig.add_hline(y=751, line_dash="dot", line_color="#3fb950", annotation_text="Low Risk (751+)")
                fig.add_hline(y=601, line_dash="dot", line_color="#d29922", annotation_text="Medium Risk (601+)")
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e6edf3", family="Inter"),
                    yaxis=dict(range=[250,950], gridcolor="#21262d", title="Score"),
                    xaxis=dict(gridcolor="#21262d"),
                    height=300, margin=dict(l=10,r=100,t=10,b=30), showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No credit score history available.")

            st.markdown('<div class="section-head">Loan History</div>', unsafe_allow_html=True)
            loans = get_loans_for_customer(int(cust_id))
            if not loans.empty:
                loans["loan_amount"]   = loans["loan_amount"].apply(lambda x: f"Rs.{float(x):,.2f}")
                loans["interest_rate"] = loans["interest_rate"].apply(lambda x: f"{float(x):.2f}%")
                loans = loans.rename(columns={"loan_id":"Loan ID","type_name":"Type","loan_amount":"Amount",
                                               "interest_rate":"Rate","tenure":"Tenure(mo)","current_status":"Status","disbursed_date":"Disbursed"})
                st.dataframe(loans[["Loan ID","Type","Amount","Rate","Tenure(mo)","Status","Disbursed"]],
                             use_container_width=True, hide_index=True)
            else:
                st.info("No loans on record.")

with tab_register:
    st.markdown("### Register New Customer")
    with st.form("register_customer"):
        c1, c2 = st.columns(2)
        with c1:
            name  = st.text_input("Full Name *")
            phone = st.text_input("Phone Number *")
        with c2:
            dob   = st.date_input("Date of Birth *", value=date(1990,1,1), min_value=date(1940,1,1), max_value=date(2005,12,31))
            email = st.text_input("Email Address *")

        c3, c4 = st.columns(2)
        with c3:
            monthly_income  = st.number_input("Monthly Income (Rs.) *", min_value=1000.0, max_value=10000000.0, value=50000.0, step=1000.0)
            employment_type = st.selectbox("Employment Type *", ["Salaried","Self-Employed","Business","Retired"])
        with c4:
            company_name = st.text_input("Company / Business Name")

        c5, c6, c7 = st.columns(3)
        with c5: street   = st.text_input("Street Address")
        with c6: city     = st.text_input("City")
        with c7: zip_code = st.text_input("ZIP Code")

        if st.form_submit_button("Register Customer", use_container_width=True):
            errors = [f for f, v in [("Name",name),("Phone",phone),("Email",email)] if not v.strip()]
            if errors:
                st.error(f"Required: {', '.join(errors)}")
            else:
                try:
                    new_id = insert_customer(name.strip(), dob, phone.strip(), email.strip(),
                                             monthly_income, employment_type, company_name.strip(),
                                             street.strip(), city.strip(), zip_code.strip())
                    st.success(f"Customer registered. New Customer ID: {new_id}")
                except Exception as ex:
                    st.error(f"Error: {ex}")

with tab_all:
    st.markdown("### All Customers")
    try:
        all_df = get_all_customers()
        search = st.text_input("Filter by name, city or email")
        if search:
            mask = (all_df["name"].str.contains(search, case=False, na=False) |
                    all_df["city"].str.contains(search, case=False, na=False) |
                    all_df["email"].str.contains(search, case=False, na=False))
            all_df = all_df[mask]
        all_df["monthly_income"] = all_df["monthly_income"].apply(lambda x: f"Rs.{float(x):,.0f}" if pd.notna(x) else "—")
        st.dataframe(all_df, use_container_width=True, hide_index=True)
        st.caption(f"{len(all_df)} record(s)")
    except Exception as e:
        st.error(str(e))
