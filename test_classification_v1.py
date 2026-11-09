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
        """Direct MH: Strong mental health indicators in standalone research"""
        # Explicit mental health in title
        cat, conf, ev = classify_grant("Mental health services in Kenya", "Program to improve mental health care")
        assert cat == "direct"
        assert conf > 0.8
        
        # Depression research (standalone)
        cat, conf, ev = classify_grant("Depression treatment in primary care", "Study of depression interventions")
        assert cat == "direct"
        
        # Suicide prevention (standalone)
        cat, conf, ev = classify_grant("Suicide prevention programme", "Community-based suicide prevention")
        assert cat == "direct"
    
    def test_integrated_hiv_mental_health(self):
        """Integrated MH: Mental health integrated into HIV services"""
        # HIV programme with depression component in description
        cat, conf, ev = classify_grant(
            "HIV treatment and care programme in urban South Africa",
            "Comprehensive HIV care including antiretroviral therapy, depression screening, and psychological support services for people living with HIV"
        )
        assert cat == "integrated", f"Expected integrated, got {cat}: {ev}"
        
        # HIV with mental health comorbidity
        cat, conf, ev = classify_grant(
            "Addressing HIV and mental health comorbidities",
            "Study of depression and anxiety among HIV-positive patients"
        )
        # Could be direct or integrated depending on title interpretation
        assert cat in ["direct", "integrated"], f"Got {cat}: {ev}"
    
    def test_integrated_maternal_psychosocial(self):
        """Integrated MH: Maternal health with embedded psychosocial support"""
        # Maternal health programme with depression screening
        cat, conf, ev = classify_grant(
            "Maternal health services strengthening in rural Malawi",
            "Programme to improve antenatal and postnatal care including screening for postnatal depression and psychosocial support"
        )
        assert cat == "integrated", f"Expected integrated, got {cat}: {ev}"
        
        # Perinatal health outcomes with mental health component
        cat, conf, ev = classify_grant(
            "Improving perinatal health outcomes through integrated care",
            "Study includes nutrition, family planning, and screening for perinatal depression and anxiety"
        )
        assert cat in ["direct", "integrated"], f"Got {cat}: {ev}"
    
    def test_integrated_primary_care(self):
        """Integrated MH: Primary care integration of mental health"""
        # Primary care programme with mental health integration
        cat, conf, ev = classify_grant(
            "Strengthening primary care services in rural India",
            "Training primary care workers in mental health screening, diabetes management, and hypertension control"
        )
        assert cat in ["direct", "integrated"], f"Got {cat}: {ev}"
    
    def test_direct_vs_integrated_title_focus(self):
        """Direct MH when title explicitly states mental health focus"""
        # Title says "mental health services" - this is direct even if HIV mentioned
        cat, conf, ev = classify_grant(
            "Mental health services for people living with HIV",
            "Programme focused on depression and anxiety treatment for HIV patients"
        )
        assert cat == "direct", f"Expected direct (title focus), got {cat}: {ev}"
        
        # Standalone depression research
        cat, conf, ev = classify_grant(
            "Depression treatment in primary care settings",
            "Randomized trial of cognitive behavioral therapy"
        )
        assert cat == "direct", f"Expected direct, got {cat}: {ev}"
    
    def test_adjacent_neuroscience_without_mh(self):
        """Adjacent: Neuroscience without explicit mental health objectives"""
        # Pure neuroscience
        cat, conf, ev = classify_grant(
            "Neural mechanisms of reward processing",
            "fMRI study of dopaminergic pathways in reward learning"
        )
        assert cat == "adjacent", f"Expected adjacent, got {cat}: {ev}"
        
        # Brain imaging without MH
        cat, conf, ev = classify_grant(
            "Neuroplasticity in learning and memory",
            "Structural brain changes during skill acquisition"
        )
        assert cat == "adjacent", f"Expected adjacent, got {cat}: {ev}"
    
    def test_not_mental_health_physical_disease(self):
        """Not MH: Physical health without mental health component"""
        # Malaria
        cat, conf, ev = classify_grant("Malaria vaccine development", "Testing new malaria vaccine candidates")
        assert cat == "not_mh", f"Expected not_mh, got {cat}: {ev}"
        
        # Tuberculosis
        cat, conf, ev = classify_grant("Tuberculosis treatment optimization", "Drug regimens for TB patients")
        assert cat == "not_mh", f"Expected not_mh, got {cat}: {ev}"
        
        # Cardiovascular without MH
        cat, conf, ev = classify_grant("Cardiovascular disease prevention", "Study of hypertension management")
        assert cat == "not_mh", f"Expected not_mh, got {cat}: {ev}"
    
    def test_uncertain_incidental_mention(self):
        """Uncertain: Broader programme mentioning mental health incidentally"""
        # Very brief mention without substance
        cat, conf, ev = classify_grant(
            "Community health worker training programme",
            "Training includes nutrition, sanitation, child health, mental wellbeing"
        )
        # Could be uncertain, not_mh, or adjacent - allow all
        assert cat in ["uncertain", "not_mh", "adjacent", "integrated"], f"Got {cat}: {ev}"
        
        # Ambiguous context
        cat, conf, ev = classify_grant(
            "Trauma care in conflict settings",
            "Emergency trauma response"
        )
        assert cat in ["uncertain", "not_mh"], f"Expected uncertain/not_mh for ambiguous trauma, got {cat}: {ev}"
    
    def test_uncertain_insufficient_info(self):
        """Uncertain: Ambiguous or insufficient information"""
        # Very short
        cat, conf, ev = classify_grant("Community health", "")
        assert cat == "uncertain" or cat == "not_mh", f"Got {cat}: {ev}"
        
        # Short ambiguous
        cat, conf, ev = classify_grant("Wellbeing study", "Quality of life research")
        assert cat in ["uncertain", "adjacent"], f"Got {cat}: {ev}"

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
        """Binary metrics with classification errors and abstentions"""
        y_true = pd.Series(['direct', 'not_mh', 'integrated', 'not_mh', 'uncertain'])
        y_pred = pd.Series(['not_mh', 'not_mh', 'integrated', 'adjacent', 'uncertain'])
        
        metrics = compute_binary_metrics(y_true, y_pred)
        
        # With uncertain: n_total=5, n_pred_uncertain=1, abstention_rate=0.2
        assert metrics['n_total'] == 5
        assert metrics['n_predicted_uncertain'] == 1
        assert metrics['abstention_rate'] == 0.2
        assert metrics['classification_coverage'] == 0.8
        
        # After filtering out uncertain predictions:
        # y_true: [direct, not_mh, integrated, not_mh]
        # y_pred: [not_mh, not_mh, integrated, adjacent]
        # Relevant: direct, integrated -> binary: [1, 0, 1, 0]
        # Not relevant: adjacent, not_mh -> binary: [0, 0, 1, 0]
        # TP=1 (position 2), FP=0, FN=1 (position 0), TN=2 (positions 1,3)
        
        assert metrics['true_positives'] == 1
        assert metrics['false_positives'] == 0
        assert metrics['false_negatives'] == 1
        assert metrics['true_negatives'] == 2
        assert metrics['precision'] == 1.0  # TP/(TP+FP) = 1/1
        assert metrics['recall'] == 0.5      # TP/(TP+FN) = 1/2
        assert metrics['n_samples'] == 4     # 4 classified (excluding uncertain prediction)
    
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
        
        # Check version is v1.x
        assert (classifications['classifier_version'].str.startswith('v1.')).all()
    
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
    
    def test_sampling_metadata_exists(self):
        """Sampling metadata file should be generated"""
        assert Path('data/wellcome_mh_review_sample_v1_sampling_metadata.csv').exists()
    
    def test_sampling_metadata_content(self):
        """Sampling metadata should have correct structure"""
        metadata = pd.read_csv('data/wellcome_mh_review_sample_v1_sampling_metadata.csv')
        
        required_cols = ['stratum', 'population_size', 'sample_size', 'sampling_probability', 'population_proportion']
        for col in required_cols:
            assert col in metadata.columns, f"Missing column: {col}"
        
        # Should have all strata
        expected_strata = {'direct', 'integrated', 'adjacent', 'not_mh', 'uncertain', 'keyword_negative'}
        actual_strata = set(metadata['stratum'].unique())
        assert expected_strata == actual_strata
        
        # Sampling probabilities should be between 0 and 1
        assert (metadata['sampling_probability'] >= 0).all()
        assert (metadata['sampling_probability'] <= 1).all()
        
        # Population proportions should sum to approximately 1
        # (keyword_negative overlaps with categories, so won't sum exactly to 1)
        # Just check they're reasonable
        assert (metadata['population_proportion'] > 0).all()
        assert (metadata['population_proportion'] < 1).all()

class TestSafeguards:
    """Test safeguards against misuse"""
    
    def test_review_sample_uniqueness(self):
        """Review sample should contain unique grant IDs"""
        review_sample = pd.read_csv('data/wellcome_mh_review_sample_v1.csv')
        
        # No duplicate grant IDs
        assert review_sample['grant_id'].duplicated().sum() == 0, "Found duplicate grant IDs in review sample"
        
        # All grant IDs should be valid (exist in source)
        classifications = pd.read_csv('data/wellcome_mh_classifications_v1.csv')
        valid_ids = set(classifications['grant_id'])
        sample_ids = set(review_sample['grant_id'])
        assert sample_ids.issubset(valid_ids), "Some sample grant IDs not in source data"
    
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
        # Check for v1.1 after refactoring
        assert (classifications['classifier_version'].str.startswith('v1.')).all()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
