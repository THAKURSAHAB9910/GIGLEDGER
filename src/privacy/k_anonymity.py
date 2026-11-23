"""K-Anonymity enforcement module for GIGLEDGER.

Ensures that no aggregated slice, dashboard chart, or cohort comparison reveals
individual worker identities when group size is below the k threshold (default: k=5).
"""

from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
from src.config import K_ANONYMITY_THRESHOLD


class KAnonymityChecker:
    """Enforces k-anonymity on analytical group-bys and aggregates."""

    def __init__(self, k: int = K_ANONYMITY_THRESHOLD):
        self.k = k

    def assess_dataframe(
        self,
        df: pd.DataFrame,
        quasi_identifiers: List[str],
        worker_id_col: str = "worker_pseudonym",
    ) -> Tuple[bool, int, pd.DataFrame]:
        """Assess the k-anonymity of a DataFrame given a set of quasi-identifiers.

        Args:
            df: The dataset to assess.
            quasi_identifiers: Attributes that could be combined to identify workers (e.g. ['city', 'vehicle_type']).
            worker_id_col: Unique identifier for each worker.

        Returns:
            Tuple of (is_k_anonymous, min_cohort_size, violation_groups_df).
        """
        valid_cols = [c for c in quasi_identifiers if c in df.columns]
        if not valid_cols or df.empty:
            return True, len(df), pd.DataFrame()

        # Count distinct workers per quasi-identifier bucket
        group_counts = (
            df.groupby(valid_cols)[worker_id_col]
            .nunique()
            .reset_index(name="distinct_workers")
        )

        min_workers = int(group_counts["distinct_workers"].min()) if not group_counts.empty else 0
        violations = group_counts[group_counts["distinct_workers"] < self.k]

        is_k_anon = min_workers >= self.k and len(violations) == 0
        return is_k_anon, min_workers, violations

    def enforce_k_anonymity(
        self,
        df: pd.DataFrame,
        group_cols: List[str],
        worker_id_col: str = "worker_pseudonym",
        suppression_label: str = "Suppressed (n < 5)",
    ) -> pd.DataFrame:
        """Enforce k-anonymity by replacing values in low-count cohorts with a suppression label.

        Args:
            df: Input DataFrame.
            group_cols: Columns used for grouping.
            worker_id_col: Column containing worker IDs.
            suppression_label: Replacement text for groups below threshold.

        Returns:
            A transformed DataFrame safe for public presentation.
        """
        if df.empty or not group_cols:
            return df.copy()

        df_out = df.copy()
        # Find distinct worker counts per group
        cohort_counts = (
            df_out.groupby(group_cols)[worker_id_col]
            .nunique()
            .reset_index(name="_worker_count")
        )

        # Merge back
        df_out = df_out.merge(cohort_counts, on=group_cols, how="left")

        # Suppress groups below k
        mask = df_out["_worker_count"] < self.k
        for col in group_cols:
            if mask.any():
                df_out.loc[mask, col] = suppression_label

        df_out.drop(columns=["_worker_count"], inplace=True)
        return df_out
