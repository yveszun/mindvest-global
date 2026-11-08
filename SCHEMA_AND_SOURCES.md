# MindVest data contract and evidence acquisition

## Entities

- `funders`: funder_id (PK), name, type, headquarters, mandate, is_demo.
- `investments`: investment_id (PK), funder_id (FK), recipient, year, theme, country, amount, currency, instrument, finance_status, mh_relevance, source_id (FK), is_demo.
- `opportunities`: opportunity_id (PK), name, theme, geography, intervention, eligible_funder_types, description, is_demo.
- `needs`: country, year, intervention, estimated_need_usd, available_financing_usd, coverage_note, source_id (FK), is_demo.
- `evidence`: source_id (PK), publisher, title, url, publication_date, access_date, quality, notes, is_demo.
- `theme_links`: opportunity_id (FK), history_theme. This is an explicitly authored baseline matching dictionary.

## Production extensions

Normalize recipient, geography, taxonomy, instrument, currency and funder classifications; create `investment_themes` join table for multiple themes per award; add transaction dates, source-specific identifiers, reported versus normalized amount, FX rate/date/source, flow type, fiscal year, recipient country, decision status, original description, verified eligibility, source-level licensing and extraction provenance. Maintain historical revisions rather than overwriting records.

## Source candidates (coverage/licensing to verify)

- OECD development finance: https://stats.oecd.org/
- IATI Datastore: https://datastore.iatistandard.org/
- Candid: https://candid.org/
- WHO Mental Health Atlas: https://www.who.int/teams/mental-health-and-substance-use/data-research/mental-health-atlas
- IHME: https://www.healthdata.org/
- Individual funder reports, grant databases, and institutional project pages.

## Validation rules

1. Never mix commitments, disbursements, grants, loans and equity in an undifferentiated sum.
2. Never infer an unfunded need from missing financing records.
3. Reconcile geography, time, intervention, financing coverage, currency and price year before computing gaps.
4. Keep direct MH, integrated MH, adjacent and uncertain investments separate.
5. Every real-world assertion must have a traceable source and an observation date.
6. Distinguish funder suitability from demonstrated willingness and actual open funding calls.
7. Do not use protected or private proposal reviews without appropriate permission.
