"""Time and currency normalizers for GIGLEDGER."""

import re
from datetime import datetime, time
from typing import Optional, Union, Tuple
import pandas as pd


class TimeNormalizer:
    """Parses and standardizes time strings and shift durations."""

    @staticmethod
    def parse_time_string(time_str: Any) -> Optional[str]:
        """Convert varied time representations into standard HH:MM 24h format."""
        if time_str is None or pd.isna(time_str):
            return None

        s = str(time_str).strip()
        if not s:
            return None

        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p", "%I %p"):
            try:
                t = datetime.strptime(s, fmt).time()
                return t.strftime("%H:%M")
            except ValueError:
                continue

        # If it looks like integer hours (e.g. 9 or 14)
        if s.isdigit():
            val = int(s)
            if 0 <= val <= 23:
                return f"{val:02d}:00"

        return None

    @staticmethod
    def calculate_duration_hours(
        start_time_str: Optional[str],
        end_time_str: Optional[str],
    ) -> Optional[float]:
        """Compute shift duration in decimal hours between start and end times, accounting for midnight crossovers."""
        t1_str = TimeNormalizer.parse_time_string(start_time_str)
        t2_str = TimeNormalizer.parse_time_string(end_time_str)

        if not t1_str or not t2_str:
            return None

        t1 = datetime.strptime(t1_str, "%H:%M")
        t2 = datetime.strptime(t2_str, "%H:%M")

        delta_seconds = (t2 - t1).total_seconds()
        if delta_seconds < 0:
            # Shift crossed midnight (e.g. 21:00 to 03:00)
            delta_seconds += 24 * 3600

        return round(delta_seconds / 3600.0, 2)


class CurrencyNormalizer:
    """Strips currency symbols (₹, $, €, Rs, INR) and thousands separators."""

    @staticmethod
    def clean_monetary_value(val: Any) -> float:
        if val is None or pd.isna(val):
            return 0.0

        if isinstance(val, (int, float)):
            return float(val)

        s = str(val).strip()
        # Remove currency symbols and formatting
        cleaned = re.sub(r"[₹\$,\s€£]|(?:Rs\.?|INR)", "", s, flags=re.IGNORECASE)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
