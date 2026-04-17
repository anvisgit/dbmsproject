import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from app.db_connect import (
    get_customer, get_loan_types, get_all_customers,
    insert_loan, generate_emi_schedule, insert_credit_score, execute
)
from ml.models import run_full_prediction

st.set_page_config(page_title="Loan Application — LoanIQ", layout="wide")

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
                letter-spacing:0.08em; border-bottom:1px solid #30363d; padding-bottom:0.5rem; margin:1.75rem 0 1rem; }
.result-banner { border-radius:8px; padding:1.25rem 1.5rem; margin:1rem 0; border:1px solid; }
.approved { background:#1a3326; border-color:#2ea043; color:#3fb950; }
.rejected { background:#2a1215; border-color:#da3633; color:#f85149; }
.metric-box { background:#161b22; border:1px solid #30363d; border-radius:8px;
              padding:1rem; text-align:center; }
.metric-val { font-size:1.7rem; font-weight:700; }
.metric-lbl { font-size:0.68rem; color:#7d8590; text-transform:uppercase; letter-spacing:0.05em; margin-top:0.2rem; }
.stButton > button { background:#238636 !important; color:#fff !important; border:1px solid #2ea043 !important;
                     border-radius:6px !important; font-weight:500 !important; }
.stButton > button:hover { background:#2ea043 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### LoanIQ")
    st.markdown("---")
    st.markdown("**Loan Application**")
    st.caption("ML-powered credit assessment and automatic approval decision.")

st.markdown("# Loan Application")
st.caption("The system runs three ML models upon submission: credit score prediction, risk classification, and default probability estimation.")

try:
    loan_types_df = get_loan_types()
    customers_df  = get_all_customers()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if customers_df.empty:
    st.warning("No customers registered. Go to Customer Management first.")
    st.stop()

with st.form("loan_application"):
    st.markdown('<div class="section-head">Customer Selection</div>', unsafe_allow_html=True)
    cust_opts  = {f"#{r['customer_id']} — {r['name']} ({r.get('city','')})": r['customer_id'] for _, r in customers_df.iterrows()}
    cust_label = st.selectbox("Customer", list(cust_opts.keys()))
    customer_id = cust_opts[cust_label]

    st.markdown('<div class="section-head">Loan Details</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        lt_opts = {f"{r['type_name']}  (max Rs.{float(r['max_amount']):,.0f} @ {float(r['base_interest_rate'])}%)": r
                   for _, r in loan_types_df.iterrows()}
        lt_label  = st.selectbox("Loan Type", list(lt_opts.keys()))
        lt_data   = lt_opts[lt_label]
        loan_amount = st.number_input("Loan Amount (Rs.)", min_value=10000.0,
                                       max_value=float(lt_data["max_amount"]),
                                       value=min(500000.0, float(lt_data["max_amount"])), step=10000.0)
    with c2:
        tenure = st.selectbox("Tenure (months)", [12,18,24,36,48,60,84,120,180,240,300,360], index=4)
        interest_rate = st.number_input("Interest Rate (% p.a.)", min_value=5.0, max_value=25.0,
                                         value=float(lt_data["base_interest_rate"]), step=0.25)

    st.markdown('<div class="section-head">Guarantor (Optional)</div>', unsafe_allow_html=True)
    gc1, gc2, gc3 = st.columns(3)
    with gc1: g_name = st.text_input("Guarantor Name")
    with gc2: g_phone = st.text_input("Guarantor Phone")
    with gc3: g_rel = st.selectbox("Relationship", ["", "Spouse", "Parent", "Sibling", "Friend", "Other"])

    submitted = st.form_submit_button("Run Assessment", use_container_width=True)

if submitted:
    customer = get_customer(customer_id)
    if not customer:
        st.error("Customer not found.")
        st.stop()

    emp_type    = customer.get("employment_type", "Salaried") or "Salaried"
    m_income    = float(customer.get("monthly_income", 50000) or 50000)
    total_loans = int(customer.get("total_loans", 0) or 0)
    total_def   = int(customer.get("total_defaults", 0) or 0)

    with st.spinner("Running ML assessment..."):
        try:
            result = run_full_prediction(m_income, emp_type, total_loans, total_def,
                                         float(loan_amount), int(tenure), float(interest_rate))
        except FileNotFoundError:
            st.error("ML models not found. Run: python ml/models.py")
            st.stop()
        except Exception as ex:
            st.error(f"ML Error: {ex}")
            st.stop()

    score    = result["credit_score"]
    risk     = result["risk_level"]
    def_prob = result["default_probability"]
    approved = result["auto_approved"]

    if approved:
        st.markdown('<div class="result-banner approved"><strong>APPROVED</strong> — Credit score and default probability meet the approval threshold.</div>', unsafe_allow_html=True)
    else:
        reason = []
        if score <= 600:    reason.append(f"credit score {score} is below 600")
        if def_prob >= 0.4: reason.append(f"default probability {def_prob:.1%} exceeds 40%")
        st.markdown(f'<div class="result-banner rejected"><strong>REJECTED</strong> — {"; ".join(reason).capitalize()}.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head">Assessment Results</div>', unsafe_allow_html=True)
    rc = {"Low":"#3fb950","Medium":"#d29922","High":"#f85149"}.get(risk,"#2f81f7")
    pc = "#3fb950" if def_prob < 0.3 else ("#d29922" if def_prob < 0.5 else "#f85149")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#2f81f7">{score}</div><div class="metric-lbl">Predicted Credit Score</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{rc}">{risk}</div><div class="metric-lbl">Risk Classification</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:{pc}">{def_prob:.1%}</div><div class="metric-lbl">Default Probability</div></div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    gauge_layout = dict(paper_bgcolor="rgba(0,0,0,0)", font_color="#e6edf3",
                        height=240, margin=dict(l=20,r=20,t=40,b=10))
    with g1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=score, domain={"x":[0,1],"y":[0,1]},
            title={"text":"Credit Score","font":{"color":"#e6edf3","size":14}},
            gauge={"axis":{"range":[300,900],"tickcolor":"#e6edf3"},
                   "bar":{"color":"#2f81f7"},
                   "steps":[{"range":[300,600],"color":"#2a1215"},
                             {"range":[600,751],"color":"#2d1e0f"},
                             {"range":[751,900],"color":"#1a3326"}],
                   "threshold":{"line":{"color":"white","width":3},"thickness":0.8,"value":score}},
            number={"font":{"color":"#2f81f7","size":32}}))
        fig.update_layout(**gauge_layout)
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number", value=round(def_prob*100,1), domain={"x":[0,1],"y":[0,1]},
            title={"text":"Default Probability (%)","font":{"color":"#e6edf3","size":14}},
            gauge={"axis":{"range":[0,100],"ticksuffix":"%","tickcolor":"#e6edf3"},
                   "bar":{"color":pc},
                   "steps":[{"range":[0,30],"color":"#1a3326"},
                             {"range":[30,50],"color":"#2d1e0f"},
                             {"range":[50,100],"color":"#2a1215"}],
                   "threshold":{"line":{"color":"white","width":3},"thickness":0.8,"value":40}},
            number={"suffix":"%","font":{"color":pc,"size":32}}))
        fig2.update_layout(**gauge_layout)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-head">EMI Calculation</div>', unsafe_allow_html=True)
    r   = float(interest_rate)/1200.0
    emi = float(loan_amount)*r*(1+r)**int(tenure)/((1+r)**int(tenure)-1) if r>0 else float(loan_amount)/int(tenure)
    e1, e2, e3 = st.columns(3)
    e1.metric("Monthly EMI", f"Rs.{emi:,.2f}")
    e2.metric("Total Payable", f"Rs.{emi*int(tenure):,.2f}")
    e3.metric("Total Interest", f"Rs.{emi*int(tenure)-float(loan_amount):,.2f}")

    if approved:
        st.markdown("---")
        if st.button("Confirm and Disburse Loan", type="primary"):
            try:
                loan_id = insert_loan(customer_id, int(lt_data["loan_type_id"]),
                                      float(loan_amount), float(interest_rate), int(tenure))
                generate_emi_schedule(loan_id, float(loan_amount), float(interest_rate), int(tenure))
                if g_name.strip():
                    execute("INSERT INTO guarantor (loan_id, name, phone, relationship) VALUES (%s,%s,%s,%s)",
                            (loan_id, g_name.strip(), g_phone.strip() or None, g_rel or None))
                insert_credit_score(customer_id, score)
                st.success(f"Loan #{loan_id} disbursed. {tenure} EMI installments generated.")
            except Exception as ex:
                st.error(f"Could not save loan: {ex}")
    else:
        st.info("Application rejected. The customer may improve their credit profile and reapply.")
