"""Data cleaning and string standardization for GIGLEDGER."""

import re
from typing import Dict, Any, List, Optional
import pandas as pd

from src.config import VEHICLE_TYPES, PLATFORM_MODES


class DataCleaner:
    """Standardizes messy input records, mapping varied category spellings to standard taxonomy."""

    VEHICLE_MAP = {
        "bike": "Motorcycle",
        "motorcycle": "Motorcycle",
        "motor bike": "Motorcycle",
        "2w": "Motorcycle",
        "two wheeler": "Motorcycle",
        "scooter": "Scooter",
        "activa": "Scooter",
        "ev": "Electric 2W",
        "ev 2w": "Electric 2W",
        "electric 2w": "Electric 2W",
        "electric scooter": "Electric 2W",
        "bicycle": "Bicycle",
        "cycle": "Bicycle",
        "cab": "Car / Cab",
        "car": "Car / Cab",
        "auto": "Auto Rickshaw",
        "walk": "Walking",
        "walking": "Walking",
    }

    PLATFORM_MAP = {
        "food": "Food Delivery",
        "food delivery": "Food Delivery",
        "restaurant": "Food Delivery",
        "grocery": "Quick Commerce / Grocery",
        "quick commerce": "Quick Commerce / Grocery",
        "instamart": "Quick Commerce / Grocery",
        "blinkit": "Quick Commerce / Grocery",
        "zepto": "Quick Commerce / Grocery",
        "parcel": "E-commerce Parcel",
        "courier": "E-commerce Parcel",
        "amazon": "E-commerce Parcel",
        "flipkart": "E-commerce Parcel",
        "ride": "Ride-hailing",
        "ride-hailing": "Ride-hailing",
        "taxi": "Ride-hailing",
        "cab": "Ride-hailing",
    }

    CITY_MAP = {
        "bangalore": "Bengaluru",
        "bengaluru": "Bengaluru",
        "blr": "Bengaluru",
        "delhi": "Delhi-NCR",
        "delhi ncr": "Delhi-NCR",
        "ncr": "Delhi-NCR",
        "gurgaon": "Delhi-NCR",
        "gurugram": "Delhi-NCR",
        "noida": "Delhi-NCR",
        "mumbai": "Mumbai",
        "bombay": "Mumbai",
        "hyderabad": "Hyderabad",
        "hyd": "Hyderabad",
        "chennai": "Chennai",
        "kolkata": "Kolkata",
        "pune": "Pune",
    }

    @classmethod
    def standardize_vehicle_type(cls, raw_type: Optional[str]) -> str:
        if not raw_type or pd.isna(raw_type):
            return "Motorcycle"
        cleaned = str(raw_type).strip().lower()
        return cls.VEHICLE_MAP.get(cleaned, "Motorcycle")

    @classmethod
    def standardize_platform_category(cls, raw_cat: Optional[str]) -> str:
        if not raw_cat or pd.isna(raw_cat):
            return "Food Delivery"
        cleaned = str(raw_cat).strip().lower()
        return cls.PLATFORM_MAP.get(cleaned, "Food Delivery")

    @classmethod
    def standardize_city(cls, raw_city: Optional[str]) -> str:
        if not raw_city or pd.isna(raw_city):
            return "Bengaluru"
        cleaned = str(raw_city).strip().lower()
        return cls.CITY_MAP.get(cleaned, str(raw_city).strip().title())

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all standardization routines to a shift DataFrame."""
        df_out = df.copy()

        # Clean string columns
        for col in ["platform_category", "vehicle_type", "city"]:
            if col in df_out.columns:
                df_out[col] = df_out[col].astype(str).str.strip()

        if "vehicle_type" in df_out.columns:
            df_out["vehicle_type"] = df_out["vehicle_type"].apply(self.standardize_vehicle_type)

        if "platform_category" in df_out.columns:
            df_out["platform_category"] = df_out["platform_category"].apply(self.standardize_platform_category)

        if "city" in df_out.columns:
            df_out["city"] = df_out["city"].apply(self.standardize_city)

        return df_out
