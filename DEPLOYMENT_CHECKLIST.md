# Streamlit Deployment Checklist

## ✅ Completed Tasks

### Data Organization
- [x] Created `data/` subdirectory
- [x] Moved all 10 CSV files from root to `data/`
- [x] Updated git tracking (files renamed in git history)
- [x] All Python scripts now correctly reference `data/` directory

### Code Path Fixes
- [x] `app.py` - Uses `ROOT = Path(__file__).parent / 'data'` ✅
- [x] `build_triage.py` - Uses `root = Path(__file__).parent / 'data'` ✅
- [x] `build_validation_sample.py` - Uses `root = Path(__file__).parent / 'data'` ✅
- [x] `wellcome_import.py` - Default output to `data/wellcome_awards_imported.csv` ✅
- [x] `test_scoring.py` - Fixed path from `parents[1]` to `parent` ✅
- [x] `validation.py` - No hardcoded paths ✅
- [x] `mental_health_triage.py` - No hardcoded paths ✅
- [x] `scoring.py` - No hardcoded paths ✅

### Dependencies
- [x] Removed unused `plotly>=5.20` from requirements.txt
- [x] Removed unused `pyarrow>=15` from requirements.txt (only needed for future Parquet catalog)
- [x] Kept `behaviorgpt>=0.10` for documentation reference
- [x] Core dependencies: `streamlit>=1.35`, `pandas>=2.0`, `pytest>=8`

### Testing
- [x] All 8 unit tests pass:
  - `test_scoring.py::test_rank` ✅
  - `test_scoring.py::test_gap` ✅
  - `test_triage.py::test_direct_title` ✅
  - `test_triage.py::test_integrated` ✅
  - `test_triage.py::test_incidental` ✅
  - `test_validation.py::test_reproducible_and_unlabelled` ✅
  - `test_wellcome_import.py::test_import_and_dedup` ✅
  - `test_wellcome_import.py::test_reject_unknown_schema` ✅

### Streamlit Startup
- [x] Syntax validation passed
- [x] All imports work correctly
- [x] All required data files present
- [x] App structure verified

### Security
- [x] No API keys in code
- [x] UNBOXAI_API_KEY only mentioned in documentation comments
- [x] No BehaviorGPT calls made in application
- [x] `.gitignore` created with `lib/` and `.venv/`

### Data Labeling
- [x] Verified vs synthetic data clearly labeled:
  - Synthetic demo funders have `is_demo=true`
  - Real Wellcome awards have `record_type=awarded_grant`, `mental_health_flag=not_reviewed`
  - Verified observations in separate CSV with source citations
  - App UI displays warnings about synthetic data

### Documentation
- [x] README.md updated to mention `data/` directory requirement
- [x] All scripts reference correct paths

## 📋 Data Files (all in data/)

1. `evidence.csv` - Synthetic evidence data
2. `funders.csv` - Synthetic funder data (marked with `is_demo=true`)
3. `investments.csv` - Synthetic investment records
4. `needs.csv` - Synthetic financing needs
5. `opportunities.csv` - Synthetic opportunities
6. `theme_links.csv` - Synthetic theme mappings
7. `verified_observations.csv` - **REAL** Wellcome aggregate financial data (sourced)
8. `wellcome_awards_imported.csv` - **REAL** Wellcome grant records (26,288 awards)
9. `wellcome_mental_health_triage.csv` - Keyword triage output (requires human review)
10. `wellcome_validation_sample.csv` - Unlabeled audit sample

## ⚠️ Known Issues & Limitations

### None Critical
All identified issues have been resolved.

### Documentation Notes
- Mental health classifications are **NOT verified** - keyword candidates only
- No summing across categories should be performed without manual audit
- BehaviorGPT integration is scaffolding only - no actual API calls
- Verified observations are aggregate annual financial statement figures, not individual grants

## 🚀 Deployment Instructions

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest test_*.py -v

# Start Streamlit
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Ensure `requirements.txt` is in repository root
2. Ensure `data/` directory with all CSV files is committed
3. Set Python version to 3.11+ in Streamlit Cloud settings
4. Main file: `app.py`
5. No environment variables required (no API keys used)

### Environment Variables (Future)
When BehaviorGPT integration is enabled:
- `UNBOXAI_API_KEY` - Set in deployment environment, NOT in code
- Never commit API keys to repository

## 📊 Test Results Summary

**Test Run Date:** November 8, 2026
**Python Version:** 3.11.15
**pytest Version:** 9.2.0
**pandas Version:** 3.1.1
**streamlit Version:** 1.67.0

**Results:** 8/8 tests passed ✅
**Time:** 0.86 seconds
**Coverage:** All core modules tested

## 🎯 Verification Checklist for Deployment

Before deploying to production:
- [ ] Verify all CSV files are in `data/` directory
- [ ] Run `pytest test_*.py -v` to confirm tests pass
- [ ] Test Streamlit locally with `streamlit run app.py`
- [ ] Verify no API keys in environment variables (unless BehaviorGPT enabled)
- [ ] Check that synthetic data warnings display correctly in UI
- [ ] Confirm Wellcome award data source attribution is visible

## 📝 Post-Deployment Testing

After deployment:
1. Load each tab in the Streamlit app
2. Verify "Verified Evidence" tab displays real data with sources
3. Verify "Award-Level Explorer" loads Wellcome data
4. Check that synthetic data warnings appear on synthetic tabs
5. Test file upload functionality (Award-Level Explorer)
6. Verify downloads work (CSV exports)
7. Check mental health triage queues display correctly

## 🔄 Branch Information

**Branch:** `streamlit-deployment-prep`
**Base:** `main`
**Status:** Ready for PR

All changes are committed and ready for pull request.
