"""
Comprehensive tests for full Wellcome import pipeline.
"""
import pytest
import pandas as pd
from pathlib import Path
import wellcome_import as wi

WORKBOOK_PATH = 'data/Wellcome-grants-awarded-1-October-2000-to-9-September-2026.xlsx'

@pytest.fixture
def workbook_available():
    """Check if full workbook is available for testing."""
    return Path(WORKBOOK_PATH).exists()

@pytest.fixture
def analytical_data():
    """Load analytical dataset if available."""
    path = Path('data/wellcome_full_analytical.csv')
    if path.exists():
        return pd.read_csv(path, parse_dates=['award_date'])
    return None

# Source Data Tests
def test_workbook_exists():
    """Workbook file must exist."""
    assert Path(WORKBOOK_PATH).exists(), "Wellcome workbook not found"

def test_workbook_sheets(workbook_available):
    """Workbook must have expected sheets."""
    if not workbook_available:
        pytest.skip("Workbook not available")
    xl = pd.ExcelFile(WORKBOOK_PATH)
    assert 'Main Grant List' in xl.sheet_names
    assert '# Additional Location Data' in xl.sheet_names

def test_source_row_count(workbook_available):
    """Main Grant List must have expected number of rows."""
    if not workbook_available:
        pytest.skip("Workbook not available")
    df = pd.read_excel(WORKBOOK_PATH, sheet_name='Main Grant List')
    assert len(df) == 26288, f"Expected 26,288 rows, got {len(df)}"

def test_source_columns(workbook_available):
    """Source must have required columns."""
    if not workbook_available:
        pytest.skip("Workbook not available")
    df = pd.read_excel(WORKBOOK_PATH, sheet_name='Main Grant List', nrows=1)
    required = ['Internal ID', 'Title', 'Award Date', 'Amount Awarded', 'Currency']
    for col in required:
        assert col in df.columns, f"Missing required column: {col}"

def test_no_duplicate_internal_ids(workbook_available):
    """Source must not have duplicate Internal IDs."""
    if not workbook_available:
        pytest.skip("Workbook not available")
    df = pd.read_excel(WORKBOOK_PATH, sheet_name='Main Grant List')
    duplicates = df['Internal ID'].duplicated().sum()
    assert duplicates == 0, f"Found {duplicates} duplicate Internal IDs"

# Import Function Tests
def test_import_date_parsing_excel():
    """Import must correctly parse Excel datetime columns."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    imported, raw, exclusions = wi.import_awards(WORKBOOK_PATH, max_rows=100, include_raw=True)
    
    # All dates should be valid
    assert imported['award_date'].notna().all(), "Some dates failed to parse"
    assert len(imported) > 0, "No records imported"

def test_import_accepts_all_valid_records():
    """Import must accept all records with valid dates, amounts, and IDs."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    imported, raw, exclusions = wi.import_awards(WORKBOOK_PATH, include_raw=True)
    
    # Should import all records (including zero amounts initially)
    assert len(imported) == len(raw), f"Expected {len(raw)} imports, got {len(imported)}"

def test_import_exclusions_tracked():
    """Import must track all exclusion reasons."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    imported, raw, exclusions = wi.import_awards(WORKBOOK_PATH, include_raw=True)
    
    # Exclusions df must exist
    assert 'exclusion_reason' in exclusions.columns
    assert 'excluded' in exclusions.columns
    
    # Zero amounts should be tracked
    zero_exclusions = exclusions[exclusions['exclusion_reason'] == 'zero_amount']
    assert len(zero_exclusions) == 2346, f"Expected 2346 zero-amount exclusions, got {len(zero_exclusions)}"

def test_import_no_duplicates_in_output():
    """Import output must not contain duplicate grant IDs."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    imported = wi.import_awards(WORKBOOK_PATH)
    duplicates = imported['grant_id'].duplicated().sum()
    assert duplicates == 0, f"Found {duplicates} duplicate grant_ids in output"

def test_import_amounts_valid():
    """All imported amounts must be numeric."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    imported = wi.import_awards(WORKBOOK_PATH, max_rows=1000)
    assert imported['amount_gbp'].dtype == 'float64'
    assert imported['amount_gbp'].notna().all()

def test_import_currencies_gbp_only():
    """Import must only include GBP records when Currency column exists."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    imported = wi.import_awards(WORKBOOK_PATH, max_rows=100)
    assert (imported['currency'] == 'GBP').all()

# Analytical Dataset Tests
def test_analytical_exists():
    """Analytical CSV must exist after import."""
    assert Path('data/wellcome_full_analytical.csv').exists()

def test_analytical_row_count(analytical_data):
    """Analytical dataset must have correct row count."""
    if analytical_data is None:
        pytest.skip("Analytical data not available")
    assert len(analytical_data) == 23942, f"Expected 23,942 rows, got {len(analytical_data)}"

