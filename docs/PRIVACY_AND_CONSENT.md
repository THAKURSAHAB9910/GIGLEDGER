# GIGLEDGER — Privacy, Consent, and Ethical Data Stewardship

## 1. Ethical Foundation & Research Integrity

Gig workers operate in an asymmetrical labor environment where account deactivation, algorithmic penalties, and surveillance are persistent operational risks. Consequently, **GIGLEDGER adheres to strict privacy-by-design, data minimization, and ethical stewardship standards**.

---

## 2. Core Privacy Guarantees

### 2.1 The Zero-Credentials Mandate
- **GIGLEDGER will NEVER request, prompt for, or store platform passwords, two-factor OTPs, bank account login credentials, or UPI PINs.**
- Any submission containing credential keywords is immediately rejected at the ingestion boundary by `DatasetValidator`.
- Platform account security remains entirely within the worker's control.

### 2.2 Cryptographic Pseudonymization
- All user identifiers and worker handles are transformed into irreversible pseudonyms using **SHA-256 salted hashing**:

$$\text{Pseudonym} = \text{"WRK-"} + \text{SHA256}(\text{Salt} \parallel \text{Raw Identifier})[:8].\text{upper}()$$

- The system salt is stored as an environment variable (`GIGLEDGER_SALT`), preventing dictionary rainbow table attacks.
- Identical raw handles map deterministically to the same pseudonym across shifts, enabling workers to track their longitudinal trends without revealing their real-world identity.

### 2.3 Automated PII Scrubbing
All free-text notes, shift comments, and location fields are sanitized via regex scanning (`DataAnonymizer`):
- Email addresses: replaced with `[REDACTED_EMAIL]`.
- Phone numbers: replaced with `[REDACTED_PHONE]`.
- Vehicle registration plates: replaced with `[REDACTED_PLATE_NUMBER]`.
- Bank account / financial strings: replaced with `[REDACTED_BANK_ACCOUNT]`.

---

## 3. K-Anonymity Privacy Layer ($k \ge 5$)

To prevent quasi-identifier linkage attacks (e.g. attempting to identify a specific worker by cross-referencing city, vehicle modality, and date), GIGLEDGER enforces **strict k-anonymity**:

- Whenever analytical queries or dashboard visualizations group by sensitive quasi-identifiers (such as `city`, `vehicle_type`, or `platform_category`), the system checks the distinct worker count ($n$):

$$\text{If } n < 5 \implies \text{Cohort is Suppressed and Labeled "Suppressed (n < 5)"}$$

- Low-sample cohorts are never displayed in individual rows on public dashboard views.

---

## 4. Informed Consent Protocol

Participant-reported data is only accepted when accompanied by an explicit, versioned informed consent record:

1. **Voluntary Participation**: Worker affirms contribution is voluntary for independent research.
2. **Zero Credentials Confirmation**: Worker affirms they have not provided passwords or account secrets.
3. **Research Purpose Acknowledgment**: Data will be used exclusively for non-commercial labor analytics and aggregated public interest reporting.
4. **Right to Withdraw**: Workers may request deletion or export of their pseudonymous shift history at any time.

---

## 5. Separation of Evidence Tiers

To maintain strict scientific honesty and prevent misleading stakeholders:
- 📚 **`PUBLIC_RESEARCH`**: Data from peer-reviewed institutional studies (Fairwork, ILO).
- 🔒 **`PARTICIPANT_REPORTED`**: Consented voluntary contributions from active couriers.
- ⚠️ **`DEMO_SYNTHETIC`**: Statistically simulated demonstration data. **Never presented as real worker evidence.**
