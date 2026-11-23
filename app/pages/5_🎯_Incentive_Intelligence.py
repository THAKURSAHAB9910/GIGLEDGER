"""Page 5: Incentive Structure, Target Thresholds, and Bonus Vulnerability."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.components.theme import apply_theme, ACCENT_BLUE, ACCENT_GREEN, ACCENT_AMBER, ACCENT_RED
from app.components.ui_widgets import (
    render_header,
    render_filters_sidebar,
    render_data_origin_badge,
)
from src.analytics.sql_engine import get_db_manager
from src.analytics.advanced_analytics import AdvancedAnalyticsEngine

st.set_page_config(page_title="Incentive Intelligence — GIGLEDGER", page_icon="🎯", layout="wide")
apply_theme()

render_header("🎯 Incentive Intelligence & Threshold Chasing", "Evaluating worker vulnerability to variable bonus structures and milestone cliffs.")

db = get_db_manager()
raw_df = db.get_financial_view()

if raw_df.empty:
    st.warning("No shift data found.")
    st.stop()

filtered_df, filters = render_filters_sidebar(raw_df)
render_data_origin_badge(filters["origin"])

analytics_engine = AdvancedAnalyticsEngine(filtered_df)

# --- Top KPI Summary ---
tot_gross = filtered_df["gross_earnings"].sum()
tot_base = filtered_df["base_payout"].sum()
tot_inc = filtered_df["incentive_pay"].sum() + filtered_df["bonus_pay"].sum()
inc_dep_overall = (tot_inc / tot_gross * 100) if tot_gross > 0 else 0.0

i1, i2, i3, i4 = st.columns(4)
with i1:
    st.metric("Total Gross Payout", f"₹{tot_gross:,.2f}")
with i2:
    st.metric("Guaranteed Base Pay", f"₹{tot_base:,.2f}", f"{(tot_base/tot_gross*100):.1f}% of gross")
with i3:
    st.metric("Variable Incentives & Bonuses", f"₹{tot_inc:,.2f}", f"{inc_dep_overall:.1f}% incentive share")
with i4:
    st.metric("Average Incentive Dependency", f"{filtered_df['incentive_dependency'].mean()*100:.1f}%")

st.markdown("---")

col_left, col_right = st.columns([1, 1])

# --- Counterfactual Simulation: With vs Without Incentives ---
with col_left:
    st.markdown("### ⚖️ Counterfactual: Earnings With vs Without Incentives")
    st.caption("What happens to worker net take-home pay if target bonuses are missed?")

    # Counterfactual net earnings = Base - Deductions - Expenses
    filtered_df["counterfactual_net_no_incentives"] = (
        filtered_df["base_payout"] - filtered_df["deductions"] - filtered_df["total_expenses"]
    )

    tot_actual_net = filtered_df["net_earnings"].sum()
    tot_counter_net = filtered_df["counterfactual_net_no_incentives"].sum()

    cf_summary = pd.DataFrame({
        "Scenario": ["Actual Net (With Incentives)", "Base-Only Net (Zero Incentives)"],
        "Total Net (₹)": [tot_actual_net, tot_counter_net],
        "Effective Hourly Net (₹/hr)": [
            tot_actual_net / filtered_df["total_hours"].sum(),
            tot_counter_net / filtered_df["total_hours"].sum(),
        ],
    })

    fig_cf = px.bar(
        cf_summary,
        x="Scenario",
        y="Total Net (₹)",
        color="Scenario",
        color_discrete_map={
            "Actual Net (With Incentives)": ACCENT_GREEN,
            "Base-Only Net (Zero Incentives)": ACCENT_RED,
        },
        title="Aggregate Net Take-Home: Base Pay vs With Incentives",
        text_auto=",.0f",
    )
    fig_cf.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_cf, use_container_width=True)

    shifts_negative_without_inc = filtered_df[filtered_df["counterfactual_net_no_incentives"] <= 0]
    pct_neg_no_inc = (len(shifts_negative_without_inc) / len(filtered_df) * 100) if len(filtered_df) > 0 else 0.0

    st.warning(
        f"🚨 **Extreme Fragility**: Without incentive bonuses, **{pct_neg_no_inc:.1f}%** of shifts would result in "
        f"**zero or negative net earnings** after fuel and operating expenses! The base payout alone fails to cover vehicle operating costs."
    )

# --- Threshold Bunching Analysis ---
with col_right:
    st.markdown("### 🧗 Target Bunching & Cliff-Edge Behavior")
    st.caption("Distribution of completed order counts revealing clustering around bonus targets.")

    fig_hist_orders = px.histogram(
        filtered_df,
        x="orders_completed",
        nbins=30,
        title="Delivery Order Count Distribution per Shift",
        color_discrete_sequence=[ACCENT_AMBER],
    )
    for target in [12, 17, 22]:
        fig_hist_orders.add_vline(
            x=target,
            line_dash="dot",
            line_color="#60A5FA",
            annotation_text=f"Tier ({target})",
            annotation_position="top left",
        )
    fig_hist_orders.update_layout(template="plotly_dark", xaxis_title="Completed Deliveries per Shift", yaxis_title="Shift Count")
    st.plotly_chart(fig_hist_orders, use_container_width=True)

    clustering_res = analytics_engine.analyze_incentive_threshold_clustering()
    if clustering_res.get("status") not in ("insufficient_data", "sample_too_small"):
        st.markdown("#### Incentive Tier Bunching Ratios")
        cluster_df = pd.DataFrame(clustering_res["tier_clusters"]).T.reset_index()
        cluster_df.columns = ["Target Tier", "At or Just Above", "Just Missed (Target - 1)", "Bunching Ratio"]
        st.dataframe(cluster_df, use_container_width=True)

st.markdown("---")

# --- Cancellation Drag Analysis ---
st.markdown("### 🚫 Financial Drag of Order Cancellations")
st.caption("Evaluating shifts with order cancellations vs clean shifts.")

cancel_res = analytics_engine.analyze_cancellation_drag()
if cancel_res.get("status") not in ("insufficient_data", "sample_too_small"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Clean Shifts Net Avg", f"₹{cancel_res['avg_net_without_cancellations']:.2f}")
    with c2:
        st.metric("Cancelled Shifts Net Avg", f"₹{cancel_res['avg_net_with_cancellations']:.2f}")
    with c3:
        st.metric("Net Shortfall per Cancelled Shift", f"-₹{cancel_res['estimated_net_shortfall_per_cancelled_shift']:.2f}", delta_color="inverse")

    st.info(
        f"**Cancellation Friction**: When an order is cancelled after acceptance, the worker incurs uncompensated waiting and deadhead travel. "
        f"In addition to an average direct platform penalty of ₹{cancel_res['avg_penalty_when_cancelled']:.2f}, "
        f"the net shift earnings drop by an average of ₹{cancel_res['estimated_net_shortfall_per_cancelled_shift']:.2f}."
    )
