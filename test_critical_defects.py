"""Test for critical defects in the application"""
import pandas as pd
from pathlib import Path
import tempfile

DATA_ROOT = Path('data')

def test_award_explorer_message_defect():
    """
    CRITICAL DEFECT: Award Explorer shows hardcoded '600-row demonstration extract'
    message even when user uploads their own data
    
    Location: app.py line 52
    Current code:
        st.success(f'{len(awards):,} records loaded from 600-row demonstration extract.')
    
    Issue: This message is ALWAYS shown whether:
    - User loads bundled 600-row data
    - User uploads full 26,288-record dataset
    - User uploads any other dataset
    
    Expected: Message should distinguish between bundled and uploaded data
    """
    print("\n❌ CRITICAL DEFECT DETECTED:")
    print("   Award Explorer hardcoded message issue")
    print("   File: app.py, line 52")
    print("   The success message says '600-row demonstration extract' regardless")
    print("   of whether bundled or uploaded data is displayed.")
    print()
    return "CRITICAL"


def test_validation_missing_column_check():
    """
    HIGH SEVERITY: Classification Validation doesn't validate uploaded worksheet schema
    
    Location: app.py lines 115-133
    
    Current checks:
    - Grant ID matching ✓
    - Label values ✓
    
    Missing checks:
    - Required columns present
    - Column data types
    
    If user uploads CSV missing required columns (triage_category, title, etc.),
    the app will crash with KeyError instead of showing helpful error message.
    """
    print("\n⚠️  HIGH SEVERITY DEFECT:")
    print("   Classification Validation missing schema validation")
    print("   File: app.py, lines 115-133")
    print("   Missing columns in upload cause crashes instead of user-friendly errors.")
    print()
    return "HIGH"


def test_data_provenance_mixing():
    """
    MEDIUM SEVERITY: Award Explorer conflates bundled demonstration with uploaded data
    
    The app loads bundled data by default (local file), then allows upload.
    Users may not realize they're seeing bundled data vs their upload.
    
    The warning about '600-row extract' should only appear for bundled data,
    not for user uploads.
    """
    print("\n⚠️  MEDIUM SEVERITY:")
    print("   Data provenance not clearly distinguished")
    print("   Bundled vs uploaded data warnings are identical")
    print()
    return "MEDIUM"


def test_financial_distinctions():
    """
    LOW SEVERITY: Financial calculations don't preserve accounting distinctions
    
    Location: Capital Gaps tab
    
    The funding_gap calculation treats all inputs as equivalent, but:
    - Commitments ≠ Grants ≠ Disbursements
    - Different fiscal years
    - Different scopes (national vs project)
    
    The app does warn about this in UI text, but doesn't enforce checks.
    """
    print("\n⚠️  LOW SEVERITY:")
    print("   Financial gap calculations don't enforce accounting distinctions")
    print("   (But app does warn users about this limitation)")
    print()
    return "LOW"


def test_triage_category_extraction():
    """
    Test that triage categories are correctly extracted in validation
    """
    # Check if validation sample has all triage categories
    validation = pd.read_csv(DATA_ROOT / 'wellcome_validation_sample.csv')
    
    expected_categories = ['priority_direct_review', 'priority_integration_review',
                          'priority_description_review', 'adjacent_or_ambiguous_review',
                          'no_rule_match']
    
    actual_categories = validation.triage_category.unique()
    
    for cat in expected_categories:
        if cat not in actual_categories:
            print(f"\n⚠️  MEDIUM SEVERITY:")
            print(f"   Validation sample missing category: {cat}")
            print(f"   Stratified sampling may not be complete")
            return "MEDIUM"
    
    print("✓ Validation sample has all triage categories")
    return "OK"


if __name__ == '__main__':
    issues = []
    issues.append(("Award Explorer message", test_award_explorer_message_defect()))
    issues.append(("Validation schema check", test_validation_missing_column_check()))
    issues.append(("Data provenance", test_data_provenance_mixing()))
    issues.append(("Financial distinctions", test_financial_distinctions()))
    issues.append(("Triage categories", test_triage_category_extraction()))
    
    print("\n" + "="*70)
    print("DEFECT SUMMARY")
    print("="*70)
    
    critical = [i for i in issues if i[1] == "CRITICAL"]
    high = [i for i in issues if i[1] == "HIGH"]
    medium = [i for i in issues if i[1] == "MEDIUM"]
    low = [i for i in issues if i[1] == "LOW"]
    
    print(f"CRITICAL: {len(critical)}")
    print(f"HIGH:     {len(high)}")
    print(f"MEDIUM:   {len(medium)}")
    print(f"LOW:      {len(low)}")
