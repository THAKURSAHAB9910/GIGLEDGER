"""Tests for econometric investigations and advanced analytics."""

import pytest
import numpy as np
import pandas as pd

from src.analytics.advanced_analytics import AdvancedAnalyticsEngine
from src.calculations.statistical import (
    calculate_volatility_metrics,
    calculate_distribution_percentiles,
    compare_weekday_weekend_earnings,
)


@pytest.fixture
def sample_analytics_dataframe():
    """Create a diverse mock dataset for statistical testing."""
    np.random.seed(42)
    n = 60
    hours = np.random.uniform(4.0, 12.0, n)
    gross = hours * np.random.uniform(90.0, 130.0, n)
    expenses = gross * np.random.uniform(0.20, 0.40, n)
    net = gross - expenses

    dates = pd.date_range("2026-01-01", periods=n, freq="D")
    waiting_hours = hours * np.random.uniform(0.15, 0.40, n)
    df = pd.DataFrame({
        "shift_id": range(1, n + 1),
        "worker_pseudonym": [f"WRK-{(i%5)+1:02d}" for i in range(n)],
        "shift_date": dates,
        "total_hours": hours,
        "orders_completed": np.random.randint(6, 26, n),
        "total_distance_km": hours * 10.0,
        "paid_distance_km": hours * 7.5,
        "waiting_time_hours": waiting_hours,
        "gross_earnings": gross,
        "total_expenses": expenses,
        "net_earnings": net,
        "effective_hourly_gross": gross / hours,
        "effective_hourly_net": net / hours,
        "expense_ratio": expenses / gross,
        "unpaid_time_ratio": waiting_hours / hours,
        "cancellations_count": np.random.choice([0, 1], p=[0.8, 0.2], size=n),
        "cancellation_penalties": np.zeros(n),
        "fuel_expense": expenses * 0.7,
        "maintenance_expense": expenses * 0.2,
        "other_expenses": expenses * 0.1,
        "platform_category": "Food Delivery",
        "vehicle_type": "Motorcycle",
        "city": "Bengaluru",
        "data_origin": "DEMO_SYNTHETIC",
        "consent_confirmed": True,
    })
    return df


class TestAdvancedAnalyticsEngine:
    """Test econometric investigations."""

    def test_hours_diminishing_returns(self, sample_analytics_dataframe):
        engine = AdvancedAnalyticsEngine(sample_analytics_dataframe)
        res = engine.analyze_hours_diminishing_returns()
        assert res["sample_size"] == len(sample_analytics_dataframe)
        assert "pearson_r" in res
        assert "pearson_p_value" in res
        assert "binned_summary" in res
        assert len(res["binned_summary"]) > 0

    def test_incentive_threshold_clustering(self, sample_analytics_dataframe):
        engine = AdvancedAnalyticsEngine(sample_analytics_dataframe)
        res = engine.analyze_incentive_threshold_clustering()
        assert res["sample_size"] == len(sample_analytics_dataframe)
        assert "tier_clusters" in res
        assert "target_15" in res["tier_clusters"]

    def test_waiting_time_impact(self, sample_analytics_dataframe):
        engine = AdvancedAnalyticsEngine(sample_analytics_dataframe)
        res = engine.analyze_waiting_time_impact()
        assert "pearson_correlation" in res
        assert "quartile_breakdown" in res

    def test_expense_composition(self, sample_analytics_dataframe):
        engine = AdvancedAnalyticsEngine(sample_analytics_dataframe)
        res = engine.analyze_expense_composition()
        assert "fuel_percentage" in res
        assert "maintenance_percentage" in res
        assert res["primary_expense_drain"] in ("Fuel / EV Recharging", "Vehicle Maintenance")

    def test_weekday_vs_weekend_hypothesis_test(self, sample_analytics_dataframe):
        ww_res = compare_weekday_weekend_earnings(sample_analytics_dataframe)
        assert "weekday_mean" in ww_res
        assert "weekend_mean" in ww_res
        assert "mann_whitney_p_value" in ww_res
        assert "t_p_value" in ww_res
