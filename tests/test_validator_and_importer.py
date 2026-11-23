"""Tests for CSV parsing, schema validation, and physical bounds checks."""

import io
import pytest
from datetime import date
import pandas as pd

from src.ingestion.validator import ShiftRecordModel, DatasetValidator
from src.ingestion.importer import CSVShiftImporter
from src.analytics.sql_engine import DatabaseManager


class TestShiftRecordModel:
    """Test individual record physical and financial validation rules."""

    def test_valid_record(self):
        rec = ShiftRecordModel(
            worker_pseudonym="WRK-1A2B3C4D",
            shift_date=date(2026, 3, 1),
            total_hours=8.0,
            orders_completed=14,
            total_distance_km=90.0,
            paid_distance_km=65.0,
            waiting_time_hours=2.0,
            base_payout=600.0,
            incentive_pay=200.0,
            fuel_expense=220.0,
        )
        assert rec.worker_pseudonym == "WRK-1A2B3C4D"
        assert rec.total_hours == 8.0

    def test_paid_distance_exceeds_total_distance_fails(self):
        with pytest.raises(ValueError, match="Paid distance .* cannot exceed total distance"):
            ShiftRecordModel(
                worker_pseudonym="WRK-1A2B3C4D",
                shift_date=date(2026, 3, 1),
                total_hours=8.0,
                total_distance_km=50.0,
                paid_distance_km=75.0,  # Invalid: paid > total
            )

    def test_waiting_time_exceeds_total_hours_fails(self):
        with pytest.raises(ValueError, match="Waiting time .* cannot exceed total shift hours"):
            ShiftRecordModel(
                worker_pseudonym="WRK-1A2B3C4D",
                shift_date=date(2026, 3, 1),
                total_hours=6.0,
                waiting_time_hours=8.5,  # Invalid: waiting > total
            )

    def test_impossible_speed_fails(self):
        with pytest.raises(ValueError, match="Implausible average speed"):
            ShiftRecordModel(
                worker_pseudonym="WRK-1A2B3C4D",
                shift_date=date(2026, 3, 1),
                total_hours=2.0,
                total_distance_km=300.0,  # 150 km/h average speed in city delivery
            )

    def test_participant_report_without_consent_fails(self):
        with pytest.raises(ValueError, match="Participant-reported shifts require explicit consent confirmation"):
            ShiftRecordModel(
                worker_pseudonym="WRK-1A2B3C4D",
                shift_date=date(2026, 3, 1),
                total_hours=8.0,
                data_origin="PARTICIPANT_REPORTED",
                consent_confirmed=False,
            )


class TestDatasetValidator:
    """Test tabular DataFrame validation and forbidden column rejection."""

    def test_forbidden_password_column_rejected(self):
        validator = DatasetValidator(reject_forbidden_columns=True)
        bad_df = pd.DataFrame({
            "worker_pseudonym": ["WRK-001"],
            "shift_date": ["2026-03-01"],
            "total_hours": [8.0],
            "password_hash": ["secret"],  # Forbidden!
        })
        is_valid, valid_df, errors = validator.validate_dataframe(bad_df)
        assert is_valid is False
        assert valid_df.empty
        assert any("matches forbidden credential" in e.reason for e in errors)

    def test_csv_shift_importer_valid_string_io(self):
        importer = CSVShiftImporter()
        csv_data = """worker_pseudonym,shift_date,total_hours,orders_completed,total_distance_km,paid_distance_km,waiting_time_hours,base_payout,incentive_pay,bonus_pay,deductions,fuel_expense,maintenance_expense,other_expenses,cancellations_count,cancellation_penalties,platform_category,vehicle_type,city,data_origin,consent_confirmed
WRK-TEST01,2026-03-01,8.0,15,100.0,75.0,2.0,600.0,200.0,0.0,0.0,250.0,40.0,10.0,0,0.0,Food Delivery,Motorcycle,Bengaluru,DEMO_SYNTHETIC,TRUE
WRK-TEST02,2026-03-01,9.0,18,120.0,85.0,2.5,750.0,250.0,50.0,20.0,300.0,50.0,15.0,1,30.0,Quick Commerce / Grocery,Scooter,Delhi-NCR,DEMO_SYNTHETIC,TRUE
"""
        res = importer.process_file_or_buffer(io.StringIO(csv_data), auto_commit_to_db=False)
        assert res["success"] is True
        assert res["valid_rows"] == 2
        assert res["rejected_rows"] == 0
        assert "gross_earnings" in res["data"].columns
        assert "net_earnings" in res["data"].columns
