# MindVest Global — working MVP with complete Wellcome dataset

**Status:** Offline prototype with real Wellcome grant data (2000-2026) + clearly labeled synthetic modules. No BehaviorGPT predictions.

## Quick Start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Complete Wellcome Dataset (November 2026)

This repository now includes the **complete official Wellcome grants dataset**: 23,942 analytically eligible awards totaling £19.8 billion (2000-2026). The bundled file (`data/wellcome_full_analytical.csv`) excludes zero-amount records (studentships, institutional awards) to focus on financial analysis.

### Data Layers

1. **Analytical Layer** (`wellcome_full_analytical.csv`): 23,942 awards with amount > £0 (bundled)
2. **Mental Health Candidates** (`wellcome_full_mh_candidates_unreviewed.csv`): 2,489 keyword matches (UNREVIEWED)
3. **Exclusions Log** (`wellcome_full_exclusions.csv`): Audit trail of excluded records
4. **Raw Source & Full Import**: Not committed (regenerate locally, see below)

### Reproducible Import Pipeline

To regenerate all data layers from the official Wellcome workbook:

```bash
# 1. Download official workbook from https://wellcome.org/research-funding/funding-portfolio
# 2. Place in data/ directory as: data/Wellcome-grants-awarded-1-October-2000-to-9-September-2026.xlsx
# 3. Run import pipeline:
PYTHONPATH=./lib python import_full_wellcome.py
```

This generates:
- Complete audit report: `data/FULL_WELLCOME_IMPORT_AUDIT.md`
- All 5 data layers with reconciliation
- Deterministic, reproducible output
- No network calls or external data transmission

### Source Attribution

**Data Source**: Wellcome Trust grants database, licensed under CC BY 4.0  
**Source URL**: https://wellcome.org/research-funding/funding-portfolio  
**Coverage**: Awards from 1 October 2000 to 9 September 2026  
**Total Records**: 26,288 (including 2,346 zero-amount records)  
**Analytical Records**: 23,942 grants (amount > £0)  
**Total Amount**: £19,787,008,487.33

See `data/FULL_WELLCOME_IMPORT_AUDIT.md` for complete reconciliation.

## Start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app expects CSV datasets in the `data/` subdirectory.

## Tests

Run all tests including full import validation:

```bash
PYTHONPATH=./lib pytest -v
```

Test coverage:
- Full dataset import and reconciliation (28 tests)
- Date parsing for Excel datetime columns
- Duplicate detection and exclusion tracking
- Financial reconciliation and reproducibility
- App integration and data layer integrity
- Validation logic and error handling

## Structure

- `app.py`: six-view interactive Streamlit prototype
- `scoring.py`: transparent theme-overlap baseline and gap formula
- `data/`: synthetic CSV records, including evidence register
- `tests/`: baseline tests
- `docs/`: schema, sources, and BehaviorGPT integration plan

## Security

Do not commit API keys. When the integration is enabled later, set `UNBOXAI_API_KEY` in your local/server environment. Do not put it in code, chat, frontend state, or screenshots. `.env` is ignored.

## Model integration status

No BehaviorGPT calls are made in the MVP. An approved catalog upload is a separate step. Institution histories must be constructed from documented events, not fabricated searches/views. Compare ranking performance against the transparent baseline before making predictive claims.

## Verified-evidence pilot (November 2026)
Open the **Verified Evidence** view for six sourced Wellcome annual-report observations. These are aggregates, not individual awards. All other dashboard views remain synthetic. See `docs/REAL_DATA_ROADMAP.md` for the acquisition and validation plan.

## Award-Level Explorer

The **Award-Level Explorer** view displays the complete 23,942-record Wellcome analytical dataset by default. Users can optionally upload alternative exports. The view clearly distinguishes:

- **Bundled complete dataset**: 23,942 official Wellcome grants (2000-2026)
- **User uploads**: Independently verified provenance required

Mental health keyword candidates (2,489 records) are flagged as UNREVIEWED and require manual classification. All thematic classifications are automated screening, not verified by domain experts.

## Mental-health triage (new)

Run `python build_triage.py` to regenerate `data/wellcome_mental_health_triage.csv` from the imported Wellcome award-level CSV. Open **Mental Health Triage** in Streamlit to inspect and export review queues. The rules use explicit mental-health keywords in titles/descriptions, adjacent-sector cues, and broad terms; all results remain `not_reviewed`. Categories are mutually exclusive and must **not** be interpreted as verified mental-health grant counts or summed as mental-health funding. Review samples for false positives and false negatives, check duplicate/supplement awards, and manually adjudicate classifications before estimating financing trends. No BehaviorGPT calls or data uploads are performed.

## Stratified classification validation (new)

Run `python build_validation_sample.py` to recreate a fixed-seed 150-record audit sample (30 from each of five keyword screening strata, including 30 **no-rule-match** records to check missed cases). Open **Classification Validation** to download the worksheet and upload adjudicated labels. No rows are labelled by the software. Valid human labels: `direct`, `integrated`, `not_mental_health`, `uncertain`. Record reviewers and rationale; a second reviewer should independently examine ambiguous cases. The app refuses to show a population estimate until all sampled records are adjudicated without uncertainty. This estimate is exploratory and lacks confidence intervals; do not use it as a funding total.
