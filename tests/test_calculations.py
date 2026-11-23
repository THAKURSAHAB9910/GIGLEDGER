"""Tests for core financial, operational, and rate calculations in GIGLEDGER."""

import pytest
import numpy as np
import pandas as pd

from src.calculations.earnings import (
    calculate_gross_earnings,
    calculate_total_expenses,
    calculate_net_earnings,
    calculate_expense_ratio,
    safe_float,
)
from src.calculations.metrics import (
    calculate_effective_hourly_net,
    calculate_effective_hourly_gross,
    calculate_net_earnings_per_km,
    calculate_incentive_dependency,
    calculate_unpaid_time_ratio,
    calculate_unpaid_distance_ratio,
    calculate_shortfall_percentage,
    compute_shift_metrics,
)


class TestFinancialCalculations:
    """Test core financial logic against known reference values."""

    def test_gross_earnings_standard(self):
        # Base: 600, Incentive: 200, Bonus: 50 -> 850
        assert calculate_gross_earnings(600.0, 200.0, 50.0) == 850.0

    def test_gross_earnings_with_missing_and_nans(self):
        assert calculate_gross_earnings(None, 100.0, np.nan) == 100.0
        assert calculate_gross_earnings("invalid", 50, None) == 50.0

    def test_total_expenses_standard(self):
        # Fuel: 250, Maint: 40, Other: 20, Penalties: 30 -> 340
        assert calculate_total_expenses(250.0, 40.0, 20.0, 30.0) == 340.0

    def test_net_earnings_positive(self):
        # Gross: 1000, Deductions: 50, Expenses: 350 -> Net: 600
        assert calculate_net_earnings(1000.0, 50.0, 350.0) == 600.0

    def test_net_earnings_negative_loss_making(self):
        # Shift where expenses exceeded gross payout
        # Gross: 400, Deductions: 50, Expenses: 500 -> Net: -150
        net = calculate_net_earnings(400.0, 50.0, 500.0)
        assert net == -150.0

    def test_expense_ratio_standard(self):
        # Expenses: 300, Gross: 1000 -> 0.30
        assert calculate_expense_ratio(300.0, 1000.0) == 0.30

    def test_expense_ratio_zero_gross_guard(self):
        # Guard against division by zero
        assert calculate_expense_ratio(150.0, 0.0) == 0.0
        assert calculate_expense_ratio(150.0, -50.0) == 0.0


class TestRateMetricsAndGuards:
    """Test hourly and per-km operational rates and zero-division guards."""

    def test_effective_hourly_net_standard(self):
        # Net: 720, Hours: 8.0 -> 90.0 / hr
        assert calculate_effective_hourly_net(720.0, 8.0) == 90.0

    def test_effective_hourly_net_zero_hours_guard(self):
        # Zero or negative hours must return 0.0, never raise ZeroDivisionError
        assert calculate_effective_hourly_net(500.0, 0.0) == 0.0
        assert calculate_effective_hourly_net(500.0, -2.0) == 0.0
        assert calculate_effective_hourly_net(500.0, None) == 0.0

    def test_net_earnings_per_km_standard(self):
        # Net: 600, Distance: 100 km -> 6.0 / km
        assert calculate_net_earnings_per_km(600.0, 100.0) == 6.0

    def test_net_earnings_per_km_zero_distance_guard(self):
        assert calculate_net_earnings_per_km(600.0, 0.0) == 0.0
        assert calculate_net_earnings_per_km(600.0, -10.0) == 0.0

    def test_incentive_dependency_calculation(self):
        # Gross: 1000, Incentive: 300, Bonus: 100 -> 400 / 1000 = 0.40
        assert calculate_incentive_dependency(300.0, 100.0, 1000.0) == 0.40

    def test_incentive_dependency_zero_gross(self):
        assert calculate_incentive_dependency(100.0, 50.0, 0.0) == 0.0

    def test_unpaid_time_ratio(self):
        # Waiting: 2.5h, Total: 10.0h -> 0.25 (25%)
        assert calculate_unpaid_time_ratio(2.5, 10.0) == 0.25
        assert calculate_unpaid_time_ratio(2.0, 0.0) == 0.0

    def test_unpaid_distance_ratio(self):
        # Total: 100 km, Paid: 75 km -> Unpaid = 25 km -> 0.25
        assert calculate_unpaid_distance_ratio(100.0, 75.0) == 0.25
        assert calculate_unpaid_distance_ratio(0.0, 0.0) == 0.0

    def test_shortfall_percentage(self):
        # Gross: 1000, Net: 700 -> Shortfall = (1000 - 700) / 1000 * 100 = 30.0%
        assert calculate_shortfall_percentage(1000.0, 700.0) == 30.0
        assert calculate_shortfall_percentage(0.0, 0.0) == 0.0


class TestVectorizedShiftMetrics:
    """Test pandas Series and DataFrame vectorized transformations."""

    def test_compute_shift_metrics_dataframe(self):
        data = {
            "worker_pseudonym": ["WRK-01", "WRK-02"],
            "base_payout": [500.0, 800.0],
            "incentive_pay": [150.0, 200.0],
            "bonus_pay": [50.0, 0.0],
            "deductions": [20.0, 0.0],
            "fuel_expense": [180.0, 250.0],
            "maintenance_expense": [30.0, 50.0],
            "other_expenses": [10.0, 0.0],
            "cancellation_penalties": [10.0, 0.0],
            "total_hours": [8.0, 10.0],
            "total_distance_km": [90.0, 120.0],
            "paid_distance_km": [65.0, 90.0],
            "waiting_time_hours": [2.0, 2.5],
        }
        df = pd.DataFrame(data)
        enriched = compute_shift_metrics(df)

        # Check WRK-01
        # Gross = 500 + 150 + 50 = 700
        # Total Expenses = 180 + 30 + 10 + 10 = 230
        # Net = 700 - 20 - 230 = 450
        # Hourly Net = 450 / 8 = 56.25
        assert enriched.loc[0, "gross_earnings"] == 700.0
        assert enriched.loc[0, "total_expenses"] == 230.0
        assert enriched.loc[0, "net_earnings"] == 450.0
        assert enriched.loc[0, "effective_hourly_net"] == 56.25
        assert enriched.loc[0, "net_earnings_per_km"] == 450.0 / 90.0
