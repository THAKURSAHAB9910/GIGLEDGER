"""Informed consent management for GIGLEDGER participant contributions.

Enforces ethical data stewardship: explicit opt-in, clear terms, no platform credentials,
and verifiable consent records.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


CONSENT_TERMS_VERSION = "2026.1"
CONSENT_TEXT = """
INFORMED CONSENT FOR VOLUNTARY GIG-WORKER EARNINGS CONTRIBUTION (GIGLEDGER)

1. PURPOSE: You are contributing anonymized shift, earnings, and operating expense records
   to an independent public-interest research and analytics project investigating real net
   earnings in platform gig labor.
2. VOLUNTARY: Your participation is 100% voluntary. You may stop at any time.
3. ZERO CREDENTIALS: You will NEVER be asked for platform passwords, two-factor OTPs,
   bank account credentials, or government identification numbers. Any request for credentials
   is unauthorized and prohibited.
4. ANONYMIZATION: All identifiers are hashed using one-way cryptographic salting (SHA-256).
   Your real identity cannot be reverse-engineered from public reports.
5. AGGREGATION & REPORTING: Contributed records are aggregated into cohorts (minimum 5 workers)
   to ensure privacy. No individual shift will be published with personally identifiable details.
6. DATA RETENTION & REMOVAL: You retain the right to request deletion of your pseudonymous
   records using your secret participant code.
"""


class ConsentRecord(BaseModel):
    """Pydantic model representing an explicit consent affirmation."""
    worker_pseudonym: str
    consent_version: str = CONSENT_TERMS_VERSION
    agreed: bool = Field(..., description="Must be explicitly True")
    agreed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agreed_no_passwords_provided: bool = Field(
        ..., description="Worker affirms they did not provide credentials"
    )
    research_purpose_accepted: bool = Field(
        ..., description="Worker acknowledges non-commercial research use"
    )
    ip_hash_redacted: Optional[str] = None


class ConsentManager:
    """Manages validation and storage of consent records."""

    def __init__(self, terms_version: str = CONSENT_TERMS_VERSION):
        self.terms_version = terms_version

    @staticmethod
    def get_consent_notice() -> Dict[str, Any]:
        """Return the current terms notice and version."""
        return {
            "version": CONSENT_TERMS_VERSION,
            "text": CONSENT_TEXT.strip(),
            "last_updated": "2026-01-15",
        }

    def validate_consent(self, consent_data: Dict[str, Any]) -> bool:
        """Validate whether a consent payload satisfies all ethical requirements."""
        if not consent_data.get("agreed", False):
            return False
        if not consent_data.get("agreed_no_passwords_provided", False):
            return False
        if not consent_data.get("research_purpose_accepted", False):
            return False
        if consent_data.get("consent_version") != self.terms_version:
            # Must agree to current version
            return False
        return True
