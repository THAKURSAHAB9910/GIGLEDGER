"""Page 7: Data Management, CSV Ingestion, Consent Audit, and Report Exports."""

import io
from datetime import date
import streamlit as st
import pandas as pd

from app.components.theme import apply_theme
from app.components.ui_widgets import render_header
from src.config import TEMPLATES_DIR, VEHICLE_TYPES, PLATFORM_MODES
from src.privacy.consent import ConsentManager, ConsentRecord, CONSENT_TERMS_VERSION
from src.privacy.anonymizer import generate_worker_pseudonym
from src.ingestion.importer import CSVShiftImporter
from src.analytics.sql_engine import get_db_manager

st.set_page_config(page_title="Data Management — GIGLEDGER", page_icon="📥", layout="wide")
apply_theme()

render_header("📥 Data Management & Ethical Ingestion", "Upload shift logs, enter manual records, audit consent, and export datasets.")

db = get_db_manager()
importer = CSVShiftImporter(db_manager=db)

tab_upload, tab_manual, tab_export, tab_privacy = st.tabs([
    "📤 CSV Upload & Validator",
    "✍️ Manual Shift Entry (Consented)",
    "💾 Export Reports & Data",
    "🛡️ Privacy & Consent Audit",
])

# ---------------------------------------------------------
# Tab 1: CSV Upload & Validation Pipeline
# ---------------------------------------------------------
with tab_upload:
    st.markdown("### 📤 Upload Worker Shift CSV")
    st.caption("Upload raw shift records. The system will scrub any PII, validate physical/financial bounds, compute net rates, and append to database.")

    # Download template links
    col_t1, col_t2 = st.columns(2)
    template_path = TEMPLATES_DIR / "gigledger_entry_template.csv"
    dict_path = TEMPLATES_DIR / "gigledger_data_dictionary.csv"

    if template_path.exists():
        with open(template_path, "rb") as f:
            col_t1.download_button(
                "📥 Download CSV Entry Template",
                data=f.read(),
                file_name="gigledger_entry_template.csv",
                mime="text/csv",
            )
    if dict_path.exists():
        with open(dict_path, "rb") as f:
            col_t2.download_button(
                "📖 Download Data Dictionary",
                data=f.read(),
                file_name="gigledger_data_dictionary.csv",
                mime="text/csv",
            )

    st.markdown("---")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        st.info("Parsing and running privacy-scrubbing and schema validation checks...")
        res = importer.process_file_or_buffer(
            uploaded_file,
            data_origin_override="PARTICIPANT_REPORTED",
            auto_commit_to_db=False,
        )

        if res["success"]:
            st.success(f"✅ Validation Passed! Processed {res['total_rows']} rows. Valid: {res['valid_rows']}, Rejected: {res['rejected_rows']}.")
            
            # Show preview
            valid_df = res["data"]
            st.markdown("#### Cleaned & Computed Metrics Preview")
            st.dataframe(valid_df.head(10).round(2), use_container_width=True)

            # Option to commit to DB
            if st.button("💾 Commit Valid Records to Database"):
                inserted = db.load_shifts_dataframe(valid_df, if_exists="append")
                st.success(f"Successfully loaded {inserted} shifts into GIGLEDGER database!")
        else:
            st.error(f"❌ Ingestion Failed: {res.get('error', 'Validation errors encountered.')}")
            if res.get("errors"):
                st.markdown("#### Detailed Error Log")
                err_df = pd.DataFrame(res["errors"])
                st.dataframe(err_df, use_container_width=True)

