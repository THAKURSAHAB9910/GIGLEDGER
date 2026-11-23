"""Page 3: Expense Intelligence and Operating Cost Decomposition."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.components.theme import apply_theme, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_AMBER
from app.components.ui_widgets import (
    render_header,
    render_filters_sidebar,
    render_data_origin_badge,
)
from src.analytics.sql_engine import get_db_manager

st.set_page_config(page_title="Expense Intelligence — GIGLEDGER", page_icon="⛽", layout="wide")
apply_theme()

render_header("⛽ Expense Intelligence & Cost Decomposition", "Auditing the true out-of-pocket operating expenses borne by gig workers.")

db = get_db_manager()
raw_df = db.get_financial_view()

if raw_df.empty:
    st.warning("No shift data found.")
    st.stop()

filtered_df, filters = render_filters_sidebar(raw_df)
render_data_origin_badge(filters["origin"])

# --- Aggregate Expense Totals ---
tot_fuel = filtered_df["fuel_expense"].sum()
tot_maint = filtered_df["maintenance_expense"].sum()
tot_penalties = filtered_df["cancellation_penalties"].sum()
tot_other = filtered_df["other_expenses"].sum()
tot_deductions = filtered_df["deductions"].sum()
tot_all_costs = tot_fuel + tot_maint + tot_penalties + tot_other + tot_deductions
tot_gross = filtered_df["gross_earnings"].sum()

exp_ratio_overall = (tot_all_costs / tot_gross * 100) if tot_gross > 0 else 0.0

e1, e2, e3, e4 = st.columns(4)
with e1:
    st.metric("Total Operating Costs", f"₹{tot_all_costs:,.2f}", help="Fuel + Maintenance + Penalties + Deductions + Other")
with e2:
    st.metric("Fuel / Energy Spent", f"₹{tot_fuel:,.2f}", f"{(tot_fuel/tot_all_costs*100):.1f}% of total" if tot_all_costs > 0 else "0%")
with e3:
    st.metric("Maintenance & Repairs", f"₹{tot_maint:,.2f}", f"{(tot_maint/tot_all_costs*100):.1f}% of total" if tot_all_costs > 0 else "0%")
with e4:
    st.metric("Overall Expense Burden", f"{exp_ratio_overall:.1f}%", help="Total costs as % of total gross payout")

st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### 🍩 Expense Category Allocation")
    st.caption("Distribution of total costs across operational categories.")

    labels = ["Fuel / EV Charging", "Vehicle Maintenance", "Cancellation Penalties", "Platform Deductions", "Mobile Data / Misc"]
    values = [tot_fuel, tot_maint, tot_penalties, tot_deductions, tot_other]

    fig_pie = px.pie(
        values=values,
        names=labels,
        hole=0.45,
        color_discrete_sequence=[ACCENT_RED, "#EA580C", ACCENT_AMBER, "#8B5CF6", "#64748B"]
    )
    fig_pie.update_layout(template="plotly_dark", legend=dict(orientation="h"))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.markdown("### 📊 Operating Cost per KM by Vehicle Modality")
    st.caption("Evaluating efficiency differences between Electric 2W, Motorcycles, and Scooters.")

    vehicle_costs = (
        filtered_df[filtered_df["total_distance_km"] > 0]
        .groupby("vehicle_type")
        .agg(
            distance=("total_distance_km", "sum"),
            fuel=("fuel_expense", "sum"),
            maint=("maintenance_expense", "sum"),
        )
        .reset_index()
    )
    vehicle_costs["fuel_per_km"] = vehicle_costs["fuel"] / vehicle_costs["distance"]
    vehicle_costs["maint_per_km"] = vehicle_costs["maint"] / vehicle_costs["distance"]
    vehicle_costs["total_cost_per_km"] = (vehicle_costs["fuel"] + vehicle_costs["maint"]) / vehicle_costs["distance"]

    fig_cost_km = go.Figure()
    fig_cost_km.add_trace(go.Bar(
        x=vehicle_costs["vehicle_type"], y=vehicle_costs["fuel_per_km"], name="Fuel / Energy per KM", marker_color=ACCENT_RED
    ))
    fig_cost_km.add_trace(go.Bar(
        x=vehicle_costs["vehicle_type"], y=vehicle_costs["maint_per_km"], name="Maintenance per KM", marker_color="#F97316"
    ))
    fig_cost_km.update_layout(
        barmode="stack",
        template="plotly_dark",
        title="Cost per KM (₹/km)",
        xaxis_title="Vehicle Type",
        yaxis_title="Cost (₹/km)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_cost_km, use_container_width=True)

st.markdown("---")

# --- Expense Ratio Distribution ---
st.markdown("### 📉 Expense-to-Gross Payout Ratio Distribution")
st.caption("Shifts with expense ratios > 40% leave workers with critically low take-home pay.")

fig_exp_hist = px.histogram(
    filtered_df,
    x="expense_ratio",
    nbins=35,
    color="platform_category",
    marginal="box",
    title="Expense-to-Gross Payout Ratio Histogram",
)
fig_exp_hist.add_vline(x=0.40, line_dash="dash", line_color="#EF4444", annotation_text="High Expense Threshold (40%)")
fig_exp_hist.update_layout(template="plotly_dark", xaxis_title="Expense Ratio (Total Expenses / Gross)", yaxis_title="Shift Count")
st.plotly_chart(fig_exp_hist, use_container_width=True)

# --- High Expense / Distressed Shifts Table ---
st.markdown("### 🚨 High Expense & Low Net Income Shifts Audit")
st.caption("Table filtering shifts where expense ratio exceeded 40% or net earnings were zero/negative.")

distressed_shifts = filtered_df[
    (filtered_df["expense_ratio"] >= 0.40) | (filtered_df["net_earnings"] <= 0)
][[
    "shift_id", "worker_pseudonym", "shift_date", "city", "vehicle_type", "total_hours",
    "gross_earnings", "fuel_expense", "maintenance_expense", "total_expenses", "net_earnings",
    "effective_hourly_net", "expense_ratio"
]].sort_values("expense_ratio", ascending=False)

st.dataframe(distressed_shifts.head(50).round(2), use_container_width=True)
st.caption(f"Showing top {min(50, len(distressed_shifts))} of {len(distressed_shifts)} flagged high-expense shifts.")
