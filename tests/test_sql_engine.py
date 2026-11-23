"""Tests for SQL schema, analytical views, and query execution."""

import pytest
import pandas as pd
from sqlalchemy import text
from src.analytics.sql_engine import DatabaseManager


@pytest.fixture
def in_memory_db():
    """Create an isolated in-memory SQLite database for testing."""
    manager = DatabaseManager(db_url="sqlite:///:memory:")
    manager.initialize_schema()
    return manager


class TestDatabaseManagerAndViews:
    """Test SQL schema migration, data insertion, and view computations."""

    def test_schema_and_view_initialization(self, in_memory_db):
        with in_memory_db.engine.connect() as conn:
            # Check tables exist
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table';")
            ).fetchall()
            table_names = [t[0] for t in tables]
            assert "shifts" in table_names
            assert "workers" in table_names
            assert "benchmark_research" in table_names

            # Check views exist
            views = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='view';")
            ).fetchall()
            view_names = [v[0] for v in views]
            assert "v_shift_financials" in view_names
            assert "v_daily_worker_summary" in view_names
            assert "v_monthly_trends" in view_names
            assert "v_high_expense_shifts" in view_names

    def test_view_financial_calculations(self, in_memory_db):
        # Insert a sample shift
        shift_data = pd.DataFrame([{
            "worker_pseudonym": "WRK-SQLTEST01",
            "shift_date": "2026-03-01",
            "start_time": "09:00",
            "end_time": "17:00",
            "total_hours": 8.0,
            "orders_completed": 16,
            "total_distance_km": 100.0,
            "paid_distance_km": 75.0,
            "waiting_time_hours": 2.0,
            "base_payout": 600.0,
            "incentive_pay": 200.0,
            "bonus_pay": 50.0,
            "deductions": 30.0,
            "cancellations_count": 1,
            "cancellation_penalties": 20.0,
            "fuel_expense": 250.0,
            "maintenance_expense": 40.0,
            "other_expenses": 10.0,
            "platform_category": "Food Delivery",
            "vehicle_type": "Motorcycle",
            "city": "Bengaluru",
            "data_origin": "DEMO_SYNTHETIC",
            "consent_confirmed": True,
        }])
        in_memory_db.load_shifts_dataframe(shift_data)

        # Query view
        view_df = in_memory_db.get_financial_view()
        assert len(view_df) == 1
        row = view_df.iloc[0]

        # Gross = 600 + 200 + 50 = 850
        assert row["gross_earnings"] == 850.0
        # Total Expenses = 250 (fuel) + 40 (maint) + 10 (other) + 20 (penalty) = 320
        assert row["total_expenses"] == 320.0
        # Net = 850 - 30 (deductions) - 320 (expenses) = 500
        assert row["net_earnings"] == 500.0
        # Effective Net Hourly = 500 / 8 = 62.5
        assert row["effective_hourly_net"] == 62.5
        # Net per km = 500 / 100 = 5.0
        assert row["net_earnings_per_km"] == 5.0
        # Unpaid time ratio = 2.0 / 8.0 = 0.25
        assert row["unpaid_time_ratio"] == 0.25
