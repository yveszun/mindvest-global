================================================================================
WELLCOME FULL IMPORT AUDIT REPORT
================================================================================

Generated: 2026-11-08 19:11:51
Source: data/Wellcome-grants-awarded-1-October-2000-to-9-September-2026.xlsx

### SOURCE DATA ###
Total source rows: 26,288
Columns: 27

Workbook sheets:
  - Main Grant List: 26,288 rows, 27 columns
  - # Additional Location Data: 10,912 rows, 5 columns

### IMPORT RESULTS ###
Successfully imported: 26,288 records
Acceptance rate: 100.00%

### EXCLUSIONS BY REASON ###
Total excluded: 2,346
  - zero_amount: 2,346 (8.92%)

### DUPLICATE ANALYSIS ###
Duplicate Internal IDs in source: 0
Duplicate grant IDs in output: 0

### MISSING VALUE ANALYSIS (SOURCE) ###
Internal ID: 0 missing (0.00%)
Title: 0 missing (0.00%)
Award Date: 0 missing (0.00%)
Amount Awarded: 0 missing (0.00%)
Currency: 0 missing (0.00%)

### DATE RANGE ###
Source date range: 2000-10-01 00:00:00 to 2026-08-31 00:00:00
Imported date range: 2000-10-01 00:00:00 to 2026-08-31 00:00:00

### CURRENCY ANALYSIS ###
GBP: 26,288 (100.00%)

### FINANCIAL RECONCILIATION ###
Source total (all records): £19,787,008,487.32
Imported total: £19,787,008,487.33
Excluded amount: £-0.00
Coverage: 100.00%

### AMOUNT STATISTICS (IMPORTED) ###
Records with amount > 0: 23,942
Mean: £826,455.96
Median: £160,792.00
Min: £1.00
Max: £575,000,000.00
Total: £19,787,008,487.33

### MENTAL HEALTH KEYWORD SCREENING ###
(Conservative keyword matching - all flagged records require manual review)
Keyword matches: 2,489 (9.47%)
Total amount in candidates: £2,171,837,214.01

WARNING: These are unreviewed candidates only.
Do NOT treat as verified mental health funding.
Manual classification required.

### DATA LAYERS ###

1. RAW SOURCE LAYER
   File: data/wellcome_full_raw_source.csv
   Records: 26,288
   Purpose: Complete unmodified source data

2. FULL IMPORTED LAYER (includes zero amounts)
   File: data/wellcome_full_imported_all.csv
   Records: 26,288
   Purpose: All successfully parsed grants

3. ANALYTICAL LAYER (amount > £0)
   File: data/wellcome_full_analytical.csv
   Records: 23,942
   Total: £19,787,008,487.33
   Purpose: Awards with financial value for analysis

4. MENTAL HEALTH CANDIDATES (UNREVIEWED)
   File: data/wellcome_full_mh_candidates_unreviewed.csv
   Records: 2,489
   Total: £2,171,837,214.01
   Purpose: Keyword matches requiring manual review
   Status: UNREVIEWED - do not use as verified MH funding

5. IMPORT LEDGER (complete status for all source rows)
   File: data/wellcome_full_import_ledger.csv
   Records: 26,288
   Included: 23,942
   Excluded: 2,346
   Purpose: Complete row-by-row status tracking

6. EXCLUSIONS ONLY (filtered view)
   File: data/wellcome_full_exclusions_only.csv
   Records: 2,346
   Purpose: Records excluded from analytical layer

### REPRODUCIBILITY ###
Command to reproduce:
  PYTHONPATH=./lib python import_full_wellcome.py

Deterministic: Yes
Network calls: None
BehaviorGPT calls: None
External data transmission: None

### STREAMLIT DEPLOYMENT NOTES ###
Recommended bundle: wellcome_full_analytical.csv
File size: ~31.58 MB
Memory estimate: ~23 MB RAM
Load time estimate: 1-3 seconds

Streamlit Community Cloud limits:
  - RAM: 1 GB
  - Should be compatible with current dataset size

================================================================================
IMPORT COMPLETE
================================================================================