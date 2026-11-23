# GIGLEDGER — Problem Statement & Research Foundation

## 1. Executive Summary

Digital labor platforms in food delivery, quick-commerce grocery, e-commerce parcel logistics, and ride-hailing recruit millions of workers globally by advertising gross payouts, surge multiples, and weekly incentive targets. In platform onboarding marketing, headline earnings figures frequently quote rates such as **"Earn up to ₹30,000–₹40,000 per month"** or **"₹150–₹200 per hour"**.

However, empirical labor research (Fairwork India 2021–2024, ILO 2021, NITI Aayog 2022) indicates a profound divergence between advertised headline earnings and the actual net income retained by workers. This divergence stems from structural features of algorithmic platform dispatch:

$$\text{Headline Payout} \gg \text{True Net Take-Home Earnings}$$

**GIGLEDGER** is an institutional-grade financial analytics and SQL intelligence platform built to systematically investigate, quantify, and model this economic divergence.

---

## 2. The Core Investigative Question

> **"How much does a gig worker actually earn after considering time, expenses, and payout conditions?"**

To answer this question rigorously, the system decomposes every shift into its operational and financial constituent parts:
1. **Total displayed gross payouts** (base delivery fee + dynamic surge + milestone bonuses).
2. **Mandatory out-of-pocket operating expenses** (fuel/EV battery swap, tire punctures, engine oil top-up, mobile data packs).
3. **Uncompensated waiting time** (idle time spent queued at restaurant counters, dark stores, and awaiting algorithmic order dispatches).
4. **Deadhead uncompensated distance** (transit kilometres driven returning from peripheral drop-off destinations back to high-density commercial zones without an active payload).
5. **Platform penalties & deductions** (cancellation fees, customer dispute deductions, uniform/onboarding deposits).

---

## 3. Why Generic Expense Trackers Fail

A frequent misconception is to treat gig worker financial tracking as a standard "personal budgeting" or "expense management" task. Generic expense trackers fail for gig labor analysis because:

1. **Failure to Model Algorithmic Time Dilution**: Personal budgeting apps track money in versus money out. They do not calculate **Effective Hourly Net Wage** ($\text{Net Earnings} / \text{Total Elapsed Shift Time}$), failing to account for 2.5–4.0 hours of uncompensated waiting time per day.
2. **Ignoring Unpaid "Deadhead" Distance**: A courier driving 120 km in a shift may only carry paid payloads for 75 km. Generic trackers do not measure the 30–40% deadhead return burden.
3. **Ignoring Milestone Cliff Vulnerabilities**: Platform incentive structures rely on non-linear threshold "cliffs" (e.g. deliver 20 orders to unlock a ₹400 bonus; delivering 19 pays ₹0). When a worker misses the cliff by 1 delivery, their effective wage collapses.
4. **Lack of Cohort & Modality Benchmarking**: Generic apps do not segment performance across vehicle modalities (Electric 2W vs. ICE Motorcycle vs. Scooter) or cross-reference against statutory minimum wage baselines.

---

## 4. Key Target Audiences

- **Labor Economists & Policy Researchers**: Investigating minimum wage compliance and fair compensation in platform economies.
- **Workers' Collectives & Gig Worker Advocates**: Requiring verifiable empirical data to contest unfair deductions and deactivations.
- **Urban Mobility & Transportation Analysts**: Modeling deadhead vehicle kilometres travelled (VKT) and urban congestion externalities.
- **Platform Workers**: Seeking transparency into their real hourly take-home pay to make informed decisions about shift timing, vehicle choice, and target chasing.
