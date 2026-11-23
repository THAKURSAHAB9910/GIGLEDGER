-- ==============================================================================
-- GIGLEDGER: Comprehensive Analytical SQL Library
-- Contains production queries using CTEs, Window Functions, and Privacy Filters.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUERY 1: Weekly Net Earnings with Week-over-Week Window Dynamics
-- Objective: Track weekly earnings progression, hours worked, and week-over-week net growth.
-- Techniques: CTE, SUM(), LAG() window function, percentage change.
-- ------------------------------------------------------------------------------
WITH weekly_worker_earnings AS (
    SELECT
        year_week,
        worker_pseudonym,
        COUNT(shift_id) AS shifts_completed,
        ROUND(SUM(total_hours), 2) AS weekly_hours,
        ROUND(SUM(gross_earnings), 2) AS weekly_gross,
        ROUND(SUM(total_expenses), 2) AS weekly_expenses,
        ROUND(SUM(net_earnings), 2) AS weekly_net,
        ROUND(SUM(net_earnings) / NULLIF(SUM(total_hours), 0), 2) AS weekly_effective_hourly
    FROM v_shift_financials
    GROUP BY year_week, worker_pseudonym
)
SELECT
    year_week,
    worker_pseudonym,
    shifts_completed,
    weekly_hours,
    weekly_gross,
    weekly_expenses,
    weekly_net,
    weekly_effective_hourly,
    LAG(weekly_net, 1) OVER (PARTITION BY worker_pseudonym ORDER BY year_week) AS prev_week_net,
    ROUND(
        (weekly_net - LAG(weekly_net, 1) OVER (PARTITION BY worker_pseudonym ORDER BY year_week)) /
        NULLIF(LAG(weekly_net, 1) OVER (PARTITION BY worker_pseudonym ORDER BY year_week), 0) * 100.0,
        2
    ) AS wow_net_growth_pct
FROM weekly_worker_earnings
ORDER BY worker_pseudonym, year_week;


-- ------------------------------------------------------------------------------
-- QUERY 2: Monthly Platform Income Trends and Deductions
-- Objective: Monitor macroeconomic trends in gross payouts, net margins, and platform take.
-- Techniques: Grouping, Multi-metric aggregations, Margin calculations.
-- ------------------------------------------------------------------------------
SELECT
    year_month,
    COUNT(DISTINCT worker_pseudonym) AS distinct_workers,
    COUNT(shift_id) AS total_shifts,
    ROUND(SUM(total_hours), 1) AS total_platform_hours,
    ROUND(SUM(gross_earnings), 2) AS total_gross_payout,
    ROUND(SUM(deductions), 2) AS total_platform_deductions,
    ROUND(SUM(total_expenses), 2) AS total_worker_expenses,
    ROUND(SUM(net_earnings), 2) AS total_worker_net_earnings,
    ROUND((SUM(net_earnings) / NULLIF(SUM(gross_earnings), 0)) * 100.0, 2) AS net_take_home_margin_pct,
    ROUND((SUM(total_expenses) / NULLIF(SUM(gross_earnings), 0)) * 100.0, 2) AS expense_burden_pct
FROM v_shift_financials
GROUP BY year_month
ORDER BY year_month ASC;


-- ------------------------------------------------------------------------------
-- QUERY 3: Effective Earnings per Working Hour (Gross vs Net Divergence)
-- Objective: Compare nominal headline hourly rates against true net take-home hourly rates.
-- Techniques: CTE, percentile banding, gap calculation.
-- ------------------------------------------------------------------------------
WITH hourly_rates AS (
    SELECT
        shift_id,
        worker_pseudonym,
        platform_category,
        total_hours,
        effective_hourly_gross,
        effective_hourly_net,
        (effective_hourly_gross - effective_hourly_net) AS hourly_shortfall,
        CASE
            WHEN total_hours < 5 THEN 'Part-Time (<5h)'
            WHEN total_hours <= 9 THEN 'Standard (5-9h)'
            ELSE 'Overtime / Long (>9h)'
        END AS shift_duration_tier
    FROM v_shift_financials
    WHERE total_hours > 0
)
SELECT
    platform_category,
    shift_duration_tier,
    COUNT(shift_id) AS sample_shifts,
    ROUND(AVG(effective_hourly_gross), 2) AS avg_headline_hourly,
    ROUND(AVG(effective_hourly_net), 2) AS avg_net_hourly,
    ROUND(AVG(hourly_shortfall), 2) AS avg_hourly_loss_to_expenses,
    ROUND(AVG(hourly_shortfall) / NULLIF(AVG(effective_hourly_gross), 0) * 100.0, 2) AS pct_lost_per_hour
