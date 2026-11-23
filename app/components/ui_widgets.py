"""Reusable UI widgets and filters for GIGLEDGER Streamlit dashboard."""

from typing import Dict, Any, Tuple
import pandas as pd
import streamlit as st
from src.config import FINANCIAL_BOUNDS, K_ANONYMITY_THRESHOLD


def render_header(title: str, subtitle: str) -> None:
    """Render consistent page header with subtitle and branding."""
    st.title(title)
    st.caption(subtitle)
    st.markdown("---")


def render_core_question_banner() -> None:
    """Display the core investigative question prominently."""
    st.info(
        "🎯 **Core Investigative Question**: *How much does a gig worker actually earn after "
        "considering time, expenses and payout conditions?* (Revealing the gap between displayed payouts and true net earnings)"
    )


def render_data_origin_badge(origin: str) -> None:
    """Render an HTML badge classifying the current data slice origin."""
    if origin == "DEMO_SYNTHETIC":
        st.markdown(
            '<span class="badge-demo">⚠️ DEMO DATA (Statistically Simulated)</span> '
            '<span style="font-size:0.8rem; color:#64748B;">— Not real worker records.</span>',
            unsafe_allow_html=True,
        )
    elif origin == "PUBLIC_RESEARCH":
        st.markdown(
            '<span class="badge-research">📚 PUBLIC RESEARCH BENCHMARK</span> '
            '<span style="font-size:0.8rem; color:#64748B;">— Extracted from peer-reviewed & institutional studies.</span>',
            unsafe_allow_html=True,
        )
    elif origin == "PARTICIPANT_REPORTED":
        st.markdown(
            '<span class="badge-participant">🔒 PARTICIPANT REPORTED (Consented)</span> '
            '<span style="font-size:0.8rem; color:#64748B;">— Voluntary anonymized contributions under strict privacy protocol.</span>',
            unsafe_allow_html=True,
        )


def render_k_anonymity_warning(worker_count: int, min_k: int = K_ANONYMITY_THRESHOLD) -> None:
    """Display alert if cohort size violates k-anonymity privacy standard."""
    if worker_count < min_k:
        st.warning(
            f"⚠️ **Privacy Warning**: Current cohort contains only **{worker_count}** unique worker(s). "
            f"Under our privacy protocol (k ≥ {min_k}), individual or low-sample breakdowns are suppressed "
            "to prevent re-identification."
        )


def render_filters_sidebar(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Render standardized global sidebar filters and return filtered DataFrame."""
    st.sidebar.header("🔍 Global Analysis Filters")

    if df.empty:
        st.sidebar.warning("No data available to filter.")
        return df, {}

    # 1. Data Origin Filter
    available_origins = ["All"] + sorted(list(df["data_origin"].dropna().unique()))
    selected_origin = st.sidebar.selectbox("Data Origin / Evidence Tier", available_origins, index=0)

    # 2. City Filter
    available_cities = ["All"] + sorted(list(df["city"].dropna().unique()))
    selected_city = st.sidebar.selectbox("Metropolitan Region", available_cities, index=0)

    # 3. Platform Category Filter
    available_platforms = ["All"] + sorted(list(df["platform_category"].dropna().unique()))
    selected_platform = st.sidebar.selectbox("Platform Sector", available_platforms, index=0)

    # 4. Vehicle Type Filter
    available_vehicles = ["All"] + sorted(list(df["vehicle_type"].dropna().unique()))
    selected_vehicle = st.sidebar.selectbox("Vehicle Modality", available_vehicles, index=0)

    # 5. Date Range Filter
    df["shift_date_dt"] = pd.to_datetime(df["shift_date"])
    min_date = df["shift_date_dt"].min().date()
    max_date = df["shift_date_dt"].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Apply filters
    filtered_df = df.copy()

    if selected_origin != "All":
        filtered_df = filtered_df[filtered_df["data_origin"] == selected_origin]

    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["city"] == selected_city]

    if selected_platform != "All":
        filtered_df = filtered_df[filtered_df["platform_category"] == selected_platform]

    if selected_vehicle != "All":
        filtered_df = filtered_df[filtered_df["vehicle_type"] == selected_vehicle]

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered_df = filtered_df[
            (filtered_df["shift_date_dt"].dt.date >= start_d) &
            (filtered_df["shift_date_dt"].dt.date <= end_d)
        ]

    # Sidebar Summary Counter
    st.sidebar.markdown("---")
    st.sidebar.metric("Filtered Shifts", f"{len(filtered_df):,}")
    unique_workers = filtered_df["worker_pseudonym"].nunique() if "worker_pseudonym" in filtered_df.columns else 0
    st.sidebar.metric("Distinct Workers", f"{unique_workers}")

    render_k_anonymity_warning(unique_workers)

    applied_filters = {
        "origin": selected_origin,
        "city": selected_city,
        "platform": selected_platform,
        "vehicle": selected_vehicle,
        "date_range": date_range,
        "sample_size": len(filtered_df),
        "worker_count": unique_workers,
    }

    return filtered_df, applied_filters
