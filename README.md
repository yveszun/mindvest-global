# MindVest Global — working MVP

**Status:** Offline synthetic-data prototype. No live financing evidence or BehaviorGPT prediction is represented as real.

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

```bash
pytest -q
```

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

## Award-level ingestion (new)
Download Wellcome's award spreadsheet from https://wellcome.org/research-funding/funding-portfolio (Wellcome states the data are CC BY 4.0, attribution required). Either upload the spreadsheet in **Award-Level Explorer** or run:

```bash
python wellcome_import.py ~/Downloads/wellcome-grants.xlsx --output data/wellcome_awards_imported.csv
```

The importer detects common column headings, removes duplicate grant IDs, preserves grant dates and source attribution, and deliberately leaves all mental-health classification unreviewed. The official spreadsheet was **not** bundled: network access to download it was unavailable in this build environment. The importer needs validation against the current actual spreadsheet headings before production use. No model calls or third-party uploads occur.

## Actual Wellcome export imported (8 November 2026)
The `data/wellcome_awards_imported.csv` file contains 26,288 grant records parsed from the user-provided Wellcome export (1 October 2000–9 September 2026). There are 1,364 broad mental-health keyword candidates **requiring manual verification**. These are not confirmed mental health grants. The source workbook is not bundled. No BehaviorGPT call has been made. `wellcome_import.py` has been updated for the source's real column headings and Excel serial dates. See `docs/WELLCOME_IMPORT_AUDIT.md`.

## Mental-health triage (new)

Run `python build_triage.py` to regenerate `data/wellcome_mental_health_triage.csv` from the imported Wellcome award-level CSV. Open **Mental Health Triage** in Streamlit to inspect and export review queues. The rules use explicit mental-health keywords in titles/descriptions, adjacent-sector cues, and broad terms; all results remain `not_reviewed`. Categories are mutually exclusive and must **not** be interpreted as verified mental-health grant counts or summed as mental-health funding. Review samples for false positives and false negatives, check duplicate/supplement awards, and manually adjudicate classifications before estimating financing trends. No BehaviorGPT calls or data uploads are performed.

## Stratified classification validation (new)

Run `python build_validation_sample.py` to recreate a fixed-seed 150-record audit sample (30 from each of five keyword screening strata, including 30 **no-rule-match** records to check missed cases). Open **Classification Validation** to download the worksheet and upload adjudicated labels. No rows are labelled by the software. Valid human labels: `direct`, `integrated`, `not_mental_health`, `uncertain`. Record reviewers and rationale; a second reviewer should independently examine ambiguous cases. The app refuses to show a population estimate until all sampled records are adjudicated without uncertainty. This estimate is exploratory and lacks confidence intervals; do not use it as a funding total.