FROM hourly_rates
GROUP BY platform_category, shift_duration_tier
ORDER BY platform_category, avg_headline_hourly DESC;


-- ------------------------------------------------------------------------------
-- QUERY 4: Net Earnings per Kilometre by Vehicle Modality
-- Objective: Evaluate fuel efficiency and vehicle economics per kilometre.
-- Techniques: Categorical grouping, per-km efficiency calculation.
-- ------------------------------------------------------------------------------
SELECT
    vehicle_type,
    COUNT(shift_id) AS total_shifts,
    ROUND(SUM(total_distance_km), 1) AS total_distance_km,
    ROUND(SUM(fuel_expense), 2) AS total_fuel_spent,
    ROUND(SUM(maintenance_expense), 2) AS total_maintenance_spent,
    ROUND(SUM(fuel_expense) / NULLIF(SUM(total_distance_km), 0), 2) AS fuel_cost_per_km,
    ROUND((SUM(fuel_expense) + SUM(maintenance_expense)) / NULLIF(SUM(total_distance_km), 0), 2) AS total_operating_cost_per_km,
    ROUND(SUM(gross_earnings) / NULLIF(SUM(total_distance_km), 0), 2) AS gross_payout_per_km,
    ROUND(SUM(net_earnings) / NULLIF(SUM(total_distance_km), 0), 2) AS net_earnings_per_km
FROM v_shift_financials
WHERE total_distance_km > 0
GROUP BY vehicle_type
ORDER BY net_earnings_per_km DESC;


-- ------------------------------------------------------------------------------
-- QUERY 5: Incentive Dependency and Base Payout Sufficiency
-- Objective: Determine what percentage of income is contingent upon variable bonuses/incentives.
-- Techniques: CTE, conditional bucketing, ratio calculations.
-- ------------------------------------------------------------------------------
WITH incentive_breakdown AS (
    SELECT
        shift_id,
        worker_pseudonym,
        platform_category,
        gross_earnings,
        base_payout,
        (incentive_pay + bonus_pay) AS variable_incentives,
        incentive_dependency,
        CASE
            WHEN incentive_dependency >= 0.50 THEN 'High Vulnerability (>=50% from incentives)'
            WHEN incentive_dependency >= 0.25 THEN 'Moderate Vulnerability (25-50%)'
            ELSE 'Base-Reliant (<25%)'
        END AS vulnerability_tier
    FROM v_shift_financials
    WHERE gross_earnings > 0
)
SELECT
    platform_category,
    vulnerability_tier,
    COUNT(shift_id) AS shift_count,
    ROUND(AVG(gross_earnings), 2) AS avg_gross,
    ROUND(AVG(base_payout), 2) AS avg_base_pay,
    ROUND(AVG(variable_incentives), 2) AS avg_variable_pay,
    ROUND(AVG(incentive_dependency) * 100.0, 2) AS avg_incentive_share_pct
FROM incentive_breakdown
GROUP BY platform_category, vulnerability_tier
ORDER BY platform_category, avg_incentive_share_pct DESC;


-- ------------------------------------------------------------------------------
-- QUERY 6: Expense Breakdown by Component
-- Objective: Reveal the exact proportion of gross income consumed by fuel, maintenance, penalties.
-- Techniques: Aggregation, percentage decomposition.
-- ------------------------------------------------------------------------------
SELECT
    platform_category,
    vehicle_type,
    COUNT(shift_id) AS shift_count,
    ROUND(SUM(gross_earnings), 2) AS total_gross,
    ROUND(SUM(fuel_expense), 2) AS fuel_expense,
    ROUND(SUM(maintenance_expense), 2) AS maintenance_expense,
    ROUND(SUM(cancellation_penalties), 2) AS cancellation_penalties,
    ROUND(SUM(other_expenses), 2) AS other_expenses,
    ROUND(SUM(total_expenses), 2) AS total_expenses,
    ROUND(SUM(fuel_expense) / NULLIF(SUM(gross_earnings), 0) * 100.0, 2) AS fuel_to_gross_pct,
    ROUND(SUM(maintenance_expense) / NULLIF(SUM(gross_earnings), 0) * 100.0, 2) AS maintenance_to_gross_pct,
    ROUND(SUM(total_expenses) / NULLIF(SUM(gross_earnings), 0) * 100.0, 2) AS total_expense_to_gross_pct
FROM v_shift_financials
GROUP BY platform_category, vehicle_type
ORDER BY total_expense_to_gross_pct DESC;