# ---------------------------------------------------------
# Tab 2: Manual Shift Entry
# ---------------------------------------------------------
with tab_manual:
    st.markdown("### ✍️ Record a Single Work Shift")
    st.caption("Submit an individual shift with explicit informed consent affirmation.")

    with st.form("manual_entry_form"):
        st.markdown("#### 1. Worker Identity & Context")
        c1, c2, c3 = st.columns(3)
        raw_worker_name = c1.text_input("Worker Handle / Pseudonym Seed", value="worker-my-shift-01")
        city = c2.selectbox("Operating City", ["Bengaluru", "Delhi-NCR", "Mumbai", "Hyderabad", "Chennai", "Kolkata", "Pune"])
        platform = c3.selectbox("Platform Sector", PLATFORM_MODES)

        v_type = st.selectbox("Vehicle Modality", VEHICLE_TYPES)

        st.markdown("#### 2. Shift Hours & Operational Volumes")
        c4, c5, c6 = st.columns(3)
        shift_date = c4.date_input("Shift Date", value=date.today())
        total_hours = c5.number_input("Total Working Hours (Elapsed)", min_value=0.5, max_value=24.0, value=8.5, step=0.5)
        orders_completed = c6.number_input("Orders Completed", min_value=0, max_value=100, value=15, step=1)

        c7, c8, c9 = st.columns(3)
        total_distance = c7.number_input("Total Distance (KM)", min_value=0.0, max_value=500.0, value=95.0, step=1.0)
        paid_distance = c8.number_input("Paid Distance (KM)", min_value=0.0, max_value=500.0, value=70.0, step=1.0)
        waiting_time = c9.number_input("Waiting / Idle Time (Hours)", min_value=0.0, max_value=24.0, value=2.0, step=0.5)

        st.markdown("#### 3. Payouts & Incentives")
        c10, c11, c12 = st.columns(3)
        base_payout = c10.number_input("Base Delivery Payout (₹)", min_value=0.0, value=650.0, step=10.0)
        incentive_pay = c11.number_input("Incentive / Surge Pay (₹)", min_value=0.0, value=220.0, step=10.0)
        bonus_pay = c12.number_input("Milestone Bonus Pay (₹)", min_value=0.0, value=50.0, step=10.0)

        st.markdown("#### 4. Expenses, Deductions & Cancellations")
        c13, c14, c15 = st.columns(3)
        fuel_expense = c13.number_input("Fuel / EV Charging Expense (₹)", min_value=0.0, value=240.0, step=10.0)
        maintenance = c14.number_input("Maintenance / Puncture Proration (₹)", min_value=0.0, value=40.0, step=5.0)
        other_exp = c15.number_input("Other Shift Expenses (Mobile, Water) (₹)", min_value=0.0, value=20.0, step=5.0)

        c16, c17, c18 = st.columns(3)
        deductions = c16.number_input("Platform Deductions (₹)", min_value=0.0, value=0.0, step=5.0)
        cancellations = c17.number_input("Cancellations Count", min_value=0, max_value=10, value=0, step=1)
        penalties = c18.number_input("Cancellation Penalties (₹)", min_value=0.0, value=0.0, step=10.0)

        st.markdown("#### 5. Informed Consent & Privacy Affirmation")
        consent_agreement = st.checkbox(
            "I voluntary contribute this anonymized shift record to the GIGLEDGER public-interest research database.",
            value=False,
        )
        no_credentials_affirmation = st.checkbox(
            "I affirm that I have NOT provided any platform passwords, OTPs, or private personal credentials.",
            value=False,
        )

        submitted = st.form_submit_button("Submit Shift Record")

        if submitted:
            if not consent_agreement or not no_credentials_affirmation:
                st.error("Submission rejected: Informed consent and zero-credentials affirmations are mandatory.")
            elif paid_distance > total_distance:
                st.error("Paid distance cannot exceed total distance.")
            elif waiting_time > total_hours:
                st.error("Waiting time cannot exceed total shift hours.")
            else:
                pseudonym = generate_worker_pseudonym(raw_worker_name)
                shift_dict = {
                    "worker_pseudonym": pseudonym,
                    "shift_date": str(shift_date),
                    "total_hours": total_hours,
                    "orders_completed": orders_completed,
                    "total_distance_km": total_distance,
                    "paid_distance_km": paid_distance,
                    "waiting_time_hours": waiting_time,
                    "base_payout": base_payout,
                    "incentive_pay": incentive_pay,
                    "bonus_pay": bonus_pay,
                    "deductions": deductions,
                    "cancellations_count": cancellations,
                    "cancellation_penalties": penalties,
                    "fuel_expense": fuel_expense,
                    "maintenance_expense": maintenance,
                    "other_expenses": other_exp,
                    "platform_category": platform,
                    "vehicle_type": v_type,
                    "city": city,
                    "data_origin": "PARTICIPANT_REPORTED",
                    "consent_confirmed": True,
                }
                new_df = pd.DataFrame([shift_dict])
                res = importer.process_file_or_buffer(
                    io.StringIO(new_df.to_csv(index=False)),
                    auto_commit_to_db=True,
                )
                if res["success"]:
                    st.success(f"🎉 Shift submitted successfully! Anonymized Pseudonym: **{pseudonym}**.")
                else:
                    st.error(f"Error saving shift: {res.get('error')}")

