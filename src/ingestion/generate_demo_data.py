"""Synthetic demonstration data generator for GIGLEDGER.

Generates statistically grounded demonstration shift records modeled on real-world
empirical findings (Fairwork India, ILO, academic literature).
All generated records are explicitly tagged with data_origin="DEMO_SYNTHETIC".
"""

from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from src.config import SAMPLE_DATA_DIR, DATA_ORIGIN_DEMO
from src.privacy.anonymizer import generate_worker_pseudonym


def generate_synthetic_shifts(
    num_workers: int = 25,
    start_date: date = date(2025, 12, 1),
    num_days: int = 90,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Generate realistic demonstration shifts across diverse cohorts."""
    np.random.seed(random_seed)

    cities = ["Bengaluru", "Delhi-NCR", "Mumbai", "Hyderabad"]
    city_weights = [0.35, 0.35, 0.18, 0.12]

    platforms = ["Food Delivery", "Quick Commerce / Grocery", "E-commerce Parcel"]
    platform_weights = [0.50, 0.32, 0.18]

    vehicles = ["Motorcycle", "Scooter", "Electric 2W", "Bicycle"]
    vehicle_weights = [0.55, 0.25, 0.16, 0.04]

    # Worker profiles
    workers: List[Dict[str, Any]] = []
    for i in range(num_workers):
        pseudonym = generate_worker_pseudonym(f"seed_worker_{i+101}")
        city = np.random.choice(cities, p=city_weights)
        platform = np.random.choice(platforms, p=platform_weights)
        vehicle = np.random.choice(vehicles, p=vehicle_weights)
        
        # Behavior tendency: full-time vs part-time
        worker_type = np.random.choice(["Full-Time", "Standard", "Part-Time"], p=[0.45, 0.40, 0.15])
        workers.append({
            "worker_pseudonym": pseudonym,
            "city": city,
            "platform_category": platform,
            "vehicle_type": vehicle,
            "worker_type": worker_type,
        })

    shifts_list: List[Dict[str, Any]] = []

    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() in (5, 6)

        for w in workers:
            # Shift probability: full-time works 85% of days, part-time 50%
            prob_work = 0.88 if w["worker_type"] == "Full-Time" else (0.75 if w["worker_type"] == "Standard" else 0.50)
            if np.random.rand() > prob_work:
                continue

            # Working hours based on worker profile
            if w["worker_type"] == "Full-Time":
                total_hours = round(float(np.random.normal(10.5, 1.2)), 1)
            elif w["worker_type"] == "Standard":
                total_hours = round(float(np.random.normal(8.0, 0.9)), 1)
            else:
                total_hours = round(float(np.random.normal(5.0, 0.8)), 1)
            total_hours = max(2.5, min(14.5, total_hours))

            # Start time
            start_hour = int(np.random.choice([7, 8, 9, 10, 11, 12, 16]))
            start_min = int(np.random.choice([0, 15, 30, 45]))
            start_time = f"{start_hour:02d}:{start_min:02d}"

            # Calculate end time
            end_minutes_total = (start_hour * 60 + start_min + int(total_hours * 60)) % (24 * 60)
            end_hour = end_minutes_total // 60
            end_min = end_minutes_total % 60
            end_time = f"{end_hour:02d}:{end_min:02d}"

            # Deliveries per hour (1.4 - 2.5) with weekend boost
            rate_per_hour = np.random.uniform(1.5, 2.2) * (1.15 if is_weekend else 1.0)
            orders_completed = max(1, int(round(total_hours * rate_per_hour)))

            # Distance driven
            if w["vehicle_type"] == "Bicycle":
                km_per_order = np.random.uniform(2.5, 4.0)
            else:
                km_per_order = np.random.uniform(5.5, 8.5)
            
            paid_distance_km = round(orders_completed * km_per_order, 1)
            # Deadhead travel: 20% to 35% extra unpaid km
            deadhead_pct = np.random.uniform(0.20, 0.35)
            total_distance_km = round(paid_distance_km / (1.0 - deadhead_pct), 1)

            # Waiting time (idle between orders and restaurant prep delays)
            # Typically 20% to 35% of shift hours
            wait_ratio = np.random.uniform(0.20, 0.38)
            waiting_time_hours = round(total_hours * wait_ratio, 1)

            # Earnings: Base payout per order
            base_rate = np.random.uniform(38.0, 52.0)
            base_payout = round(orders_completed * base_rate, 2)

            # Incentives (Tiered thresholds)
            incentive_pay = 0.0
            if orders_completed >= 22:
                incentive_pay += np.random.choice([400.0, 450.0, 500.0])
            elif orders_completed >= 17:
                incentive_pay += np.random.choice([250.0, 300.0, 350.0])
            elif orders_completed >= 12:
                incentive_pay += np.random.choice([120.0, 150.0, 180.0])

            # Weekend peak surge incentive
            if is_weekend:
                incentive_pay += np.random.uniform(50.0, 150.0)
            incentive_pay = round(incentive_pay, 2)

            # Occasional weekly performance bonus
            bonus_pay = 0.0
            if current_date.weekday() == 6 and np.random.rand() < 0.35:
                bonus_pay = round(float(np.random.choice([200.0, 350.0, 500.0])), 2)

            # Deductions (platform penalties, equipment lease)
            deductions = 0.0
            if np.random.rand() < 0.15:
                deductions = round(float(np.random.choice([20.0, 35.0, 50.0])), 2)

            # Cancellations
            cancellations_count = 0
            cancellation_penalties = 0.0
            if np.random.rand() < 0.12:
                cancellations_count = 1
                cancellation_penalties = round(float(np.random.choice([25.0, 35.0, 50.0])), 2)
            elif np.random.rand() < 0.02:
                cancellations_count = 2
                cancellation_penalties = round(float(np.random.choice([60.0, 80.0, 100.0])), 2)

            # Operating Expenses
            # Fuel / EV cost per km
            if w["vehicle_type"] == "Motorcycle":
                fuel_cost_per_km = np.random.uniform(2.5, 3.1)  # ~₹100/L petrol, 35-40 km/L
                fuel_expense = round(total_distance_km * fuel_cost_per_km, 2)
                maintenance_expense = round(np.random.uniform(25.0, 65.0), 2)
            elif w["vehicle_type"] == "Scooter":
                fuel_cost_per_km = np.random.uniform(2.8, 3.4)  # ~₹100/L petrol, 30-35 km/L
                fuel_expense = round(total_distance_km * fuel_cost_per_km, 2)
                maintenance_expense = round(np.random.uniform(25.0, 60.0), 2)
            elif w["vehicle_type"] == "Electric 2W":
                fuel_cost_per_km = np.random.uniform(0.45, 0.75)  # Battery charging/swap fee
                fuel_expense = round(total_distance_km * fuel_cost_per_km, 2)
                maintenance_expense = round(np.random.uniform(30.0, 80.0), 2)  # Battery lease/service
            else:  # Bicycle
                fuel_expense = 0.0
                maintenance_expense = round(np.random.uniform(10.0, 25.0), 2)

            # Occasional puncture / maintenance spike
            if np.random.rand() < 0.05:
                maintenance_expense += round(float(np.random.choice([150.0, 250.0, 350.0])), 2)

            other_expenses = round(float(np.random.choice([10.0, 20.0, 30.0, 40.0])), 2)  # mobile data, tea/water

            shifts_list.append({
                "worker_pseudonym": w["worker_pseudonym"],
                "shift_date": current_date.strftime("%Y-%m-%d"),
                "start_time": start_time,
                "end_time": end_time,
                "total_hours": total_hours,
                "orders_completed": orders_completed,
                "total_distance_km": total_distance_km,
                "paid_distance_km": paid_distance_km,
                "waiting_time_hours": waiting_time_hours,
                "base_payout": base_payout,
                "incentive_pay": incentive_pay,
                "bonus_pay": bonus_pay,
                "deductions": deductions,
                "cancellations_count": cancellations_count,
                "cancellation_penalties": cancellation_penalties,
                "fuel_expense": fuel_expense,
                "maintenance_expense": maintenance_expense,
                "other_expenses": other_expenses,
                "platform_category": w["platform_category"],
                "vehicle_type": w["vehicle_type"],
                "city": w["city"],
                "data_origin": DATA_ORIGIN_DEMO,
                "consent_confirmed": True,
            })

    df = pd.DataFrame(shifts_list)
    return df


if __name__ == "__main__":
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_synthetic = generate_synthetic_shifts(num_workers=25, num_days=90)
    out_path = SAMPLE_DATA_DIR / "demo_shifts.csv"
    df_synthetic.to_csv(out_path, index=False)
    print(f"Generated {len(df_synthetic)} demo shifts saved to {out_path}")
