import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.db_connect import (
    get_kpis, get_loans_by_risk, get_monthly_repayments,
    get_defaulters_table, fetch_df
)

st.set_page_config(page_title="Risk Dashboard — LoanIQ", layout="wide")

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
.kpi { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:1.25rem 1.5rem; }
.kpi-val { font-size:2rem; font-weight:700; color:#e6edf3; margin:0.25rem 0; }
.kpi-lbl { font-size:0.68rem; color:#7d8590; text-transform:uppercase; letter-spacing:0.06em; }
</style>
""", unsafe_allow_html=True)

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e6edf3", family="Inter"),
    margin=dict(l=10,r=10,t=10,b=30),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
)

with st.sidebar:
    st.markdown("### LoanIQ")
    st.markdown("---")
    st.markdown("**Risk Dashboard**")
    st.caption("Portfolio KPIs, risk distribution, default monitoring.")

st.markdown("# Risk Dashboard")

try:
    kpis = get_kpis()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
for col, lbl, val in zip(
    [c1, c2, c3, c4],
    ["Total Customers", "Active Loans", "Defaulters", "Penalties Collected"],
    [kpis["total_customers"], kpis["active_loans"], kpis["defaulters"], f"Rs.{kpis['penalties_collected']:,.0f}"]
):
    with col:
        st.markdown(f'<div class="kpi"><div class="kpi-lbl">{lbl}</div><div class="kpi-val">{val}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-head">Risk Distribution and Score Histogram</div>', unsafe_allow_html=True)
r1, r2 = st.columns(2, gap="large")

cmap = {"Low":"#3fb950","Medium":"#d29922","High":"#f85149","Unknown":"#7d8590"}

with r1:
    try:
        risk_df = get_loans_by_risk()
        if not risk_df.empty:
            fig = go.Figure()
            fig.add_bar(x=risk_df["risk_level"], y=risk_df["loan_count"],
                        marker_color=[cmap.get(r,"#7d8590") for r in risk_df["risk_level"]],
                        text=risk_df["loan_count"], textposition="outside", textfont=dict(color="#e6edf3"))
            fig.update_layout(**PLOT, height=280, showlegend=False,
                              yaxis=dict(**PLOT["yaxis"], title="Loan Count"))
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(str(e))

with r2:
    try:
        scores = fetch_df("""
            SELECT cs.score_value, rc.risk_level FROM credit_score cs
            JOIN risk_category rc ON rc.risk_id=cs.risk_id
            WHERE cs.score_date=(SELECT MAX(s2.score_date) FROM credit_score s2 WHERE s2.customer_id=cs.customer_id)
        """)
        if not scores.empty:
            fig2 = px.histogram(scores, x="score_value", color="risk_level",
                                nbins=20, color_discrete_map=cmap,
                                labels={"score_value":"Credit Score","risk_level":"Risk"})
            fig2.update_layout(**PLOT, height=280, bargap=0.1,
                               legend=dict(font=dict(color="#e6edf3")))
            st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(str(e))

st.markdown('<div class="section-head">Monthly Repayment Collections and Loan Status</div>', unsafe_allow_html=True)
r3, r4 = st.columns([3,2], gap="large")

with r3:
    try:
        rep = get_monthly_repayments()
        if not rep.empty:
            fig3 = go.Figure()
            fig3.add_bar(x=rep["month"], y=rep["total_collected"],
                         marker_color="#2f81f7", name="Collected")
            fig3.add_scatter(x=rep["month"],
                             y=rep["total_collected"].rolling(3, min_periods=1).mean(),
                             mode="lines", name="3-mo avg",
                             line=dict(color="#3fb950", width=2, dash="dot"))
            fig3.update_layout(**PLOT, height=280, showlegend=True,
                               legend=dict(font=dict(color="#e6edf3")),
                               yaxis=dict(**PLOT["yaxis"], title="Amount (Rs.)"))
            st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.error(str(e))

with r4:
    try:
        stdf = fetch_df("SELECT current_status, COUNT(*) AS count FROM loan GROUP BY current_status")
        if not stdf.empty:
            sc_colors = {"Active":"#3fb950","Closed":"#2f81f7","Defaulted":"#f85149"}
            fig4 = go.Figure(go.Pie(
                labels=stdf["current_status"], values=stdf["count"], hole=0.55,
                marker=dict(colors=[sc_colors.get(s,"#7d8590") for s in stdf["current_status"]]),
                textfont=dict(color="#e6edf3")
            ))
            fig4.update_layout(**{k:v for k,v in PLOT.items() if k not in ("xaxis","yaxis")},
                               height=280, showlegend=True, legend=dict(font=dict(color="#e6edf3")),
                               annotations=[dict(text="Loans",x=0.5,y=0.5,font=dict(size=13,color="#e6edf3"),showarrow=False)])
            st.plotly_chart(fig4, use_container_width=True)
    except Exception as e:
        st.error(str(e))

st.markdown('<div class="section-head">Loan Type Exposure</div>', unsafe_allow_html=True)
try:
    exp = fetch_df("""
        SELECT lt.type_name, COUNT(l.loan_id) AS loan_count,
               COALESCE(SUM(l.loan_amount),0) AS total_exposure,
               ROUND(AVG(l.interest_rate)::NUMERIC,2) AS avg_rate,
               COUNT(l.loan_id) FILTER (WHERE l.current_status='Defaulted') AS defaults
        FROM loan_type lt LEFT JOIN loan l ON l.loan_type_id=lt.loan_type_id
        GROUP BY lt.type_name ORDER BY total_exposure DESC NULLS LAST
    """)
    if not exp.empty:
        fig5 = px.bar(exp, x="type_name", y="total_exposure", color="defaults",
                      color_continuous_scale=["#3fb950","#d29922","#f85149"],
                      text="loan_count", labels={"type_name":"Loan Type","total_exposure":"Total Exposure (Rs.)","defaults":"Defaults"})
        fig5.update_layout(**PLOT, height=280,
                           coloraxis_colorbar=dict(title="Defaults",tickfont=dict(color="#e6edf3")))
        fig5.update_traces(texttemplate="%{text} loans", textposition="outside")
        st.plotly_chart(fig5, use_container_width=True)
except Exception as e:
    st.error(str(e))

st.markdown('<div class="section-head">Defaulters</div>', unsafe_allow_html=True)
try:
    def_df = get_defaulters_table()
    if not def_df.empty:
        sort_col = st.selectbox("Sort by", ["overdue_days","penalty_amount","loan_amount"])
        def_df   = def_df.sort_values(sort_col, ascending=False)
        def_df["loan_amount"]    = def_df["loan_amount"].apply(lambda x: f"Rs.{float(x):,.2f}")
        def_df["penalty_amount"] = def_df["penalty_amount"].apply(lambda x: f"Rs.{float(x):,.2f}")
        def_df["default_date"]   = pd.to_datetime(def_df["default_date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(def_df.rename(columns={"customer_id":"Cust ID","name":"Customer","phone":"Phone",
                                             "loan_id":"Loan ID","loan_type":"Type","loan_amount":"Amount",
                                             "default_date":"Default Date","overdue_days":"Overdue Days","penalty_amount":"Penalty"}),
                     use_container_width=True, hide_index=True)
    else:
        st.success("No defaulters currently in the system.")
except Exception as e:
    st.error(str(e))

st.markdown('<div class="section-head">Overdue EMIs</div>', unsafe_allow_html=True)
try:
    ov = fetch_df("""
        SELECT e.emi_id, c.name AS customer, l.loan_id, lt.type_name,
               e.due_date, e.emi_amount, CURRENT_DATE-e.due_date AS days_overdue
        FROM emi_schedule e
        JOIN loan l ON l.loan_id=e.loan_id
        JOIN customer c ON c.customer_id=l.customer_id
        JOIN loan_type lt ON lt.loan_type_id=l.loan_type_id
        WHERE e.status='Overdue' ORDER BY e.due_date LIMIT 20
    """)
    if not ov.empty:
        ov["emi_amount"] = ov["emi_amount"].apply(lambda x: f"Rs.{float(x):,.2f}")
        ov["due_date"]   = pd.to_datetime(ov["due_date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(ov, use_container_width=True, hide_index=True)
    else:
        st.success("No overdue EMIs at the moment.")
except Exception as e:
    st.error(str(e))
