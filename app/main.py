import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from app.db_connect import get_kpis, get_monthly_repayments, get_loans_by_risk, fetch_df

st.set_page_config(page_title="LoanIQ", page_icon=None, layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0d1117; color: #e6edf3; }
[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
[data-testid="stSidebar"] * { color: #e6edf3 !important; }
[data-testid="stSidebar"] hr { border-color: #30363d; }
.block-container { padding-top: 2rem; }
h1,h2,h3 { color: #e6edf3; font-weight: 600; }
.stMetric label { color: #7d8590 !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.05em; }
.stMetric [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 1.8rem !important; font-weight: 700 !important; }
.kpi { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.25rem 1.5rem; }
.kpi-val { font-size: 2rem; font-weight: 700; color: #e6edf3; margin: 0.25rem 0; }
.kpi-lbl { font-size: 0.72rem; color: #7d8590; text-transform: uppercase; letter-spacing: 0.06em; }
.kpi-badge { display: inline-block; font-size: 0.68rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; margin-top: 0.4rem; }
.badge-up   { background: #1a3326; color: #3fb950; }
.badge-warn { background: #2d1e0f; color: #d29922; }
.badge-down { background: #2a1215; color: #f85149; }
.section-head { font-size: 0.72rem; font-weight: 600; color: #7d8590; text-transform: uppercase;
                letter-spacing: 0.08em; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem;
                margin: 1.75rem 0 1rem; }
.stButton > button { background: #238636 !important; color: #fff !important; border: 1px solid #2ea043 !important;
                     border-radius: 6px !important; font-weight: 500 !important; font-size: 0.85rem !important; }
.stButton > button:hover { background: #2ea043 !important; }
div[data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### LoanIQ")
    st.markdown("---")
    st.markdown("**Navigation**")
    st.markdown("""
- Home (current)
- Customer Management
- Loan Application
- EMI Tracker
- Risk Dashboard
- Administration
""")
    st.markdown("---")
    st.caption("PostgreSQL + scikit-learn + Streamlit")

st.markdown("# Loan & Risk Intelligence System")
st.caption("Portfolio overview — real-time data from PostgreSQL")

try:
    kpis = get_kpis()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.info("Ensure PostgreSQL is running and run `python setup_db.py` to initialize the database.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi"><div class="kpi-lbl">Total Customers</div><div class="kpi-val">{kpis["total_customers"]}</div><span class="kpi-badge badge-up">Registered</span></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi"><div class="kpi-lbl">Active Loans</div><div class="kpi-val">{kpis["active_loans"]}</div><span class="kpi-badge badge-up">Ongoing</span></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi"><div class="kpi-lbl">Defaulters</div><div class="kpi-val">{kpis["defaulters"]}</div><span class="kpi-badge badge-down">At Risk</span></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi"><div class="kpi-lbl">Penalties Collected</div><div class="kpi-val">Rs.{kpis["penalties_collected"]:,.0f}</div><span class="kpi-badge badge-warn">Recovered</span></div>', unsafe_allow_html=True)

st.markdown('<div class="section-head">Monthly Collections vs Risk Distribution</div>', unsafe_allow_html=True)
col_l, col_r = st.columns([3, 2], gap="large")

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e6edf3", family="Inter"),
    margin=dict(l=10, r=10, t=10, b=30),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
)

with col_l:
    try:
        rep = get_monthly_repayments()
        if not rep.empty:
            fig = go.Figure()
            fig.add_bar(x=rep["month"], y=rep["total_collected"],
                        marker_color="#2f81f7", name="Collected")
            fig.add_scatter(x=rep["month"],
                            y=rep["total_collected"].rolling(3, min_periods=1).mean(),
                            mode="lines", name="3-mo avg",
                            line=dict(color="#3fb950", width=2, dash="dot"))
            fig.update_layout(**PLOT_LAYOUT, height=290, showlegend=True,
                              legend=dict(font=dict(color="#e6edf3")))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No repayment data yet.")
    except Exception as e:
        st.error(str(e))

with col_r:
    try:
        risk = get_loans_by_risk()
        if not risk.empty:
            cmap = {"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149", "Unknown": "#7d8590"}
            fig2 = go.Figure(go.Pie(
                labels=risk["risk_level"], values=risk["loan_count"], hole=0.55,
                marker=dict(colors=[cmap.get(r, "#7d8590") for r in risk["risk_level"]]),
                textfont=dict(color="#e6edf3"),
            ))
            fig2.update_layout(**{k: v for k, v in PLOT_LAYOUT.items() if k not in ("xaxis","yaxis")},
                               height=290, showlegend=True,
                               legend=dict(font=dict(color="#e6edf3")),
                               annotations=[dict(text="Risk", x=0.5, y=0.5,
                                                 font=dict(size=13, color="#e6edf3"), showarrow=False)])
            st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(str(e))

st.markdown('<div class="section-head">Recent Loan Activity</div>', unsafe_allow_html=True)
try:
    df = fetch_df("""
        SELECT l.loan_id, c.name AS customer, lt.type_name AS type,
               l.loan_amount, l.interest_rate, l.tenure, l.current_status, l.disbursed_date
        FROM loan l
        JOIN customer c   ON c.customer_id   = l.customer_id
        JOIN loan_type lt ON lt.loan_type_id = l.loan_type_id
        ORDER BY l.loan_id DESC LIMIT 10
    """)
    df["loan_amount"]    = df["loan_amount"].apply(lambda x: f"Rs.{float(x):,.2f}")
    df["interest_rate"]  = df["interest_rate"].apply(lambda x: f"{float(x):.2f}%")
    st.dataframe(df, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(str(e))
