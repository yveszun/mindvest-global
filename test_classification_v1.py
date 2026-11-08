"""
Tests for Mental Health Classification v1

Tests classification logic, evaluation metrics, and integration.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, './lib')

from mental_health_classifier_v1 import classify_grant, classify_population
from evaluate_classification_v1 import compute_binary_metrics, compute_multiclass_metrics, confusion_matrix

class TestClassificationLogic:
    """Test classification rules and logic"""
    
    def test_direct_mental_health_strong_signals(self):
        """Direct MH: Strong mental health indicators"""
        # Explicit mental health
        cat, conf, ev = classify_grant("Mental health services in Kenya", "Program to improve mental health care")
        assert cat == "direct"
        assert conf > 0.8
        
        # Depression
        cat, conf, ev = classify_grant("Depression treatment in primary care", "Study of depression interventions")
        assert cat == "direct"
        
        # Suicide prevention
        cat, conf, ev = classify_grant("Suicide prevention programme", "Community-based suicide prevention")
        assert cat == "direct"
    
    def test_integrated_mental_health(self):
        """Integrated MH: Mental health within broader programs"""
        # HIV + depression (without "mental health" in title)
        cat, conf, ev = classify_grant("HIV treatment programme", "HIV care including depression screening and psychological support")
        # This might be direct if strong MH terms are present, or integrated
        assert cat in ["direct", "integrated"]
        
        # Maternal + depression (integrated approach)
        cat, conf, ev = classify_grant("Maternal health services", "Antenatal care with postnatal depression screening")
        assert cat in ["direct", "integrated"]
    
    def test_adjacent_neuroscience(self):
        """Adjacent: Neuroscience without mental health"""
        cat, conf, ev = classify_grant("Neural mechanisms of reward processing", "fMRI study of brain function")
        assert cat == "adjacent"
        
        cat, conf, ev = classify_grant("Neuroplasticity in learning", "Brain imaging of cognitive function")
        assert cat == "adjacent"
    
    def test_adjacent_behavioral_wellbeing(self):
        """Adjacent: Behavioral science and wellbeing without MH"""
        cat, conf, ev = classify_grant("Behavioral economics and health decisions", "Nudge interventions for healthy choices")
        assert cat == "adjacent"
        
        cat, conf, ev = classify_grant("Workplace wellbeing programme", "Quality of life interventions")
        assert cat == "adjacent"
    
    def test_not_mental_health(self):
        """Not MH: Physical health without mental health component"""
        cat, conf, ev = classify_grant("Malaria vaccine development", "Testing new malaria vaccine candidates")
        assert cat == "not_mh"
        
        cat, conf, ev = classify_grant("Tuberculosis treatment optimization", "Drug regimens for TB patients")
        assert cat == "not_mh"
    
    def test_uncertain_insufficient_info(self):
        """Uncertain: Ambiguous or insufficient information"""
        cat, conf, ev = classify_grant("Community health", "")
        assert cat == "uncertain" or cat == "not_mh"
        
        # Very short text
        cat, conf, ev = classify_grant("Trauma", "Study")
        assert conf < 0.7  # Low confidence

class TestEvaluationMetrics:
    """Test evaluation metrics calculation"""
    
    def test_binary_metrics_perfect(self):
        """Binary metrics with perfect classifier"""
        y_true = pd.Series(['direct', 'integrated', 'adjacent', 'not_mh'])
        y_pred = pd.Series(['direct', 'integrated', 'adjacent', 'not_mh'])
        
        metrics = compute_binary_metrics(y_true, y_pred)
        
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1_score'] == 1.0
        assert metrics['accuracy'] == 1.0
    
    def test_binary_metrics_with_errors(self):
        """Binary metrics with classification errors"""
        y_true = pd.Series(['direct', 'not_mh', 'integrated', 'not_mh'])
        y_pred = pd.Series(['not_mh', 'not_mh', 'integrated', 'adjacent'])
        
        metrics = compute_binary_metrics(y_true, y_pred)
        
        # Relevant: direct, integrated
        # Not relevant: adjacent, not_mh
        # y_true relevant: [1, 0, 1, 0]
        # y_pred relevant: [0, 0, 1, 0]
        # TP=1, FP=0, FN=1, TN=2
        
        assert metrics['true_positives'] == 1
        assert metrics['false_positives'] == 0
        assert metrics['false_negatives'] == 1
        assert metrics['true_negatives'] == 2
        assert metrics['precision'] == 1.0  # TP/(TP+FP) = 1/1
        assert metrics['recall'] == 0.5      # TP/(TP+FN) = 1/2
    
    def test_multiclass_metrics(self):
        """Multi-class metrics across categories"""
        y_true = pd.Series(['direct', 'integrated', 'adjacent', 'not_mh', 'uncertain'])
        y_pred = pd.Series(['direct', 'integrated', 'adjacent', 'adjacent', 'uncertain'])
        
        metrics = compute_multiclass_metrics(y_true, y_pred)
        
        assert 'by_category' in metrics
        assert 'overall_accuracy' in metrics
        assert metrics['overall_accuracy'] == 0.8  # 4 correct out of 5
    
    def test_confusion_matrix(self):
        """Confusion matrix generation"""
        y_true = pd.Series(['direct', 'direct', 'adjacent'])
        y_pred = pd.Series(['direct', 'integrated', 'adjacent'])
        
        conf_mat = confusion_matrix(y_true, y_pred)
        
        assert conf_mat.loc['direct', 'direct'] == 1
        assert conf_mat.loc['direct', 'integrated'] == 1
        assert conf_mat.loc['adjacent', 'adjacent'] == 1

class TestDataIntegrity:
    """Test data integrity and file generation"""
    
    def test_classifications_file_exists(self):
        """Classifications file should be generated"""
        assert Path('data/wellcome_mh_classifications_v1.csv').exists()
    
    def test_classifications_completeness(self):
        """All grants should be classified"""
        classifications = pd.read_csv('data/wellcome_mh_classifications_v1.csv')
        
        # Should have all source grants
        assert len(classifications) == 26288
        
        # Should have classification columns
        assert 'mh_category_v1' in classifications.columns
        assert 'mh_confidence_v1' in classifications.columns
        assert 'mh_evidence_v1' in classifications.columns
        assert 'classifier_version' in classifications.columns
        assert 'review_status' in classifications.columns
        
        # All should be classified
        assert classifications['mh_category_v1'].notna().all()
        assert classifications['mh_confidence_v1'].notna().all()
        
        # All should start as automated
        assert (classifications['review_status'] == 'automated').all()
    
    def test_classifications_categories_valid(self):
        """Only valid categories should be used"""
        classifications = pd.read_csv('data/wellcome_mh_classifications_v1.csv')
        
        valid_categories = {'direct', 'integrated', 'adjacent', 'not_mh', 'uncertain'}
        actual_categories = set(classifications['mh_category_v1'].unique())
        
        assert actual_categories.issubset(valid_categories)
    
    def test_classifications_confidence_range(self):
        """Confidence scores should be in valid range"""
        classifications = pd.read_csv('data/wellcome_mh_classifications_v1.csv')
        
        assert (classifications['mh_confidence_v1'] >= 0).all()
        assert (classifications['mh_confidence_v1'] <= 1).all()
    
    def test_review_sample_file_exists(self):
        """Review sample should be generated"""
        assert Path('data/wellcome_mh_review_sample_v1.csv').exists()
    
    def test_review_sample_structure(self):
        """Review sample should have correct structure"""
        review_sample = pd.read_csv('data/wellcome_mh_review_sample_v1.csv')
        
        required_cols = [
            'grant_id', 'title', 'automated_category', 'confidence_score',
            'matched_evidence', 'human_category', 'reviewer_confidence',
            'reviewer_notes', 'reviewer_id', 'review_date'
        ]
        
        for col in required_cols:
            assert col in review_sample.columns, f"Missing column: {col}"
        
        # Human columns should be blank initially
        assert review_sample['human_category'].isna().all() or (review_sample['human_category'] == '').all()
    
    def test_review_sample_size(self):
        """Review sample should be appropriate size"""
        review_sample = pd.read_csv('data/wellcome_mh_review_sample_v1.csv')
        
        # Should be 200-300 grants
        assert 200 <= len(review_sample) <= 300

class TestSafeguards:
    """Test safeguards against misuse"""
    
    def test_no_verified_claims_without_validation(self):
        """Evaluation should refuse to run without human labels"""
        from evaluate_classification_v1 import load_validated_sample
        
        # With unreviewed sample, should return no validation
        validated, has_validation = load_validated_sample('data/wellcome_mh_review_sample_v1.csv')
        assert has_validation is False
    
    def test_review_status_is_automated(self):
        """All classifications should be marked as automated"""
        classifications = pd.read_csv('data/wellcome_mh_classifications_v1.csv')
        assert (classifications['review_status'] == 'automated').all()
    
    def test_neuroscience_not_direct_mh(self):
        """Neuroscience without MH context should be adjacent, not direct"""
        cat, conf, ev = classify_grant("Neural circuits in visual cortex", "fMRI study of vision processing")
        assert cat == "adjacent", "Pure neuroscience should be adjacent, not direct MH"
        
        cat, conf, ev = classify_grant("Neuroplasticity mechanisms", "Brain adaptation study")
        assert cat == "adjacent"
    
    def test_wellbeing_not_direct_mh(self):
        """Wellbeing without specific MH conditions should be adjacent"""
        cat, conf, ev = classify_grant("Workplace wellbeing", "Employee wellbeing interventions")
        assert cat == "adjacent"
        
        cat, conf, ev = classify_grant("Quality of life in aging", "Wellbeing measures in elderly")
        assert cat == "adjacent"

class TestReproducibility:
    """Test reproducibility of classification and sampling"""
    
    def test_classification_deterministic(self):
        """Same input should produce same classification"""
        title = "Mental health services in Kenya"
        desc = "Program to improve mental health care access"
        
        cat1, conf1, ev1 = classify_grant(title, desc)
        cat2, conf2, ev2 = classify_grant(title, desc)
        
        assert cat1 == cat2
        assert conf1 == conf2
        assert ev1 == ev2
    
    def test_classifier_version_tracked(self):
        """Classifier version should be recorded"""
        classifications = pd.read_csv('data/wellcome_mh_classifications_v1.csv')
        assert 'classifier_version' in classifications.columns
        assert (classifications['classifier_version'] == 'v1.0').all()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
