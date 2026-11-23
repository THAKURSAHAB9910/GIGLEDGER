"""Page 2: Comprehensive Earnings Dynamics, Rates per KM, and Volatility Analysis."""

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
from src.calculations.statistical import (
    calculate_volatility_metrics,
    calculate_distribution_percentiles,
    compare_weekday_weekend_earnings,
)

st.set_page_config(page_title="Earnings Analysis — GIGLEDGER", page_icon="📈", layout="wide")
apply_theme()

render_header("📈 Earnings Dynamics & Volatility", "Multi-frequency temporal trends, per-kilometre economics, and income volatility.")

db = get_db_manager()
raw_df = db.get_financial_view()

if raw_df.empty:
    st.warning("No shift data found.")
    st.stop()

filtered_df, filters = render_filters_sidebar(raw_df)
render_data_origin_badge(filters["origin"])

# --- Tabs for Organized Exploration ---
tab_trends, tab_per_km, tab_volatility, tab_weekdays = st.tabs([
    "📅 Multi-Frequency Trends",
    "🚗 Net Earnings per KM",
    "📊 Income Volatility & Dispersion",
    "🗓️ Weekday vs Weekend Dynamics",
])

# ---------------------------------------------------------
# Tab 1: Multi-Frequency Trends
# ---------------------------------------------------------
with tab_trends:
    st.markdown("### Temporal Aggregations: Weekly & Monthly Net Margins")
    freq_choice = st.radio("Aggregation Cadence", ["Weekly", "Monthly"], horizontal=True)

    if freq_choice == "Weekly":
        # Aggregate by year_week
        trend_df = (
            filtered_df.groupby("year_week")
            .agg(
                shifts=("shift_id", "count"),
                workers=("worker_pseudonym", "nunique"),
                gross=("gross_earnings", "sum"),
                net=("net_earnings", "sum"),
                expenses=("total_expenses", "sum"),
                hours=("total_hours", "sum"),
            )
            .reset_index()
        )
        trend_df["effective_hourly_net"] = trend_df["net"] / trend_df["hours"]
        trend_df["margin_pct"] = (trend_df["net"] / trend_df["gross"]) * 100
        x_col = "year_week"
        x_label = "Calendar Week (Year-W)"
    else:
        trend_df = (
            filtered_df.groupby("year_month")
            .agg(
                shifts=("shift_id", "count"),
                workers=("worker_pseudonym", "nunique"),
                gross=("gross_earnings", "sum"),
                net=("net_earnings", "sum"),
                expenses=("total_expenses", "sum"),
                hours=("total_hours", "sum"),
            )
            .reset_index()
        )
        trend_df["effective_hourly_net"] = trend_df["net"] / trend_df["hours"]
        trend_df["margin_pct"] = (trend_df["net"] / trend_df["gross"]) * 100
        x_col = "year_month"
        x_label = "Calendar Month (Year-Month)"

    col_chart, col_margin = st.columns([3, 2])
    with col_chart:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=trend_df[x_col], y=trend_df["gross"], name="Gross Payout", marker_color=ACCENT_BLUE
        ))
        fig_trend.add_trace(go.Bar(
            x=trend_df[x_col], y=trend_df["net"], name="Net Take-Home", marker_color=ACCENT_GREEN
        ))
        fig_trend.update_layout(
            barmode="group",
            template="plotly_dark",
            title=f"Total Aggregate Payout vs Net Earnings ({freq_choice})",
            xaxis_title=x_label,
            yaxis_title="Amount (₹)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_margin:
        fig_margin = px.line(
            trend_df,
            x=x_col,
            y="margin_pct",
            markers=True,
            title="Net Take-Home Margin (% of Gross Retained)",
            labels={"margin_pct": "Net Margin %", x_col: x_label},
            color_discrete_sequence=[ACCENT_AMBER],
        )
        fig_margin.update_layout(template="plotly_dark", yaxis_range=[40, 100])
        st.plotly_chart(fig_margin, use_container_width=True)

    st.dataframe(trend_df.round(2), use_container_width=True)

# ---------------------------------------------------------
# Tab 2: Net Earnings per KM
# ---------------------------------------------------------
with tab_per_km:
    st.markdown("### 🚗 Distance Economics: Net Earnings per Kilometre")
    st.caption("How vehicle technology, fuel prices, and return deadhead distance determine distance profitability.")

    km_summary = (
        filtered_df[filtered_df["total_distance_km"] > 0]
        .groupby(["vehicle_type", "platform_category"])
        .agg(
            shifts=("shift_id", "count"),
            total_km=("total_distance_km", "sum"),
            avg_distance_per_shift=("total_distance_km", "mean"),
            avg_gross_per_km=("gross_earnings", lambda s: s.sum() / filtered_df.loc[s.index, "total_distance_km"].sum()),
            avg_fuel_cost_per_km=("fuel_expense", lambda s: s.sum() / filtered_df.loc[s.index, "total_distance_km"].sum()),
            avg_net_per_km=("net_earnings", lambda s: s.sum() / filtered_df.loc[s.index, "total_distance_km"].sum()),
            avg_deadhead_ratio=("unpaid_distance_ratio", "mean"),
        )
        .reset_index()
    )

    fig_km = px.bar(
        km_summary,
        x="vehicle_type",
        y="avg_net_per_km",
        color="platform_category",
        barmode="group",
        title="Net Earnings per Kilometre by Vehicle Modality & Platform",
        labels={"avg_net_per_km": "Net Earnings (₹/km)", "vehicle_type": "Vehicle Type"},
        text_auto=".2f",
    )
    fig_km.update_layout(template="plotly_dark")
    st.plotly_chart(fig_km, use_container_width=True)

    st.markdown("#### Vehicle Modality Distance Breakdown Table")
    st.dataframe(km_summary.round(2), use_container_width=True)

# ---------------------------------------------------------
# Tab 3: Income Volatility & Dispersion
# ---------------------------------------------------------
with tab_volatility:
    st.markdown("### 📊 Income Uncertainty: Standard Deviation & Interquartile Spread")
    st.caption("Gig earnings exhibit pronounced volatility due to shifting order allocations, weather, and traffic conditions.")

    vol_metrics = calculate_volatility_metrics(filtered_df["net_earnings"])
    pct_metrics = calculate_distribution_percentiles(filtered_df["net_earnings"])

    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.metric("Mean Shift Net Earnings", f"₹{vol_metrics['mean']:.2f}")
    with v2:
        st.metric("Standard Deviation (σ)", f"₹{vol_metrics['std']:.2f}", help="Sample standard deviation across shifts")
    with v3:
        st.metric("Interquartile Range (IQR)", f"₹{vol_metrics['iqr']:.2f}", help="P75 - P25 spread")
    with v4:
        st.metric("Coefficient of Variation (CV)", f"{vol_metrics['cv']:.3f}", help="CV = σ / μ. Higher value indicates greater income uncertainty.")

    col_box, col_worker_vol = st.columns([1, 1])
    with col_box:
        fig_box = px.box(
            filtered_df,
            x="vehicle_type",
            y="net_earnings",
            color="vehicle_type",
            points="all",
            title="Net Shift Earnings Distribution Spread by Vehicle",
            labels={"net_earnings": "Net Shift Earnings (₹)"},
        )
        fig_box.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    with col_worker_vol:
        st.markdown("#### Worker-Level Volatility Ranking")
        # Workers with >= 5 shifts
        worker_vol = (
            filtered_df.groupby("worker_pseudonym")
            .filter(lambda g: len(g) >= 5)
            .groupby(["worker_pseudonym", "platform_category", "vehicle_type"])
            .agg(
                shifts=("shift_id", "count"),
                avg_net=("net_earnings", "mean"),
                std_net=("net_earnings", "std"),
                min_net=("net_earnings", "min"),
                max_net=("net_earnings", "max"),
            )
            .reset_index()
        )
        worker_vol["coeff_of_variation"] = worker_vol["std_net"] / worker_vol["avg_net"]
        worker_vol = worker_vol.sort_values("coeff_of_variation", ascending=False)
        st.dataframe(worker_vol.round(2), use_container_width=True)

# ---------------------------------------------------------
# Tab 4: Weekday vs Weekend Dynamics
# ---------------------------------------------------------
with tab_weekdays:
    st.markdown("### 🗓️ Weekday vs Weekend Empirical Comparison")
    st.caption("Testing whether weekend demand surges yield statistically higher net hourly pay.")

    ww_test = compare_weekday_weekend_earnings(filtered_df)

    if "error" not in ww_test and "warning" not in ww_test:
        w1, w2, w3, w4 = st.columns(4)
        with w1:
            st.metric("Weekday Mean Net", f"₹{ww_test['weekday_mean']:.2f}")
        with w2:
            st.metric("Weekend Mean Net", f"₹{ww_test['weekend_mean']:.2f}")
        with w3:
            st.metric("Difference", f"₹{ww_test['difference_mean']:.2f}", delta=f"{ww_test['percentage_difference']:.1f}%")
        with w4:
            sig_badge = "✅ Significant (p < 0.05)" if ww_test["is_statistically_significant_005"] else "❌ Not Significant"
            st.metric("Hypothesis Test (p-val)", f"{ww_test['mann_whitney_p_value']:.4f}", help=sig_badge)

        st.info(
            f"**Statistical Verdict**: Mann-Whitney U test p-value = **{ww_test['mann_whitney_p_value']:.4f}** (Welch's t = {ww_test['t_statistic']:.2f}, p = {ww_test['t_p_value']:.4f}). "
            f"Weekend net earnings difference is **{'statistically significant at α = 0.05' if ww_test['is_statistically_significant_005'] else 'not statistically significant'}**."
        )

    # Day of week breakdown
    filtered_df["day_name"] = pd.to_datetime(filtered_df["shift_date"]).dt.day_name()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_df = (
        filtered_df.groupby("day_name", observed=False)
        .agg(
            shifts=("shift_id", "count"),
            avg_gross=("gross_earnings", "mean"),
            avg_net=("net_earnings", "mean"),
            avg_hourly_net=("effective_hourly_net", "mean"),
            avg_hours=("total_hours", "mean"),
        )
        .reindex(day_order)
        .reset_index()
    )

    fig_dow = px.bar(
        dow_df,
        x="day_name",
        y=["avg_gross", "avg_net"],
        barmode="group",
        title="Day-of-Week Average Shift Earnings (Gross vs Net)",
        labels={"value": "Amount (₹)", "day_name": "Day of Week", "variable": "Metric"},
        color_discrete_map={"avg_gross": ACCENT_BLUE, "avg_net": ACCENT_GREEN},
    )
    fig_dow.update_layout(template="plotly_dark")
    st.plotly_chart(fig_dow, use_container_width=True)
