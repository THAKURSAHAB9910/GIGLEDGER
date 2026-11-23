# GIGLEDGER — SQL Analytics Library & Query Documentation

This document catalogs the analytical views and 12 production SQL queries implemented in GIGLEDGER, detailing the business purpose, SQL techniques, window functions, and economic interpretation for each.

---

## 1. Core Analytical Views (`sql/views.sql`)

### 1.1 `v_shift_financials`
- **Purpose**: Computes shift-level derived metrics (`gross_earnings`, `total_expenses`, `net_earnings`, `effective_hourly_net`, `net_earnings_per_km`, `expense_ratio`, `incentive_dependency`, and `unpaid_time_ratio`) dynamically from raw operational columns.
- **SQL Guards**: Implements `CASE WHEN s.total_hours > 0` and `CASE WHEN s.total_distance_km > 0` to safeguard against division by zero.
- **Date Attributes**: Extracts `is_weekend`, `day_of_week_num`, `year_month`, and `year_week` using SQLite date formatting.

### 1.2 `v_daily_worker_summary`
- **Purpose**: Consolidates multiple shifts completed by the same worker on a single calendar day into daily net earnings, total hours, and effective daily rates.

### 1.3 `v_monthly_trends`
- **Purpose**: Produces macro-level monthly platform summaries: total active workers, aggregate platform hours, total gross payout, net margin %, and expense burden %.

### 1.4 `v_high_expense_shifts`
- **Purpose**: Pre-filters distressed shifts where `expense_ratio >= 0.40` or `net_earnings <= 0.0`.

---

## 2. Production Analytical Queries (`sql/analytics_queries.sql`)

### Query 1: Weekly Net Earnings with Week-over-Week Window Dynamics
- **Objective**: Track weekly earnings progression and compute week-over-week (WoW) net growth.
- **Techniques**: Common Table Expression (CTE), `LAG()` window function partitioned by `worker_pseudonym` ordered by `year_week`, `NULLIF()` division guard.
- **Interpretation**: Reveals weekly income trajectory and identifies sudden earnings collapses caused by platform policy or algorithm updates.

### Query 2: Monthly Platform Income Trends and Deductions
- **Objective**: Monitor platform-wide take-home margins and deduction burdens across multi-month windows.
- **Techniques**: Aggregation functions (`SUM`, `AVG`, `COUNT(DISTINCT)`), ratio calculations.
- **Interpretation**: Provides macroeconomic tracking of the net margin percentage retained by workers over time.

### Query 3: Earnings per Working Hour (Gross vs Net Divergence)
- **Objective**: Directly compare displayed headline hourly payouts against true net hourly earnings.
- **Techniques**: CTE duration tiering (`CASE WHEN total_hours < 5 THEN 'Part-Time' ...`), shortfall gap calculation (`effective_hourly_gross - effective_hourly_net`).
- **Interpretation**: Quantifies the exact rupee shortfall lost per working hour to operational expenses.

### Query 4: Net Earnings per Kilometre by Vehicle Modality
- **Objective**: Evaluate distance economics across Electric 2W, Motorcycles, and Scooters.
- **Techniques**: Categorical grouping, per-km efficiency calculation (`SUM(net_earnings) / SUM(total_distance_km)`).
- **Interpretation**: Demonstrates how vehicle technology choices directly impact take-home yield per kilometre.

### Query 5: Incentive Dependency & Target Vulnerability
- **Objective**: Segment shifts into vulnerability tiers based on the percentage of pay derived from conditional incentives.
- **Techniques**: CTE conditional bucketing (`CASE WHEN incentive_dependency >= 0.50 THEN 'High Vulnerability' ...`).
- **Interpretation**: Measures the financial cliff faced by workers if algorithmic bonuses are withheld.

### Query 6: Expense Breakdown by Component
- **Objective**: Decompose total out-of-pocket expenses into fuel, maintenance, penalties, and mobile data.
- **Techniques**: Component summation, percentage contribution to gross earnings.
- **Interpretation**: Identifies whether fuel price shocks or vehicle maintenance spikes represent the primary cost driver.

### Query 7: Waiting-Time Impact on Real Hourly Rates
- **Objective**: Measure wage dilution caused by uncompensated idle waiting.
- **Techniques**: Waiting ratio bucketing (`<15%`, `15-30%`, `30-45%`, `>45%`), average hourly net yield calculation.
- **Interpretation**: Quantifies the opportunity cost of idle queues at restaurant pick-ups and dark stores.

### Query 8: Earnings Volatility (Standard Deviation & Coefficient of Variation)
- **Objective**: Quantify income uncertainty across active workers.
- **Techniques**: Multi-stage CTE, variance computation (`SUM((net - avg_net)^2) / (N - 1)`), square root for standard deviation, `NULLIF()` guard.
- **Interpretation**: Evaluates the unpredictability of take-home pay for full-time platform workers.

### Query 9: Worker Cohort Comparison (Full-Time vs Part-Time)
- **Objective**: Segment workers by commitment level to observe net margins and fatigue effects.
- **Techniques**: Subquery classification (`Full-Time Heavy`, `Standard`, `Part-Time / Flex`), aggregate financial comparisons.
- **Interpretation**: Tests whether working extreme shifts yields diminishing returns in hourly net pay.

### Query 10: Location-Level Comparisons with K-Anonymity (n ≥ 5)
- **Objective**: Benchmark metropolitan markets while strictly enforcing privacy standards.
- **Techniques**: `HAVING COUNT(DISTINCT worker_pseudonym) >= 5`.
- **Interpretation**: Prevents re-identification of workers in smaller geographical clusters.

### Query 11: Weekday vs Weekend Shift Earnings Comparison
- **Objective**: Test whether weekend demand surges yield higher net take-home earnings.
- **Techniques**: Conditional aggregation on `is_weekend`.
- **Interpretation**: Establishes whether surge pricing compensates for higher weekend traffic and longer order preparation queues.

### Query 12: High-Expense and Sub-Minimum Wage Shift Identification
- **Objective**: Identify vulnerable shifts where net pay fell below the statutory minimum wage (₹100/hr) or where expenses exceeded 45% of gross payout.
- **Techniques**: Filtered CTE, categorical risk tagging.
- **Interpretation**: Essential for regulatory compliance monitoring and labor vulnerability auditing.
