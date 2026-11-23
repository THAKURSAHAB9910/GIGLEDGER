# GIGLEDGER — Data Dictionary

## 1. Entity: `shifts` (Fact Table)

| Field Name | Type | Nullable | Units / Format | Description | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `shift_id` | INTEGER | NO | Auto-increment | Primary key for shift event. | Positive integer |
| `worker_pseudonym` | VARCHAR(32) | NO | `WRK-[A-Z0-9]{8}` | Salted SHA-256 pseudonymous identifier. | Must match format |
| `shift_date` | DATE | NO | `YYYY-MM-DD` | Calendar date on which shift commenced. | Valid date (2020–present) |
| `start_time` | TIME | YES | `HH:MM` (24h) | Time worker logged into platform app. | Valid time string |
| `end_time` | TIME | YES | `HH:MM` (24h) | Time worker logged out of platform app. | Valid time string |
| `total_hours` | REAL | NO | Hours (decimal) | Total elapsed shift time (logged-in duration). | $0.05 \le \text{hours} \le 24.0$ |
| `orders_completed` | INTEGER | NO | Integer count | Number of successful trips / drops. | $\ge 0$ |
| `total_distance_km` | REAL | NO | Kilometres | Total odometer distance travelled during shift. | $\ge 0.0$ |
| `paid_distance_km` | REAL | YES | Kilometres | Distance travelled carrying active deliveries. | $\le \text{total\_distance\_km}$ |
| `waiting_time_hours` | REAL | YES | Hours (decimal) | Time spent waiting between trips and at stores. | $\le \text{total\_hours}$ |
| `base_payout` | REAL | NO | Currency (₹) | Guaranteed trip fee / base rate pay. | $\ge 0.0$ |
| `incentive_pay` | REAL | NO | Currency (₹) | Surge, peak-hour, and target tier pay. | $\ge 0.0$ |
| `bonus_pay` | REAL | NO | Currency (₹) | Weekly milestone or loyalty bonus. | $\ge 0.0$ |
| `deductions` | REAL | NO | Currency (₹) | Platform equipment lease, uniform, bag fee. | $\ge 0.0$ |
| `cancellations_count`| INTEGER | YES | Integer count | Customer or merchant cancelled orders. | $\ge 0$ |
| `cancellation_penalties` | REAL | YES | Currency (₹) | Uncompensated cancellation fees or fines. | $\ge 0.0$ |
| `fuel_expense` | REAL | NO | Currency (₹) | Direct fuel purchased or EV charging fees. | $\ge 0.0$ |
| `maintenance_expense` | REAL | NO | Currency (₹) | Prorated wear, oil, punctures, or repairs. | $\ge 0.0$ |
| `other_expenses` | REAL | NO | Currency (₹) | Mobile data pack, parking, tolls, hydration. | $\ge 0.0$ |
| `platform_category` | VARCHAR(64) | YES | Categorical | Sector: Food, Quick Commerce, Parcel, Ride. | Recognized sector |
| `vehicle_type` | VARCHAR(64) | YES | Categorical | Modality: Motorcycle, Scooter, EV 2W, Cycle. | Recognized modality |
| `city` | VARCHAR(64) | YES | Text | Metropolitan operational area. | Standardized city name |
| `data_origin` | VARCHAR(32) | NO | Enum string | Evidence classification. | One of valid origins |
| `consent_confirmed` | BOOLEAN | NO | Boolean | Affirmation of voluntary consent. | Must be TRUE |

---

## 2. Entity: `workers` (Dimension Table)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `worker_pseudonym` | VARCHAR(32) PRIMARY KEY | Unique salted pseudonym. |
| `platform_category` | VARCHAR(64) | Primary operating sector. |
| `vehicle_type` | VARCHAR(64) | Primary vehicle technology. |
| `primary_city` | VARCHAR(64) | Operating metropolitan area. |
| `data_origin` | VARCHAR(32) | Data classification (`PUBLIC_RESEARCH`, `PARTICIPANT_REPORTED`, `DEMO_SYNTHETIC`). |
| `consent_confirmed` | BOOLEAN | Confirmation of informed consent. |
| `created_at` | TIMESTAMP | Record creation timestamp. |

---

## 3. Entity: `benchmark_research` (Reference Table)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `benchmark_id` | INTEGER PRIMARY KEY | Identifier for empirical benchmark source. |
| `source_title` | VARCHAR(128) | Name of published research study or report. |
| `publication_year` | INTEGER | Year of publication (e.g. 2021–2024). |
| `geography` | VARCHAR(64) | Geographical scope of the study. |
| `platform_type` | VARCHAR(64) | Platform segment studied. |
| `reported_gross_hourly` | REAL | Published gross payout per hour (converted to INR). |
| `reported_net_hourly` | REAL | Published net take-home earnings per hour. |
| `reported_fuel_expense_ratio` | REAL | Proportion of gross income spent on fuel/charging. |
| `reported_waiting_time_ratio` | REAL | Proportion of shift time spent in unpaid waiting. |
| `sample_size` | INTEGER | Number of workers or shifts surveyed. |
| `notes` | TEXT | Key findings and qualitative context. |

---

## 4. Evidence Classification Tiers (`data_origin`)

1. **`PUBLIC_RESEARCH`**:
   - Records derived directly from published institutional and academic empirical literature (e.g. Fairwork India, ILO, NITI Aayog).
   - Used for macro benchmarking, living wage comparisons, and cross-validation.
2. **`PARTICIPANT_REPORTED`**:
   - Real shift records voluntarily contributed by platform workers.
   - Requires explicit informed consent and zero credentials affirmation.
   - Protected by salted pseudonymization and k-anonymity (k ≥ 5).
3. **`DEMO_SYNTHETIC`**:
   - Statistically simulated demonstration data modeled after empirical distributions.
   - Generated for application demonstration, testing, and algorithmic evaluation.
   - **Never presented as real worker evidence.**
