"""Tests for privacy, anonymization, consent enforcement, and k-anonymity."""

import pytest
import pandas as pd
from src.privacy.anonymizer import (
    generate_worker_pseudonym,
    DataAnonymizer,
)
from src.privacy.consent import ConsentManager, ConsentRecord, CONSENT_TERMS_VERSION
from src.privacy.k_anonymity import KAnonymityChecker


class TestAnonymizer:
    """Test one-way cryptographic salting and PII scrubbing."""

    def test_pseudonym_deterministic(self):
        id1 = generate_worker_pseudonym("worker_john_doe_99", salt="custom-salt-1")
        id2 = generate_worker_pseudonym("worker_john_doe_99", salt="custom-salt-1")
        assert id1 == id2
        assert id1.startswith("WRK-")
        assert len(id1) == 12  # WRK- + 8 hex chars

    def test_pseudonym_salt_variation(self):
        id_salt_a = generate_worker_pseudonym("worker_test", salt="salt_A")
        id_salt_b = generate_worker_pseudonym("worker_test", salt="salt_B")
        assert id_salt_a != id_salt_b

    def test_pii_scrubbing_text(self):
        anonymizer = DataAnonymizer()
        sample_text = "Driver phone is 9876543210 and email is courier@gigwork.com driving plate KA01AB1234"
        scrubbed = anonymizer.scrub_text(sample_text)
        assert "9876543210" not in scrubbed
        assert "courier@gigwork.com" not in scrubbed
        assert "[REDACTED_EMAIL]" in scrubbed

    def test_dataframe_anonymization_and_forbidden_column_stripping(self):
        anonymizer = DataAnonymizer()
        raw_df = pd.DataFrame({
            "worker_id": ["driver_01", "driver_02"],
            "password": ["secret123", "pass456"],
            "phone": ["9876543210", "9123456780"],
            "notes": ["Contact at user@test.com", "Regular shift"],
            "base_payout": [500.0, 600.0],
        })
        clean_df = anonymizer.anonymize_dataframe(raw_df, worker_id_col="worker_id")
        
        # worker_id must be gone, replaced by worker_pseudonym
        assert "worker_id" not in clean_df.columns
        assert "worker_pseudonym" in clean_df.columns
        assert clean_df["worker_pseudonym"].iloc[0].startswith("WRK-")

        # Forbidden columns must be stripped
        assert "password" not in clean_df.columns
        assert "phone" not in clean_df.columns
        assert "user@test.com" not in clean_df["notes"].iloc[0]


class TestConsentManager:
    """Test ethical consent validation rules."""

    def test_valid_consent(self):
        manager = ConsentManager()
        valid_payload = {
            "agreed": True,
            "agreed_no_passwords_provided": True,
            "research_purpose_accepted": True,
            "consent_version": CONSENT_TERMS_VERSION,
        }
        assert manager.validate_consent(valid_payload) is True

    def test_rejected_without_password_affirmation(self):
        manager = ConsentManager()
        invalid_payload = {
            "agreed": True,
            "agreed_no_passwords_provided": False,  # Missing affirmation
            "research_purpose_accepted": True,
            "consent_version": CONSENT_TERMS_VERSION,
        }
        assert manager.validate_consent(invalid_payload) is False

    def test_rejected_outdated_version(self):
        manager = ConsentManager()
        invalid_payload = {
            "agreed": True,
            "agreed_no_passwords_provided": True,
            "research_purpose_accepted": True,
            "consent_version": "1999.0",
        }
        assert manager.validate_consent(invalid_payload) is False


class TestKAnonymityChecker:
    """Test k-anonymity cohort assessment and suppression."""

    def test_k_anonymity_assessment_pass(self):
        checker = KAnonymityChecker(k=3)
        # 3 distinct workers in city A
        df = pd.DataFrame({
            "worker_pseudonym": ["W1", "W2", "W3", "W1", "W2"],
            "city": ["Bengaluru", "Bengaluru", "Bengaluru", "Bengaluru", "Bengaluru"],
        })
        is_safe, min_count, violations = checker.assess_dataframe(df, quasi_identifiers=["city"])
        assert is_safe is True
        assert min_count == 3
        assert violations.empty

    def test_k_anonymity_assessment_fail(self):
        checker = KAnonymityChecker(k=5)
        # Only 2 distinct workers in Mumbai
        df = pd.DataFrame({
            "worker_pseudonym": ["W1", "W2", "W1"],
            "city": ["Mumbai", "Mumbai", "Mumbai"],
        })
        is_safe, min_count, violations = checker.assess_dataframe(df, quasi_identifiers=["city"])
        assert is_safe is False
        assert min_count == 2
        assert len(violations) == 1

    def test_enforce_k_anonymity_suppression(self):
        checker = KAnonymityChecker(k=3)
        df = pd.DataFrame({
            "worker_pseudonym": ["W1", "W2", "W3", "W4", "W5"],
            "city": ["Bengaluru", "Bengaluru", "Bengaluru", "Mysuru", "Mysuru"],  # Mysuru has only 2
        })
        suppressed = checker.enforce_k_anonymity(df, group_cols=["city"], suppression_label="Suppressed (<3)")
        
        # Bengaluru should remain
        assert (suppressed[suppressed["worker_pseudonym"] == "W1"]["city"] == "Bengaluru").all()
        # Mysuru must be suppressed
        assert (suppressed[suppressed["worker_pseudonym"] == "W4"]["city"] == "Suppressed (<3)").all()
