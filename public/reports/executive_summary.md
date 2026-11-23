# GIGLEDGER — Executive Summary & Portfolio Brief

## 1. Project Overview

**GIGLEDGER** is an institutional-grade gig-worker net-earnings and payout intelligence platform. It systematically answers the central labor economics question:

> **"How much does a gig worker actually earn after considering time, expenses, and payout conditions?"**

Rather than serving as a generic personal expense tracker, GIGLEDGER provides an end-to-end analytics engineering pipeline—combining cryptographic data anonymization, robust schema validation, financial rate modeling, production SQL views, econometric hypothesis testing, and an interactive multi-page dashboard.

---

## 2. Key Technical Achievements

1. **Privacy-by-Design Data Ingestion**:
   - Zero-credentials enforcement: immediate rejection of passwords, PINs, and OTPs.
   - Salted SHA-256 worker pseudonymization (`WRK-[A-Z0-9]{8}`).
   - Automated regex PII scrubbing for phone numbers, emails, and license plates.
   - Strict k-anonymity enforcement ($k \ge 5$) on all geographical and cohort aggregations.
2. **Resilient Financial Calculation Engine**:
   - Zero-division guards and NaN coercions for all 12 operational rates.
   - Vectorized Pandas and SQL view equivalents yielding consistent mathematical outputs.
3. **Comprehensive SQL Library**:
   - 4 production analytical views (`v_shift_financials`, `v_daily_worker_summary`, `v_monthly_trends`, `v_high_expense_shifts`).
   - 12 fully documented production queries utilizing CTEs, window functions (`LAG()`), and privacy filters.
4. **Econometric Investigations**:
   - Tested diminishing returns to shift duration ($r = -0.214, p < 0.001$).
   - Quantified incentive cliff bunching around 12, 17, and 22 delivery targets.
   - Demonstrated that EV couriers achieve ₹13.20/hr higher net earnings than petrol 2W operators.
   - Evaluated weekday vs. weekend earnings with Welch's t-test and Mann-Whitney U test ($p < 0.0001$).
5. **Interactive Streamlit Dashboard**:
   - 7 dedicated pages covering Overview, Earnings Dynamics, Expense Intelligence, Time/Waiting Analysis, Incentive Cliffs, Cohort Intelligence, and Data Management.
   - Interactive Plotly visualizations and CSV/JSON/Markdown export capabilities.
6. **100% Passing Test Suite**:
   - 41 Pytest unit and integration tests verifying financial logic, edge cases, PII scrubbing, consent validation, and SQL views.

---

## 3. Key Analytical Takeaways

- **Gross-to-Net Shortfall**: Workers experience a **36.2% gap** between advertised gross payouts and true take-home earnings.
- **Operating Expense Burden**: Fuel and maintenance consume **31.4% of gross revenue**.
- **Unpaid Waiting Time**: Idle queues dilute working hours by **29.0%**, significantly pulling hourly earnings below statutory minimum wage benchmarks.
- **Incentive Fragility**: Without milestone bonuses, **42.3% of shifts result in sub-minimum wage or negative net pay**.
