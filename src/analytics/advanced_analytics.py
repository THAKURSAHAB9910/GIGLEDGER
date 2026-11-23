"""Advanced analytical and econometric investigation engine for GIGLEDGER.

Implements rigorous tests for:
1. Diminishing marginal returns to working hours.
2. Incentive threshold chasing and target clustering.
3. Uncompensated waiting-time wage degradation.
4. Relative expense category burden.
5. Day-of-week and weekend earnings variance.
6. Financial drag of order cancellations.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

from src.calculations.statistical import (
    calculate_volatility_metrics,
    calculate_distribution_percentiles,
    compare_weekday_weekend_earnings,
    evaluate_hours_vs_net_returns,
)


class AdvancedAnalyticsEngine:
    """Performs statistical investigations on gig worker shift and earnings data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def analyze_hours_diminishing_returns(self) -> Dict[str, Any]:
        """Examine whether additional shift hours yield diminishing net hourly returns."""
        if self.df.empty or "total_hours" not in self.df.columns or "effective_hourly_net" not in self.df.columns:
            return {"status": "insufficient_data"}

        valid_df = self.df[(self.df["total_hours"] > 0) & (self.df["total_hours"] <= 24)].copy()
        if len(valid_df) < 5:
            return {"status": "sample_too_small", "sample_size": len(valid_df)}

        # Correlation between total hours and hourly net earnings
        pearson_r, p_val = stats.pearsonr(valid_df["total_hours"], valid_df["effective_hourly_net"])
        spearman_rho, sp_pval = stats.spearmanr(valid_df["total_hours"], valid_df["effective_hourly_net"])

        # Group by hour bins
        binned_table = evaluate_hours_vs_net_returns(valid_df)

        return {
            "sample_size": int(len(valid_df)),
            "pearson_r": round(float(pearson_r), 4),
            "pearson_p_value": round(float(p_val), 4),
            "spearman_rho": round(float(spearman_rho), 4),
            "spearman_p_value": round(float(sp_pval), 4),
            "binned_summary": binned_table.to_dict(orient="records"),
            "diminishing_returns_detected": bool(pearson_r < -0.15 and p_val < 0.05),
            "caveat": "Observational correlation only; fatigue, off-peak shift timing, and traffic may confound.",
        }

    def analyze_incentive_threshold_clustering(self) -> Dict[str, Any]:
        """Investigate whether delivery volumes cluster around common daily incentive tiers (e.g. 10, 15, 20 orders)."""
        if self.df.empty or "orders_completed" not in self.df.columns:
            return {"status": "insufficient_data"}

        orders = self.df["orders_completed"].dropna()
        if len(orders) < 10:
            return {"status": "sample_too_small", "sample_size": len(orders)}

        order_dist = orders.value_counts().sort_index()

        # Check for clustering near typical threshold intervals (multiples of 5: 10, 15, 20)
        tier_targets = [10, 15, 20, 25]
        tier_clusters = {}
        for target in tier_targets:
            # Count shifts finishing exactly at target or target+1
            hit_target = int(orders[orders.isin([target, target + 1])].count())
            just_below = int(orders[orders == target - 1].count())
            tier_clusters[f"target_{target}"] = {
                "at_or_just_above": hit_target,
                "just_missed": just_below,
                "bunching_ratio": round(hit_target / max(1, just_below), 2),
            }

        return {
            "sample_size": int(len(orders)),
            "mean_orders": round(float(orders.mean()), 2),
            "median_orders": round(float(orders.median()), 2),
            "tier_clusters": tier_clusters,
            "caveat": "High bunching ratios suggest workers extend shifts specifically to unlock fixed bonus cliffs.",
        }

    def analyze_waiting_time_impact(self) -> Dict[str, Any]:
        """Quantify the wage degradation caused by uncompensated waiting time."""
        if self.df.empty or "waiting_time_hours" not in self.df.columns or "effective_hourly_net" not in self.df.columns:
            return {"status": "insufficient_data"}

        valid_df = self.df[self.df["total_hours"] > 0].copy()
        if len(valid_df) < 5:
            return {"status": "sample_too_small"}

        # Check for constant variance
        if valid_df["unpaid_time_ratio"].nunique() <= 1 or valid_df["effective_hourly_net"].nunique() <= 1:
            r_corr, p_val = 0.0, 1.0
        else:
            r_corr, p_val = stats.pearsonr(valid_df["unpaid_time_ratio"], valid_df["effective_hourly_net"])

        # Quartile or rank breakdown of waiting ratio
        if valid_df["unpaid_time_ratio"].nunique() >= 4:
            valid_df["wait_quartile"] = pd.qcut(
                valid_df["unpaid_time_ratio"],
                q=4,
                labels=["Q1 (Low)", "Q2 (Medium)", "Q3 (High)", "Q4 (Severe)"],
                duplicates="drop",
            )
        else:
            valid_df["wait_quartile"] = "All Shifts"

        q_summary = (
            valid_df.groupby("wait_quartile", observed=False)
            .agg(
                count=("effective_hourly_net", "count"),
                avg_wait_ratio=("unpaid_time_ratio", "mean"),
                avg_gross_hourly=("effective_hourly_gross", "mean"),
                avg_net_hourly=("effective_hourly_net", "mean"),
            )
            .reset_index()
        )
        q_summary["hourly_wage_penalty"] = q_summary["avg_gross_hourly"] - q_summary["avg_net_hourly"]

        return {
            "sample_size": int(len(valid_df)),
            "pearson_correlation": round(float(r_corr), 4),
            "p_value": round(float(p_val), 4),
            "quartile_breakdown": q_summary.round(2).to_dict(orient="records"),
            "caveat": "Unpaid idle time directly reduces the denominator efficiency of gig work.",
        }

    def analyze_expense_composition(self) -> Dict[str, Any]:
        """Decompose operating costs to identify the dominant drain on worker take-home pay."""
        if self.df.empty or "total_expenses" not in self.df.columns:
            return {"status": "insufficient_data"}

        fuel_sum = float(self.df["fuel_expense"].sum()) if "fuel_expense" in self.df.columns else 0.0
        maint_sum = float(self.df["maintenance_expense"].sum()) if "maintenance_expense" in self.df.columns else 0.0
        other_sum = float(self.df["other_expenses"].sum()) if "other_expenses" in self.df.columns else 0.0
        penalties_sum = float(self.df["cancellation_penalties"].sum()) if "cancellation_penalties" in self.df.columns else 0.0
        tot_expenses = float(self.df["total_expenses"].sum())

        if tot_expenses <= 0.0:
            return {"status": "zero_expenses"}

        return {
            "total_recorded_expenses": round(tot_expenses, 2),
            "fuel_percentage": round((fuel_sum / tot_expenses) * 100.0, 2),
            "maintenance_percentage": round((maint_sum / tot_expenses) * 100.0, 2),
            "other_percentage": round((other_sum / tot_expenses) * 100.0, 2),
            "penalties_percentage": round((penalties_sum / tot_expenses) * 100.0, 2),
            "primary_expense_drain": "Fuel / EV Recharging" if fuel_sum >= maint_sum else "Vehicle Maintenance",
        }

    def analyze_cancellation_drag(self) -> Dict[str, Any]:
        """Evaluate the earnings difference between shifts with zero cancellations vs one or more cancellations."""
        if self.df.empty or "cancellations_count" not in self.df.columns:
            return {"status": "insufficient_data"}

        zero_cancels = self.df[self.df["cancellations_count"] == 0]
        with_cancels = self.df[self.df["cancellations_count"] > 0]

        if len(zero_cancels) < 3 or len(with_cancels) < 3:
            return {
                "status": "sample_too_small",
                "shifts_without_cancellations": len(zero_cancels),
                "shifts_with_cancellations": len(with_cancels),
            }

        avg_net_zero = float(zero_cancels["net_earnings"].mean())
        avg_net_with = float(with_cancels["net_earnings"].mean())
        avg_penalties = float(with_cancels["cancellation_penalties"].mean())

        diff_net = avg_net_zero - avg_net_with

        return {
            "shifts_without_cancellations": int(len(zero_cancels)),
            "shifts_with_cancellations": int(len(with_cancels)),
            "avg_net_without_cancellations": round(avg_net_zero, 2),
            "avg_net_with_cancellations": round(avg_net_with, 2),
            "avg_penalty_when_cancelled": round(avg_penalties, 2),
            "estimated_net_shortfall_per_cancelled_shift": round(diff_net, 2),
            "caveat": "Cancellations entail wasted deadhead travel and waiting time in addition to explicit penalty fees.",
        }

    def analyze_day_of_week_variation(self) -> Dict[str, Any]:
        """Perform ANOVA / Kruskal-Wallis test across all days of the week."""
        if self.df.empty or "shift_date" not in self.df.columns or "net_earnings" not in self.df.columns:
            return {"status": "insufficient_data"}

        df_temp = self.df.copy()
        df_temp["shift_date"] = pd.to_datetime(df_temp["shift_date"])
        df_temp["day_name"] = df_temp["shift_date"].dt.day_name()
        df_temp["day_num"] = df_temp["shift_date"].dt.dayofweek

        # Collect groups
        day_groups = [group["net_earnings"].dropna().values for _, group in df_temp.groupby("day_num")]
        valid_groups = [g for g in day_groups if len(g) >= 2]

        if len(valid_groups) < 3:
            return {"status": "insufficient_days_data"}

        # Kruskal-Wallis non-parametric test
        h_stat, p_val = stats.kruskal(*valid_groups)

        # Day-by-day summary
        summary = (
            df_temp.groupby(["day_num", "day_name"], observed=False)
            .agg(
                shifts=("net_earnings", "count"),
                avg_net=("net_earnings", "mean"),
                median_net=("net_earnings", "median"),
                avg_hourly_net=("effective_hourly_net", "mean"),
            )
            .reset_index()
            .sort_values("day_num")
        )

        return {
            "kruskal_wallis_h": round(float(h_stat), 3),
            "p_value": round(float(p_val), 4),
            "is_significant_005": bool(p_val < 0.05),
            "daily_breakdown": summary.round(2).to_dict(orient="records"),
            "caveat": "Earnings variance by day reflects peak consumer ordering patterns and local surge pricing.",
        }
