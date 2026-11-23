# GIGLEDGER — Public Research Literature & Empirical Data Sources

To ensure GIGLEDGER's analytical models are grounded in empirical reality, the platform integrates historical benchmarks and methodological frameworks from leading labor economics research institutions.

---

## 1. Primary Empirical Literature Survey

### 1. Fairwork India Ratings (2021–2024)
- **Institution**: Centre for IT and Public Policy (CITAPP), IIIT-Bangalore & Fairwork Foundation, Oxford Internet Institute.
- **Key Findings**: Consistently highlighted that after accounting for vehicle loan repayments, fuel, data plans, and platform commissions, a majority of app-based couriers earn below local statutory minimum wage thresholds. Emphasized the extreme volatility introduced by algorithmic target bonuses and deactivations.
- **Reference**: Fairwork India Ratings: *Evaluating Platform Labour Standards in the Gig Economy*.

### 2. NITI Aayog Policy Report (June 2022)
- **Institution**: National Institution for Transforming India (NITI Aayog, Government of India).
- **Report Title**: *"Booming Gig and Platform Economy: Perspectives and Recommendations on the Future of Work"*.
- **Key Findings**: Documented the exponential rise of 10-minute grocery and food delivery couriers (projecting platform workers to expand to 23.5 million by 2029–30). Identified high out-of-pocket fuel burdens for 2-wheeler operators and recommended occupational social security codes.

### 3. International Labour Organization (ILO, 2021)
- **Institution**: International Labour Organization (United Nations).
- **Report Title**: *World Employment and Social Outlook 2021: The role of digital labour platforms in transforming the world of work*.
- **Key Findings**: Multi-country survey of 12,000 app-based couriers and ride-hail drivers across developing and developed economies. Documented that couriers spend an average of **30–35% of their working day in uncompensated idle waiting time**.

### 4. National Council of Applied Economic Research (NCAER, 2023)
- **Institution**: NCAER, New Delhi.
- **Report Title**: *Socio-Economic Impact Assessment of App-Based Platform Workers in India*.
- **Key Findings**: Documented that average active couriers work 9.8–11.2 hours per day across peak meal windows. Highlighted the efficiency and fuel cost divergence between internal combustion engine (ICE) 2-wheelers and electric 2-wheelers (EVs).

### 5. Centre for Internet and Society (CIS, 2021)
- **Institution**: CIS India, Bengaluru.
- **Report Title**: *Algorithmic Management and Delivery Couriers in Bengaluru*.
- **Key Findings**: Detailed worker field interviews showing how tiered milestone targets induce workers to skip meals, ignore fatigue, and drive under extreme monsoonal conditions to avoid missing fixed bonus cliffs.

### 6. UC Berkeley Labor Center (2020)
- **Institution**: University of California, Berkeley.
- **Study**: *Rideshare and Delivery Worker Net Earnings Analysis*.
- **Key Findings**: Demonstrated that failure to deduct deadhead transit miles and vehicle operating wear results in an overestimation of worker hourly earnings by **40% to 50%**.

---

## 2. Integration into GIGLEDGER

These empirical benchmarks are permanently ingested into the `benchmark_research` database table and stored in:
- `data/sample/benchmark_research_data.csv`

The data is surfaced in **Dashboard Page 6 (Public Research Benchmarks)**, enabling live cross-referencing between participant-reported shifts and published institutional findings.
