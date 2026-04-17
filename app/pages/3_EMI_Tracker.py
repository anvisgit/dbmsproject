import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from app.db_connect import (
    get_all_customers, get_loans_for_customer, get_emi_schedule,
    record_payment, mark_overdue_emis, auto_default_overdue, fetch_df
)

st.set_page_config(page_title="EMI Tracker — LoanIQ", layout="wide")

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
.loan-info { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:1.25rem 1.5rem; margin-bottom:1rem; }
.stat-row { display:flex; gap:1.5rem; flex-wrap:wrap; margin-top:0.8rem; }
.stat-box { background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:0.6rem 1rem; min-width:100px; text-align:center; }
.stat-val { font-size:1.3rem; font-weight:700; }
.stat-lbl { font-size:0.65rem; color:#7d8590; text-transform:uppercase; margin-top:0.1rem; }
.stButton > button { background:#238636 !important; color:#fff !important; border:1px solid #2ea043 !important;
                     border-radius:6px !important; font-weight:500 !important; }
.stButton > button:hover { background:#2ea043 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### LoanIQ")
    st.markdown("---")
    st.markdown("**EMI Tracker**")
    st.caption("View schedules, record payments, and monitor defaults.")

st.markdown("# EMI Tracker")

try:
    mark_overdue_emis()
except Exception:
    pass

try:
    customers_df = get_all_customers()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if customers_df.empty:
    st.warning("No customers found.")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    cust_opts   = {f"#{r['customer_id']} — {r['name']}": r["customer_id"] for _, r in customers_df.iterrows()}
    cust_label  = st.selectbox("Customer", list(cust_opts.keys()))
    customer_id = cust_opts[cust_label]

loans_df = get_loans_for_customer(customer_id)
with c2:
    if loans_df.empty:
        st.warning("This customer has no loans.")
        st.stop()
    loan_opts  = {f"Loan #{r['loan_id']} — {r['type_name']}  Rs.{float(r['loan_amount']):,.0f}  [{r['current_status']}]": r["loan_id"]
                  for _, r in loans_df.iterrows()}
    loan_label = st.selectbox("Loan", list(loan_opts.keys()))
    loan_id    = loan_opts[loan_label]

loan_row = loans_df[loans_df["loan_id"] == loan_id].iloc[0]
emi_df   = get_emi_schedule(loan_id)

if emi_df.empty:
    st.info("No EMI schedule found for this loan.")
    st.stop()

try:
    auto_default_overdue(loan_id)
except Exception:
    pass

paid    = (emi_df["status"] == "Paid").sum()
overdue = (emi_df["status"] == "Overdue").sum()
pending = (emi_df["status"] == "Pending").sum()
total   = len(emi_df)
pct     = paid / total if total > 0 else 0

sc_color = {"Active":"#3fb950","Closed":"#2f81f7","Defaulted":"#f85149"}.get(loan_row["current_status"],"#7d8590")

st.markdown(f"""
<div class="loan-info">
  <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;align-items:flex-start;">
    <div>
      <div style="font-size:1.1rem;font-weight:700;">Loan #{loan_id} — {loan_row['type_name']}</div>
      <div style="color:#7d8590;font-size:0.82rem;margin-top:0.2rem;">
        Rs.{float(loan_row['loan_amount']):,.2f} @ {float(loan_row['interest_rate']):.2f}% p.a. for {loan_row['tenure']} months
      </div>
    </div>
    <div style="font-size:0.8rem;font-weight:600;color:{sc_color};">{loan_row['current_status'].upper()}</div>
  </div>
  <div class="stat-row">
    <div class="stat-box"><div class="stat-val" style="color:#3fb950">{paid}</div><div class="stat-lbl">Paid</div></div>
    <div class="stat-box"><div class="stat-val" style="color:#f85149">{overdue}</div><div class="stat-lbl">Overdue</div></div>
    <div class="stat-box"><div class="stat-val" style="color:#7d8590">{pending}</div><div class="stat-lbl">Pending</div></div>
    <div class="stat-box"><div class="stat-val" style="color:#2f81f7">{total}</div><div class="stat-lbl">Total</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**Repayment Progress** — {paid}/{total} EMIs paid ({pct:.0%})")
st.progress(pct)

st.markdown('<div class="section-head">EMI Schedule</div>', unsafe_allow_html=True)

display = emi_df.copy()
display["due_date"]    = pd.to_datetime(display["due_date"]).dt.strftime("%Y-%m-%d")
display["emi_amount"]  = display["emi_amount"].apply(lambda x: f"Rs.{float(x):,.2f}")
display["paid_amount"] = display["paid_amount"].apply(lambda x: f"Rs.{float(x):,.2f}" if float(x) > 0 else "—")
display["payment_date"]= display["payment_date"].apply(lambda x: str(x)[:10] if pd.notna(x) else "—")
display["payment_mode"]= display["payment_mode"].fillna("—")
display = display.rename(columns={"emi_id":"EMI#","due_date":"Due Date","emi_amount":"EMI Amount",
                                   "status":"Status","paid_amount":"Paid Amount",
                                   "payment_date":"Payment Date","payment_mode":"Mode"})

def row_style(row):
    bg = {"Paid":"#1a3326","Overdue":"#2a1215","Pending":"#161b22"}.get(row["Status"],"#161b22")
    return [f"background-color:{bg};color:#e6edf3"] * len(row)

st.dataframe(display[["EMI#","Due Date","EMI Amount","Status","Paid Amount","Payment Date","Mode"]].style.apply(row_style, axis=1),
             use_container_width=True, hide_index=True)

st.markdown('<div class="section-head">Record Payment</div>', unsafe_allow_html=True)
payable = emi_df[emi_df["status"].isin(["Pending","Overdue"])].copy()

if payable.empty:
    st.success("All EMIs for this loan have been paid.")
else:
    payable["label"] = payable.apply(
        lambda r: f"EMI #{r['emi_id']}  |  Due: {str(r['due_date'])[:10]}  |  Rs.{float(r['emi_amount']):,.2f}  [{r['status']}]", axis=1)
    emi_map = dict(zip(payable["label"], payable["emi_id"]))

    with st.form("record_payment"):
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            emi_label = st.selectbox("Select EMI", list(emi_map.keys()))
            sel_emi   = emi_map[emi_label]
        with pc2:
            sel_row   = payable[payable["emi_id"]==sel_emi].iloc[0]
            amount    = st.number_input("Payment Amount (Rs.)", min_value=0.01,
                                         max_value=float(sel_row["emi_amount"])*1.5,
                                         value=float(sel_row["emi_amount"]), step=100.0)
        with pc3:
            mode = st.selectbox("Payment Mode", ["Online","UPI","Cheque","Cash"])
        if st.form_submit_button("Record Payment", use_container_width=True):
            try:
                record_payment(sel_emi, amount, mode)
                st.success(f"Payment of Rs.{amount:,.2f} recorded for EMI #{sel_emi} via {mode}.")
                st.rerun()
            except Exception as ex:
                st.error(f"Error: {ex}")

if overdue > 0:
    st.markdown("---")
    pen = fetch_df("SELECT COALESCE(SUM(p.penalty_amount),0) AS t FROM penalty p JOIN default_record dr ON dr.default_id=p.default_id WHERE dr.loan_id=%s", (loan_id,))
    pen_val = float(pen["t"].iloc[0]) if not pen.empty else 0
    st.warning(f"This loan has {overdue} overdue EMI(s). A penalty of Rs.{pen_val:,.2f} has been applied. Clear overdue payments to stop further charges.")
