"""Data validation and integrity auditing for GIGLEDGER.

Verifies logical consistency, physical feasibility (speed limits, shift durations),
non-negativity of monetary quantities, consent verification, and absence of PII.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator

from src.config import (
    VALID_DATA_ORIGINS,
    FINANCIAL_BOUNDS,
    DATA_ORIGIN_PARTICIPANT,
    VEHICLE_TYPES,
    PLATFORM_MODES,
)


class ValidationErrorItem(BaseModel):
    """Detailed item describing a validation anomaly."""
    row_index: int
    field_name: str
    rejected_value: Any
    reason: str


class ShiftRecordModel(BaseModel):
    """Pydantic model representing a single shift record for strict schema verification."""
    worker_pseudonym: str
    shift_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_hours: float = Field(..., ge=0.05, le=24.0)
    orders_completed: int = Field(default=0, ge=0)
    total_distance_km: float = Field(default=0.0, ge=0.0)
    paid_distance_km: Optional[float] = Field(default=None, ge=0.0)
    waiting_time_hours: Optional[float] = Field(default=0.0, ge=0.0)
    
    base_payout: float = Field(default=0.0, ge=0.0)
    incentive_pay: float = Field(default=0.0, ge=0.0)
    bonus_pay: float = Field(default=0.0, ge=0.0)
    deductions: float = Field(default=0.0, ge=0.0)
    cancellations_count: int = Field(default=0, ge=0)
    cancellation_penalties: float = Field(default=0.0, ge=0.0)
    
    fuel_expense: float = Field(default=0.0, ge=0.0)
    maintenance_expense: float = Field(default=0.0, ge=0.0)
    other_expenses: float = Field(default=0.0, ge=0.0)
    
    platform_category: Optional[str] = None
    vehicle_type: Optional[str] = None
    city: Optional[str] = None
    data_origin: str = "DEMO_SYNTHETIC"
    consent_confirmed: bool = True

    @field_validator("data_origin")
    @classmethod
    def validate_origin(cls, v: str) -> str:
        if v not in VALID_DATA_ORIGINS:
            raise ValueError(f"Invalid data_origin '{v}'. Must be one of {VALID_DATA_ORIGINS}")
        return v

    @model_validator(mode="after")
    def validate_cross_field_logic(self) -> "ShiftRecordModel":
        # 1. Paid distance cannot exceed total distance
        if self.paid_distance_km is not None and self.paid_distance_km > self.total_distance_km:
            raise ValueError(
                f"Paid distance ({self.paid_distance_km} km) cannot exceed total distance ({self.total_distance_km} km)"
            )

        # 2. Waiting time cannot exceed total shift hours
        if self.waiting_time_hours is not None and self.waiting_time_hours > self.total_hours:
            raise ValueError(
                f"Waiting time ({self.waiting_time_hours}h) cannot exceed total shift hours ({self.total_hours}h)"
            )

        # 3. Speed sanity check
        if self.total_hours > 0 and (self.total_distance_km / self.total_hours) > FINANCIAL_BOUNDS["max_speed_kmh"]:
            raise ValueError(
                f"Implausible average speed: {self.total_distance_km / self.total_hours:.1f} km/h (exceeds {FINANCIAL_BOUNDS['max_speed_kmh']} km/h)"
            )

        # 4. Consent confirmation required for participant reports
        if self.data_origin == DATA_ORIGIN_PARTICIPANT and not self.consent_confirmed:
            raise ValueError("Participant-reported shifts require explicit consent confirmation (consent_confirmed=True)")

        return self


class DatasetValidator:
    """Validates raw tabular shift DataFrames, cataloging all errors and row discrepancies."""

    def __init__(self, reject_forbidden_columns: bool = True):
        self.reject_forbidden_columns = reject_forbidden_columns
        self.forbidden_keywords = [
            "password", "secret", "pin", "otp", "aadhaar", "pan_card", "ssn",
            "bank_account", "cvv", "credit_card", "upi_pin"
        ]

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, pd.DataFrame, List[ValidationErrorItem]]:
        """Validate an entire DataFrame.

        Returns:
            Tuple of (is_fully_valid, valid_cleaned_df, error_items_list).
        """
        errors: List[ValidationErrorItem] = []

        # 1. Check for unauthorized credential/PII columns
        for col in df.columns:
            for forbidden in self.forbidden_keywords:
                if forbidden in str(col).lower():
                    errors.append(
                        ValidationErrorItem(
                            row_index=-1,
                            field_name=str(col),
                            rejected_value="[REDACTED_SECURITY_RISK]",
                            reason=f"Column '{col}' matches forbidden credential or sensitive identifier keyword.",
                        )
                    )

        if errors and self.reject_forbidden_columns:
            return False, pd.DataFrame(), errors

        valid_rows: List[Dict[str, Any]] = []

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            # Normalize field names
            row_clean = {str(k).strip().lower(): v for k, v in row_dict.items()}

            # Parse date
            try:
                if "shift_date" in row_clean and not pd.isna(row_clean["shift_date"]):
                    if isinstance(row_clean["shift_date"], (datetime, date)):
                        row_clean["shift_date"] = pd.to_datetime(row_clean["shift_date"]).date()
                    else:
                        row_clean["shift_date"] = pd.to_datetime(str(row_clean["shift_date"])).date()
                else:
                    errors.append(
                        ValidationErrorItem(
                            row_index=int(idx),
                            field_name="shift_date",
                            rejected_value=row_clean.get("shift_date"),
                            reason="Missing or unparseable shift_date.",
                        )
                    )
                    continue
            except Exception as e:
                errors.append(
                    ValidationErrorItem(
                        row_index=int(idx),
                        field_name="shift_date",
                        rejected_value=row_clean.get("shift_date"),
                        reason=f"Date parsing error: {str(e)}",
                    )
                )
                continue

            # Check required numeric fields
            try:
                total_hours = float(row_clean.get("total_hours", 0.0))
                if total_hours <= 0.0 or total_hours > 24.0:
                    errors.append(
                        ValidationErrorItem(
                            row_index=int(idx),
                            field_name="total_hours",
                            rejected_value=total_hours,
                            reason=f"total_hours must be between 0.1 and 24.0 (got {total_hours})",
                        )
                    )
                    continue
            except (ValueError, TypeError):
                errors.append(
                    ValidationErrorItem(
                        row_index=int(idx),
                        field_name="total_hours",
                        rejected_value=row_clean.get("total_hours"),
                        reason="total_hours must be a valid numeric value.",
                    )
                )
                continue

            # Fill defaults for optional numerics
            for num_col in [
                "orders_completed", "total_distance_km", "paid_distance_km", "waiting_time_hours",
                "base_payout", "incentive_pay", "bonus_pay", "deductions", "cancellations_count",
                "cancellation_penalties", "fuel_expense", "maintenance_expense", "other_expenses"
            ]:
                if num_col not in row_clean or pd.isna(row_clean[num_col]):
                    row_clean[num_col] = 0.0 if num_col != "paid_distance_km" else None
                else:
                    try:
                        row_clean[num_col] = float(row_clean[num_col])
                    except (ValueError, TypeError):
                        row_clean[num_col] = 0.0

            # Convert orders and cancellations to int
            row_clean["orders_completed"] = int(row_clean.get("orders_completed", 0))
            row_clean["cancellations_count"] = int(row_clean.get("cancellations_count", 0))

            # Default consent_confirmed
            consent_val = str(row_clean.get("consent_confirmed", "true")).strip().lower()
            row_clean["consent_confirmed"] = consent_val in ("true", "1", "yes", "t")

            # Default data_origin
            origin_val = str(row_clean.get("data_origin", "DEMO_SYNTHETIC")).strip().upper()
            row_clean["data_origin"] = origin_val if origin_val in VALID_DATA_ORIGINS else "DEMO_SYNTHETIC"

            # Validate with Pydantic
            try:
                validated_model = ShiftRecordModel(**row_clean)
                valid_rows.append(validated_model.model_dump())
            except Exception as e:
                errors.append(
                    ValidationErrorItem(
                        row_index=int(idx),
                        field_name="schema_validation",
                        rejected_value=str(row_clean.get("worker_pseudonym", "UNKNOWN")),
                        reason=str(e),
                    )
                )

        valid_df = pd.DataFrame(valid_rows)
        is_valid = len(errors) == 0
        return is_valid, valid_df, errors
