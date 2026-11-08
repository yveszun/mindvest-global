# Wellcome source import audit

Source: user-uploaded `Wellcome-grants-awarded-1-October-2000-to-9-September-2026.xlsx`; original source https://wellcome.org/research-funding/funding-portfolio .

- Worksheet 1 (grants) imported: **26,288** records; no duplicate/missing identifiers, invalid amounts, non-GBP records, or invalid award dates encountered.
- Worksheet 2 is a supplementary recipient-organization table and was not treated as additional awards.
- Fields retained: identifier, internal ID, award title, description, recipient, recipient country, award date, GBP amount, financial year, programme, and source URL.
- **1,364** keyword candidates flagged by a deliberately broad text search of title plus description. False positives and false negatives are expected; no record is labeled a confirmed mental-health investment.
- Amounts are awarded amounts, not verified cash disbursements. Zero-value awards may be present. Do not sum as a measure of mental-health funding until award scope, transfers, revisions, and classification are validated.
- Data covers Wellcome only. Institutional behavioral prediction cannot be validated across multiple funders from this dataset.
- No third-party uploads or BehaviorGPT calls.

Next: manual review of candidate classification, distinguish direct from integrated mental-health investments, and acquire award-level records from additional funders.
