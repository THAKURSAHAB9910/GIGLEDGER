"""Database connectivity and SQL analytics runner for GIGLEDGER.

Manages SQLite/PostgreSQL schemas, views, data loads, and provides safe execution
of analytical queries with pandas DataFrame returns.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine

from src.config import DATABASE_URL, SQL_DIR, DB_ECHO

logger = logging.getLogger("gigledger.sql_engine")


class DatabaseManager:
    """Manages database connection, DDL migration, and query execution."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or DATABASE_URL
        self.engine: Engine = create_engine(self.db_url, echo=DB_ECHO)
        logger.info(f"Initialized DatabaseManager connected to {self.db_url}")

    def initialize_schema(self) -> None:
        """Run schema.sql and views.sql DDL scripts."""
        schema_file = SQL_DIR / "schema.sql"
        views_file = SQL_DIR / "views.sql"

        with self.engine.begin() as conn:
            if schema_file.exists():
                schema_sql = schema_file.read_text(encoding="utf-8")
                # Split statements by semicolon for SQLite compatibility
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        conn.execute(text(stmt))
                logger.info("Executed schema.sql successfully.")

            if views_file.exists():
                views_sql = views_file.read_text(encoding="utf-8")
                for statement in views_sql.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        conn.execute(text(stmt))
                logger.info("Executed views.sql successfully.")

    def load_shifts_dataframe(self, df: pd.DataFrame, if_exists: str = "append") -> int:
        """Insert or replace cleaned shifts into the shifts table."""
        if df.empty:
            return 0

        # Match columns with database table schema
        expected_cols = [
            "worker_pseudonym", "shift_date", "start_time", "end_time", "total_hours",
            "orders_completed", "total_distance_km", "paid_distance_km", "waiting_time_hours",
            "base_payout", "incentive_pay", "bonus_pay", "deductions", "cancellations_count",
            "cancellation_penalties", "fuel_expense", "maintenance_expense", "other_expenses",
            "platform_category", "vehicle_type", "city", "data_origin", "consent_confirmed"
        ]
        insert_df = df[[c for c in expected_cols if c in df.columns]].copy()
        
        # Populate workers dimension table first to satisfy foreign keys
        workers_df = (
            insert_df[["worker_pseudonym", "platform_category", "vehicle_type", "city", "data_origin", "consent_confirmed"]]
            .drop_duplicates(subset=["worker_pseudonym"])
        )
        workers_df.rename(columns={"city": "primary_city"}, inplace=True)

        with self.engine.begin() as conn:
            # Upsert/ignore workers
            for _, row in workers_df.iterrows():
                conn.execute(
                    text("""
                    INSERT OR IGNORE INTO workers (worker_pseudonym, platform_category, vehicle_type, primary_city, data_origin, consent_confirmed)
                    VALUES (:w, :p, :v, :c, :o, :con)
                    """),
                    {
                        "w": row["worker_pseudonym"],
                        "p": row["platform_category"],
                        "v": row["vehicle_type"],
                        "c": row["primary_city"],
                        "o": row["data_origin"],
                        "con": 1 if row["consent_confirmed"] else 0,
                    }
                )

        # Write shifts fact records
        with self.engine.begin() as conn:
            insert_df.to_sql("shifts", conn, if_exists=if_exists, index=False)
            logger.info(f"Loaded {len(insert_df)} shifts into database.")

        return len(insert_df)

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute any SELECT SQL query and return a pandas DataFrame."""
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(query), conn, params=params or {})

    def get_financial_view(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Fetch records from v_shift_financials with optional filtering."""
        base_query = "SELECT * FROM v_shift_financials WHERE 1=1"
        params: Dict[str, Any] = {}

        if filters:
            if "city" in filters and filters["city"] and filters["city"] != "All":
                base_query += " AND city = :city"
                params["city"] = filters["city"]
            if "vehicle_type" in filters and filters["vehicle_type"] and filters["vehicle_type"] != "All":
                base_query += " AND vehicle_type = :vehicle_type"
                params["vehicle_type"] = filters["vehicle_type"]
            if "platform_category" in filters and filters["platform_category"] and filters["platform_category"] != "All":
                base_query += " AND platform_category = :platform_category"
                params["platform_category"] = filters["platform_category"]
            if "data_origin" in filters and filters["data_origin"] and filters["data_origin"] != "All":
                base_query += " AND data_origin = :data_origin"
                params["data_origin"] = filters["data_origin"]
            if "start_date" in filters and filters["start_date"]:
                base_query += " AND shift_date >= :start_date"
                params["start_date"] = str(filters["start_date"])
            if "end_date" in filters and filters["end_date"]:
                base_query += " AND shift_date <= :end_date"
                params["end_date"] = str(filters["end_date"])

        base_query += " ORDER BY shift_date DESC"
        return self.execute_query(base_query, params)

    def get_monthly_trends(self) -> pd.DataFrame:
        """Fetch aggregated monthly platform trends."""
        return self.execute_query("SELECT * FROM v_monthly_trends ORDER BY year_month ASC")

    def get_high_expense_shifts(self) -> pd.DataFrame:
        """Fetch shifts flagging extreme expense ratios or negative net earnings."""
        return self.execute_query("SELECT * FROM v_high_expense_shifts ORDER BY expense_ratio DESC")


# Global Singleton accessor
_DB_INSTANCE: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    global _DB_INSTANCE
    if _DB_INSTANCE is None:
        _DB_INSTANCE = DatabaseManager()
    return _DB_INSTANCE
