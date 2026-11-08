# Verified evidence and expansion plan

## Current verified records
`data/verified_observations.csv` contains six sourced, *aggregate* Wellcome observations, drawn from the 2024 and 2025 annual reports. These are **not** six grants and must never be used as six independent BehaviorGPT `Order` events. Values remain in GBP millions, without currency conversion or combining different measures.

## First reproducible acquisition route
1. Download Wellcome's published grants dataset from https://wellcome.org/research-funding/funding-portfolio . It provides award amounts, dates and summaries. Verify license and inspect columns before import.
2. Filter awarded grants to a defined date window; retain original grant identifiers, dates, funder, recipient, currency, amount, theme, and source URL. Maintain original and derived classifications separately.
3. Expand with IATI Datastore Search https://iatidatastore.iatistandard.org/ using activity-level exports for descriptive context and transaction-level exports for financing flows. IATI version 3 API requires its **own** subscription key: https://docs.datastore.iatistandard.org/en/latest/api/ . Do not treat activity totals and transaction amounts as additive.
4. Add other funders only when award-level records can be verified and compared. Deduplicate by original identifier, publisher, date, amount and reporting role.
5. Maintain an explicit `source_status` field: `verified`, `derived`, `unverified`, or `synthetic`. No synthetic row may appear in the real-evidence dashboard.

## BehaviorGPT experiment
The first proper behavioral test requires a *catalog of individual fundable choices*, not annual accounting totals. Use historical grants as candidate items only after establishing the intended decision and temporal eligibility. Each institution's observed awards form a chronological sequence of completed choices; do not manufacture views or searches. Prevent leakage: at prediction date T, do not include awards first announced after T in history or features. Compare against recency, frequency, and theme-similarity baselines; report funder-specific coverage and Recall@5. Institutional grantmaking is out-of-domain for a model trained on consumer behavioral sequences, so treat rankings as exploratory.

## Data quality gates
- No inferred zeros for missing amounts.
- Separate awards, commitments, disbursements, expenditure, and investment.
- Preserve currency and price year; no currency summation without a documented conversion.
- Separate direct mental health, integrated mental health, and uncertain classification.
- Source URL and source document for each record.
- Confirm eligibility and geographic restrictions before calling any candidate a prospect.
