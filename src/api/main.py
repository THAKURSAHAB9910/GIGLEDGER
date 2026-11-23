"""GIGLEDGER Production FastAPI Application.

Provides decoupled REST API endpoints for the financial analytics engine,
allowing the backend to be hosted independently on Render, Railway, Fly.io, or AWS.
"""

import os
from datetime import date
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import FINANCIAL_BOUNDS
from src.analytics.sql_engine import get_db_manager
from src.analytics.advanced_analytics import AdvancedAnalyticsEngine
from src.ingestion.validator import DatasetValidator
from src.ingestion.importer import CSVShiftImporter
from src.api.models import (
    MetricsSummaryResponse,
    PayoutReconciliationItem,
    ShiftProfitabilityResponse,
)

app = FastAPI(
    title="GIGLEDGER Financial Analytics API",
    description="Decoupled backend API for gig-worker net-earnings, expense decomposition, and payout reconciliation.",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS configuration to allow Vercel frontend, localhost, and custom domains
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = get_db_manager()


@app.get("/")
def root():
    return {
        "platform": "GIGLEDGER",
        "description": "Gig Worker Net-Earnings & Payout Intelligence API",
        "version": "1.0.0",
        "documentation": "/api/docs",
        "health": "/api/health",
        "repository": "https://github.com/THAKURSAHAB9910/GIGLEDGER",
    }


@app.get("/api/health")
def health_check():
    """Verify API operational health and database connectivity."""
    try:
        df = db.execute_query("SELECT COUNT(*) AS shift_count FROM shifts;")
        count = int(df["shift_count"].iloc[0]) if not df.empty else 0
        return {
            "status": "healthy",
            "database_connected": True,
            "total_shifts_in_db": count,
            "statutory_min_wage_hourly": FINANCIAL_BOUNDS["statutory_min_wage_hourly"],
            "currency": FINANCIAL_BOUNDS["currency_code"],
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database_connected": False, "error": str(e)},
        )


@app.get("/api/metrics/summary", response_model=MetricsSummaryResponse)
def get_metrics_summary(
    city: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    platform_category: Optional[str] = Query(None),
    data_origin: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    """Retrieve aggregated financial and operational KPIs with optional filtering."""
    filters = {
        "city": city,
        "vehicle_type": vehicle_type,
        "platform_category": platform_category,
        "data_origin": data_origin,
        "start_date": start_date,
        "end_date": end_date,
    }
    df = db.get_financial_view(filters)
    if df.empty:
        raise HTTPException(status_code=404, detail="No shifts match the specified filter criteria.")

    tot_gross = float(df["gross_earnings"].sum())
    tot_exp = float(df["total_expenses"].sum())
    tot_ded = float(df["deductions"].sum())
    tot_net = float(df["net_earnings"].sum())
    tot_hours = float(df["total_hours"].sum())
    tot_wait = float(df["waiting_time_hours"].sum())
    tot_km = float(df["total_distance_km"].sum())
    tot_paid_km = float(df["paid_distance_km"].sum())

    sub_min_shifts = int((df["effective_hourly_net"] < FINANCIAL_BOUNDS["statutory_min_wage_hourly"]).sum())
    sub_min_pct = round((sub_min_shifts / len(df) * 100), 2) if len(df) > 0 else 0.0

    return MetricsSummaryResponse(
        total_shifts=len(df),
        distinct_workers=int(df["worker_pseudonym"].nunique()),
        total_gross_earnings=round(tot_gross, 2),
        total_operating_expenses=round(tot_exp, 2),
        total_platform_deductions=round(tot_ded, 2),
        total_net_earnings=round(tot_net, 2),
        total_working_hours=round(tot_hours, 1),
        total_waiting_hours=round(tot_wait, 1),
        total_distance_km=round(tot_km, 1),
        total_paid_distance_km=round(tot_paid_km, 1),
        effective_hourly_gross=round(tot_gross / tot_hours, 2) if tot_hours > 0 else 0.0,
        effective_hourly_net=round(tot_net / tot_hours, 2) if tot_hours > 0 else 0.0,
        overall_shortfall_pct=round(((tot_gross - tot_net) / tot_gross * 100), 2) if tot_gross > 0 else 0.0,
        overall_expense_ratio_pct=round((tot_exp / tot_gross * 100), 2) if tot_gross > 0 else 0.0,
        overall_unpaid_time_pct=round((tot_wait / tot_hours * 100), 2) if tot_hours > 0 else 0.0,
        overall_deadhead_pct=round(((tot_km - tot_paid_km) / tot_km * 100), 2) if tot_km > 0 else 0.0,
        sub_minimum_wage_shift_count=sub_min_shifts,
        sub_minimum_wage_pct=sub_min_pct,
        currency=FINANCIAL_BOUNDS["currency_code"],
        currency_symbol=FINANCIAL_BOUNDS["currency_symbol"],
    )


@app.get("/api/analytics/reconciliation", response_model=List[PayoutReconciliationItem])
def get_payout_reconciliation(
    limit: int = Query(50, ge=1, le=500),
    discrepancy_only: bool = Query(False),
):
    """Audit table reconciling platform gross payouts against actual bank take-home."""
    df = db.get_financial_view()
    if df.empty:
        return []

    reconciled_items: List[PayoutReconciliationItem] = []
    for _, row in df.iterrows():
        gross = float(row["gross_earnings"])
        net = float(row["net_earnings"])
        retention = (net / gross * 100) if gross > 0 else 0.0

        # Classify reconciliation status
        if net <= 0:
            rec_status = "CRITICAL: Negative Net Settlement"
        elif retention < 50.0:
            rec_status = "WARNING: Heavy Deduction Drain (>50%)"
        else:
            rec_status = "RECONCILED: Standard Margin"

        if discrepancy_only and rec_status == "RECONCILED: Standard Margin":
            continue

        reconciled_items.append(
            PayoutReconciliationItem(
                shift_id=int(row["shift_id"]),
                shift_date=str(row["shift_date"]),
                worker_pseudonym=str(row["worker_pseudonym"]),
                city=str(row["city"]),
                platform_category=str(row["platform_category"]),
                gross_advertised_payout=round(gross, 2),
                base_fare_payout=round(float(row["base_payout"]), 2),
                variable_incentives=round(float(row["incentive_pay"]), 2),
                milestone_bonuses=round(float(row["bonus_pay"]), 2),
                platform_deductions=round(float(row["deductions"]), 2),
                cancellation_penalties=round(float(row["cancellation_penalties"]), 2),
                direct_fuel_expense=round(float(row["fuel_expense"]), 2),
                vehicle_maintenance=round(float(row["maintenance_expense"]), 2),
                other_operating_costs=round(float(row["other_expenses"]), 2),
                net_bank_settlement=round(net, 2),
                take_home_retention_pct=round(retention, 2),
                reconciliation_status=rec_status,
            )
        )
        if len(reconciled_items) >= limit:
            break

    return reconciled_items


@app.get("/api/analytics/shift-profitability", response_model=ShiftProfitabilityResponse)
def get_shift_profitability():
    """Analyze shift profitability tiers, break-even delivery thresholds, and loss-making shifts."""
    df = db.get_financial_view()
    if df.empty:
        raise HTTPException(status_code=404, detail="No shift records available.")

    profitable = int((df["net_earnings"] > 0).sum())
    loss_making = int((df["net_earnings"] <= 0).sum())

    # Profit Margin Tiers (Net / Gross)
    tier_high = int(((df["net_earnings"] / df["gross_earnings"]) >= 0.60).sum())
    tier_mod = int((((df["net_earnings"] / df["gross_earnings"]) >= 0.40) & ((df["net_earnings"] / df["gross_earnings"]) < 0.60)).sum())
    tier_low = int((((df["net_earnings"] / df["gross_earnings"]) > 0.0) & ((df["net_earnings"] / df["gross_earnings"]) < 0.40)).sum())
    tier_negative = loss_making

    # Calculate average break-even deliveries per shift
    # Break-even = total operating expenses / average base payout per order
    avg_expense = df["total_expenses"].mean()
    avg_base_per_order = (df["base_payout"] / df["orders_completed"].replace(0, np.nan)).mean()
    break_even_orders = round(float(avg_expense / avg_base_per_order), 1) if avg_base_per_order > 0 else 6.5

    # Modality profitability
    modality_net = df.groupby("vehicle_type")["effective_hourly_net"].mean()
    top_modality = str(modality_net.idxmax()) if not modality_net.empty else "Electric 2W"

    distressed = df[df["expense_ratio"] >= 0.40].head(10)[[
        "shift_id", "worker_pseudonym", "city", "vehicle_type", "total_hours",
        "gross_earnings", "total_expenses", "net_earnings", "effective_hourly_net", "expense_ratio"
    ]].to_dict(orient="records")

    return ShiftProfitabilityResponse(
        total_shifts_analyzed=len(df),
        profitable_shifts_count=profitable,
        loss_making_shifts_count=loss_making,
        profit_margin_tiers={
            "High Profit Margin (>=60%)": tier_high,
            "Moderate Margin (40-60%)": tier_mod,
            "Low Margin (<40%)": tier_low,
            "Distressed / Loss-Making (<=0%)": tier_negative,
        },
        avg_break_even_deliveries=break_even_orders,
        highest_profit_modality=top_modality,
        distressed_shifts_sample=distressed,
    )


@app.get("/api/analytics/benchmarks")
def get_benchmarks():
    """Retrieve published research literature benchmark records."""
    benchmarks = db.execute_query("SELECT * FROM benchmark_research ORDER BY publication_year DESC;")
    return benchmarks.to_dict(orient="records")


@app.get("/api/shifts")
def get_shifts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    city: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    platform_category: Optional[str] = Query(None),
):
    """Retrieve paginated shift records with derived metrics."""
    filters = {"city": city, "vehicle_type": vehicle_type, "platform_category": platform_category}
    df = db.get_financial_view(filters)
    total = len(df)
    paginated = df.iloc[offset : offset + limit]
    return {
        "total_count": total,
        "offset": offset,
        "limit": limit,
        "records": paginated.to_dict(orient="records"),
    }
