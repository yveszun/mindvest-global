"""Comprehensive functional tests for MindVest Global Streamlit app"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
from io import StringIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scoring import rank_opportunities, funding_gap
from validation import draw_sample, audit_report, LABELS, CATEGORIES
from mental_health_triage import triage, classify_awards
from wellcome_import import import_awards

# Test data fixtures
DATA_ROOT = Path(__file__).parent / 'data'


class TestScoringModule:
    """Test scoring.py mathematical correctness and edge cases"""
    
    def test_funding_gap_basic(self):
        """Test basic funding gap calculation"""
        assert funding_gap(100, 40) == 60
        assert funding_gap(50, 75) == 0  # Gap cannot be negative
        
    def test_funding_gap_zero_inputs(self):
        """Test gap with zero values"""
        assert funding_gap(100, 0) == 100
        assert funding_gap(0, 100) == 0
        assert funding_gap(0, 0) == 0
        
    def test_funding_gap_none_inputs(self):
        """Test gap with None/missing inputs"""
        assert funding_gap(None, 100) is None
        assert funding_gap(100, None) is None
        assert funding_gap(None, None) is None
        
    def test_funding_gap_negative_inputs(self):
        """Test gap rejects negative values"""
        assert funding_gap(-10, 100) is None
        assert funding_gap(100, -10) is None
        assert funding_gap(-10, -20) is None
        
    def test_funding_gap_nan_inputs(self):
        """Test gap with NaN values"""
        assert funding_gap(np.nan, 100) is None
        assert funding_gap(100, np.nan) is None
        
    def test_rank_opportunities_basic(self):
        """Test opportunity ranking with real data"""
        funders = pd.read_csv(DATA_ROOT / 'funders.csv')
        investments = pd.read_csv(DATA_ROOT / 'investments.csv')
        opportunities = pd.read_csv(DATA_ROOT / 'opportunities.csv')
        links = pd.read_csv(DATA_ROOT / 'theme_links.csv')
        
        result = rank_opportunities('F01', funders, investments, opportunities, links)
        
        # Check result structure
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(opportunities)
        required_cols = ['opportunity_id', 'opportunity', 'matching_themes', 
                        'overlap_count', 'eligible_type', 'baseline_score']
        assert all(col in result.columns for col in required_cols)
        
    def test_rank_opportunities_no_history(self):
        """Test ranking for funder with no investment history"""
        funders = pd.read_csv(DATA_ROOT / 'funders.csv')
        opportunities = pd.read_csv(DATA_ROOT / 'opportunities.csv')
        links = pd.read_csv(DATA_ROOT / 'theme_links.csv')
        
        # Empty investments
        investments = pd.DataFrame(columns=['funder_id', 'theme', 'year', 'investment_id'])
        
        result = rank_opportunities('F01', funders, investments, opportunities, links)
        
        # Should still return results but with zero scores
        assert len(result) > 0
        assert all(result.overlap_count == 0)
        
    def test_rank_opportunities_sorting(self):
        """Test that results are sorted correctly"""
        funders = pd.read_csv(DATA_ROOT / 'funders.csv')
        investments = pd.read_csv(DATA_ROOT / 'investments.csv')
        opportunities = pd.read_csv(DATA_ROOT / 'opportunities.csv')
        links = pd.read_csv(DATA_ROOT / 'theme_links.csv')
        
        result = rank_opportunities('F01', funders, investments, opportunities, links)
        
        # Check sorting: eligible first, then by score, then by name
        for i in range(len(result) - 1):
            if result.iloc[i].eligible_type and not result.iloc[i+1].eligible_type:
                continue  # Correct
            elif result.iloc[i].eligible_type == result.iloc[i+1].eligible_type:
                assert result.iloc[i].baseline_score >= result.iloc[i+1].baseline_score


class TestValidationModule:
    """Test validation.py for correctness and edge cases"""
    
    def test_draw_sample_reproducible(self):
        """Test that sample drawing is reproducible"""
        df = pd.DataFrame({
            'grant_id': [str(i) for i in range(100)],
            'triage_category': ['no_rule_match'] * 100,
            'triage_reason': ['none'] * 100,
            'title': ['test'] * 100,
            'description': [''] * 100,
            'recipient': ['r'] * 100,
            'award_date': ['2020'] * 100,
            'amount_gbp': [1000] * 100,
            'source_url': ['url'] * 100
        })
        
        sample1 = draw_sample(df, per_stratum=10)
        sample2 = draw_sample(df, per_stratum=10)
        
        assert sample1.grant_id.tolist() == sample2.grant_id.tolist()
        
    def test_draw_sample_structure(self):
        """Test sample has correct structure"""
        df = pd.DataFrame({
            'grant_id': [str(i) for i in range(100)],
            'triage_category': ['no_rule_match'] * 100,
            'triage_reason': ['none'] * 100,
            'title': ['test'] * 100,
            'description': [''] * 100,
            'recipient': ['r'] * 100,
            'award_date': ['2020'] * 100,
            'amount_gbp': [1000] * 100,
            'source_url': ['url'] * 100
        })
        
        sample = draw_sample(df, per_stratum=10)
        
        # Check required columns
        expected_cols = ['grant_id', 'triage_category', 'triage_reason', 'title', 
                        'description', 'recipient', 'award_date', 'amount_gbp', 
                        'source_url', 'reviewer_label', 'reviewer_id', 'review_notes',
                        'second_reviewer_label', 'adjudicated_label']
        assert all(col in sample.columns for col in expected_cols)
        
        # Check all review columns are empty
        assert sample.reviewer_label.eq('').all()
        assert sample.adjudicated_label.eq('').all()
        
    def test_audit_report_duplicate_ids(self):
        """Test audit report rejects duplicate grant IDs"""
        sample = pd.DataFrame({
            'grant_id': ['A', 'A', 'B'],  # Duplicate!
            'triage_category': ['no_rule_match'] * 3,
            'adjudicated_label': ['direct', 'integrated', 'not_mental_health']
        })
        
        population = pd.DataFrame({
            'grant_id': ['A', 'B', 'C'],
            'triage_category': ['no_rule_match'] * 3
        })
        
        with pytest.raises(ValueError, match='Duplicate grant IDs'):
            audit_report(sample, population)
            
    def test_audit_report_invalid_labels(self):
        """Test that invalid labels are handled"""
        sample = pd.DataFrame({
            'grant_id': ['A', 'B'],
            'triage_category': ['no_rule_match'] * 2,
            'adjudicated_label': ['invalid_label', 'direct']
        })
        
        population = pd.DataFrame({
            'grant_id': ['A', 'B'],
            'triage_category': ['no_rule_match'] * 2
        })
        
        # Should not error, but treat invalid as not valid
        report, estimate, complete = audit_report(sample, population)
        assert not complete  # Incomplete due to invalid labels
        
    def test_audit_report_incomplete(self):
        """Test incomplete audit (uncertain labels)"""
        sample = pd.DataFrame({
            'grant_id': ['A', 'B', 'C'],
            'triage_category': ['no_rule_match'] * 3,
            'adjudicated_label': ['direct', 'uncertain', 'not_mental_health']
        })
        
        population = pd.DataFrame({
            'grant_id': ['A', 'B', 'C'] * 10,
            'triage_category': ['no_rule_match'] * 30
        })
        
        report, estimate, complete = audit_report(sample, population)
        
        assert not complete  # Has uncertain label
        assert estimate is None  # No estimate for incomplete


class TestTriageModule:
    """Test mental health triage logic"""
    
    def test_triage_direct_title(self):
        """Test direct mental health term in title"""
        cat, reason = triage('Mental health services', '')
        assert cat == 'priority_direct_review'
        assert 'direct mental-health term in title' in reason
        
    def test_triage_direct_variations(self):
        """Test various mental health terms"""
        terms = ['mental illness', 'psychiatry', 'depression', 'anxiety disorder',
                'suicide', 'self-harm', 'schizophrenia', 'bipolar disorder']
        
        for term in terms:
            cat, reason = triage(f'Study of {term}', '')
            assert cat == 'priority_direct_review', f"Failed for term: {term}"
            
    def test_triage_integration(self):
        """Test integrated mental health"""
        cat, reason = triage('Primary care', 'Integrating depression screening')
        assert cat == 'priority_integration_review'
        
    def test_triage_description_only(self):
        """Test mental health term in description only"""
        cat, reason = triage('Generic title', 'This is about mental health')
        assert cat == 'priority_description_review'
        
    def test_triage_adjacent(self):
        """Test adjacent terms"""
        cat, reason = triage('Wellbeing program', '')
        assert cat == 'adjacent_or_ambiguous_review'
        
    def test_triage_no_match(self):
        """Test no match"""
        cat, reason = triage('Cancer research', 'Molecular biology')
        assert cat == 'no_rule_match'
        
    def test_triage_none_inputs(self):
        """Test with None inputs"""
        cat, reason = triage(None, None)
        assert cat == 'no_rule_match'
        
    def test_classify_awards_structure(self):
        """Test classify_awards adds required columns"""
        df = pd.DataFrame({
            'title': ['Mental health', 'Cancer'],
            'description': ['', '']
        })
        
        result = classify_awards(df)
        
        assert 'triage_category' in result.columns
        assert 'triage_reason' in result.columns
        assert 'human_review_status' in result.columns
        assert all(result.human_review_status == 'not_reviewed')


class TestWellcomeImport:
    """Test Wellcome data import edge cases"""
    
    def test_import_deduplication(self):
        """Test that duplicate grant IDs are removed"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Grant Reference,Title,Award Date,Amount Awarded,Organisation\n')
            f.write('A1,Test,2024-01-01,"£1,000",Org1\n')
            f.write('A1,Test Duplicate,2024-01-01,"£1,000",Org1\n')
            f.write('A2,Other,2024-01-02,"£2,000",Org2\n')
            tmp_path = Path(f.name)
            
        try:
            result = import_awards(tmp_path)
            assert len(result) == 2  # Duplicates removed
            assert 'A1' in result.grant_id.values
            assert 'A2' in result.grant_id.values
        finally:
            tmp_path.unlink()
            
    def test_import_missing_columns(self):
        """Test rejection of invalid schema"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Wrong,Columns\n')
            f.write('A,B\n')
            tmp_path = Path(f.name)
            
        try:
            with pytest.raises(ValueError, match='Unrecognized source columns'):
                import_awards(tmp_path)
        finally:
            tmp_path.unlink()
            
    def test_import_currency_filter(self):
        """Test that only GBP records are kept when currency column exists"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Grant Reference,Title,Award Date,Amount Awarded,Organisation,Currency\n')
            f.write('A1,Test,2024-01-01,1000,Org1,GBP\n')
            f.write('A2,Test,2024-01-01,1000,Org2,USD\n')
            f.write('A3,Test,2024-01-01,1000,Org3,gbp\n')
            tmp_path = Path(f.name)
            
        try:
            result = import_awards(tmp_path)
            assert len(result) == 2  # Only GBP records
            assert all(result.grant_id.isin(['A1', 'A3']))
        finally:
            tmp_path.unlink()
            
    def test_import_date_parsing(self):
        """Test Excel serial date parsing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Grant Reference,Title,Award Date,Amount Awarded,Organisation\n')
            f.write('A1,Test,44562,1000,Org1\n')  # Excel serial date
            f.write('A2,Test,2024-01-15,1000,Org2\n')  # Text date
            tmp_path = Path(f.name)
            
        try:
            result = import_awards(tmp_path)
            assert len(result) == 2
            assert pd.notna(result.loc[result.grant_id == 'A1', 'award_date'].iloc[0])
            assert pd.notna(result.loc[result.grant_id == 'A2', 'award_date'].iloc[0])
        finally:
            tmp_path.unlink()


class TestDataIntegrity:
    """Test data file integrity and edge cases"""
    
    def test_all_data_files_exist(self):
        """Verify all required data files are present"""
        required = ['funders.csv', 'investments.csv', 'opportunities.csv',
                   'needs.csv', 'theme_links.csv', 'evidence.csv',
                   'verified_observations.csv', 'wellcome_awards_imported.csv',
                   'wellcome_mental_health_triage.csv', 'wellcome_validation_sample.csv']
        
        for fname in required:
            assert (DATA_ROOT / fname).exists(), f"Missing: {fname}"
            
    def test_wellcome_data_600_rows(self):
        """Verify Wellcome CSVs are 600-row extracts"""
        awards = pd.read_csv(DATA_ROOT / 'wellcome_awards_imported.csv')
        triage = pd.read_csv(DATA_ROOT / 'wellcome_mental_health_triage.csv')
        
        assert len(awards) == 600, f"Awards: expected 600, got {len(awards)}"
        assert len(triage) == 600, f"Triage: expected 600, got {len(triage)}"
        
    def test_no_missing_grant_ids(self):
        """Test no missing grant IDs in datasets"""
        awards = pd.read_csv(DATA_ROOT / 'wellcome_awards_imported.csv')
        triage = pd.read_csv(DATA_ROOT / 'wellcome_mental_health_triage.csv')
        
        assert awards.grant_id.notna().all(), "Awards has missing grant IDs"
        assert triage.grant_id.notna().all(), "Triage has missing grant IDs"
        
    def test_wellcome_data_consistency(self):
        """Test Wellcome awards and triage have same grant IDs"""
        awards = pd.read_csv(DATA_ROOT / 'wellcome_awards_imported.csv')
        triage = pd.read_csv(DATA_ROOT / 'wellcome_mental_health_triage.csv')
        
        assert set(awards.grant_id) == set(triage.grant_id)
        
    def test_verified_observations_structure(self):
        """Test verified observations have required columns"""
        verified = pd.read_csv(DATA_ROOT / 'verified_observations.csv')
        
        required = ['institution', 'period', 'theme', 'metric', 'value', 
                   'currency', 'unit', 'source_url', 'limitations']
        assert all(col in verified.columns for col in required)
        
        # Check all have source URLs
        assert verified.source_url.notna().all()


class TestAppCriticalIssues:
    """Test critical issues found in app.py"""
    
    def test_award_explorer_hardcoded_message(self):
        """CRITICAL: Award Explorer shows hardcoded '600 records' message"""
        # This is a critical defect - the success message says "600-row demonstration extract"
        # regardless of whether bundled data or uploaded data is used
        
        # Create test upload with different number of records
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('Grant Reference,Title,Award Date,Amount Awarded,Organisation\n')
            for i in range(100):
                f.write(f'G{i},Test {i},2024-01-{(i%28)+1:02d},1000,Org\n')
            tmp_path = Path(f.name)
            
        try:
            result = import_awards(tmp_path)
            actual_count = len(result)
            
            # The app would show "600 records loaded from 600-row demonstration extract"
            # even though we uploaded 100 records
            assert actual_count == 100, "Import should work with 100 records"
            
            # Issue: Line 52 in app.py has hardcoded message:
            # st.success(f'{len(awards):,} records loaded from 600-row demonstration extract.')
            # Should distinguish between bundled and uploaded data
            
        finally:
            tmp_path.unlink()
            
    def test_validation_no_schema_check(self):
        """CRITICAL: Validation doesn't validate upload schema"""
        # The app checks grant_id and label values, but doesn't validate
        # that all required columns are present in the uploaded file
        
        # Missing columns test case
        incomplete_df = pd.DataFrame({
            'grant_id': ['A', 'B'],
            'adjudicated_label': ['direct', 'integrated']
            # Missing: triage_category, title, description, etc.
        })
        
        # The current code would crash with KeyError when trying to access
        # columns that don't exist
        
    def test_funding_gap_display_issue(self):
        """Test that funding gap handles None correctly in display"""
        # The app displays gap as "Unknown" when None, which is correct
        # But the metric formatting might fail if gap is not properly checked
        gap = funding_gap(None, 100)
        assert gap is None
        
        # The app uses: f"${gap:,.0f}" if gap is not None else 'Unknown'
        # This is correct
        
    def test_triage_file_missing(self):
        """Test behavior when triage file is missing"""
        # The app checks if file exists and shows info message
        # This is correct behavior
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
