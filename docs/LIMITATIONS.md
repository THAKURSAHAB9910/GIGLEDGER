# GIGLEDGER — Methodological Limitations & Analytical Caveats

This document outlines the methodological boundaries, data limitations, and analytical constraints inherent to GIGLEDGER.

---

## 1. Non-Representativeness of Sample

> **Explicit Disclaimer**: The dataset collected by GIGLEDGER does NOT claim to represent the entire gig-worker population of any city, country, or platform.

- **Convenience Sampling**: Voluntary contributions are collected via self-reporting. Workers who choose to track shifts may possess higher digital literacy or different work motivations than the median courier.
- **Participation Bias**: Couriers experiencing either unusually severe earnings distress or highly optimized shift strategies may be disproportionately motivated to submit logs.
- **Geographical Clustering**: Findings currently reflect shifts concentrated in major tier-1 metropolitan markets (Bengaluru, Delhi-NCR, Mumbai, Hyderabad). Generalizing to tier-2 or semi-urban delivery markets is invalid.

---

## 2. Observational Correlation vs. Causation

- GIGLEDGER analyzes **observational field data**. Statistical associations (e.g. between longer working hours and lower hourly rates, or between waiting times and net wages) **do not imply direct monocausal mechanisms**.
- Unobserved confounding variables—including sudden weather shifts, micro-market order density, traffic bottlenecks, and algorithmic priority scoring—cannot be fully controlled in non-experimental settings.

---

## 3. Exclusion of Long-Term Capital Depreciation

- Baseline financial calculations measure direct out-of-pocket shift operating expenses (fuel, routine maintenance, punctures, mobile data).
- Unless explicitly recorded, **long-term vehicle capital depreciation**, financing interest (EMIs), vehicle insurance amortization, and health/injury risk costs are not subtracted from net earnings.
- Consequently, true economic profit after full capital amortization is likely **even lower** than the reported net take-home earnings.

---

## 4. Unpaid Deadhead Distance Estimations

- Where workers do not record exact odometer readings at each order pickup and drop-off, deadhead uncompensated distance is estimated from total shift odometer distance minus paid trip delivery distances.
- Short personal diversions (e.g. taking a detour for lunch) may slightly inflate estimated deadhead kilometres.

---

## 5. Platform Algorithmic Opacity

- Delivery platforms do not publish their dispatch scoring logic, batching algorithms, or individual surge pricing formulas.
- Analytical conclusions are drawn strictly from empirical outputs (shift payouts received) rather than internal platform algorithmic code.
