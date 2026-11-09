"""
Evaluation Module for Mental Health Classification v1

Computes precision, recall, F1, confusion matrices when human labels are available.
Does not fabricate results or make claims without validation data.

Version: 1.0
Date: November 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path
import argparse

def load_validated_sample(review_sample_path: str) -> Tuple[Optional[pd.DataFrame], bool]:
    """
    Load review sample and check if human validation is complete.
    
    Returns:
        (DataFrame, has_validation) where has_validation indicates if human labels exist
    """
    df = pd.read_csv(review_sample_path)
    
    # Check if human_category column is filled
    has_validation = df['human_category'].notna().any() and (df['human_category'] != '').any()
    
    if has_validation:
        # Filter to only validated records
        validated = df[df['human_category'].notna() & (df['human_category'] != '')]
        return validated, True
    
    return df, False

def compute_binary_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
    """
    Compute binary classification metrics (mental health relevant vs not).
    
    Relevant = direct + integrated
    Not relevant = adjacent + not_mh
    Uncertain predictions are reported separately as abstentions.
    
    NOTE: Uncertain predictions are NOT treated as negative classifications.
    Abstention rate and classification coverage are reported separately.
    """
    # Map categories to binary
    relevant_categories = {'direct', 'integrated'}
    not_relevant_categories = {'adjacent', 'not_mh'}
    
    # Total sample size
    n_total = len(y_true)
    
    # Count uncertain predictions (abstentions)
    n_pred_uncertain = (y_pred == 'uncertain').sum()
    abstention_rate = n_pred_uncertain / n_total if n_total > 0 else 0.0
    classification_coverage = 1 - abstention_rate
    
    # Filter: only evaluate where human labeled as relevant or not_relevant
    # AND prediction was not uncertain
    mask_human = y_true.isin(relevant_categories | not_relevant_categories)
    mask_pred = y_pred.isin(relevant_categories | not_relevant_categories)
    mask = mask_human & mask_pred
    
    y_true_filtered = y_true[mask]
    y_pred_filtered = y_pred[mask]
    
    if len(y_true_filtered) == 0:
        return {
            'error': 'No relevant/not_relevant labels for binary metrics',
            'abstention_rate': abstention_rate,
            'classification_coverage': classification_coverage,
            'n_total': int(n_total),
            'n_predicted_uncertain': int(n_pred_uncertain)
        }
    
    # Convert to binary
    y_true_binary = y_true_filtered.isin(relevant_categories).astype(int)
    y_pred_binary = y_pred_filtered.isin(relevant_categories).astype(int)
    
    # Compute metrics
    tp = ((y_true_binary == 1) & (y_pred_binary == 1)).sum()
    fp = ((y_true_binary == 0) & (y_pred_binary == 1)).sum()
    fn = ((y_true_binary == 1) & (y_pred_binary == 0)).sum()
    tn = ((y_true_binary == 0) & (y_pred_binary == 0)).sum()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'accuracy': accuracy,
        'true_positives': int(tp),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'true_negatives': int(tn),
        'n_samples': len(y_true_filtered),
        'abstention_rate': abstention_rate,
        'classification_coverage': classification_coverage,
        'n_total': int(n_total),
        'n_predicted_uncertain': int(n_pred_uncertain),
        'n_human_uncertain': int((y_true == 'uncertain').sum())
    }

def compute_multiclass_metrics(y_true: pd.Series, y_pred: pd.Series) -> Dict[str, any]:
    """Compute per-category precision, recall, F1."""
    categories = sorted(set(y_true) | set(y_pred))
    
    category_metrics = {}
    for category in categories:
        tp = ((y_true == category) & (y_pred == category)).sum()
        fp = ((y_true != category) & (y_pred == category)).sum()
        fn = ((y_true == category) & (y_pred != category)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        support = (y_true == category).sum()
        
        category_metrics[category] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'support': int(support)
        }
    
    # Overall accuracy
    accuracy = (y_true == y_pred).mean()
    
    return {
        'by_category': category_metrics,
        'overall_accuracy': accuracy,
        'n_samples': len(y_true)
    }

def confusion_matrix(y_true: pd.Series, y_pred: pd.Series) -> pd.DataFrame:
    """Generate confusion matrix as DataFrame."""
    categories = sorted(set(y_true) | set(y_pred))
    
    matrix = pd.DataFrame(
        index=categories,
        columns=categories,
        data=0
    )
    
    for true_cat in categories:
        for pred_cat in categories:
            count = ((y_true == true_cat) & (y_pred == pred_cat)).sum()
            matrix.loc[true_cat, pred_cat] = count
    
    return matrix

def evaluate_classification(review_sample_path: str, output_path: str = None) -> Dict:
    """
    Evaluate classification performance against human labels.
    
    Args:
        review_sample_path: Path to review sample CSV with human labels
        output_path: Optional path to save evaluation report
    
    Returns:
        Dictionary with evaluation results or None if no validation available
    """
    validated, has_validation = load_validated_sample(review_sample_path)
    
    if not has_validation:
        print("=" * 80)
        print("NO HUMAN VALIDATION AVAILABLE")
        print("=" * 80)
        print(f"File: {review_sample_path}")
        print("\nThe review sample has been generated but not yet completed.")
        print("Human reviewers must fill in 'human_category' column before evaluation.")
        print("\nCannot compute evaluation metrics without validated labels.")
        print("Do not fabricate results or make performance claims.")
        return None
    
    print("=" * 80)
    print("CLASSIFICATION EVALUATION - WITH HUMAN VALIDATION")
    print("=" * 80)
    print(f"Validated samples: {len(validated)}")
    
    y_true = validated['human_category']
    y_pred = validated['automated_category']
    
    # Binary metrics (relevant vs not relevant)
    print("\n### BINARY CLASSIFICATION (Mental Health Relevant vs Not) ###")
    binary_metrics = compute_binary_metrics(y_true, y_pred)
    
    # Report abstention/coverage first
    print(f"  Total samples:       {binary_metrics['n_total']}")
    print(f"  Predicted uncertain: {binary_metrics['n_predicted_uncertain']}")
    print(f"  Abstention rate:     {binary_metrics['abstention_rate']:.3f}")
    print(f"  Classification coverage: {binary_metrics['classification_coverage']:.3f}")
    print(f"  Human labeled uncertain: {binary_metrics.get('n_human_uncertain', 0)}")
    
    if 'error' in binary_metrics:
        print(f"\n  {binary_metrics['error']}")
    else:
        print(f"\n  Performance on classified samples:")
        print(f"  Precision: {binary_metrics['precision']:.3f}")
        print(f"  Recall:    {binary_metrics['recall']:.3f}")
        print(f"  F1 Score:  {binary_metrics['f1_score']:.3f}")
        print(f"  Accuracy:  {binary_metrics['accuracy']:.3f}")
        print(f"\n  True Positives:  {binary_metrics['true_positives']}")
        print(f"  False Positives: {binary_metrics['false_positives']}")
        print(f"  False Negatives: {binary_metrics['false_negatives']}")
        print(f"  True Negatives:  {binary_metrics['true_negatives']}")
        print(f"  Evaluated samples: {binary_metrics['n_samples']}")
    
    # Multi-class metrics
    print("\n### MULTI-CLASS CLASSIFICATION (By Category) ###")
    multiclass_metrics = compute_multiclass_metrics(y_true, y_pred)
    
    print(f"  Overall Accuracy: {multiclass_metrics['overall_accuracy']:.3f}")
    print("\n  Per-Category Performance:")
    for category, metrics in sorted(multiclass_metrics['by_category'].items()):
        print(f"\n  {category}:")
        print(f"    Precision: {metrics['precision']:.3f}")
        print(f"    Recall:    {metrics['recall']:.3f}")
        print(f"    F1 Score:  {metrics['f1_score']:.3f}")
        print(f"    Support:   {metrics['support']}")
    
    # Confusion matrix
    print("\n### CONFUSION MATRIX ###")
    conf_matrix = confusion_matrix(y_true, y_pred)
    print("\nRows: Human labels | Columns: Automated predictions")
    print(conf_matrix)
    
    # Collect all results
    results = {
        'n_validated': len(validated),
        'binary_metrics': binary_metrics,
        'multiclass_metrics': multiclass_metrics,
        'confusion_matrix': conf_matrix.to_dict()
    }
    
    if output_path:
        import json
        with open(output_path, 'w') as f:
            # Convert confusion matrix to serializable format
            results_serializable = results.copy()
            results_serializable['confusion_matrix'] = conf_matrix.to_dict()
            json.dump(results_serializable, f, indent=2, default=str)
        print(f"\nEvaluation results saved to {output_path}")
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print("Based on actual human validation. These are real performance metrics.")
    
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Evaluate mental health classification against human labels'
    )
    parser.add_argument(
        '--review_sample',
        default='data/wellcome_mh_review_sample_v1.csv',
        help='Path to review sample CSV with human labels'
    )
    parser.add_argument(
        '--output',
        default='data/wellcome_mh_evaluation_v1.json',
        help='Path to save evaluation results JSON'
    )
    
    args = parser.parse_args()
    
    evaluate_classification(args.review_sample, args.output)
