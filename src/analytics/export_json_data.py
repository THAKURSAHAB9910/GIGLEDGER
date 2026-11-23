"""Export sample datasets to JSON for the static live web dashboard."""

import json
from pathlib import Path
import pandas as pd
from src.config import SAMPLE_DATA_DIR, BASE_DIR
from src.analytics.sql_engine import get_db_manager


def export_json_datasets():
    db = get_db_manager()
    df_shifts = db.get_financial_view()

    # Drop columns not needed on frontend to keep JSON compact (~150 KB)
    compact_cols = [
        "shift_id", "worker_pseudonym", "shift_date", "total_hours", "orders_completed",
        "total_distance_km", "paid_distance_km", "waiting_time_hours",
        "gross_earnings", "base_payout", "incentive_pay", "bonus_pay", "deductions",
        "total_expenses", "fuel_expense", "maintenance_expense", "other_expenses",
        "cancellations_count", "cancellation_penalties", "net_earnings",
        "effective_hourly_gross", "effective_hourly_net", "net_earnings_per_km",
        "expense_ratio", "incentive_dependency", "unpaid_time_ratio", "unpaid_distance_ratio",
        "is_weekend", "year_month", "platform_category", "vehicle_type", "city", "data_origin"
    ]
    df_compact = df_shifts[[c for c in compact_cols if c in df_shifts.columns]].copy()
    
    # Save to data/sample/shifts_data.json
    shifts_json_path = SAMPLE_DATA_DIR / "shifts_data.json"
    df_compact.to_json(shifts_json_path, orient="records", date_format="iso")
    print(f"Exported {len(df_compact)} shifts to {shifts_json_path}")

    # Also save benchmark research
    bench_file = SAMPLE_DATA_DIR / "benchmark_research_data.csv"
    if bench_file.exists():
        df_bench = pd.read_csv(bench_file)
        bench_json_path = SAMPLE_DATA_DIR / "benchmark_data.json"
        df_bench.to_json(bench_json_path, orient="records")
        print(f"Exported {len(df_bench)} benchmarks to {bench_json_path}")


if __name__ == "__main__":
    export_json_datasets()
