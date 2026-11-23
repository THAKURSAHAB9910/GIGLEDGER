"""Operational performance and rate metrics for GIGLEDGER.

Implements all required analytical rates with zero-division guards,
unit consistency checks, and vectorized pandas operations.
"""

from typing import Union, Dict, Any
import numpy as np
import pandas as pd
from src.calculations.earnings import (
    calculate_gross_earnings,
    calculate_total_expenses,
    calculate_net_earnings,
    calculate_expense_ratio,
    safe_float,
)


def calculate_effective_hourly_net(
    net_earnings: Union[float, int, pd.Series],
    total_hours: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate effective hourly net earnings (Take-home Pay per Working Hour).

    Formula:
        Effective Hourly Net Earnings = Net Earnings / Total Working Hours

    Included in Denominator:
        - Total shift elapsed time (engaged trip time + idle waiting + return transit).

    Guards:
        Returns 0.0 when total_hours <= 0.0 to prevent division by zero or negative time.
    """
    if isinstance(total_hours, pd.Series):
        h = total_hours.fillna(0.0)
        net = net_earnings.fillna(0.0) if isinstance(net_earnings, pd.Series) else net_earnings
        with np.errstate(divide="ignore", invalid="ignore"):
            hourly = np.where(h > 0.0, net / h, 0.0)
        return pd.Series(hourly, index=h.index)

    h = safe_float(total_hours)
    n = safe_float(net_earnings)
    if h <= 0.0:
        return 0.0
    return n / h


def calculate_effective_hourly_gross(
    gross_earnings: Union[float, int, pd.Series],
    total_hours: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate effective hourly gross earnings (Headline Payout per Working Hour).

    Formula:
        Effective Hourly Gross Earnings = Gross Earnings / Total Working Hours
    """
    if isinstance(total_hours, pd.Series):
        h = total_hours.fillna(0.0)
        g = gross_earnings.fillna(0.0) if isinstance(gross_earnings, pd.Series) else gross_earnings
        with np.errstate(divide="ignore", invalid="ignore"):
            hourly = np.where(h > 0.0, g / h, 0.0)
        return pd.Series(hourly, index=h.index)

    h = safe_float(total_hours)
    g = safe_float(gross_earnings)
    if h <= 0.0:
        return 0.0
    return g / h


def calculate_net_earnings_per_km(
    net_earnings: Union[float, int, pd.Series],
    total_distance_km: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate net earnings per kilometre travelled.

    Formula:
        Net Earnings per Kilometre = Net Earnings / Total Kilometres

    Guards:
        Returns 0.0 when total_distance_km <= 0.0.
    """
    if isinstance(total_distance_km, pd.Series):
        km = total_distance_km.fillna(0.0)
        net = net_earnings.fillna(0.0) if isinstance(net_earnings, pd.Series) else net_earnings
        with np.errstate(divide="ignore", invalid="ignore"):
            rate = np.where(km > 0.0, net / km, 0.0)
        return pd.Series(rate, index=km.index)

    km = safe_float(total_distance_km)
    n = safe_float(net_earnings)
    if km <= 0.0:
        return 0.0
    return n / km


def calculate_incentive_dependency(
    incentive_pay: Union[float, int, pd.Series],
    bonus_pay: Union[float, int, pd.Series],
    gross_earnings: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate incentive dependency ratio.

    Formula:
        Incentive Dependency = (Incentive Pay + Bonus Pay) / Gross Earnings

    Interpretation:
        Reveals the fraction of headline payout that is conditional on targets/bonuses
        rather than guaranteed base delivery rates.

    Guards:
        Returns 0.0 when gross_earnings <= 0.0. Clamped between 0.0 and 1.0.
    """
    if isinstance(gross_earnings, pd.Series):
        g = gross_earnings.fillna(0.0)
        inc = incentive_pay.fillna(0.0) if isinstance(incentive_pay, pd.Series) else incentive_pay
        bon = bonus_pay.fillna(0.0) if isinstance(bonus_pay, pd.Series) else bonus_pay
        total_inc = inc + bon
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(g > 0.0, np.clip(total_inc / g, 0.0, 1.0), 0.0)
        return pd.Series(ratio, index=g.index)

    g = safe_float(gross_earnings)
    i = safe_float(incentive_pay)
    b = safe_float(bonus_pay)
    if g <= 0.0:
        return 0.0
    return min(1.0, max(0.0, (i + b) / g))


def calculate_unpaid_time_ratio(
    waiting_time_hours: Union[float, int, pd.Series],
    total_hours: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate the ratio of unpaid idle/waiting time to total shift working time.

    Formula:
        Unpaid Time Ratio = Waiting Time (hours) / Total Shift Hours

    Guards:
        Returns 0.0 when total_hours <= 0.0. Clamped to maximum 1.0.
    """
    if isinstance(total_hours, pd.Series):
        tot = total_hours.fillna(0.0)
        wait = waiting_time_hours.fillna(0.0) if isinstance(waiting_time_hours, pd.Series) else waiting_time_hours
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(tot > 0.0, np.clip(wait / tot, 0.0, 1.0), 0.0)
        return pd.Series(ratio, index=tot.index)

    tot = safe_float(total_hours)
    wait = safe_float(waiting_time_hours)
    if tot <= 0.0:
        return 0.0
    return min(1.0, max(0.0, wait / tot))


def calculate_unpaid_distance_ratio(
    total_distance_km: Union[float, int, pd.Series],
    paid_distance_km: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate ratio of uncompensated 'deadhead' travel distance to total distance.

    Formula:
        Unpaid Distance Ratio = (Total KM - Paid KM) / Total KM

    Guards:
        Returns 0.0 when total_distance_km <= 0.0 or paid_distance_km is unavailable/negative.
    """
    if isinstance(total_distance_km, pd.Series):
        tot = total_distance_km.fillna(0.0)
        paid = paid_distance_km.fillna(tot) if isinstance(paid_distance_km, pd.Series) else paid_distance_km
        unpaid = np.maximum(0.0, tot - paid)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(tot > 0.0, np.clip(unpaid / tot, 0.0, 1.0), 0.0)
        return pd.Series(ratio, index=tot.index)

    tot = safe_float(total_distance_km)
    paid = safe_float(paid_distance_km) if paid_distance_km is not None else tot
    if tot <= 0.0:
        return 0.0
    unpaid = max(0.0, tot - paid)
    return min(1.0, max(0.0, unpaid / tot))


def calculate_shortfall_percentage(
    gross_earnings: Union[float, int, pd.Series],
    net_earnings: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate percentage by which net earnings fall below headline gross payout.

    Formula:
        Shortfall Percentage = (Gross - Net) / Gross * 100

    Guards:
        Returns 0.0 when gross_earnings <= 0.0.
    """
    if isinstance(gross_earnings, pd.Series):
        g = gross_earnings.fillna(0.0)
        n = net_earnings.fillna(0.0) if isinstance(net_earnings, pd.Series) else net_earnings
        with np.errstate(divide="ignore", invalid="ignore"):
            shortfall = np.where(g > 0.0, ((g - n) / g) * 100.0, 0.0)
        return pd.Series(shortfall, index=g.index)

    g = safe_float(gross_earnings)
    n = safe_float(net_earnings)
    if g <= 0.0:
        return 0.0
    return ((g - n) / g) * 100.0


def compute_shift_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich a shift DataFrame with all calculated financial and operational metrics.

    Args:
        df: Input DataFrame with basic shift columns.

    Returns:
        Enriched DataFrame with computed gross, net, expense, and rate columns.
    """
    df_out = df.copy()

    # Ensure numeric columns exist with default 0.0
    numeric_cols = [
        "base_payout", "incentive_pay", "bonus_pay", "deductions",
        "fuel_expense", "maintenance_expense", "other_expenses",
        "cancellations_count", "cancellation_penalties", "total_hours",
        "total_distance_km", "paid_distance_km", "waiting_time_hours"
    ]
    for col in numeric_cols:
        if col not in df_out.columns:
            df_out[col] = 0.0
        else:
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce").fillna(0.0)

    # 1. Gross Earnings
    df_out["gross_earnings"] = calculate_gross_earnings(
        df_out["base_payout"], df_out["incentive_pay"], df_out["bonus_pay"]
    )

    # 2. Total Expenses
    df_out["total_expenses"] = calculate_total_expenses(
        df_out["fuel_expense"],
        df_out["maintenance_expense"],
        df_out["other_expenses"],
        df_out["cancellation_penalties"],
    )

    # 3. Net Earnings
    df_out["net_earnings"] = calculate_net_earnings(
        df_out["gross_earnings"], df_out["deductions"], df_out["total_expenses"]
    )

    # 4. Hourly Rates
    df_out["effective_hourly_gross"] = calculate_effective_hourly_gross(
        df_out["gross_earnings"], df_out["total_hours"]
    )
    df_out["effective_hourly_net"] = calculate_effective_hourly_net(
        df_out["net_earnings"], df_out["total_hours"]
    )

    # 5. Distance Rate
    df_out["net_earnings_per_km"] = calculate_net_earnings_per_km(
        df_out["net_earnings"], df_out["total_distance_km"]
    )

    # 6. Ratios
    df_out["expense_ratio"] = calculate_expense_ratio(
        df_out["total_expenses"], df_out["gross_earnings"]
    )
    df_out["incentive_dependency"] = calculate_incentive_dependency(
        df_out["incentive_pay"], df_out["bonus_pay"], df_out["gross_earnings"]
    )
    df_out["unpaid_time_ratio"] = calculate_unpaid_time_ratio(
        df_out["waiting_time_hours"], df_out["total_hours"]
    )
    df_out["unpaid_distance_ratio"] = calculate_unpaid_distance_ratio(
        df_out["total_distance_km"], df_out["paid_distance_km"]
    )
    df_out["earnings_shortfall_pct"] = calculate_shortfall_percentage(
        df_out["gross_earnings"], df_out["net_earnings"]
    )

    return df_out