-- ------------------------------------------------------------------------------
-- QUERY 7: Waiting-Time Impact on Real Hourly Rates
-- Objective: Measure hourly wage degradation caused by uncompensated idle time.
-- Techniques: NTILE() window function or categorical bucketing, average hourly yield.
-- ------------------------------------------------------------------------------
WITH waiting_buckets AS (
    SELECT
        shift_id,
        worker_pseudonym,
        waiting_time_hours,
        total_hours,
        unpaid_time_ratio,
        effective_hourly_gross,
        effective_hourly_net,
        CASE
            WHEN unpaid_time_ratio < 0.15 THEN 'Low Waiting (<15% of shift)'
            WHEN unpaid_time_ratio < 0.30 THEN 'Moderate Waiting (15-30%)'
            WHEN unpaid_time_ratio < 0.45 THEN 'High Waiting (30-45%)'
            ELSE 'Severe Waiting (>=45% of shift)'
        END AS waiting_tier
    FROM v_shift_financials
    WHERE total_hours > 0
)
SELECT
    waiting_tier,
    COUNT(shift_id) AS shift_count,
    ROUND(AVG(waiting_time_hours), 2) AS avg_waiting_hours,
    ROUND(AVG(unpaid_time_ratio) * 100.0, 2) AS avg_unpaid_time_pct,
    ROUND(AVG(effective_hourly_gross), 2) AS avg_effective_gross_hourly,
    ROUND(AVG(effective_hourly_net), 2) AS avg_effective_net_hourly,
    ROUND(AVG(effective_hourly_gross) - AVG(effective_hourly_net), 2) AS hourly_divergence
FROM waiting_buckets
GROUP BY waiting_tier
ORDER BY avg_unpaid_time_pct ASC;


-- ------------------------------------------------------------------------------
-- QUERY 8: Earnings Volatility (Standard Deviation and Coefficient of Variation)
-- Objective: Quantify income uncertainty across active workers.
-- Techniques: CTE, variance calculation, standard deviation, coefficient of variation.
-- ------------------------------------------------------------------------------
WITH worker_stats AS (
    SELECT
        worker_pseudonym,
        platform_category,
        COUNT(shift_id) AS total_shifts,
        ROUND(AVG(net_earnings), 2) AS avg_shift_net,
        ROUND(MIN(net_earnings), 2) AS min_shift_net,
        ROUND(MAX(net_earnings), 2) AS max_shift_net
    FROM v_shift_financials
    GROUP BY worker_pseudonym, platform_category
    HAVING COUNT(shift_id) >= 5  -- Only workers with sufficient shift history
),
worker_squared_diffs AS (
    SELECT
        w.worker_pseudonym,
        w.platform_category,
        w.total_shifts,
        w.avg_shift_net,
        w.min_shift_net,
        w.max_shift_net,
        SUM((s.net_earnings - w.avg_shift_net) * (s.net_earnings - w.avg_shift_net)) AS sum_sq_diff
    FROM worker_stats w
    JOIN v_shift_financials s ON w.worker_pseudonym = s.worker_pseudonym
    GROUP BY w.worker_pseudonym, w.platform_category, w.total_shifts, w.avg_shift_net, w.min_shift_net, w.max_shift_net
)
SELECT
    worker_pseudonym,
    platform_category,
    total_shifts,
    avg_shift_net,
    min_shift_net,
    max_shift_net,
    ROUND(SQRT(sum_sq_diff / NULLIF(total_shifts - 1, 0)), 2) AS std_dev_net_earnings,
    ROUND(SQRT(sum_sq_diff / NULLIF(total_shifts - 1, 0)) / NULLIF(avg_shift_net, 0), 4) AS coefficient_of_variation
FROM worker_squared_diffs
ORDER BY coefficient_of_variation DESC;


-- ------------------------------------------------------------------------------
-- QUERY 9: Worker Cohort Comparison (Full-Time vs Part-Time)
-- Objective: Segment workers by commitment level to observe net margins and fatigue effects.
-- Techniques: Subquery classification, aggregate financial comparison.
-- ------------------------------------------------------------------------------
WITH worker_aggregates AS (
    SELECT
        worker_pseudonym,
        platform_category,
        vehicle_type,
        COUNT(shift_id) AS total_shifts,
        SUM(total_hours) AS total_hours_worked,
        AVG(total_hours) AS avg_hours_per_shift,
        SUM(gross_earnings) AS total_gross,
        SUM(net_earnings) AS total_net,
        SUM(net_earnings) / NULLIF(SUM(total_hours), 0) AS overall_hourly_net,
        CASE
            WHEN AVG(total_hours) >= 8.5 THEN 'Full-Time Heavy (>8.5h/shift)'
            WHEN AVG(total_hours) >= 6.0 THEN 'Standard Shift (6-8.5h/shift)'
            ELSE 'Part-Time / Flex (<6h/shift)'
        END AS cohort_type
    FROM v_shift_financials
    GROUP BY worker_pseudonym, platform_category, vehicle_type
)
SELECT
    cohort_type,
    platform_category,
    COUNT(worker_pseudonym) AS worker_count,
    ROUND(AVG(avg_hours_per_shift), 2) AS avg_shift_duration,
    ROUND(AVG(total_gross / total_shifts), 2) AS avg_shift_gross,
    ROUND(AVG(total_net / total_shifts), 2) AS avg_shift_net,
    ROUND(AVG(overall_hourly_net), 2) AS cohort_hourly_net
