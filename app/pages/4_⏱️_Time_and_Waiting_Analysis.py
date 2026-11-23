"""Page 4: Working Hours, Idle Waiting Time, and Diminishing Returns Analysis."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.components.theme import apply_theme, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_PURPLE, ACCENT_AMBER
from app.components.ui_widgets import (
    render_header,
    render_filters_sidebar,
    render_data_origin_badge,
)
from src.analytics.sql_engine import get_db_manager
from src.analytics.advanced_analytics import AdvancedAnalyticsEngine

st.set_page_config(page_title="Time & Waiting Analysis — GIGLEDGER", page_icon="⏱️", layout="wide")
apply_theme()

render_header("⏱️ Working Hours & Idle Waiting Economics", "Measuring uncompensated time, queue fatigue, and diminishing returns to long shifts.")

db = get_db_manager()
raw_df = db.get_financial_view()

if raw_df.empty:
    st.warning("No shift data found.")
    st.stop()

filtered_df, filters = render_filters_sidebar(raw_df)
render_data_origin_badge(filters["origin"])

analytics_engine = AdvancedAnalyticsEngine(filtered_df)

# --- Top Time Metrics Strip ---
tot_hours = filtered_df["total_hours"].sum()
tot_waiting = filtered_df["waiting_time_hours"].sum()
avg_wait_ratio = (tot_waiting / tot_hours * 100) if tot_hours > 0 else 0.0

tot_km = filtered_df["total_distance_km"].sum()
tot_paid_km = filtered_df["paid_distance_km"].sum()
deadhead_pct = ((tot_km - tot_paid_km) / tot_km * 100) if tot_km > 0 else 0.0

t1, t2, t3, t4 = st.columns(4)
with t1:
    st.metric("Total Shift Hours", f"{tot_hours:,.1f} hrs")
with t2:
    st.metric("Unpaid Waiting Time", f"{tot_waiting:,.1f} hrs", f"{avg_wait_ratio:.1f}% of total shift time")
with t3:
    st.metric("Average Waiting per Shift", f"{filtered_df['waiting_time_hours'].mean():.2f} hrs", help="Time spent idle between trips and in store queues")
with t4:
    st.metric("Deadhead Travel Ratio", f"{deadhead_pct:.1f}%", help="Uncompensated return travel distance without orders")

st.markdown("---")

# --- Investigation 1: Do Longer Hours Consistently Increase Net Earnings? ---
st.markdown("### 🔬 Investigation: Do Longer Working Hours Consistently Increase Net Earnings?")
st.caption("Econometric test examining non-linear fatigue and diminishing returns in extended gig shifts.")

dim_returns = analytics_engine.analyze_hours_diminishing_returns()

if dim_returns.get("status") not in ("insufficient_data", "sample_too_small"):
    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Pearson Correlation (Hours vs Net Hourly)", f"{dim_returns['pearson_r']:.3f}", f"p = {dim_returns['pearson_p_value']:.4f}")
    with r2:
        st.metric("Spearman Rank Correlation", f"{dim_returns['spearman_rho']:.3f}", f"p = {dim_returns['spearman_p_value']:.4f}")
    with r3:
        status_text = "⚠️ Diminishing Returns Observed" if dim_returns["diminishing_returns_detected"] else "ℹ️ Stable / Weak Correlation"
        st.metric("Analytical Verdict", status_text)

    # Diminishing Returns Scatter + Trendline
    fig_scatter = px.scatter(
        filtered_df[filtered_df["total_hours"] > 0],
        x="total_hours",
        y="effective_hourly_net",
        color="platform_category",
        trendline="ols",
        title="Shift Duration (Hours) vs Effective Net Hourly Pay (₹/hr)",
        labels={"total_hours": "Total Shift Duration (Hours)", "effective_hourly_net": "Effective Net Hourly Rate (₹/hr)"},
        opacity=0.6,
    )
    fig_scatter.update_layout(template="plotly_dark")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Hour Duration Binned Table
    st.markdown("#### Binned Shift Duration Performance")
    binned_df = pd.DataFrame(dim_returns["binned_summary"])
    st.dataframe(binned_df, use_container_width=True)

st.markdown("---")

# --- Investigation 2: Unpaid Waiting Time Wage Drag ---
st.markdown("### ⏳ Uncompensated Waiting Time & Hourly Wage Degradation")
st.caption("How idle waiting intervals dilute actual take-home earnings per hour.")

wait_res = analytics_engine.analyze_waiting_time_impact()
if wait_res.get("status") not in ("insufficient_data", "sample_too_small"):
    col_w1, col_w2 = st.columns([1, 1])
    with col_w1:
        st.info(
            f"**Wage Drag Metric**: The correlation between unpaid waiting percentage and effective net hourly wage is **r = {wait_res['pearson_correlation']:.3f}** (p = {wait_res['p_value']:.4f}). "
            "As waiting time expands, workers suffer a sharp decline in hourly productivity that base trip payouts fail to offset."
        )

        q_table = pd.DataFrame(wait_res["quartile_breakdown"])
        fig_q = px.bar(
            q_table,
            x="wait_quartile",
            y=["avg_gross_hourly", "avg_net_hourly"],
            barmode="group",
            title="Hourly Wage by Waiting Time Quartile",
            labels={"value": "Hourly Rate (₹/hr)", "wait_quartile": "Waiting Ratio Quartile", "variable": "Rate Type"},
            color_discrete_map={"avg_gross_hourly": ACCENT_BLUE, "avg_net_hourly": ACCENT_GREEN},
        )
        fig_q.update_layout(template="plotly_dark")
        st.plotly_chart(fig_q, use_container_width=True)

    with col_w2:
        st.markdown("#### Quartile Wage Degradation Table")
        st.dataframe(q_table, use_container_width=True)

        fig_wait_dist = px.box(
            filtered_df,
            x="platform_category",
            y="waiting_time_hours",
            color="platform_category",
            title="Waiting Time Distribution by Platform Sector",
            labels={"waiting_time_hours": "Unpaid Waiting Time (Hours)"},
        )
        fig_wait_dist.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_wait_dist, use_container_width=True)
