# GIGLEDGER — Metric Definitions & Mathematical Formulations

This document specifies the exact mathematical definitions, inputs, inclusions, exclusions, and edge-case guards for all financial and operational indicators implemented in GIGLEDGER.

---

## 1. Gross Earnings ($G$)

$$\text{Gross Earnings} = \text{Base Payout} + \text{Incentive Pay} + \text{Bonus Pay}$$

- **Inclusions**:
  - Guaranteed trip fees and distance-based base rates.
  - Surge multipliers, rain incentives, and daily peak-hour rewards.
  - Weekly loyalty or milestone completion bonuses.
- **Exclusions**:
  - Direct cash tips paid by customers off-platform.
  - Toll and parking reimbursements.
- **Edge Cases**:
  - Missing/NaN inputs are coerced to $0.0$. Negative inputs are rejected by validation.

---

## 2. Total Operating Expenses ($E$)

$$\text{Total Expenses} = \text{Fuel} + \text{Maintenance} + \text{Other Direct Costs} + \text{Cancellation Penalties}$$

- **Inclusions**:
  - Direct fuel purchases (petrol/diesel) or EV battery recharge/swap fees.
  - Prorated routine vehicle maintenance (oil change, chain lube, puncture repairs).
  - Shift-specific operating costs (mobile data pack, parking fees, tolls, drinking water).
  - Uncompensated direct cancellation fees or penalties debited to the worker.
- **Exclusions**:
  - General personal living costs (home rent, non-shift groceries).
  - Long-term capital purchase depreciation (unless specified in advanced vehicle modeling).
- **Edge Cases**:
  - Coerced to $0.0$ if absent; values $< 0$ are invalid.

---

## 3. Net Take-Home Earnings ($N$)

$$\text{Net Earnings} = \text{Gross Earnings} - \text{Platform Deductions} - \text{Total Operating Expenses}$$

$$N = G - D - E$$

- **Interpretation**: Represents the actual disposable income left in the worker's possession after all platform deductions and shift expenses have been paid.
- **Edge Cases**:
  - $N$ can be **negative** in distressed shifts where fuel, maintenance breakdowns, and penalty fees exceed the gross payout earned.

---

## 4. Effective Hourly Net Earnings ($R_{\text{net}}$)

$$R_{\text{net}} = \begin{cases} \dfrac{\text{Net Earnings}}{\text{Total Shift Working Hours}}, & \text{if Total Hours} > 0 \\ 0.0, & \text{if Total Hours} \le 0 \end{cases}$$

- **Denominator**: Total elapsed shift time from login to logout (trip time + waiting time + return deadhead transit).
- **Benchmark**: Evaluated directly against the statutory minimum wage baseline ($\approx ₹100/\text{hr}$).
- **Edge Cases**:
  - If $\text{Total Hours} \le 0.0$, returns $0.0$ (never raises `ZeroDivisionError`).

---

## 5. Effective Hourly Gross Earnings ($R_{\text{gross}}$)

$$R_{\text{gross}} = \begin{cases} \dfrac{\text{Gross Earnings}}{\text{Total Shift Working Hours}}, & \text{if Total Hours} > 0 \\ 0.0, & \text{if Total Hours} \le 0 \end{cases}$$

- **Interpretation**: The headline payout per hour advertised or displayed on platform summary cards.

---

## 6. Gross-to-Net Shortfall Percentage ($S$)

$$S = \begin{cases} \dfrac{G - N}{G} \times 100, & \text{if } G > 0 \\ 0.0, & \text{if } G \le 0 \end{cases}$$

- **Interpretation**: The exact percentage of displayed gross payout erased by operational costs and deductions.

---

## 7. Net Earnings per Kilometre ($R_{\text{km}}$)

$$R_{\text{km}} = \begin{cases} \dfrac{\text{Net Earnings}}{\text{Total Distance (km)}}, & \text{if Total Distance} > 0 \\ 0.0, & \text{if Total Distance} \le 0 \end{cases}$$

- **Interpretation**: Net profitability per unit of vehicle wear and travel.

---

## 8. Operating Expense Ratio ($\rho_{\text{exp}}$)

$$\rho_{\text{exp}} = \begin{cases} \dfrac{\text{Total Expenses}}{\text{Gross Earnings}}, & \text{if Gross Earnings} > 0 \\ 0.0, & \text{if Gross Earnings} \le 0 \end{cases}$$

- **Interpretation**: The proportion of gross revenue consumed by out-of-pocket costs. A ratio $\ge 0.40$ indicates severe economic distress.

---

## 9. Incentive Dependency Ratio ($\rho_{\text{inc}}$)

$$\rho_{\text{inc}} = \begin{cases} \min\left(1.0, \max\left(0.0, \dfrac{\text{Incentive Pay} + \text{Bonus Pay}}{\text{Gross Earnings}}\right)\right), & \text{if Gross} > 0 \\ 0.0, & \text{if Gross} \le 0 \end{cases}$$

- **Interpretation**: The share of total income contingent upon meeting platform targets and surge rules rather than guaranteed base trip rates.
- **Vulnerability Tiers**:
  - $\rho_{\text{inc}} < 0.25$: Base-reliant.
  - $0.25 \le \rho_{\text{inc}} < 0.50$: Moderate vulnerability.
  - $\rho_{\text{inc}} \ge 0.50$: High vulnerability (worker livelihood threatened if targets are missed).

---

## 10. Unpaid Time Ratio ($\tau_{\text{unpaid}}$)

$$\tau_{\text{unpaid}} = \begin{cases} \min\left(1.0, \max\left(0.0, \dfrac{\text{Waiting Time (hours)}}{\text{Total Shift Hours}}\right)\right), & \text{if Total Hours} > 0 \\ 0.0, & \text{if Total Hours} \le 0 \end{cases}$$

- **Interpretation**: Fraction of shift duration spent in uncompensated idle queues.

---

## 11. Unpaid Distance (Deadhead) Ratio ($\delta_{\text{deadhead}}$)

$$\delta_{\text{deadhead}} = \begin{cases} \min\left(1.0, \max\left(0.0, \dfrac{\text{Total KM} - \text{Paid KM}}{\text{Total KM}}\right)\right), & \text{if Total KM} > 0 \\ 0.0, & \text{if Total KM} \le 0 \end{cases}$$

- **Interpretation**: Fraction of total travel distance spent returning empty or repositioning between order dispatches.

---

## 12. Income Volatility Index (Coefficient of Variation, $CV$)

$$CV = \dfrac{\sigma_{\text{net}}}{\mu_{\text{net}}}$$

- Where $\sigma_{\text{net}}$ is sample standard deviation ($ddof = 1$) and $\mu_{\text{net}}$ is the arithmetic mean of shift net earnings.
- Used to quantify day-to-day income unpredictability across workers.