# ---------------------------------------------------------
# Tab 3: Export Reports & Data
# ---------------------------------------------------------
with tab_export:
    st.markdown("### 💾 Export Research Data & Executive Summaries")
    st.caption("Download cleaned datasets and summaries in CSV, JSON, and Markdown formats.")

    export_df = db.get_financial_view()
    if not export_df.empty:
        col_e1, col_e2, col_e3 = st.columns(3)

        # 1. CSV Export
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        col_e1.download_button(
            "📥 Export Full Dataset (CSV)",
            data=csv_buffer.getvalue(),
            file_name="gigledger_shifts_export.csv",
            mime="text/csv",
        )

        # 2. JSON Export
        json_str = export_df.to_json(orient="records", indent=2)
        col_e2.download_button(
            "📥 Export Full Dataset (JSON)",
            data=json_str,
            file_name="gigledger_shifts_export.json",
            mime="application/json",
        )

        # 3. Markdown Executive Summary
        report_text = f"""# GIGLEDGER Executive Analytics Export
Generated: {date.today()}
Total Shifts Analyzed: {len(export_df):,}
Unique Anonymized Workers: {export_df['worker_pseudonym'].nunique()}

## Financial Summary
- Total Gross Payouts: ₹{export_df['gross_earnings'].sum():,.2f}
- Total Operating Expenses: ₹{export_df['total_expenses'].sum():,.2f}
- Total Net Take-Home Earnings: ₹{export_df['net_earnings'].sum():,.2f}
- Mean Gross Hourly Rate: ₹{export_df['gross_earnings'].sum() / export_df['total_hours'].sum():.2f}/hr
- Mean Net Hourly Rate: ₹{export_df['net_earnings'].sum() / export_df['total_hours'].sum():.2f}/hr
- Gross-to-Net Shortfall: {((export_df['gross_earnings'].sum() - export_df['net_earnings'].sum()) / export_df['gross_earnings'].sum() * 100):.1f}%
- Mean Incentive Dependency: {export_df['incentive_dependency'].mean()*100:.1f}%
- Mean Unpaid Waiting Ratio: {export_df['unpaid_time_ratio'].mean()*100:.1f}%
"""
        col_e3.download_button(
            "📄 Download Executive Summary (MD)",
            data=report_text,
            file_name="gigledger_executive_summary.md",
            mime="text/markdown",
        )

# ---------------------------------------------------------
# Tab 4: Privacy & Consent Audit
# ---------------------------------------------------------
with tab_privacy:
    st.markdown("### 🛡️ Privacy Safeguards & Consent Architecture")
    notice = ConsentManager.get_consent_notice()
    st.markdown(f"**Consent Terms Version**: `{notice['version']}` (Updated: {notice['last_updated']})")
    st.text_area("Ethical Data Stewardship Charter", value=notice["text"], height=250, disabled=True)

    st.markdown("#### Pseudonymization Hash Tester")
    st.caption("Verify that raw handles are converted to irreversible pseudonyms using salted SHA-256.")
    test_raw = st.text_input("Enter any test handle or phone number to test", "delivery_partner_blr_42")
    if test_raw:
        gen_pseudo = generate_worker_pseudonym(test_raw)
        st.code(f"Raw Input: '{test_raw}'  ==>  Deterministic Pseudonym: '{gen_pseudo}'")