FROM worker_aggregates
GROUP BY cohort_type, platform_category
ORDER BY cohort_hourly_net DESC;


-- ------------------------------------------------------------------------------
-- QUERY 10: Location-Level Comparisons with K-Anonymity Guard (n >= 5)
-- Objective: Compare metropolitan markets while strictly enforcing k-anonymity (>=5 distinct workers).
-- Techniques: HAVING COUNT(DISTINCT worker_pseudonym) >= 5.
-- ------------------------------------------------------------------------------
SELECT
    city,
    COUNT(DISTINCT worker_pseudonym) AS consented_workers,
    COUNT(shift_id) AS total_shifts,
    ROUND(SUM(total_hours), 1) AS total_hours,
    ROUND(AVG(effective_hourly_gross), 2) AS avg_gross_hourly,
    ROUND(AVG(effective_hourly_net), 2) AS avg_net_hourly,
    ROUND(AVG(expense_ratio) * 100.0, 2) AS avg_expense_pct,
    ROUND(AVG(net_earnings_per_km), 2) AS avg_net_per_km
FROM v_shift_financials
GROUP BY city
HAVING COUNT(DISTINCT worker_pseudonym) >= 5  -- K-anonymity enforcement
ORDER BY avg_net_hourly DESC;


-- ------------------------------------------------------------------------------
-- QUERY 11: Weekday vs Weekend Shift Earnings Comparison
-- Objective: Determine whether weekend demand surges translate to higher net take-home pay.
-- Techniques: Conditional aggregation, CASE statement day filtering.
-- ------------------------------------------------------------------------------
SELECT
    CASE WHEN is_weekend = 1 THEN 'Weekend (Sat-Sun)' ELSE 'Weekday (Mon-Fri)' END AS day_type,
    COUNT(shift_id) AS shift_count,
    ROUND(AVG(total_hours), 2) AS avg_shift_hours,
    ROUND(AVG(orders_completed), 2) AS avg_orders,
    ROUND(AVG(gross_earnings), 2) AS avg_gross,
    ROUND(AVG(incentive_pay + bonus_pay), 2) AS avg_incentives,
    ROUND(AVG(total_expenses), 2) AS avg_expenses,
    ROUND(AVG(net_earnings), 2) AS avg_net_earnings,
    ROUND(AVG(effective_hourly_net), 2) AS avg_net_hourly_rate,
    ROUND(AVG(expense_ratio) * 100.0, 2) AS avg_expense_pct
FROM v_shift_financials
GROUP BY is_weekend
ORDER BY is_weekend DESC;


-- ------------------------------------------------------------------------------
-- QUERY 12: High-Expense and Sub-Minimum Wage Shift Identification
-- Objective: Detect vulnerable shifts where net pay fell below nominal minimum wage (₹100/hr)
--            or where operating expenses consumed over 45% of gross earnings.
-- Techniques: Filtered CTE, ranking, risk flags.
-- ------------------------------------------------------------------------------
WITH shift_risk_analysis AS (
    SELECT
        shift_id,
        worker_pseudonym,
        shift_date,
        city,
        vehicle_type,
        total_hours,
        gross_earnings,
        total_expenses,
        net_earnings,
        effective_hourly_net,
        expense_ratio,
        CASE
            WHEN net_earnings <= 0 THEN 'Negative Net Income (Loss-making)'
            WHEN effective_hourly_net < 100.0 THEN 'Sub-Minimum Wage (<₹100/hr)'
            WHEN expense_ratio >= 0.45 THEN 'Severe Expense Drain (>=45% of Gross)'
            ELSE 'Nominal'
        END AS economic_distress_category
    FROM v_shift_financials
)
SELECT
    economic_distress_category,
    COUNT(shift_id) AS distressed_shift_count,
    ROUND(AVG(total_hours), 2) AS avg_hours_worked,
    ROUND(AVG(gross_earnings), 2) AS avg_gross_payout,
    ROUND(AVG(total_expenses), 2) AS avg_shift_expenses,
    ROUND(AVG(net_earnings), 2) AS avg_net_earnings,
    ROUND(AVG(effective_hourly_net), 2) AS avg_net_hourly
FROM shift_risk_analysis
WHERE economic_distress_category != 'Nominal'
GROUP BY economic_distress_category
ORDER BY distressed_shift_count DESC;
