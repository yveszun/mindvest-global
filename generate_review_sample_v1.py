"""
Generate Human Review Sample for Mental Health Classification v1

Creates a stratified sample of grants for human validation, including:
- Automated classifications from all categories
- Keyword-positive and keyword-negative grants
- Range of confidence scores and award amounts

Reproducible with fixed seed.

Version: 1.0
Date: November 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse

def generate_review_sample(
    classifications_path: str,
    output_path: str,
    sample_size: int = 250,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate stratified review sample for human validation.
    
    IMPORTANT: The stratified sample is NOT representative of population category prevalence.
    It deliberately oversamples rare categories (integrated, uncertain) and undersamples 
    common categories (not_mh) to ensure adequate evaluation across all categories.
    
    Sample metrics are UNWEIGHTED and cannot be extrapolated to population estimates without
    applying appropriate sampling weights.
    
    Args:
        classifications_path: Path to classified grants CSV
        output_path: Path to save review sample CSV
        sample_size: Total sample size (default: 250)
        seed: Random seed for reproducibility (default: 42)
    
    Returns:
        DataFrame with review sample and sampling metadata
    """
    print(f"Loading classifications from {classifications_path}...")
    df = pd.read_csv(classifications_path, parse_dates=['award_date'])
    
    np.random.seed(seed)
    
    # Define strata - fixed sample sizes
    categories = ['direct', 'integrated', 'adjacent', 'not_mh', 'uncertain']
    per_category = sample_size // (len(categories) + 1)  # +1 for keyword-negative stratum
    
    samples = []
    sampling_metadata = []
    
    print(f"\nGenerating stratified sample (total target: {sample_size}):")
    print(f"⚠️  STRATIFIED SAMPLE - NOT representative of population prevalence")
    print(f"    Each category sampled equally to ensure evaluation coverage")
    
    # Sample from each automated category
    for category in categories:
        category_df = df[df['mh_category_v1'] == category]
        population_size = len(category_df)
        
        if population_size == 0:
            print(f"  {category}: No grants available")
            continue
        
        # Stratify within category by confidence
        n_sample = min(per_category, population_size)
        
        # Calculate sampling probability
        sampling_prob = n_sample / population_size if population_size > 0 else 0.0
        
        # Ensure diversity: mix of high, medium, low confidence
        if population_size >= n_sample:
            # Sort by confidence and sample evenly
            category_sorted = category_df.sort_values('mh_confidence_v1')
            indices = np.linspace(0, len(category_sorted) - 1, n_sample, dtype=int)
            category_sample = category_sorted.iloc[indices]
        else:
            category_sample = category_df
        
        # Record sampling metadata
        sampling_metadata.append({
            'stratum': category,
            'population_size': population_size,
            'sample_size': len(category_sample),
            'sampling_probability': sampling_prob,
            'population_proportion': population_size / len(df)
        })
        
        samples.append(category_sample)
        print(f"  {category}: {len(category_sample)} sampled from {population_size:,} (p={sampling_prob:.4f})")
    
    # Add keyword-negative stratum (not in existing keyword candidates)
    # These are baseline controls
    keyword_negative = df[~df['grant_id'].isin(
        pd.read_csv('data/wellcome_full_mh_candidates_unreviewed.csv')['grant_id']
    )]
    
    # Sample from keyword-negative, preferring not_mh and uncertain
    if len(keyword_negative) > 0:
        n_keyword_neg = sample_size - sum(len(s) for s in samples)
        
        # Prefer not_mh and uncertain from keyword-negative
        keyword_neg_sample = keyword_negative[
            keyword_negative['mh_category_v1'].isin(['not_mh', 'uncertain'])
        ]
        
        if len(keyword_neg_sample) >= n_keyword_neg:
            keyword_neg_sample = keyword_neg_sample.sample(n=n_keyword_neg, random_state=seed)
        else:
            # Fill with any keyword-negative if not enough not_mh/uncertain
            remaining = n_keyword_neg - len(keyword_neg_sample)
            if remaining > 0:
                other_keyword_neg = keyword_negative[
                    ~keyword_negative['grant_id'].isin(keyword_neg_sample['grant_id'])
                ].sample(n=min(remaining, len(keyword_negative) - len(keyword_neg_sample)), random_state=seed)
                keyword_neg_sample = pd.concat([keyword_neg_sample, other_keyword_neg])
        
        sampling_prob_kn = len(keyword_neg_sample) / len(keyword_negative) if len(keyword_negative) > 0 else 0.0
        sampling_metadata.append({
            'stratum': 'keyword_negative',
            'population_size': len(keyword_negative),
            'sample_size': len(keyword_neg_sample),
            'sampling_probability': sampling_prob_kn,
            'population_proportion': len(keyword_negative) / len(df)
        })
        
        samples.append(keyword_neg_sample)
        print(f"  keyword_negative: {len(keyword_neg_sample)} sampled from {len(keyword_negative):,} (p={sampling_prob_kn:.4f})")
    
    # Combine all samples
    review_sample = pd.concat(samples, ignore_index=True)
    
    # Shuffle to avoid ordering bias
    review_sample = review_sample.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    # Save sampling metadata
    metadata_df = pd.DataFrame(sampling_metadata)
    metadata_path = output_path.replace('.csv', '_sampling_metadata.csv')
    metadata_df.to_csv(metadata_path, index=False)
    print(f"\n📊 Sampling metadata saved to: {metadata_path}")
    print("\nTo estimate population-level metrics, apply inverse probability weights:")
    print("  weight = population_proportion / (sample_size / total_sample_size)")
    
    # Prepare review CSV with necessary columns
    review_csv = review_sample[[
        'grant_id',
        'title',
        'description',
        'recipient',
        'amount_gbp',
        'award_date',
        'mh_category_v1',
        'mh_confidence_v1',
        'mh_evidence_v1'
    ]].copy()
    
    # Truncate long descriptions
    review_csv['description_truncated'] = review_csv['description'].apply(
        lambda x: x[:500] + '...' if pd.notna(x) and len(str(x)) > 500 else x
    )
    review_csv = review_csv.drop('description', axis=1).rename(
        columns={'description_truncated': 'description'}
    )
    
    # Rename columns for clarity
    review_csv = review_csv.rename(columns={
        'mh_category_v1': 'automated_category',
        'mh_confidence_v1': 'confidence_score',
        'mh_evidence_v1': 'matched_evidence'
    })
    
    # Add blank columns for human reviewers
    review_csv['human_category'] = ''
    review_csv['reviewer_confidence'] = ''
    review_csv['reviewer_notes'] = ''
    review_csv['reviewer_id'] = ''
    review_csv['review_date'] = ''
    
    # Reorder columns for reviewer-friendly layout
    column_order = [
        'grant_id',
        'title',
        'description',
        'recipient',
        'amount_gbp',
        'award_date',
        'automated_category',
        'confidence_score',
        'matched_evidence',
        'human_category',
        'reviewer_confidence',
        'reviewer_notes',
        'reviewer_id',
        'review_date'
    ]
    review_csv = review_csv[column_order]
    
    print(f"\n{'='*80}")
    print(f"Review sample generated: {len(review_csv)} grants")
    print(f"Random seed: {seed} (for reproducibility)")
    print(f"\nCategory distribution in sample:")
    print(review_csv['automated_category'].value_counts().sort_index())
    
    print(f"\nSaving to {output_path}...")
    review_csv.to_csv(output_path, index=False)
    
    print(f"\n{'='*80}")
    print("REVIEW SAMPLE READY")
    print('='*80)
    print(f"File: {output_path}")
    print(f"Total grants: {len(review_csv)}")
    print(f"\n⚠️  IMPORTANT: This is a STRATIFIED sample, NOT representative of population")
    print(f"    - Rare categories oversampled (integrated, uncertain)")
    print(f"    - Common categories undersampled (not_mh)")
    print(f"    - Sample metrics ≠ population metrics")
    print(f"    - Use sampling weights for population estimates")
    print("\nInstructions for reviewers:")
    print("1. Fill in 'human_category' column: direct, integrated, adjacent, not_mh, or uncertain")
    print("2. Fill in 'reviewer_confidence': high, medium, or low")
    print("3. Add notes in 'reviewer_notes' for borderline/uncertain cases")
    print("4. Enter your ID in 'reviewer_id' and date in 'review_date'")
    print("\nDo not fabricate reviews. Return completed CSV for evaluation.")
    print(f"\nSampling seed: {seed} (for reproducibility)")
    print(f"Sampling metadata: {metadata_path}")
    
    return review_csv

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate human review sample for mental health classification validation'
    )
    parser.add_argument(
        '--classifications',
        default='data/wellcome_mh_classifications_v1.csv',
        help='Input CSV with classifications'
    )
    parser.add_argument(
        '--output',
        default='data/wellcome_mh_review_sample_v1.csv',
        help='Output CSV for human review'
    )
    parser.add_argument(
        '--sample_size',
        type=int,
        default=250,
        help='Total sample size (default: 250)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    generate_review_sample(
        args.classifications,
        args.output,
        args.sample_size,
        args.seed
    )
