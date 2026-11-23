"""Pydantic schemas for GIGLEDGER REST API."""

from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ShiftFilterParams(BaseModel):
    """Query filter parameters for shift searches."""
    city: Optional[str] = None
    vehicle_type: Optional[str] = None
    platform_category: Optional[str] = None
    data_origin: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=500, ge=1, le=2000)
    offset: int = Field(default=0, ge=0)


class MetricsSummaryResponse(BaseModel):
    """Aggregated financial KPI summary response."""
    total_shifts: int
    distinct_workers: int
    total_gross_earnings: float
    total_operating_expenses: float
    total_platform_deductions: float
    total_net_earnings: float
    total_working_hours: float
    total_waiting_hours: float
    total_distance_km: float
    total_paid_distance_km: float
    effective_hourly_gross: float
    effective_hourly_net: float
    overall_shortfall_pct: float
    overall_expense_ratio_pct: float
    overall_unpaid_time_pct: float
    overall_deadhead_pct: float
    sub_minimum_wage_shift_count: int
    sub_minimum_wage_pct: float
    currency: str = "INR"
    currency_symbol: str = "₹"


class PayoutReconciliationItem(BaseModel):
    """Detailed reconciliation breakdown comparing platform gross to bank net."""
    shift_id: int
    shift_date: str
    worker_pseudonym: str
    city: str
    platform_category: str
    gross_advertised_payout: float
    base_fare_payout: float
    variable_incentives: float
    milestone_bonuses: float
    platform_deductions: float
    cancellation_penalties: float
    direct_fuel_expense: float
    vehicle_maintenance: float
    other_operating_costs: float
    net_bank_settlement: float
    take_home_retention_pct: float
    reconciliation_status: str


class ShiftProfitabilityResponse(BaseModel):
    """Shift profitability and break-even audit response."""
    total_shifts_analyzed: int
    profitable_shifts_count: int
    loss_making_shifts_count: int
    profit_margin_tiers: Dict[str, int]
    avg_break_even_deliveries: float
    highest_profit_modality: str
    distressed_shifts_sample: List[Dict[str, Any]]
