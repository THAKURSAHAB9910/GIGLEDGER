"""Robust CSV and data import pipeline for GIGLEDGER.

Parses files, scrubs potential PII, pseudonymizes identifiers, validates rows,
computes financial metrics, and writes to database.
"""

import io
from pathlib import Path
from typing import Union, Tuple, List, Dict, Any, Optional
import pandas as pd

from src.privacy.anonymizer import DataAnonymizer
from src.ingestion.validator import DatasetValidator, ValidationErrorItem
from src.calculations.metrics import compute_shift_metrics
from src.analytics.sql_engine import DatabaseManager, get_db_manager


class CSVShiftImporter:
    """End-to-end importer orchestrating file ingestion, privacy scrubbing, validation, and storage."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or get_db_manager()
        self.anonymizer = DataAnonymizer()
        self.validator = DatasetValidator()

    def process_file_or_buffer(
        self,
        file_input: Union[str, Path, io.StringIO, io.BytesIO],
        data_origin_override: Optional[str] = None,
        auto_commit_to_db: bool = False,
    ) -> Dict[str, Any]:
        """Process a CSV input, returning validation results and cleaned metrics.

        Args:
            file_input: File path or in-memory file buffer.
            data_origin_override: Force origin tag (e.g. PARTICIPANT_REPORTED).
            auto_commit_to_db: Whether to write valid rows directly to database.

        Returns:
            Dict containing summary stats, valid_df, and validation_errors.
        """
        # 1. Read CSV
        try:
            if isinstance(file_input, (io.StringIO, io.BytesIO)):
                raw_df = pd.read_csv(file_input)
            else:
                raw_df = pd.read_csv(Path(file_input))
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse CSV file: {str(e)}",
                "total_rows": 0,
                "valid_rows": 0,
                "rejected_rows": 0,
                "errors": [],
            }

        total_rows = len(raw_df)
        if total_rows == 0:
            return {
                "success": False,
                "error": "Uploaded CSV file is empty.",
                "total_rows": 0,
                "valid_rows": 0,
                "rejected_rows": 0,
                "errors": [],
            }

        # 2. Privacy & PII Anonymization
        # Detect if worker_id column exists and pseudonymize it
        id_col = "worker_pseudonym" if "worker_pseudonym" in raw_df.columns else "worker_id"
        anon_df = self.anonymizer.anonymize_dataframe(raw_df, worker_id_col=id_col)

        # Apply data origin override if provided
        if data_origin_override:
            anon_df["data_origin"] = data_origin_override

        # 3. Validation
        is_valid, validated_df, validation_errors = self.validator.validate_dataframe(anon_df)

        if validated_df.empty:
            return {
                "success": False,
                "error": "All submitted rows failed validation checks.",
                "total_rows": total_rows,
                "valid_rows": 0,
                "rejected_rows": total_rows,
                "errors": [err.model_dump() for err in validation_errors],
            }

        # 4. Compute Derived Financial & Operational Metrics
        enriched_df = compute_shift_metrics(validated_df)

        # 5. Optional DB Commit
        inserted_count = 0
        if auto_commit_to_db and not enriched_df.empty:
            inserted_count = self.db_manager.load_shifts_dataframe(enriched_df, if_exists="append")

        return {
            "success": True,
            "total_rows": total_rows,
            "valid_rows": len(enriched_df),
            "rejected_rows": total_rows - len(enriched_df),
            "inserted_to_db": inserted_count,
            "errors": [err.model_dump() for err in validation_errors],
            "data": enriched_df,
        }
