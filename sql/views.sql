-- GIGLEDGER Core Analytical Views

-- 1. Base Financial & Operational Metrics per Shift
DROP VIEW IF EXISTS v_shift_financials;
CREATE VIEW v_shift_financials AS
SELECT
    s.shift_id,
    s.worker_pseudonym,
    s.shift_date,
    s.start_time,
    s.end_time,
    s.total_hours,
    s.orders_completed,
    s.total_distance_km,
    s.paid_distance_km,
    s.waiting_time_hours,
    s.platform_category,
    s.vehicle_type,
    s.city,
    s.data_origin,
    s.consent_confirmed,
    
    -- Component Totals
    (s.base_payout + s.incentive_pay + s.bonus_pay) AS gross_earnings,
    s.base_payout,
    s.incentive_pay,
    s.bonus_pay,
    s.deductions,
    (s.fuel_expense + s.maintenance_expense + s.other_expenses + s.cancellation_penalties) AS total_expenses,
    s.fuel_expense,
    s.maintenance_expense,
    s.other_expenses,
    s.cancellations_count,
    s.cancellation_penalties,
    
    -- Net Earnings: Gross - Deductions - Total Expenses
    ((s.base_payout + s.incentive_pay + s.bonus_pay) - s.deductions - 
     (s.fuel_expense + s.maintenance_expense + s.other_expenses + s.cancellation_penalties)) AS net_earnings,
    
    -- Effective Hourly Rates
    CASE 
        WHEN s.total_hours > 0 
        THEN ((s.base_payout + s.incentive_pay + s.bonus_pay) / s.total_hours)
        ELSE 0.0 
    END AS effective_hourly_gross,
    
    CASE 
        WHEN s.total_hours > 0 
        THEN (((s.base_payout + s.incentive_pay + s.bonus_pay) - s.deductions - 
               (s.fuel_expense + s.maintenance_expense + s.other_expenses + s.cancellation_penalties)) / s.total_hours)
        ELSE 0.0 
    END AS effective_hourly_net,
    
    -- Distance Rate (Net / Total KM)
    CASE 
        WHEN s.total_distance_km > 0 
        THEN (((s.base_payout + s.incentive_pay + s.bonus_pay) - s.deductions - 
               (s.fuel_expense + s.maintenance_expense + s.other_expenses + s.cancellation_penalties)) / s.total_distance_km)
        ELSE 0.0 
    END AS net_earnings_per_km,
    
    -- Financial Ratios
    CASE 
        WHEN (s.base_payout + s.incentive_pay + s.bonus_pay) > 0 
        THEN ((s.fuel_expense + s.maintenance_expense + s.other_expenses + s.cancellation_penalties) / 
              (s.base_payout + s.incentive_pay + s.bonus_pay))
        ELSE 0.0 
    END AS expense_ratio,
    
    CASE 
        WHEN (s.base_payout + s.incentive_pay + s.bonus_pay) > 0 
        THEN ((s.incentive_pay + s.bonus_pay) / (s.base_payout + s.incentive_pay + s.bonus_pay))
        ELSE 0.0 
    END AS incentive_dependency,
    
    CASE 
        WHEN s.total_hours > 0 
        THEN (s.waiting_time_hours / s.total_hours)
        ELSE 0.0 
    END AS unpaid_time_ratio,
    
    CASE 
        WHEN s.total_distance_km > 0 
        THEN ((s.total_distance_km - COALESCE(s.paid_distance_km, s.total_distance_km)) / s.total_distance_km)
        ELSE 0.0 
    END AS unpaid_distance_ratio,
    
    -- Date Attributes
    strftime('%w', s.shift_date) AS day_of_week_num,
    CASE strftime('%w', s.shift_date)
        WHEN '0' THEN 1
        WHEN '6' THEN 1
        ELSE 0
    END AS is_weekend,
    strftime('%Y-%m', s.shift_date) AS year_month,
    strftime('%Y-W%W', s.shift_date) AS year_week
FROM shifts s;

-- 2. Daily Summary per Worker
DROP VIEW IF EXISTS v_daily_worker_summary;
CREATE VIEW v_daily_worker_summary AS
SELECT
    shift_date,
    worker_pseudonym,
    city,
    platform_category,
    vehicle_type,
    is_weekend,
    COUNT(shift_id) AS shifts_count,
    SUM(total_hours) AS total_hours,
    SUM(orders_completed) AS total_orders,
    SUM(total_distance_km) AS total_distance_km,
    SUM(gross_earnings) AS gross_earnings,
    SUM(total_expenses) AS total_expenses,
    SUM(net_earnings) AS net_earnings,
    CASE WHEN SUM(total_hours) > 0 THEN SUM(net_earnings) / SUM(total_hours) ELSE 0.0 END AS daily_effective_hourly_net,
    CASE WHEN SUM(total_distance_km) > 0 THEN SUM(net_earnings) / SUM(total_distance_km) ELSE 0.0 END AS daily_net_per_km
FROM v_shift_financials
GROUP BY shift_date, worker_pseudonym, city, platform_category, vehicle_type, is_weekend;

-- 3. Monthly Platform Trends
DROP VIEW IF EXISTS v_monthly_trends;
CREATE VIEW v_monthly_trends AS
SELECT
    year_month,
    COUNT(DISTINCT worker_pseudonym) AS active_workers,
    COUNT(shift_id) AS total_shifts,
    ROUND(SUM(total_hours), 1) AS aggregate_hours,
    ROUND(SUM(gross_earnings), 2) AS aggregate_gross,
    ROUND(SUM(total_expenses), 2) AS aggregate_expenses,
    ROUND(SUM(net_earnings), 2) AS aggregate_net,
    ROUND(AVG(gross_earnings), 2) AS avg_shift_gross,
    ROUND(AVG(net_earnings), 2) AS avg_shift_net,
    ROUND(AVG(effective_hourly_gross), 2) AS avg_hourly_gross,
    ROUND(AVG(effective_hourly_net), 2) AS avg_hourly_net,
    ROUND(AVG(expense_ratio) * 100, 2) AS avg_expense_percentage,
    ROUND(AVG(incentive_dependency) * 100, 2) AS avg_incentive_dependency_pct
FROM v_shift_financials
GROUP BY year_month;

-- 4. High Expense and Low Net Income Shifts View
DROP VIEW IF EXISTS v_high_expense_shifts;
CREATE VIEW v_high_expense_shifts AS
SELECT
    shift_id,
    worker_pseudonym,
    shift_date,
    city,
    vehicle_type,
    total_hours,
    gross_earnings,
    fuel_expense,
    maintenance_expense,
    total_expenses,
    net_earnings,
    effective_hourly_net,
    expense_ratio
FROM v_shift_financials
WHERE expense_ratio >= 0.40 OR net_earnings <= 0.0;
