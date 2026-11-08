"""
Full Wellcome Import Pipeline - Reproducible import with comprehensive audit trail.

Creates distinct data layers:
1. Raw source data (all 26,288 grants preserved)
2. Analytically eligible grants (excludes zero-amount records)
3. Mental health keyword candidates (separate unreviewed layer)

No BehaviorGPT calls. No external data transmission.
Fully deterministic and reproducible.
"""
import pandas as pd
from pathlib import Path
import wellcome_import as wi
from datetime import datetime

def generate_import_audit(workbook_path, output_dir='data'):
    """Generate comprehensive audit report for Wellcome import."""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    audit_report = []
    audit_report.append("=" * 80)
    audit_report.append("WELLCOME FULL IMPORT AUDIT REPORT")
    audit_report.append("=" * 80)
    audit_report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    audit_report.append(f"Source: {workbook_path}")
    
    # Import with full audit trail
    print("Loading Wellcome workbook...")
    imported, raw, exclusions = wi.import_awards(workbook_path, include_raw=True)
    
    audit_report.append(f"\n### SOURCE DATA ###")
    audit_report.append(f"Total source rows: {len(raw):,}")
    audit_report.append(f"Columns: {len(raw.columns)}")
    
    # Check for additional sheets
    xl = pd.ExcelFile(workbook_path)
    audit_report.append(f"\nWorkbook sheets:")
    for sheet in xl.sheet_names:
        df = pd.read_excel(workbook_path, sheet_name=sheet)
        audit_report.append(f"  - {sheet}: {len(df):,} rows, {len(df.columns)} columns")
    
    audit_report.append(f"\n### IMPORT RESULTS ###")
    audit_report.append(f"Successfully imported: {len(imported):,} records")
    audit_report.append(f"Acceptance rate: {len(imported)/len(raw)*100:.2f}%")
    
    # Exclusion breakdown
    audit_report.append(f"\n### EXCLUSIONS BY REASON ###")
    excluded_count = exclusions['excluded'].sum()
    audit_report.append(f"Total excluded: {excluded_count:,}")
    
    if excluded_count > 0:
        exclusion_summary = exclusions[exclusions['excluded']].groupby('exclusion_reason').size()
        for reason, count in exclusion_summary.items():
            pct = count / len(raw) * 100
            audit_report.append(f"  - {reason}: {count:,} ({pct:.2f}%)")
    
    # Duplicate check
    audit_report.append(f"\n### DUPLICATE ANALYSIS ###")
    source_dups = raw['Internal ID'].duplicated().sum()
    imported_dups = imported['grant_id'].duplicated().sum()
    audit_report.append(f"Duplicate Internal IDs in source: {source_dups}")
    audit_report.append(f"Duplicate grant IDs in output: {imported_dups}")
    
    # Missing values
    audit_report.append(f"\n### MISSING VALUE ANALYSIS (SOURCE) ###")
    key_cols = ['Internal ID', 'Title', 'Award Date', 'Amount Awarded', 'Currency']
    for col in key_cols:
        if col in raw.columns:
            null_count = raw[col].isnull().sum()
            pct = null_count / len(raw) * 100
            audit_report.append(f"{col}: {null_count:,} missing ({pct:.2f}%)")
    
    # Date range
    audit_report.append(f"\n### DATE RANGE ###")
    audit_report.append(f"Source date range: {raw['Award Date'].min()} to {raw['Award Date'].max()}")
    audit_report.append(f"Imported date range: {imported['award_date'].min()} to {imported['award_date'].max()}")
    
    # Currency analysis
    audit_report.append(f"\n### CURRENCY ANALYSIS ###")
    if 'Currency' in raw.columns:
        currency_counts = raw['Currency'].value_counts()
        for curr, count in currency_counts.items():
            pct = count / len(raw) * 100
            audit_report.append(f"{curr}: {count:,} ({pct:.2f}%)")
    
    # Financial reconciliation
    audit_report.append(f"\n### FINANCIAL RECONCILIATION ###")
    source_total = raw['Amount Awarded'].sum()
    imported_total = imported['amount_gbp'].sum()
    excluded_total = source_total - imported_total
    
    audit_report.append(f"Source total (all records): £{source_total:,.2f}")
    audit_report.append(f"Imported total: £{imported_total:,.2f}")
    audit_report.append(f"Excluded amount: £{excluded_total:,.2f}")
    audit_report.append(f"Coverage: {imported_total/source_total*100:.2f}%")
    
    # Amount statistics
    audit_report.append(f"\n### AMOUNT STATISTICS (IMPORTED) ###")
    non_zero = imported[imported['amount_gbp'] > 0]
    audit_report.append(f"Records with amount > 0: {len(non_zero):,}")
    audit_report.append(f"Mean: £{non_zero['amount_gbp'].mean():,.2f}")
    audit_report.append(f"Median: £{non_zero['amount_gbp'].median():,.2f}")
    audit_report.append(f"Min: £{non_zero['amount_gbp'].min():,.2f}")
    audit_report.append(f"Max: £{non_zero['amount_gbp'].max():,.2f}")
    audit_report.append(f"Total: £{non_zero['amount_gbp'].sum():,.2f}")
    
    # Mental health keyword analysis
    audit_report.append(f"\n### MENTAL HEALTH KEYWORD SCREENING ###")
    audit_report.append("(Conservative keyword matching - all flagged records require manual review)")
    
    mental_health_keywords = [
        'mental health', 'mental illness', 'mental disorder', 'psychiatr',
        'psychology', 'psychiat', 'depression', 'anxiety', 'schizophrenia',
        'bipolar', 'psychosis', 'neurodevelopmental', 'autism', 'adhd',
        'wellbeing', 'well-being', 'suicide', 'self-harm'
    ]
    
    keyword_matches = pd.Series([False] * len(imported))
    for keyword in mental_health_keywords:
        keyword_matches |= imported['title'].str.lower().str.contains(keyword, na=False)
        keyword_matches |= imported['description'].str.lower().str.contains(keyword, na=False)
    
    mh_candidates = imported[keyword_matches].copy()
    audit_report.append(f"Keyword matches: {len(mh_candidates):,} ({len(mh_candidates)/len(imported)*100:.2f}%)")
    audit_report.append(f"Total amount in candidates: £{mh_candidates['amount_gbp'].sum():,.2f}")
    audit_report.append("\nWARNING: These are unreviewed candidates only.")
    audit_report.append("Do NOT treat as verified mental health funding.")
    audit_report.append("Manual classification required.")
    
    audit_report.append(f"\n### DATA LAYERS ###")
    
    # Layer 1: Raw source (all records)
    raw_output = output_dir / 'wellcome_full_raw_source.csv'
    raw.to_csv(raw_output, index=False)
    audit_report.append(f"\n1. RAW SOURCE LAYER")
    audit_report.append(f"   File: {raw_output}")
    audit_report.append(f"   Records: {len(raw):,}")
    audit_report.append(f"   Purpose: Complete unmodified source data")
    
    # Layer 2: All imported (includes zero-amount)
    all_imported_output = output_dir / 'wellcome_full_imported_all.csv'
    imported.to_csv(all_imported_output, index=False)
    audit_report.append(f"\n2. FULL IMPORTED LAYER (includes zero amounts)")
    audit_report.append(f"   File: {all_imported_output}")
    audit_report.append(f"   Records: {len(imported):,}")
    audit_report.append(f"   Purpose: All successfully parsed grants")
    
    # Layer 3: Analytically eligible (non-zero amounts)
    analytical = imported[imported['amount_gbp'] > 0].copy()
    analytical_output = output_dir / 'wellcome_full_analytical.csv'
    analytical.to_csv(analytical_output, index=False)
    audit_report.append(f"\n3. ANALYTICAL LAYER (amount > £0)")
    audit_report.append(f"   File: {analytical_output}")
    audit_report.append(f"   Records: {len(analytical):,}")
    audit_report.append(f"   Total: £{analytical['amount_gbp'].sum():,.2f}")
    audit_report.append(f"   Purpose: Awards with financial value for analysis")
    
    # Layer 4: Mental health candidates (unreviewed)
    mh_candidates_output = output_dir / 'wellcome_full_mh_candidates_unreviewed.csv'
    mh_candidates.to_csv(mh_candidates_output, index=False)
    audit_report.append(f"\n4. MENTAL HEALTH CANDIDATES (UNREVIEWED)")
    audit_report.append(f"   File: {mh_candidates_output}")
    audit_report.append(f"   Records: {len(mh_candidates):,}")
    audit_report.append(f"   Total: £{mh_candidates['amount_gbp'].sum():,.2f}")
    audit_report.append(f"   Purpose: Keyword matches requiring manual review")
    audit_report.append(f"   Status: UNREVIEWED - do not use as verified MH funding")
    
    # Exclusions ledger (complete)
    ledger_output = output_dir / 'wellcome_full_import_ledger.csv'
    exclusions.to_csv(ledger_output, index=False)
    audit_report.append(f"\n5. IMPORT LEDGER (complete status for all source rows)")
    audit_report.append(f"   File: {ledger_output}")
    audit_report.append(f"   Records: {len(exclusions):,}")
    audit_report.append(f"   Included: {(~exclusions['excluded']).sum():,}")
    audit_report.append(f"   Excluded: {exclusions['excluded'].sum():,}")
    audit_report.append(f"   Purpose: Complete row-by-row status tracking")
    
    # Exclusions-only (filtered)
    exclusions_only = exclusions[exclusions['excluded']].copy()
    exclusions_output = output_dir / 'wellcome_full_exclusions_only.csv'
    exclusions_only.to_csv(exclusions_output, index=False)
    audit_report.append(f"\n6. EXCLUSIONS ONLY (filtered view)")
    audit_report.append(f"   File: {exclusions_output}")
    audit_report.append(f"   Records: {len(exclusions_only):,}")
    audit_report.append(f"   Purpose: Records excluded from analytical layer")
    
    audit_report.append(f"\n### REPRODUCIBILITY ###")
    audit_report.append(f"Command to reproduce:")
    audit_report.append(f"  PYTHONPATH=./lib python import_full_wellcome.py")
    audit_report.append(f"\nDeterministic: Yes")
    audit_report.append(f"Network calls: None")
    audit_report.append(f"BehaviorGPT calls: None")
    audit_report.append(f"External data transmission: None")
    
    audit_report.append(f"\n### STREAMLIT DEPLOYMENT NOTES ###")
    audit_report.append(f"Recommended bundle: wellcome_full_analytical.csv")
    audit_report.append(f"File size: ~{analytical_output.stat().st_size / 1024 / 1024:.2f} MB")
    audit_report.append(f"Memory estimate: ~{len(analytical) * 1000 / 1024 / 1024:.0f} MB RAM")
    audit_report.append(f"Load time estimate: 1-3 seconds")
    audit_report.append(f"\nStreamlit Community Cloud limits:")
    audit_report.append(f"  - RAM: 1 GB")
    audit_report.append(f"  - Should be compatible with current dataset size")
    
    audit_report.append(f"\n" + "=" * 80)
    audit_report.append("IMPORT COMPLETE")
    audit_report.append("=" * 80)
    
    # Write audit report
    audit_file = output_dir / 'FULL_WELLCOME_IMPORT_AUDIT.md'
    audit_file.write_text('\n'.join(audit_report))
    
    print(f"\n{'=' * 80}")
    print("IMPORT COMPLETE")
    print('=' * 80)
    print(f"\nFiles created:")
    print(f"  - {raw_output}")
    print(f"  - {all_imported_output}")
    print(f"  - {analytical_output}")
    print(f"  - {mh_candidates_output}")
    print(f"  - {ledger_output}")
    print(f"  - {exclusions_output}")
    print(f"  - {audit_file}")
    print(f"\nAudit report: {audit_file}")
    print(f"\nSource: {len(raw):,} records")
    print(f"Imported: {len(imported):,} records")
    print(f"Analytical: {len(analytical):,} records (£{analytical['amount_gbp'].sum():,.2f})")
    print(f"MH candidates: {len(mh_candidates):,} records (UNREVIEWED)")
    
    return analytical, audit_file

if __name__ == '__main__':
    workbook_path = 'data/Wellcome-grants-awarded-1-October-2000-to-9-September-2026.xlsx'
    analytical, audit_file = generate_import_audit(workbook_path)
    print(f"\n✓ Import pipeline complete. Review audit report: {audit_file}")
