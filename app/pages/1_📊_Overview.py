"""Page 1: Overview & Headline Divergence Analysis."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.components.theme import apply_theme, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_AMBER
from app.components.ui_widgets import (
    render_header,
    render_core_question_banner,
    render_filters_sidebar,
    render_data_origin_badge,
)
from src.analytics.sql_engine import get_db_manager
from src.config import FINANCIAL_BOUNDS

st.set_page_config(page_title="Overview — GIGLEDGER", page_icon="📊", layout="wide")
apply_theme()

render_header("📊 Overview & Headline Divergence", "Executive synthesis of gross platform payouts vs true net worker earnings.")
render_core_question_banner()

db = get_db_manager()
raw_df = db.get_financial_view()

if raw_df.empty:
    st.warning("No shift data found. Please bootstrap database or upload CSV.")
    st.stop()

# Sidebar filters
filtered_df, filters = render_filters_sidebar(raw_df)

if filtered_df.empty:
    st.warning("No records match the selected filter criteria.")
    st.stop()

render_data_origin_badge(filters["origin"])

# --- Core Metric Aggregations ---
tot_gross = filtered_df["gross_earnings"].sum()
tot_expenses = filtered_df["total_expenses"].sum()
tot_deductions = filtered_df["deductions"].sum()
tot_net = filtered_df["net_earnings"].sum()
tot_hours = filtered_df["total_hours"].sum()
tot_orders = filtered_df["orders_completed"].sum()

avg_gross_hourly = (tot_gross / tot_hours) if tot_hours > 0 else 0.0
avg_net_hourly = (tot_net / tot_hours) if tot_hours > 0 else 0.0
shortfall_pct = ((tot_gross - tot_net) / tot_gross * 100) if tot_gross > 0 else 0.0
expense_pct = (tot_expenses / tot_gross * 100) if tot_gross > 0 else 0.0

sub_min_wage_shifts = filtered_df[filtered_df["effective_hourly_net"] < FINANCIAL_BOUNDS["statutory_min_wage_hourly"]]
pct_sub_min = (len(sub_min_wage_shifts) / len(filtered_df) * 100) if len(filtered_df) > 0 else 0.0

# --- Top KPI Cards Strip ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Gross Payout", f"₹{tot_gross:,.2f}", help="Base payout + incentives + bonuses")
with c2:
    st.metric("Total Net Earnings", f"₹{tot_net:,.2f}", delta=f"-{shortfall_pct:.1f}% vs Gross", delta_color="inverse")
with c3:
    st.metric("Total Working Hours", f"{tot_hours:,.1f} hrs", help="Includes trip time, waiting time, and return transit")
with c4:
    st.metric("Effective Net Hourly Rate", f"₹{avg_net_hourly:.2f}/hr", delta=f"₹{avg_gross_hourly:.2f}/hr gross", delta_color="off")

st.markdown("---")

# --- Key Divergence Highlights ---
col_divergence, col_risk = st.columns([2, 1])

with col_divergence:
    st.markdown("### 📉 The Net Earnings Divergence Timeline")
    st.caption("Daily comparison of displayed gross payouts vs take-home net earnings after operational costs.")

    # Group daily
    daily_trend = (
        filtered_df.groupby("shift_date")
        .agg(
            gross=("gross_earnings", "sum"),
            net=("net_earnings", "sum"),
            expenses=("total_expenses", "sum"),
            hours=("total_hours", "sum"),
        )
        .reset_index()
    )

    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Scatter(
        x=daily_trend["shift_date"], y=daily_trend["gross"],
        mode="lines", name="Displayed Gross Payout",
        line=dict(color=ACCENT_BLUE, width=2.5)
    ))
    fig_timeline.add_trace(go.Scatter(
        x=daily_trend["shift_date"], y=daily_trend["net"],
        mode="lines", name="Actual Net Take-Home",
        line=dict(color=ACCENT_GREEN, width=2.5),
        fill="tonexty", fillcolor="rgba(239, 68, 68, 0.15)"  # Red-shaded gap representing expense drain
    ))
    fig_timeline.update_layout(
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Shift Date",
        yaxis_title="Amount (₹)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

with col_risk:
    st.markdown("### ⚠️ Economic Exposure Summary")
    st.markdown(f"""
    - **Gross-to-Net Shortfall**: **{shortfall_pct:.1f}%** of displayed earnings are wiped out by operational expenses and platform deductions.
    - **Operating Expense Ratio**: For every ₹100 in gross payout, the worker spends **₹{expense_pct:.1f}** out of pocket.
    - **Sub-Minimum Wage Exposure**: **{pct_sub_min:.1f}%** of shifts yielded an effective net hourly rate below the statutory benchmark of **₹{FINANCIAL_BOUNDS['statutory_min_wage_hourly']:.0f}/hr**.
    - **Unpaid Waiting & Travel**: Workers spent an average of **{filtered_df['waiting_time_hours'].mean():.1f} hours** in unpaid idle queues per shift.
    """)

    # Donut breakdown of gross payout allocation
    alloc_labels = ["Take-Home Net", "Fuel & Energy", "Vehicle Maintenance", "Platform Deductions & Penalties", "Other Operating"]
    alloc_values = [
        max(0.0, tot_net),
        filtered_df["fuel_expense"].sum(),
        filtered_df["maintenance_expense"].sum(),
        tot_deductions + filtered_df["cancellation_penalties"].sum(),
        filtered_df["other_expenses"].sum(),
    ]
    fig_donut = px.pie(
        values=alloc_values,
        names=alloc_labels,
        hole=0.55,
        color_discrete_sequence=[ACCENT_GREEN, ACCENT_RED, "#F97316", ACCENT_AMBER, "#64748B"]
    )
    fig_donut.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=True,
        legend=dict(orientation="h", font=dict(size=10)),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# --- Hourly Rate Distribution vs Benchmark ---
st.markdown("### ⏱️ Hourly Rate Distribution vs Statutory Living Wage Benchmark")
st.caption(f"Histogram of effective net hourly earnings across {len(filtered_df):,} shifts, benchmarked against ₹{FINANCIAL_BOUNDS['statutory_min_wage_hourly']:.0f}/hr.")

fig_hist = px.histogram(
    filtered_df,
    x="effective_hourly_net",
    nbins=40,
    color="vehicle_type",
    marginal="box",
    title="Distribution of Effective Net Hourly Earnings (₹/hr)",
)
fig_hist.add_vline(
    x=FINANCIAL_BOUNDS["statutory_min_wage_hourly"],
    line_dash="dash",
    line_color="#F87171",
    annotation_text=f"Statutory Benchmark (₹{FINANCIAL_BOUNDS['statutory_min_wage_hourly']:.0f}/hr)",
    annotation_position="top right",
)
fig_hist.update_layout(
    template="plotly_dark",
    xaxis_title="Effective Net Hourly Earnings (₹/hr)",
    yaxis_title="Shift Count",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_hist, use_container_width=True)
