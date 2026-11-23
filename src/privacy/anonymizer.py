"""Data anonymization and pseudonymization for GIGLEDGER.

Implements one-way salted hashing, deterministic pseudonyms, and automatic
PII scrubbing according to privacy-by-design principles.
"""

import hashlib
import re
from typing import Optional, List, Dict, Any
import pandas as pd

from src.config import PRIVACY_SALT

# Regex patterns for common PII that should never enter the database
REGEX_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phone": re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
    "in_phone": re.compile(r"(?:\+91|91)?\s?[6789]\d{9}"),  # Indian 10-digit mobile
    "plate_number": re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}\b"),  # Vehicle plates
    "bank_account": re.compile(r"\b[0-9]{9,18}\b"),  # Typical bank account numbers
}


def generate_worker_pseudonym(raw_identifier: str, salt: Optional[str] = None) -> str:
    """Generate a stable, irreversible pseudonymous worker ID from any raw identifier.

    Args:
        raw_identifier: Any worker handle, raw ID, or persistent seed.
        salt: Optional salt override; defaults to config.PRIVACY_SALT.

    Returns:
        Formatted pseudonym string, e.g., 'WRK-7B29F0'.
    """
    if not raw_identifier or pd.isna(raw_identifier):
        return "WRK-ANON-000000"

    effective_salt = salt if salt is not None else PRIVACY_SALT
    raw_str = str(raw_identifier).strip().lower()
    salted_bytes = f"{effective_salt}:{raw_str}".encode("utf-8")
    sha_hash = hashlib.sha256(salted_bytes).hexdigest()
    # Take first 8 uppercase hex characters
    short_code = sha_hash[:8].upper()
    return f"WRK-{short_code}"


class DataAnonymizer:
    """Class to scrub PII and anonymize worker datasets."""

    def __init__(self, salt: Optional[str] = None):
        self.salt = salt if salt is not None else PRIVACY_SALT

    def scrub_text(self, text: Any) -> Any:
        """Scan string content and replace any matched PII patterns with redacted tokens."""
        if not isinstance(text, str):
            return text

        scrubbed = text
        for pii_type, pattern in REGEX_PATTERNS.items():
            scrubbed = pattern.sub(f"[REDACTED_{pii_type.upper()}]", scrubbed)
        return scrubbed

    def anonymize_identifier(self, raw_id: str) -> str:
        """Pseudonymize a single raw worker identifier."""
        return generate_worker_pseudonym(raw_id, self.salt)

    def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        worker_id_col: str = "worker_id",
        columns_to_scrub: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Transform a DataFrame into an anonymized version with pseudonyms and scrubbed text.

        Args:
            df: Input raw DataFrame.
            worker_id_col: Column containing raw or user-provided worker identifier.
            columns_to_scrub: List of free-text columns to scrub for accidental PII.

        Returns:
            Anonymized DataFrame with 'worker_pseudonym' and sanitized fields.
        """
        df_clean = df.copy()

        if worker_id_col in df_clean.columns:
            df_clean["worker_pseudonym"] = df_clean[worker_id_col].apply(
                lambda x: generate_worker_pseudonym(str(x), self.salt)
            )
            # Remove raw identifier column if different from worker_pseudonym
            if worker_id_col != "worker_pseudonym":
                df_clean.drop(columns=[worker_id_col], inplace=True)
        elif "worker_pseudonym" not in df_clean.columns:
            # If neither present, generate anonymized fallback
            df_clean["worker_pseudonym"] = "WRK-ANON-DEFAULT"

        # Scrub free text fields
        scrub_targets = columns_to_scrub or ["notes", "remarks", "location_detail", "feedback"]
        for col in scrub_targets:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(self.scrub_text)

        # Drop forbidden columns if accidentally present
        forbidden_cols = [
            "password", "pin", "credential", "phone", "email", "mobile",
            "account_number", "upi_id", "aadhaar", "ssn", "full_name", "real_name"
        ]
        to_drop = [c for c in df_clean.columns if c.lower() in forbidden_cols]
        if to_drop:
            df_clean.drop(columns=to_drop, inplace=True)

        return df_clean
