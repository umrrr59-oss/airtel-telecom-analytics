from pathlib import Path
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Airtel Telecom Analytics | Group 3 - Network Usage
# Place the supplied database at data/raw/airtel.db (or set AIRTel_DB_PATH).

st.set_page_config(
    page_title="Airtel Telecom Analytics",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "raw" / "airtel.db"
DB_PATH = Path(__import__("os").environ.get("AIRTEL_DB_PATH", str(DEFAULT_DB)))

RED = "#E31E24"
BLUE = "#38BDF8"
GREEN = "#34D399"
ORANGE = "#FBBF24"
INK = "#EAF2FF"
MUTED = "#9BAFC8"
PANEL = "#13243A"
BG = "#071426"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@keyframes airtelGlow {{ 0%,100% {{ box-shadow: 0 0 14px rgba(227,30,36,.18); }} 50% {{ box-shadow: 0 0 28px rgba(227,30,36,.38); }} }}
@keyframes drift {{ 0% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} 100% {{ transform: translateY(0); }} }}
@keyframes shimmer {{ 0% {{ background-position: -200% 0; }} 100% {{ background-position: 200% 0; }} }}
@keyframes fadeUp {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}

html, body, [class*="css"] {{ font-family: Inter, sans-serif; }}
.stApp {{ background: radial-gradient(ellipse at 12% 0%, #203F64 0%, {BG} 46%, #06101f 100%); color: {INK}; }}
[data-testid="stAppViewContainer"] {{ animation: fadeUp .55s ease-out; }}
.block-container {{ padding-top: .35rem; padding-bottom: .15rem; max-width: 1680px; }}
[data-testid="stSidebar"] {{ background: #0B1B30; border-right: 1px solid #243D5A; }}
[data-testid="stSidebar"] * {{ color: #EAF2FF !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] {{ background: #13243A; }}
h1, h2, h3 {{ color: {INK}; font-weight: 750; letter-spacing: -.45px; }}
h1 {{ font-size: 1.65rem !important; }}
h2, h3 {{ margin-bottom: .35rem !important; }}
h2 {{ font-size: 1.18rem !important; }}
h3 {{ font-size: 1.02rem !important; }}
[data-testid="stMetric"] {{ background: linear-gradient(145deg,#1A3451,#102036); border: 1px solid #365777; border-radius: 16px; padding: 8px 12px; box-shadow: 0 8px 22px rgba(0,0,0,.18); min-height: 82px; transition: transform .22s ease, border-color .22s ease; }}
[data-testid="stMetric"]:hover {{ transform: translateY(-3px); border-color: #FF5B61; animation: airtelGlow 2s ease-in-out infinite; }}
[data-testid="stMetricLabel"] p {{ color: #AFC4DB !important; font-weight: 600; font-size: .82rem; }}
[data-testid="stMetricValue"] {{ color: #F4F8FF !important; font-weight: 800; font-size: 1.45rem !important; }}
[data-testid="stMetricDelta"] {{ font-size: .75rem; }}
[data-testid="stAlert"] {{ border-radius: 12px; }}
div.stTabs [data-baseweb="tab-list"] {{ gap: 7px; background: #0E2035; border: 1px solid #233D5A; padding: 5px; border-radius: 13px; }}
div.stTabs [data-baseweb="tab"] {{ border-radius: 9px; padding: 7px 18px; color: #B8CBE0; }}
div.stTabs [aria-selected="true"] {{ background: linear-gradient(90deg,{RED},#FF5B61) !important; color: white !important; }}
.card-note {{ color: {MUTED}; font-size: .70rem; line-height: 1.3; margin-top: -7px; }}
.section-note {{ background: linear-gradient(100deg,#173957,#10263D); border: 1px solid #2E5779; border-radius: 14px; padding: 10px 15px; color: #DCEBFA; font-size: .86rem; }}
.hero-banner {{ position:relative; overflow:hidden; background: linear-gradient(110deg,#162E49,#0C1B2E 65%,#281A2C); border: 1px solid #2D4C68; border-radius: 18px; padding: 15px 19px; margin: 0 0 8px 0; box-shadow: 0 10px 28px rgba(0,0,0,.2); animation: fadeUp .65s ease-out; }}
.hero-banner:after {{ content:""; position:absolute; inset:0; background:linear-gradient(110deg,transparent 20%,rgba(255,255,255,.06) 45%,transparent 65%); background-size:200% 100%; animation:shimmer 8s linear infinite; pointer-events:none; }}
.airtel-mark {{ display:inline-flex; align-items:center; justify-content:center; width:48px; height:48px; border-radius:15px; background:linear-gradient(135deg,{RED},#FF676C); box-shadow:0 7px 22px rgba(227,30,36,.3); animation:drift 4s ease-in-out infinite; margin-right:12px; vertical-align:middle; }}
.airtel-mark svg {{ width:30px;height:30px; }}
.hero-row {{ display:flex;align-items:center;gap:12px; }}
.hero-kicker {{ color:#FF6A70; font-size:.74rem; font-weight:800; letter-spacing:2px; text-transform:uppercase; }}
.hero-title {{ color:#F4F8FF; font-size:1.8rem; font-weight:800; letter-spacing:-1px; margin-top:2px; }}
.hero-sub {{ color:#AFC4DB; font-size:.82rem; margin-top:3px; }}
.chart-card {{ background:#102238; border:1px solid #28445F; border-radius:15px; padding:6px 10px 2px; }}
[data-testid="stPlotlyChart"] {{ border-radius:14px; animation:fadeUp .45s ease-out; }}
[data-testid="stSelectbox"] {{ border-radius:12px; }}
[data-testid="stSidebar"] h2 {{ animation:fadeUp .5s ease-out; }}
hr {{ border-color:#29435D !important; }}
footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def query_db(sql: str, params: tuple = ()) -> pd.DataFrame:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)

def q(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run every dashboard metric/chart query in SQLite."""
    return query_db(sql, params)

def filters_sql(connection_type: str, experiment_group: str, alias: str = "cf"):
    clauses, params = [], []
    if connection_type != "All":
        clauses.append(f"{alias}.connection_type = ?")
        params.append(connection_type)
    if experiment_group != "All":
        clauses.append(f"{alias}.ab_group = ?")
        params.append(experiment_group)
    return (" AND " + " AND ".join(clauses)) if clauses else "", tuple(params)

def metric_value(df, column, default=0):
    if df.empty or column not in df or pd.isna(df.iloc[0][column]):
        return default
    return df.iloc[0][column]

def fmt_gb(mb):
    return f"{mb / 1024:,.2f} GB"

# Database readiness and source-of-truth metadata
try:
    db_check = q("SELECT COUNT(*) AS n FROM customers")
    customer_total = int(metric_value(db_check, "n"))
except Exception as exc:
    st.title("Airtel Telecom Analytics")
    st.error(f"Cannot open the SQLite database. {exc}")
    st.info("Put airtel.db in the project's data/raw/ folder, or set the AIRTEL_DB_PATH environment variable.")
    st.stop()

st.sidebar.markdown(f"""<div style='text-align:center;padding:14px 0 8px'>
<div style='display:inline-flex;align-items:center;gap:9px;font-size:1.25rem;font-weight:850;letter-spacing:.3px'>
<span style='display:inline-flex;width:38px;height:38px;border-radius:12px;background:linear-gradient(135deg,{RED},#FF676C);align-items:center;justify-content:center;box-shadow:0 5px 18px rgba(227,30,36,.28)'>
<svg viewBox='0 0 40 40' width='27' height='27' aria-label='airtel symbol'><path d='M8 26 Q13 8 28 8 Q32 8 33 13 Q31 19 23 24 Q16 28 11 29 Q8 29 8 26 M15 31 Q23 29 29 24' fill='none' stroke='white' stroke-width='4' stroke-linecap='round'/></svg></span><span style='color:{RED}'>airtel</span></div><div style='font-size:.68rem;color:{MUTED};letter-spacing:1.4px;margin-top:6px'>NETWORK INTELLIGENCE</div></div>""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
conn_options = q("SELECT DISTINCT connection_type FROM customer_features WHERE connection_type IS NOT NULL ORDER BY connection_type")
group_options = q("SELECT DISTINCT ab_group FROM customer_features WHERE ab_group IS NOT NULL ORDER BY ab_group")
connection_type = st.sidebar.selectbox("Connection Type", ["All"] + conn_options["connection_type"].tolist())
experiment_group = st.sidebar.selectbox("Experiment Group", ["All"] + group_options["ab_group"].tolist())
st.sidebar.caption("Filters apply to customer-level and usage visuals. The validated usage-days total and T3 test card are fixed validation results.")
where, params = filters_sql(connection_type, experiment_group)

st.markdown(
    '<div class="hero-banner"><div class="hero-row"><div class="airtel-mark"><svg viewBox="0 0 40 40"><path d="M8 26 Q13 8 28 8 Q32 8 33 13 Q31 19 23 24 Q16 28 11 29 Q8 29 8 26 M15 31 Q23 29 29 24" fill="none" stroke="white" stroke-width="4" stroke-linecap="round"/></svg></div><div><div class="hero-kicker">Airtel · Network intelligence</div>'
    '<div class="hero-title">Telecom Analytics <span style="color:#FF5B61">●</span></div>'
    '<div class="hero-sub">Capacity planning insights · Data demand · Subscriber behaviour</div></div></div></div>',
    unsafe_allow_html=True,
)
st.caption("SOURCE PERIOD  ·  1 JAN — 30 JUN 2025  |  DATABASE-BACKED METRICS")

overview_tab, detail_tab = st.tabs(["Overview", "Detail"])

with overview_tab:
    # Three cards only. Fixed values are explicitly labelled.
    fixed = q("SELECT SUM(usage_days) AS usage_days FROM v_usage_customer")
    selected = q(f"""
        SELECT COUNT(*) AS subscribers,
               SUM(COALESCE(v.usage_days,0)) AS usage_days,
               SUM(COALESCE(v.total_data_mb,0)) AS total_mb,
               SUM(COALESCE(v.total_data_mb,0)) / NULLIF(SUM(COALESCE(v.usage_days,0)),0) AS mb_per_usage_day,
               SUM(COALESCE(v.total_data_mb,0)) / NULLIF(COUNT(*) * 181.0,0) AS mb_per_subscriber_calendar_day
        FROM customer_features cf
        LEFT JOIN v_usage_customer v ON v.customer_id = cf.customer_id
        WHERE 1=1 {where}
    """, params)
    s = selected.iloc[0] if not selected.empty else {}
    usage_days_fixed = int(metric_value(fixed, "usage_days", 0))
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.metric("Validated Usage-Days", f"{usage_days_fixed:,}")
        st.markdown('<div class="card-note">Fixed validation total · 1 row = one subscriber-day with a usage record. Ignores sidebar filters.</div>', unsafe_allow_html=True)
    with c2:
        st.metric("T3 Test Result", "Not available")
        st.markdown('<div class="card-note">The uploaded SQLite database does not contain the validated T3 statistic, p-value or direction. Add these from your validation notebook before submission.</div>', unsafe_allow_html=True)
    with c3:
        st.metric("Data per Day", fmt_gb(float(s.get("mb_per_usage_day") or 0)))
        st.markdown(
            f'<div class="card-note">Per usage-day. Calendar-day rate: {fmt_gb(float(s.get("mb_per_subscriber_calendar_day") or 0))} per subscriber-calendar-day (selected subscribers × 181 days).</div>',
            unsafe_allow_html=True
        )

    # Hero chart: monthly usage by experiment group
    st.subheader("How does monthly data demand differ between experiment groups?")
    monthly = q(f"""
        SELECT um.month, cf.ab_group,
               SUM(um.total_mb) / 1024.0 AS data_gb,
               SUM(um.usage_days) AS usage_days,
               COUNT(DISTINCT um.customer_id) AS subscribers
        FROM v_usage_month um
        JOIN customer_features cf ON cf.customer_id = um.customer_id
        WHERE 1=1 {where}
        GROUP BY um.month, cf.ab_group
        ORDER BY um.month, cf.ab_group
    """, params)
    if not monthly.empty:
        fig = px.bar(monthly, x="month", y="data_gb", color="ab_group", barmode="group",
                     color_discrete_map={"A": BLUE, "B": RED},
                     labels={"month":"Month", "data_gb":"Data carried (GB)", "ab_group":"Experiment group"},
                     hover_data={"usage_days":":,", "subscribers":":,"})
        fig.update_layout(height=235, margin=dict(l=8,r=8,t=8,b=8), paper_bgcolor="#102238",
                          plot_bgcolor="#102238", legend_title_text="Group",
                          font=dict(color=INK), bargap=.24)
        fig.update_xaxes(showgrid=False, color="#AFC4DB")
        fig.update_yaxes(gridcolor="#28445F", color="#AFC4DB")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No monthly usage rows match the selected filters.")

    left, right = st.columns([1.15, 1], gap="medium")
    with left:
        st.subheader("How many subscribers used the network each month?")
        subs = q(f"""
            SELECT um.month, cf.ab_group, COUNT(DISTINCT um.customer_id) AS active_subscribers
            FROM v_usage_month um
            JOIN customer_features cf ON cf.customer_id = um.customer_id
            WHERE 1=1 {where}
            GROUP BY um.month, cf.ab_group ORDER BY um.month, cf.ab_group
        """, params)
        if not subs.empty:
            fig2 = px.line(subs, x="month", y="active_subscribers", color="ab_group",
                           color_discrete_map={"A": BLUE, "B": RED}, markers=True,
                           labels={"month":"Month","active_subscribers":"Active subscribers"})
            fig2.update_layout(height=190, margin=dict(l=8,r=8,t=8,b=8), paper_bgcolor="#102238",
                               plot_bgcolor="#102238", font=dict(color=INK))
            fig2.update_yaxes(gridcolor="#28445F", color="#AFC4DB")
            fig2.update_xaxes(color="#AFC4DB")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No subscriber usage data for these filters.")
    with right:
        st.subheader("Which plans use the most of their data allowance?")
        allowance = q(f"""
            WITH customer_month AS (
                SELECT um.customer_id, um.month, SUM(um.total_mb)/1024.0 AS used_gb
                FROM v_usage_month um
                GROUP BY um.customer_id, um.month
            )
            SELECT cf.plan_name, cm.month,
                   ROUND(SUM(cm.used_gb),2) AS used_gb,
                   ROUND(SUM(COALESCE(vp.monthly_gb,0)),2) AS allowance_gb,
                   ROUND(100.0*SUM(cm.used_gb)/NULLIF(SUM(COALESCE(vp.monthly_gb,0)),0),1) AS utilisation_pct,
                   COUNT(DISTINCT cm.customer_id) AS subscribers
            FROM customer_month cm
            JOIN customer_features cf ON cf.customer_id=cm.customer_id
            LEFT JOIN v_plans_clean vp ON vp.plan_name=cf.plan_name
            WHERE 1=1 {where}
            GROUP BY cf.plan_name, cm.month
            ORDER BY utilisation_pct DESC
        """, params)
        if not allowance.empty:
            fig3 = px.bar(allowance, x="plan_name", y="utilisation_pct", color="month", barmode="group",
                          color_discrete_sequence=[BLUE, RED],
                          labels={"plan_name":"Plan","utilisation_pct":"Usage / allowance (%)"},
                          hover_data={"used_gb":":.1f","allowance_gb":":.1f","subscribers":":,"})
            fig3.update_layout(height=190, margin=dict(l=8,r=8,t=8,b=8), paper_bgcolor="#102238",
                               plot_bgcolor="#102238", font=dict(color=INK))
            fig3.update_xaxes(tickangle=-25, showgrid=False)
            fig3.update_yaxes(gridcolor="#28445F", color="#AFC4DB")
            fig3.update_xaxes(color="#AFC4DB")
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            st.caption("Formula: total observed GB ÷ summed monthly plan allowance for customer-months with usage. Plan allowance uses v_plans_clean.monthly_gb.")
        else:
            st.info("Plan allowance data is unavailable for these filters.")

with detail_tab:
    months_df = q("SELECT DISTINCT month FROM v_usage_month ORDER BY month")
    months = months_df["month"].tolist() if not months_df.empty else []
    if not months:
        st.warning("No month-level usage data found.")
    else:
        selected_month = st.selectbox("Month", months, index=len(months)-1, key="detail_month")
        st.subheader(f"Detailed network usage — {selected_month}")
        month_stats = q(f"""
            SELECT COUNT(DISTINCT um.customer_id) AS active_subscribers,
                   SUM(um.total_mb) AS total_mb,
                   SUM(um.usage_days) AS usage_days,
                   SUM(um.total_mb)/NULLIF(SUM(um.usage_days),0) AS mb_per_usage_day
            FROM v_usage_month um
            JOIN customer_features cf ON cf.customer_id=um.customer_id
            WHERE um.month=? {where}
        """, (selected_month,) + params)
        m = month_stats.iloc[0] if not month_stats.empty else {}
        k1,k2,k3 = st.columns(3, gap="medium")
        with k1:
            st.metric("Active Subscribers", f"{int(m.get('active_subscribers') or 0):,}")
            st.markdown('<div class="card-note">Distinct subscribers with at least one usage record in the selected month.</div>', unsafe_allow_html=True)
        with k2:
            st.metric("Data Carried", f"{float(m.get('total_mb') or 0)/1_000_000:,.3f} TB")
            st.markdown('<div class="card-note">Decimal conversion: 1 TB = 1,000,000 MB.</div>', unsafe_allow_html=True)
        with k3:
            st.metric("Data per Usage-Day", fmt_gb(float(m.get("mb_per_usage_day") or 0)))
            st.markdown(f'<div class="card-note">{int(m.get("usage_days") or 0):,} validated usage-days in this month and filter selection.</div>', unsafe_allow_html=True)

        daily = q(f"""
            SELECT u.usage_date, SUM(u.data_mb)/1024.0 AS data_gb,
                   COUNT(DISTINCT u.customer_id) AS subscribers,
                   COUNT(*) AS usage_days
            FROM usage_daily u
            JOIN customer_features cf ON cf.customer_id=u.customer_id
            WHERE strftime('%Y-%m',u.usage_date)=? {where}
            GROUP BY u.usage_date ORDER BY u.usage_date
        """, (selected_month,) + params)
        ab = q(f"""
            SELECT cf.ab_group, COUNT(DISTINCT um.customer_id) AS subscribers,
                   SUM(um.total_mb)/1024.0 AS data_gb,
                   SUM(um.usage_days) AS usage_days,
                   SUM(um.total_mb)/NULLIF(SUM(um.usage_days),0) AS mb_per_usage_day
            FROM v_usage_month um
            JOIN customer_features cf ON cf.customer_id=um.customer_id
            WHERE um.month=? {where}
            GROUP BY cf.ab_group ORDER BY cf.ab_group
        """, (selected_month,) + params)
        device = q(f"""
            SELECT cf.device_type, COUNT(DISTINCT um.customer_id) AS subscribers,
                   SUM(um.total_mb)/1024.0 AS data_gb,
                   SUM(um.usage_days) AS usage_days
            FROM v_usage_month um
            JOIN customer_features cf ON cf.customer_id=um.customer_id
            WHERE um.month=? {where}
            GROUP BY cf.device_type ORDER BY data_gb DESC
        """, (selected_month,) + params)

        # Compact 2-column dashboard grid to avoid vertical scrolling.
        top_left, top_right = st.columns([1.15, 1], gap="small")
        with top_left:
            st.subheader(f"Daily data load — {selected_month}")
            if not daily.empty:
                daily["usage_date"] = pd.to_datetime(daily["usage_date"])
                min_day, max_day = daily["usage_date"].min().date(), daily["usage_date"].max().date()
                
                fig4 = px.area(daily, x="usage_date", y="data_gb",
                               labels={"usage_date":"Date","data_gb":"Data carried (GB)"},
                               color_discrete_sequence=[BLUE],
                               hover_data={"subscribers":":,","usage_days":":,"})
                fig4.update_traces(line=dict(color=BLUE, width=2), fillcolor="rgba(22,119,232,.18)")
                fig4.update_layout(height=175, margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="#102238",
                                   plot_bgcolor="#102238", font=dict(color=INK))
                fig4.update_yaxes(gridcolor="#28445F", color="#AFC4DB")
                fig4.update_xaxes(color="#AFC4DB")
                st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No daily usage records for this selection.")
        with top_right:
            st.subheader("A/B group comparison")
            if not ab.empty:
                ab_metric = st.selectbox("A/B comparison · Metric",
                    options=["data_gb", "subscribers", "usage_days", "mb_per_usage_day"],
                    format_func=lambda x: {"data_gb":"Data carried (GB)", "subscribers":"Subscribers",
                                           "usage_days":"Usage-days", "mb_per_usage_day":"MB per usage-day"}[x],
                    key="ab_metric_filter")
                fig5 = px.bar(ab, x="ab_group", y=ab_metric, color="ab_group",
                              color_discrete_map={"A":BLUE,"B":RED},
                              labels={"ab_group":"Experiment group", ab_metric: {
                                  "data_gb":"Data carried (GB)", "subscribers":"Subscribers",
                                  "usage_days":"Usage-days", "mb_per_usage_day":"MB per usage-day"}[ab_metric]},
                              hover_data={"subscribers":":,","usage_days":":,","mb_per_usage_day":":.1f"})
                fig5.update_layout(height=175, margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="#102238",
                                   plot_bgcolor="#102238", showlegend=False, font=dict(color=INK))
                fig5.update_yaxes(gridcolor="#28445F", color="#AFC4DB")
                fig5.update_xaxes(color="#AFC4DB")
                st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
                st.caption("Group values include subscriber count, usage-days and the selected comparison metric.")
            else:
                st.info("No A/B comparison data for this selection.")

        # Third visual shares a row with a concise explanatory panel.
        device_left, device_right = st.columns([1.15, 1], gap="small")
        with device_left:
            st.subheader("Device usage comparison")
            if not device.empty:
                device_metric = "data_gb"
                fig6 = px.bar(device, x="device_type", y=device_metric, color="device_type",
                              color_discrete_sequence=[BLUE, ORANGE],
                              labels={"device_type":"Device category", device_metric:"Data carried (GB)"},
                              hover_data={"subscribers":":,","usage_days":":,"})
                fig6.update_layout(height=165, margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="#102238",
                                   plot_bgcolor="#102238", showlegend=False, font=dict(color=INK))
                fig6.update_yaxes(gridcolor="#28445F", color="#AFC4DB")
                fig6.update_xaxes(color="#AFC4DB")
                st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No device comparison data for this selection.")
        with device_right:
            st.subheader("Monthly snapshot")
            device_count = device["device_type"].nunique() if not device.empty else 0
            st.markdown(f"""<div class=\"section-note\">
            <b>{selected_month}</b><br><br>
            Active subscribers: {int(m.get('active_subscribers') or 0):,}<br>
            Validated usage-days: {int(m.get('usage_days') or 0):,}<br>
            Device categories: {device_count}<br><br>
            <small>Active subscribers have at least one usage record in the selected month. Device labels are sourced from customer_features.device_type.</small>
            </div>""", unsafe_allow_html=True)

st.divider()
st.caption("Airtel Telecom Analytics · Group 3 · Domain C — Network Usage | Metrics are queried from the supplied SQLite database.")
    
