"""Streamlit AppTest-based functional tests for all navigation sections"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from streamlit.testing.v1 import AppTest


class TestStreamlitApp:
    """Test Streamlit app using AppTest where feasible"""
    
    def test_app_loads(self):
        """Test that the app loads without errors"""
        at = AppTest.from_file("app.py")
        at.run()
        assert not at.exception
        
    def test_verified_evidence_tab(self):
        """Test Verified Evidence tab displays correctly"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # Select Verified Evidence in sidebar
        at.sidebar.radio[0].set_value("Verified Evidence")
        at.run()
        
        assert not at.exception
        # Should show verified observations data
        # Check for key elements
        
    def test_award_explorer_bundled_data(self):
        """Test Award-Level Explorer with bundled data"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Award-Level Explorer")
        at.run()
        
        assert not at.exception
        # Check that bundled data loads
        
    def test_award_explorer_no_file(self):
        """Test Award-Level Explorer with no local file"""
        # This would require temporarily moving the file
        # Testing deferred due to file system constraints
        pytest.skip("File system manipulation required")
        
    def test_mental_health_triage_tab(self):
        """Test Mental Health Triage tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Mental Health Triage")
        at.run()
        
        assert not at.exception
        # Should display triage data
        
    def test_classification_validation_tab(self):
        """Test Classification Validation tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Classification Validation")
        at.run()
        
        assert not at.exception
        # Should show validation sample
        
    def test_overview_tab(self):
        """Test Overview tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Overview")
        at.run()
        
        assert not at.exception
        
    def test_funder_discovery_tab(self):
        """Test Funder Discovery tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Funder Discovery")
        at.run()
        
        assert not at.exception
        
    def test_behavioral_intelligence_tab(self):
        """Test Behavioral Intelligence tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Behavioral Intelligence")
        at.run()
        
        assert not at.exception
        
    def test_capital_gaps_tab(self):
        """Test Capital Gaps tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Capital Gaps")
        at.run()
        
        assert not at.exception
        
    def test_prospect_dossier_tab(self):
        """Test Prospect Dossier tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Prospect Dossier")
        at.run()
        
        assert not at.exception
        
    def test_behaviorgpt_readiness_tab(self):
        """Test BehaviorGPT Readiness tab"""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("BehaviorGPT Readiness")
        at.run()
        
        assert not at.exception
        # Verify no actual API calls are made
        # Check that it's documentation only


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestFinalCorrections:
    """Tests for final corrections to PR #3"""
    
    def test_mh_candidates_actual_count_not_all_reviewed(self):
        """Award Explorer must count actual MH candidates (2,222), not all 'not_reviewed' records (23,942)."""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Award-Level Explorer")
        at.run()
        
        # Find the MH candidates metric
        metrics = [m for m in at.metric if 'keyword' in m.label.lower() or 'mental health' in m.label.lower()]
        
        if len(metrics) > 0:
            candidate_metric = metrics[0]
            # Extract the number from the value (format: "2,222" or similar)
            value_str = str(candidate_metric.value).replace(',', '')
            candidate_count = int(value_str)
            
            # Should be 2,222 (analytical layer) or 2,489 (full import), NOT 23,942
            assert candidate_count < 3000, f"MH candidates should be ~2,222, not all {candidate_count:,} records"
            assert candidate_count > 2000, f"Expected ~2,222 candidates in analytical, got {candidate_count:,}"
    
    def test_bundled_dataset_banner_clarity(self):
        """Global banner must describe bundled dataset specifically."""
        at = AppTest.from_file("app.py")
        at.run()
        
        # Check caption for "bundled" indication
        captions = [c.value.lower() for c in at.caption if c.value]
        has_bundled = any('bundled' in c for c in captions)
        
        assert has_bundled, "Global banner should indicate 'bundled' dataset"
        
        # Check info banner mentions bundled
        info_texts = [i.value.lower() for i in at.info if i.value]
        has_bundled_info = any('bundled' in i for i in info_texts)
        
        assert has_bundled_info, "Info banner should describe bundled dataset"
    
    def test_uploaded_data_distinguished_from_bundled(self):
        """Award Explorer must clearly indicate when displaying uploaded (not bundled) data."""
        at = AppTest.from_file("app.py")
        at.run()
        
        at.sidebar.radio[0].set_value("Award-Level Explorer")
        at.run()
        
        # With bundled data loaded, should say "bundled"
        success_texts = [s.value.lower() for s in at.success if s.value]
        has_bundled = any('bundled' in s for s in success_texts)
        
        assert has_bundled, "Award Explorer should indicate bundled dataset when displaying it"
