import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import subprocess, io
import zipfile
from app.db_connect import (
    get_loan_types, insert_loan_type, update_loan_type, delete_loan_type,
    get_risk_categories, insert_risk_category, update_risk_category, delete_risk_category,
    run_raw_sql, export_table_csv, fetch_df
)

st.set_page_config(page_title="Administration — LoanIQ", layout="wide")

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
.stButton > button { background:#238636 !important; color:#fff !important; border:1px solid #2ea043 !important;
                     border-radius:6px !important; font-weight:500 !important; }
.stButton > button:hover { background:#2ea043 !important; }
textarea { background:#161b22 !important; color:#e6edf3 !important; font-family:monospace !important; border-color:#30363d !important; }
.model-tile { background:#161b22; border:1px solid #30363d; border-radius:6px;
              padding:0.75rem; text-align:center; font-size:0.8rem; color:#7d8590; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### LoanIQ")
    st.markdown("---")
    st.markdown("**Administration**")
    st.caption("CRUD, SQL runner, ML retraining, data export.")

st.markdown("# Administration")

tab_lt, tab_rc, tab_sql, tab_ml, tab_export = st.tabs([
    "Loan Types", "Risk Categories", "SQL Runner", "ML Models", "Export"
])

with tab_lt:
    st.markdown('<div class="section-head">Existing Loan Types</div>', unsafe_allow_html=True)
    try:
        lt_df = get_loan_types()
        if not lt_df.empty:
            d = lt_df.copy()
            d["max_amount"]         = d["max_amount"].apply(lambda x: f"Rs.{float(x):,.2f}")
            d["base_interest_rate"] = d["base_interest_rate"].apply(lambda x: f"{float(x):.2f}%")
            st.dataframe(d, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(str(e))

    st.markdown('<div class="section-head">Add Loan Type</div>', unsafe_allow_html=True)
    with st.form("add_lt"):
        a1,a2,a3 = st.columns(3)
        with a1: new_name = st.text_input("Type Name *")
        with a2: new_rate = st.number_input("Base Interest Rate (%)", 1.0, 30.0, 10.0, 0.25)
        with a3: new_max  = st.number_input("Max Amount (Rs.)", 10000.0, 50000000.0, 500000.0, 10000.0)
        if st.form_submit_button("Add", use_container_width=True):
            if not new_name.strip():
                st.error("Name is required.")
            else:
                try:
                    insert_loan_type(new_name.strip(), new_rate, new_max)
                    st.success("Loan type added.")
                    st.rerun()
                except Exception as ex:
                    st.error(str(ex))

    st.markdown('<div class="section-head">Edit / Delete Loan Type</div>', unsafe_allow_html=True)
    try:
        lt_df = get_loan_types()
        if not lt_df.empty:
            opts = {f"#{r['loan_type_id']} — {r['type_name']}": r for _, r in lt_df.iterrows()}
            sel_label = st.selectbox("Select", list(opts.keys()), key="edit_lt")
            row = opts[sel_label]
            with st.form("edit_lt"):
                e1,e2,e3 = st.columns(3)
                with e1: e_name = st.text_input("Name", value=row["type_name"])
                with e2: e_rate = st.number_input("Rate (%)", 1.0, 30.0, float(row["base_interest_rate"]), 0.25)
                with e3: e_max  = st.number_input("Max Amount (Rs.)", 10000.0, 50000000.0, float(row["max_amount"]), 10000.0)
                b1,b2 = st.columns(2)
                with b1:
                    if st.form_submit_button("Save Changes", use_container_width=True):
                        try:
                            update_loan_type(row["loan_type_id"], e_name, e_rate, e_max)
                            st.success("Updated.")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
                with b2:
                    if st.form_submit_button("Delete", use_container_width=True):
                        try:
                            delete_loan_type(row["loan_type_id"])
                            st.success("Deleted.")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
    except Exception as e:
        st.error(str(e))


with tab_rc:
    st.markdown('<div class="section-head">Risk Categories</div>', unsafe_allow_html=True)
    try:
        rc_df = get_risk_categories()
        if not rc_df.empty:
            st.dataframe(rc_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(str(e))

    st.markdown('<div class="section-head">Add Risk Category</div>', unsafe_allow_html=True)
    with st.form("add_rc"):
        ra1,ra2,ra3 = st.columns(3)
        with ra1: new_rl = st.text_input("Risk Level")
        with ra2: new_mn = st.number_input("Min Score", 300, 899, 300)
        with ra3: new_mx = st.number_input("Max Score", 301, 900, 400)
        if st.form_submit_button("Add", use_container_width=True):
            try:
                insert_risk_category(new_rl.strip(), new_mn, new_mx)
                st.success("Category added.")
                st.rerun()
            except Exception as ex:
                st.error(str(ex))

    st.markdown('<div class="section-head">Edit / Delete Risk Category</div>', unsafe_allow_html=True)
    try:
        rc_df = get_risk_categories()
        if not rc_df.empty:
            rc_opts = {f"#{r['risk_id']} — {r['risk_level']}": r for _, r in rc_df.iterrows()}
            rc_label = st.selectbox("Select", list(rc_opts.keys()), key="edit_rc")
            rc_row   = rc_opts[rc_label]
            with st.form("edit_rc"):
                re1,re2,re3 = st.columns(3)
                with re1: e_rl = st.text_input("Risk Level", value=rc_row["risk_level"])
                with re2: e_mn = st.number_input("Min Score", 300, 899, int(rc_row["min_score"]))
                with re3: e_mx = st.number_input("Max Score", 301, 900, int(rc_row["max_score"]))
                rb1,rb2 = st.columns(2)
                with rb1:
                    if st.form_submit_button("Save Changes", use_container_width=True):
                        try:
                            update_risk_category(rc_row["risk_id"], e_rl, e_mn, e_mx)
                            st.success("Updated.")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
                with rb2:
                    if st.form_submit_button("Delete", use_container_width=True):
                        try:
                            delete_risk_category(rc_row["risk_id"])
                            st.success("Deleted.")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
    except Exception as e:
        st.error(str(e))


with tab_sql:
    st.markdown('<div class="section-head">Raw SQL Runner</div>', unsafe_allow_html=True)
    st.warning("Admin access only. Incorrect queries may permanently modify data.")

    presets = {
        "-- Select a preset --": "",
        "Top defaulters":           "SELECT c.customer_id, c.name, COUNT(DISTINCT dr.default_id) AS defaults, SUM(dr.overdue_days) AS total_overdue\nFROM customer c JOIN loan l ON l.customer_id=c.customer_id JOIN default_record dr ON dr.loan_id=l.loan_id\nGROUP BY c.customer_id, c.name ORDER BY defaults DESC;",
        "Monthly collections":      "SELECT TO_CHAR(payment_date,'YYYY-MM') AS month, SUM(paid_amount) AS total FROM repayment GROUP BY month ORDER BY month;",
        "Credit score trends":      "SELECT c.name, cs.score_date, cs.score_value,\n  AVG(cs.score_value) OVER (PARTITION BY cs.customer_id ORDER BY cs.score_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_avg\nFROM credit_score cs JOIN customer c ON c.customer_id=cs.customer_id ORDER BY c.customer_id, cs.score_date;",
        "Eligible customers":       "SELECT c.customer_id, c.name, i.monthly_income, cs.score_value FROM customer c JOIN income_details i ON i.customer_id=c.customer_id JOIN credit_history ch ON ch.customer_id=c.customer_id JOIN LATERAL (SELECT score_value FROM credit_score WHERE customer_id=c.customer_id ORDER BY score_date DESC LIMIT 1) cs ON TRUE WHERE cs.score_value>600 AND ch.total_defaults=0 AND i.monthly_income>30000 ORDER BY cs.score_value DESC;",
        "Loan portfolio summary":   "SELECT lt.type_name, COUNT(l.loan_id) AS loans, SUM(l.loan_amount) AS total_disbursed, ROUND(AVG(l.interest_rate)::NUMERIC,2) AS avg_rate FROM loan_type lt LEFT JOIN loan l ON l.loan_type_id=lt.loan_type_id GROUP BY lt.type_name ORDER BY total_disbursed DESC NULLS LAST;",
        "Loan status breakdown":    "SELECT current_status, COUNT(*) FROM loan GROUP BY current_status;",
        "Penalty ranking (window)": "SELECT c.name, SUM(p.penalty_amount) AS total_penalty, RANK() OVER (ORDER BY SUM(p.penalty_amount) DESC) AS rank FROM customer c JOIN loan l ON l.customer_id=c.customer_id JOIN default_record dr ON dr.loan_id=l.loan_id JOIN penalty p ON p.default_id=dr.default_id GROUP BY c.name ORDER BY rank;",
    }
    preset = st.selectbox("Preset queries", list(presets.keys()))
    sql    = st.text_area("SQL Query", value=presets[preset], height=160, placeholder="SELECT * FROM customer LIMIT 10;")

    if st.button("Execute Query"):
        if sql.strip():
            with st.spinner("Running..."):
                try:
                    result = run_raw_sql(sql.strip())
                    if result is not None:
                        st.success(f"{len(result)} row(s) returned.")
                        st.dataframe(result, use_container_width=True, hide_index=True)
                        st.download_button("Download CSV", result.to_csv(index=False).encode(),
                                           "query_result.csv", "text/csv")
                    else:
                        st.success("Query executed successfully.")
                except Exception as ex:
                    st.error(f"SQL Error: {ex}")


with tab_ml:
    st.markdown('<div class="section-head">Model Status</div>', unsafe_allow_html=True)
    base  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mdir  = os.path.join(base, "ml", "models")
    files = ["credit_score_model.pkl","risk_classifier.pkl","default_predictor.pkl","risk_label_encoder.pkl","default_scaler.pkl"]

    cols = st.columns(len(files))
    for col, f in zip(cols, files):
        exists = os.path.exists(os.path.join(mdir, f))
        with col:
            st.markdown(f'<div class="model-tile">{"LOADED" if exists else "MISSING"}<br><span style="color:{"#3fb950" if exists else "#f85149"};font-weight:700;">{f.replace(".pkl","")}</span></div>',
                        unsafe_allow_html=True)

    st.markdown("")
    st.info("Training generates 5,000 synthetic samples and fits three models (RF Regressor, RF Classifier, Logistic Regression). Takes ~30-60 seconds.")

    if st.button("Retrain All Models"):
        script = os.path.join(base, "ml", "models.py")
        with st.spinner("Training... please wait"):
            r = subprocess.run([sys.executable, script], capture_output=True, text=True, cwd=base)
        if r.returncode == 0:
            st.success("All models retrained successfully.")
            st.code(r.stdout, language="text")
        else:
            st.error("Training failed.")
            st.code(r.stderr, language="text")


with tab_export:
    st.markdown('<div class="section-head">Export Table</div>', unsafe_allow_html=True)
    tables = ["customer","income_details","address_details","credit_history","credit_score",
              "loan","loan_type","emi_schedule","repayment","default_record","penalty",
              "guarantor","risk_category","loan_status_history"]
    tbl = st.selectbox("Table", tables)
    e1, e2 = st.columns(2)
    with e1:
        if st.button("Preview (20 rows)"):
            try:
                st.dataframe(fetch_df(f"SELECT * FROM {tbl} LIMIT 20"), use_container_width=True, hide_index=True)
            except Exception as ex:
                st.error(str(ex))
    with e2:
        if st.button("Download CSV"):
            try:
                df_full = export_table_csv(tbl)
                st.download_button(f"Save {tbl}.csv", df_full.to_csv(index=False).encode("utf-8"),
                                   f"{tbl}.csv", "text/csv", use_container_width=True)
                st.success(f"{len(df_full)} rows ready.")
            except Exception as ex:
                st.error(str(ex))

    st.markdown('<div class="section-head">Export All Tables (ZIP)</div>', unsafe_allow_html=True)
    if st.button("Download All as ZIP"):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for t in tables:
                try:
                    zf.writestr(f"{t}.csv", export_table_csv(t).to_csv(index=False))
                except Exception:
                    pass
        buf.seek(0)
        st.download_button("Save loaniq_export.zip", buf, "loaniq_export.zip", "application/zip")

    st.markdown('<div class="section-head">System Row Counts</div>', unsafe_allow_html=True)
    try:
        info = fetch_df("""SELECT (SELECT COUNT(*) FROM customer) AS customers,
                                  (SELECT COUNT(*) FROM loan) AS loans,
                                  (SELECT COUNT(*) FROM emi_schedule) AS emis,
                                  (SELECT COUNT(*) FROM repayment) AS repayments,
                                  (SELECT COUNT(*) FROM default_record) AS defaults,
                                  (SELECT COUNT(*) FROM penalty) AS penalties""")
        if not info.empty:
            row = info.iloc[0]
            for col, (lbl, val) in zip(st.columns(6),
                                        zip(["Customers","Loans","EMIs","Repayments","Defaults","Penalties"], row)):
                col.metric(lbl, int(val))
    except Exception as e:
        st.error(str(e))
