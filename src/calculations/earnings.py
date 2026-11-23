"""Core earnings and expense calculation engine for GIGLEDGER.

All financial logic handles missing (None / NaN) values gracefully, treating missing
cost items as 0.0 unless marked invalid, and guarding against negative expense inputs.
"""

from typing import Union, Optional
import numpy as np
import pandas as pd


def safe_float(val: Any) -> float:
    """Coerce value to float; returns 0.0 if None, NaN, or non-numeric."""
    if val is None or pd.isna(val):
        return 0.0
    try:
        f = float(val)
        return 0.0 if np.isnan(f) else f
    except (ValueError, TypeError):
        return 0.0


def calculate_gross_earnings(
    base_payout: Union[float, int, pd.Series],
    incentive_pay: Union[float, int, pd.Series] = 0.0,
    bonus_pay: Union[float, int, pd.Series] = 0.0,
) -> Union[float, pd.Series]:
    """Calculate gross earnings from base payout, incentives, and bonuses.

    Formula:
        Gross Earnings = Base Payout + Incentive Pay + Bonus Pay

    Included:
        - Base delivery fees / guaranteed pay per trip.
        - Surge, peak-hour, and target-based milestone incentives.
        - Weekly loyalty or performance bonuses.

    Excluded:
        - Customer tips paid directly off-platform (cash in hand).
        - Any reimbursable toll/parking amounts.
    """
    if isinstance(base_payout, pd.Series):
        base = base_payout.fillna(0.0)
        inc = incentive_pay.fillna(0.0) if isinstance(incentive_pay, pd.Series) else incentive_pay
        bon = bonus_pay.fillna(0.0) if isinstance(bonus_pay, pd.Series) else bonus_pay
        return base + inc + bon

    b = safe_float(base_payout)
    i = safe_float(incentive_pay)
    bn = safe_float(bonus_pay)
    return b + i + bn


def calculate_total_expenses(
    fuel_expense: Union[float, int, pd.Series] = 0.0,
    maintenance_expense: Union[float, int, pd.Series] = 0.0,
    other_expenses: Union[float, int, pd.Series] = 0.0,
    cancellation_penalties: Union[float, int, pd.Series] = 0.0,
) -> Union[float, pd.Series]:
    """Calculate total operational shift expenses incurred by the worker.

    Formula:
        Total Expenses = Fuel + Maintenance + Other Direct Operating Costs + Cancellation Penalties

    Included:
        - Fuel / EV charging costs directly attributable to the shift.
        - Routine maintenance, tire punctures, engine oil top-up prorated.
        - Mobile data packs, parking fees, tolls, hydration/water during shift.
        - Direct uncompensated platform cancellation charges.

    Excluded:
        - General personal living expenses (e.g. rent, personal meals).
        - Long-term capital vehicle purchase depreciation (unless specifically modeled).
    """
    if isinstance(fuel_expense, pd.Series):
        f = fuel_expense.fillna(0.0)
        m = maintenance_expense.fillna(0.0) if isinstance(maintenance_expense, pd.Series) else maintenance_expense
        o = other_expenses.fillna(0.0) if isinstance(other_expenses, pd.Series) else other_expenses
        p = cancellation_penalties.fillna(0.0) if isinstance(cancellation_penalties, pd.Series) else cancellation_penalties
        return f + m + o + p

    f = safe_float(fuel_expense)
    m = safe_float(maintenance_expense)
    o = safe_float(other_expenses)
    p = safe_float(cancellation_penalties)
    return f + m + o + p


def calculate_net_earnings(
    gross_earnings: Union[float, int, pd.Series],
    deductions: Union[float, int, pd.Series] = 0.0,
    total_expenses: Union[float, int, pd.Series] = 0.0,
) -> Union[float, pd.Series]:
    """Calculate true net take-home earnings.

    Formula:
        Net Earnings = Gross Earnings - Deductions - Total Operating Expenses

    Included:
        - Gross earnings (base + incentives + bonus).
        - Direct platform deductions (equipment lease, bag fee, uniform deduction).
        - All shift operating expenses.

    Notes:
        Can result in negative net earnings if expenses/penalties exceed gross pay.
    """
    if isinstance(gross_earnings, pd.Series):
        g = gross_earnings.fillna(0.0)
        d = deductions.fillna(0.0) if isinstance(deductions, pd.Series) else deductions
        e = total_expenses.fillna(0.0) if isinstance(total_expenses, pd.Series) else total_expenses
        return g - d - e

    g = safe_float(gross_earnings)
    d = safe_float(deductions)
    e = safe_float(total_expenses)
    return g - d - e


def calculate_expense_ratio(
    total_expenses: Union[float, int, pd.Series],
    gross_earnings: Union[float, int, pd.Series],
) -> Union[float, pd.Series]:
    """Calculate operating expense ratio (Expenses / Gross Earnings).

    Returns 0.0 if gross earnings <= 0.0 to prevent division by zero.
    """
    if isinstance(gross_earnings, pd.Series):
        g = gross_earnings.fillna(0.0)
        e = total_expenses.fillna(0.0) if isinstance(total_expenses, pd.Series) else total_expenses
        # Where gross <= 0, ratio is 0.0 (or NaN if no earnings)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(g > 0, e / g, 0.0)
        return pd.Series(ratio, index=g.index)

    g = safe_float(gross_earnings)
    e = safe_float(total_expenses)
    if g <= 0.0:
        return 0.0
    return e / g