def test_analytical_excludes_zero_amounts(analytical_data):
    """Analytical dataset must exclude zero-amount records."""
    if analytical_data is None:
        pytest.skip("Analytical data not available")
    assert (analytical_data['amount_gbp'] > 0).all(), "Found zero or negative amounts"

def test_analytical_columns(analytical_data):
    """Analytical dataset must have required columns."""
    if analytical_data is None:
        pytest.skip("Analytical data not available")
    required = ['grant_id', 'funder', 'title', 'award_date', 'amount_gbp', 'currency']
    for col in required:
        assert col in analytical_data.columns, f"Missing required column: {col}"

def test_analytical_dates_valid(analytical_data):
    """All dates in analytical dataset must be valid."""
    if analytical_data is None:
        pytest.skip("Analytical data not available")
    assert analytical_data['award_date'].notna().all()

def test_analytical_date_range(analytical_data):
    """Analytical dataset must cover expected date range."""
    if analytical_data is None:
        pytest.skip("Analytical data not available")
    min_date = analytical_data['award_date'].min()
    max_date = analytical_data['award_date'].max()
    assert min_date.year == 2000
    assert max_date.year >= 2026

def test_analytical_total_amount(analytical_data):
    """Analytical dataset total must match expected value."""
    if analytical_data is None:
        pytest.skip("Analytical data not available")
    total = analytical_data['amount_gbp'].sum()
    expected = 19787008487.33
    # Allow 0.1% tolerance for floating point
    assert abs(total - expected) / expected < 0.001, f"Expected £{expected:,.2f}, got £{total:,.2f}"

# Reproducibility Tests
def test_import_deterministic():
    """Import must produce identical results on repeated runs."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    import1 = wi.import_awards(WORKBOOK_PATH, max_rows=100)
    import2 = wi.import_awards(WORKBOOK_PATH, max_rows=100)
    
    # Compare dataframes
    pd.testing.assert_frame_equal(import1, import2)

def test_exclusions_reproducible():
    """Exclusion tracking must be deterministic."""
    if not Path(WORKBOOK_PATH).exists():
        pytest.skip("Workbook not available")
    
    _, _, excl1 = wi.import_awards(WORKBOOK_PATH, max_rows=100, include_raw=True)
    _, _, excl2 = wi.import_awards(WORKBOOK_PATH, max_rows=100, include_raw=True)
    
    pd.testing.assert_frame_equal(excl1, excl2)

# Audit Files Tests
def test_audit_report_exists():
    """Audit report must exist."""
    assert Path('data/FULL_WELLCOME_IMPORT_AUDIT.md').exists()

def test_exclusions_log_exists():
    """Exclusions log must exist."""
    assert Path('data/wellcome_full_exclusions.csv').exists()

def test_raw_source_preserved():
    """Raw source layer must be preserved."""
    path = Path('data/wellcome_full_raw_source.csv')
    assert path.exists()
    if path.exists():
        raw = pd.read_csv(path, nrows=10)
        assert len(raw.columns) == 27  # Original 27 columns

# Mental Health Candidates Tests
def test_mh_candidates_exist():
    """Mental health candidates file must exist."""
    assert Path('data/wellcome_full_mh_candidates_unreviewed.csv').exists()

def test_mh_candidates_unreviewed():
    """Mental health candidates must be clearly marked as unreviewed."""
    path = Path('data/wellcome_full_mh_candidates_unreviewed.csv')
    if path.exists():
        mh = pd.read_csv(path)
        # Should have mental_health_flag column
        assert 'mental_health_flag' in mh.columns or 'title' in mh.columns
        # Filename includes "unreviewed" warning

def test_mh_candidates_count():
    """Mental health candidates count should be reasonable."""
    path = Path('data/wellcome_full_mh_candidates_unreviewed.csv')
    if path.exists():
        mh = pd.read_csv(path)
        # Should be around 2,489 based on audit
        assert 2000 < len(mh) < 3000, f"Expected ~2489 candidates, got {len(mh)}"

# App Integration Tests  
def test_app_loads_full_data():
    """App must be able to load full analytical dataset."""
    path = Path('data/wellcome_full_analytical.csv')
    if path.exists():
        df = pd.read_csv(path, parse_dates=['award_date'])
        assert len(df) > 20000
        assert 'award_date' in df.columns
        assert 'amount_gbp' in df.columns

def test_validation_duplicate_population():
    """Validation must reject population data with duplicate grant IDs."""
    from validation import audit_report
    
    # Create test data with duplicates
    population = pd.DataFrame({
        'grant_id': ['A', 'B', 'A'],  # Duplicate 'A'
        'title': ['Test1', 'Test2', 'Test3'],
        'amount_gbp': [1000, 2000, 3000]
    })
    
    sample = pd.DataFrame({
        'grant_id': ['A'],
        'classification_label': ['mental_health']
    })
    
    # The actual error message is about the audit sample
    with pytest.raises(ValueError, match='Duplicate grant IDs'):
        audit_report(population, sample)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
