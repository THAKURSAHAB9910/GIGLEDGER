"""GIGLEDGER: Gig Worker Net-Earnings & Payout Intelligence Platform.
Main Streamlit Application Entrypoint.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from src.config import BASE_DIR, FINANCIAL_BOUNDS
from app.components.theme import apply_theme
from app.components.ui_widgets import render_core_question_banner
from src.analytics.sql_engine import get_db_manager

# Configure Streamlit
st.set_page_config(
    page_title="GIGLEDGER — Gig Worker Net-Earnings Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()


def main():
    st.title("⚖️ GIGLEDGER")
    st.subheader("Gig Worker Net-Earnings & Payout Intelligence Platform")
    st.caption("A rigorous econometric and financial analytics system revealing the real net take-home earnings of platform workers.")

    render_core_question_banner()

    # Database & System Health Check
    db = get_db_manager()
    try:
        df_shifts = db.get_financial_view()
        total_shifts = len(df_shifts)
        total_workers = df_shifts["worker_pseudonym"].nunique() if not df_shifts.empty else 0
        origins = df_shifts["data_origin"].unique().tolist() if not df_shifts.empty else []
    except Exception as e:
        total_shifts = 0
        total_workers = 0
        origins = []
        st.error(f"Database connection error: {e}")

    # Top KPI summary strip
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records Ingested", f"{total_shifts:,}")
    with col2:
        st.metric("Consented / Pseudonymized Workers", f"{total_workers:,}")
    with col3:
        st.metric("Active Evidence Tiers", f"{len(origins)}")
    with col4:
        st.metric("Statutory Baseline Wage", f"{FINANCIAL_BOUNDS['currency_symbol']}{FINANCIAL_BOUNDS['statutory_min_wage_hourly']:.0f}/hr")

    st.markdown("---")

    # Platform Introduction & Executive Framing
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("""
        ### Why GIGLEDGER?
        Digital labor platforms advertise gross trip earnings, surge multipliers, and weekly target bonuses. 
        However, the **actual net economic yield** experienced by workers is drastically eroded by three uncompensated burdens:
        
        1. **Direct Operational Out-of-Pocket Expenses**: Petrol/diesel, EV battery lease/swaps, tires, punctures, mobile data, and vehicle maintenance.
        2. **Uncompensated Waiting & Idle Time**: Hours spent logged in waiting between orders or queued at restaurant counters without pay.
        3. **Deadhead Unpaid Distance**: Kilometres driven returning from drop-off locations to order hubs without active passenger or parcel payloads.
        4. **Platform Deductions & Penalties**: Cancellation penalties, uniform/bag deductions, and target cliffs where a single missed delivery wipes out expected bonuses.
        
        **GIGLEDGER is not a personal expense tracker.** It is an institutional-grade financial analytics and SQL intelligence engine designed to bridge the gap between platform payout displays and true labor economics.
        """)

    with right_col:
        st.info("""
        #### 🛡️ Privacy & Research Standards
        - **Zero Credentials Policy**: We NEVER request passwords, OTPs, or platform credentials.
        - **Cryptographic Pseudonymization**: Worker IDs are salted and hashed (SHA-256).
        - **Strict K-Anonymity (k ≥ 5)**: Cohorts with fewer than 5 workers are automatically suppressed.
        - **Evidence Separation**:
          - 📚 **Public Research Data**: Peer-reviewed studies (Fairwork, ILO, NITI Aayog).
          - 🔒 **Participant Reported Data**: Consented voluntary logs.
          - ⚠️ **Demonstration Data**: Statistically simulated models (never passed as real evidence).
        """)

    st.markdown("---")

    # Module Directory Navigation Cards
    st.markdown("### 🧭 Platform Intelligence Modules")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("""
        **1. 📊 Overview & Headline Divergence**  
        High-level executive metrics: Gross vs Net divergence, aggregate hours, and average hourly shortfall.
        
        **2. 📈 Earnings Dynamics & Volatility**  
        Daily, weekly, and monthly net income trends, earnings per kilometre, and income instability indices.
        """)
    with m2:
        st.markdown("""
        **3. ⛽ Operating Expense Intelligence**  
        Decomposition of fuel, maintenance, and penalties. Fuel costs per km across EV and ICE modalities.
        
        **4. ⏱️ Time & Idle Waiting Economics**  
        Impact of unpaid waiting hours on effective hourly rates and diminishing returns from extended shift hours.
        """)
    with m3:
        st.markdown("""
        **5. 🎯 Incentive Cliff Analysis**  
        Dependency on variable bonuses, threshold target bunching (10/15/20 orders), and counterfactual earnings without bonuses.
        
        **6. 👥 Cohorts & 📥 Data Management**  
        Full-time vs part-time comparisons, k-anonymity location views, CSV upload validator, and report export.
        """)


if __name__ == "__main__":
    main()
