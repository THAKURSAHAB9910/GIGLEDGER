"""Statistical and econometric analysis module for GIGLEDGER.

Provides rigorous statistical evaluations: distribution percentiles, volatility
indices, non-linear diminishing returns, and hypothesis tests.
Avoids assuming causation from observational gig work data.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats


def calculate_volatility_metrics(data: Union[pd.Series, List[float]]) -> Dict[str, float]:
    """Calculate earnings volatility, spread, and dispersion metrics.

    Returns:
        Dict with mean, standard deviation, variance, interquartile range (IQR),
        and coefficient of variation (CV).
    """
    s = pd.Series(data).dropna()
    if len(s) < 2:
        val = float(s.iloc[0]) if len(s) == 1 else 0.0
        return {
            "count": float(len(s)),
            "mean": val,
            "std": 0.0,
            "variance": 0.0,
            "iqr": 0.0,
            "cv": 0.0,
            "min": val,
            "max": val,
        }

    mean_val = float(s.mean())
    std_val = float(s.std(ddof=1))
    q75, q25 = np.percentile(s, [75, 25])
    iqr_val = float(q75 - q25)
    cv_val = float(std_val / mean_val) if mean_val != 0.0 else 0.0

    return {
        "count": float(len(s)),
        "mean": round(mean_val, 2),
        "std": round(std_val, 2),
        "variance": round(float(s.var(ddof=1)), 2),
        "iqr": round(iqr_val, 2),
        "cv": round(cv_val, 4),
        "min": round(float(s.min()), 2),
        "max": round(float(s.max()), 2),
    }


def calculate_distribution_percentiles(
    data: Union[pd.Series, List[float]],
    percentiles: Optional[List[int]] = None,
) -> Dict[str, float]:
    """Calculate key distribution percentiles for financial benchmarking."""
    p_list = percentiles or [10, 25, 50, 75, 90]
    s = pd.Series(data).dropna()
    if s.empty:
        return {f"p{p}": 0.0 for p in p_list}

    results = {}
    for p in p_list:
        results[f"p{p}"] = round(float(np.percentile(s, p)), 2)
    return results


def compare_weekday_weekend_earnings(df: pd.DataFrame) -> Dict[str, Any]:
    """Compare weekday vs weekend earnings distributions with parametric & non-parametric tests.

    Returns statistical summary including mean difference, Welch's t-test,
    and Mann-Whitney U test p-values.
    """
    if "shift_date" not in df.columns or "net_earnings" not in df.columns or df.empty:
        return {"error": "Insufficient data"}

    df_temp = df.copy()
    df_temp["shift_date"] = pd.to_datetime(df_temp["shift_date"])
    df_temp["is_weekend"] = df_temp["shift_date"].dt.dayofweek.isin([5, 6])

    weekday_net = df_temp.loc[~df_temp["is_weekend"], "net_earnings"].dropna()
    weekend_net = df_temp.loc[df_temp["is_weekend"], "net_earnings"].dropna()

    if len(weekday_net) < 2 or len(weekend_net) < 2:
        return {
            "weekday_count": len(weekday_net),
            "weekend_count": len(weekend_net),
            "weekday_mean": float(weekday_net.mean()) if not weekday_net.empty else 0.0,
            "weekend_mean": float(weekend_net.mean()) if not weekend_net.empty else 0.0,
            "warning": "Sample size too small for hypothesis testing (n < 2)",
        }

    # Welch's t-test (unequal variances assumed)
    t_stat, t_pval = stats.ttest_ind(weekend_net, weekday_net, equal_var=False)

    # Mann-Whitney U test (non-parametric rank sum test)
    u_stat, u_pval = stats.mannwhitneyu(weekend_net, weekday_net, alternative="two-sided")

    diff_mean = float(weekend_net.mean() - weekday_net.mean())
    pct_diff = (diff_mean / weekday_net.mean() * 100) if weekday_net.mean() != 0 else 0.0

    return {
        "weekday_count": int(len(weekday_net)),
        "weekend_count": int(len(weekend_net)),
        "weekday_mean": round(float(weekday_net.mean()), 2),
        "weekend_mean": round(float(weekend_net.mean()), 2),
        "difference_mean": round(diff_mean, 2),
        "percentage_difference": round(pct_diff, 2),
        "t_statistic": round(float(t_stat), 3),
        "t_p_value": round(float(t_pval), 4),
        "mann_whitney_u": round(float(u_stat), 3),
        "mann_whitney_p_value": round(float(u_pval), 4),
        "is_statistically_significant_005": bool(u_pval < 0.05),
    }


def evaluate_hours_vs_net_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze whether longer working hours yield diminishing returns in hourly net pay.

    Bins shifts into duration bands and computes median effective hourly net earnings.
    """
    if "total_hours" not in df.columns or "effective_hourly_net" not in df.columns or df.empty:
        return pd.DataFrame()

    df_valid = df[df["total_hours"] > 0].copy()
    bins = [0, 4, 8, 10, 12, 24]
    labels = ["<4h (Micro)", "4-8h (Standard)", "8-10h (Extended)", "10-12h (Long)", ">12h (Extreme)"]

    df_valid["hour_bin"] = pd.cut(df_valid["total_hours"], bins=bins, labels=labels, right=True)

    summary = (
        df_valid.groupby("hour_bin", observed=False)
        .agg(
            shift_count=("net_earnings", "count"),
            avg_gross_earnings=("gross_earnings", "mean"),
            avg_net_earnings=("net_earnings", "mean"),
            median_effective_hourly_net=("effective_hourly_net", "median"),
            avg_effective_hourly_net=("effective_hourly_net", "mean"),
            avg_waiting_ratio=("unpaid_time_ratio", "mean"),
            avg_expense_ratio=("expense_ratio", "mean"),
        )
        .reset_index()
    )

    return summary.round(2)
