# GIGLEDGER — User & Operator Guide

A comprehensive operational guide for launching, navigating, and utilizing the GIGLEDGER platform.

---

## 1. Quick Start & Setup

### 1.1 Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Virtual environment (recommended)

### 1.2 Installation
```bash
# Clone or navigate to the repository
cd c:/Users/Vishe/OneDrive/Desktop/GIG

# Install required dependencies
python -m pip install -r requirements.txt
```

### 1.3 Database Initialization & Seeding
Bootstrap the SQLite database, load DDL schemas, views, and demonstration seed datasets:
```bash
python -m src.analytics.init_db
```

### 1.4 Run Automated Test Suite
Verify that all 41 financial, privacy, validation, and SQL tests pass:
```bash
python -m pytest tests/ -v
```

### 1.5 Launch the Interactive Dashboard
Launch the multi-page Streamlit application:
```bash
python -m streamlit run app/streamlit_app.py
```
Open your browser to `http://localhost:8501`.

---

## 2. Navigating the Dashboard Pages

### 1. 📊 Overview
- View total gross payout, actual net take-home earnings, aggregate hours, and the headline divergence timeline.
- Check the percentage of shifts earning below the statutory minimum wage benchmark (₹100/hr).
- Use the global sidebar filters to slice by city, vehicle modality, or date range.

### 2. 📈 Earnings Dynamics & Volatility
- Explore weekly and monthly net margins.
- Examine net earnings per kilometre across vehicle types.
- Review income volatility metrics ($\sigma$, IQR, Coefficient of Variation) and worker-level stability rankings.
- Review statistical hypothesis tests for weekday vs. weekend earnings.

### 3. ⛽ Operating Expense Intelligence
- Deconstruct operating expenses into fuel, maintenance, penalties, and mobile data.
- Compare operating cost per kilometre between Electric 2W, Motorcycles, and Scooters.
- Inspect the High Expense Shifts audit table.

### 4. ⏱️ Working Hours & Idle Waiting Economics
- Analyze whether longer shift hours yield diminishing net hourly returns.
- Review the waiting-time quartile breakdown and wage drag correlation.

### 5. 🎯 Incentive Intelligence & Threshold Chasing
- Model the counterfactual: what workers would earn without variable bonuses.
- Inspect delivery order count histograms for bunching around 12, 17, and 22 order tiers.
- Review the financial friction of cancelled orders.

### 6. 👥 Worker Cohorts & Location Intelligence
- Compare Full-Time, Standard, and Part-Time worker commitment tiers.
- Review metropolitan city comparisons protected by automatic k-anonymity (k ≥ 5) suppression.
- Cross-reference current metrics against published empirical research benchmarks.

### 7. 📥 Data Management & Ethical Ingestion
- Download the CSV entry template and data dictionary.
- Upload shift CSVs with live validation and error tracking.
- Submit a single shift via the consented manual entry form.
- Export full cleaned datasets as CSV, JSON, or download the Markdown Executive Summary.

---

## 3. CSV File Upload Guide

1. Download the template from **Page 7 (Data Management)**: `gigledger_entry_template.csv`.
2. Populate shift rows according to the rules in `gigledger_data_dictionary.csv`.
3. Upload via the file uploader. The validator will check:
   - Feasible speed limits ($\le 120\text{ km/h}$).
   - Shift duration ($0.05 \le \text{hours} \le 24.0$).
   - Paid distance $\le$ total distance.
   - Waiting time $\le$ total shift hours.
   - Non-negative monetary amounts.
   - Absence of forbidden password/credential columns.
4. Click **Commit Valid Records to Database** to persist.
