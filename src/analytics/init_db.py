"""Database initialization and bootstrapping script for GIGLEDGER.

Applies DDL schema and views, then loads benchmark research data and demo shifts.
"""

from pathlib import Path
import pandas as pd
from sqlalchemy import text

from src.config import SAMPLE_DATA_DIR
from src.analytics.sql_engine import get_db_manager
from src.ingestion.importer import CSVShiftImporter


def bootstrap_database() -> None:
    """Initialize DB tables, views, and seed datasets."""
    print("--- Initializing GIGLEDGER Database ---")
    db_manager = get_db_manager()
    db_manager.initialize_schema()

    # 1. Load benchmark research
    benchmark_file = SAMPLE_DATA_DIR / "benchmark_research_data.csv"
    if benchmark_file.exists():
        df_benchmarks = pd.read_csv(benchmark_file)
        with db_manager.engine.begin() as conn:
            conn.execute(text("DELETE FROM benchmark_research;"))
            df_benchmarks.to_sql("benchmark_research", conn, if_exists="append", index=False)
        print(f"Loaded {len(df_benchmarks)} public research benchmark records.")

    # 2. Ingest demo shifts
    demo_file = SAMPLE_DATA_DIR / "demo_shifts.csv"
    if demo_file.exists():
        importer = CSVShiftImporter(db_manager=db_manager)
        # Clear existing shifts to ensure clean state
        with db_manager.engine.begin() as conn:
            conn.execute(text("DELETE FROM shifts;"))
            conn.execute(text("DELETE FROM workers;"))
        res = importer.process_file_or_buffer(demo_file, auto_commit_to_db=True)
        print(f"Demo shifts ingestion result: Success={res['success']}, Valid Rows={res['valid_rows']}, Inserted={res['inserted_to_db']}")

    # 3. Verify views
    with db_manager.engine.connect() as conn:
        shift_count = conn.execute(text("SELECT COUNT(*) FROM shifts;")).scalar()
        view_count = conn.execute(text("SELECT COUNT(*) FROM v_shift_financials;")).scalar()
        monthly_count = conn.execute(text("SELECT COUNT(*) FROM v_monthly_trends;")).scalar()
        print(f"Verification: {shift_count} rows in 'shifts', {view_count} rows in 'v_shift_financials', {monthly_count} months aggregated.")
    print("--- Database Bootstrap Complete ---")


if __name__ == "__main__":
    bootstrap_database()
