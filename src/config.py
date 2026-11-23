"""Configuration module for GIGLEDGER platform.

Centralizes paths, database URLs, privacy parameters, financial validation rules,
and analytical thresholds.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
TEMPLATES_DIR = DATA_DIR / "templates"
SQL_DIR = BASE_DIR / "sql"
REPORTS_DIR = BASE_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'gigledger.db'}")
DB_ECHO = os.getenv("DB_ECHO", "False").lower() in ("true", "1")

# Privacy & Consent Configuration
PRIVACY_SALT = os.getenv("GIGLEDGER_SALT", "gigledger-secure-salt-2026-anonymize")
K_ANONYMITY_THRESHOLD = 5  # Minimum cohort size required to report aggregated statistics
CONSENT_REQUIRED = True

# Data Classification Identifiers
DATA_ORIGIN_PUBLIC_RESEARCH = "PUBLIC_RESEARCH"
DATA_ORIGIN_PARTICIPANT = "PARTICIPANT_REPORTED"
DATA_ORIGIN_DEMO = "DEMO_SYNTHETIC"

VALID_DATA_ORIGINS = {
    DATA_ORIGIN_PUBLIC_RESEARCH,
    DATA_ORIGIN_PARTICIPANT,
    DATA_ORIGIN_DEMO,
}

# Financial & Operating Limits for Validation
FINANCIAL_BOUNDS: Dict[str, Any] = {
    "max_shift_hours": 24.0,
    "min_shift_hours": 0.1,
    "max_speed_kmh": 120.0,  # Filter impossible travel speeds (distance / hours)
    "max_single_shift_payout": 50000.0,
    "max_fuel_cost_per_km": 50.0,
    "statutory_min_wage_hourly": 100.0,  # Benchmark comparison (INR/hr nominal baseline)
    "currency_symbol": "₹",
    "currency_code": "INR"
}

# Vehicle Types & Platform Categories
VEHICLE_TYPES = ["Motorcycle", "Scooter", "Bicycle", "Electric 2W", "Car / Cab", "Walking"]
PLATFORM_MODES = ["Food Delivery", "Quick Commerce / Grocery", "E-commerce Parcel", "Ride-hailing"]

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
