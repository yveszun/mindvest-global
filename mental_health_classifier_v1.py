"""
Mental Health Classification v1 - Rule-Based Classifier

Transparent, reproducible classification of Wellcome grants into mental health categories.
All classifications are automated and require human validation.

Categories:
- direct: Direct mental health research/programmes
- integrated: Mental health embedded in broader programmes  
- adjacent: Neuroscience, behavioral science, wellbeing (potentially relevant)
- not_mh: No substantiated mental health relevance
- uncertain: Insufficient information for confident classification

Version: 1.0
Date: November 2026
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Classification rules version
CLASSIFIER_VERSION = "v1.0"

#===============================================================================
# RULE DEFINITIONS
#===============================================================================

DIRECT_MH_STRONG = [
    # Explicit mental health terms
    r'\bmental\s+health\b',
    r'\bmental\s+illness\b',
    r'\bmental\s+disorder[s]?\b',
    r'\bpsychiatric\b',
    r'\bpsychiatry\b',
    r'\bpsychological\s+therapy\b',
    r'\bpsychotherapy\b',
    
    # Specific conditions
    r'\bdepression\b',
    r'\banxiety\b',
    r'\bschizophrenia\b',
    r'\bbipolar\b',
    r'\bpsychosis\b',
    r'\bptsd\b',
    r'\bpost[-\s]?traumatic\s+stress\b',
    
    # Suicide/self-harm
    r'\bsuicide\b',
    r'\bsuicidal\b',
    r'\bself[-\s]?harm\b',
    
    # Systems/services
    r'\bmental\s+health\s+service[s]?\b',
    r'\bmental\s+health\s+system[s]?\b',
    r'\bmental\s+health\s+care\b',
]

DIRECT_MH_MEDIUM = [
    # Weaker signals requiring context
    r'\bpsychological\s+wellbeing\b',
    r'\bcounseling\b',
    r'\bcounselling\b',
    r'\bpsychological\s+trauma\b',
    r'\bemotional\s+wellbeing\b',
]

INTEGRATED_MH_PATTERNS = [
    # Integration keywords - require explicit mental health terms
    (r'\bintegrated\b', r'\b(mental\s+health|psychosocial|psychological\s+(support|services?))\b'),
    
    # HIV/AIDS + mental health (must have explicit MH component)
    (r'\b(hiv|aids)\b', r'\b(mental\s+health|depression|psychological\s+(distress|support|wellbeing))\b'),
    
    # Maternal/perinatal + mental health (must specify depression or MH)
    (r'\b(maternal|perinatal|postnatal|postpartum|antenatal)\b', r'\b(depression|mental\s+health|psychosocial\s+support)\b'),
    
    # Primary care + mental health (must be mental health in context, not just "screening")
    (r'\b(primary\s+care|community\s+health\s+program)', r'\b(mental\s+health\s+(screening|integration|services)|psychological\s+services)\b'),
    
    # Humanitarian + psychosocial
    (r'\bhumanitarian\b', r'\b(psychosocial\s+support|mental\s+health\s+(services|support))\b'),
    
    # NCD + mental health (explicit comorbidity)
    (r'\bnon[-\s]?communicable\s+disease[s]?\b', r'\b(mental\s+health|depression|psychological)\b'),
]

ADJACENT_NEUROSCIENCE = [
    r'\bneuroscience\b',
    r'\bneuroimaging\b',
    r'\bbrain\s+imaging\b',
    r'\bfmri\b',
    r'\bneuroplasticity\b',
    r'\bneural\s+mechanisms\b',
    r'\bbrain\s+function\b',
    r'\bneural\s+circuits\b',
    r'\bneurological\b',  # Note: neurological ≠ psychiatric
]

ADJACENT_BEHAVIORAL = [
    r'\bbehavioral\s+economics\b',
    r'\bbehavioral\s+science\b',
    r'\bbehaviour\s+change\b',
    r'\bwellbeing\b',
    r'\bwell[-\s]?being\b',
    r'\bquality\s+of\s+life\b',
    r'\bresilience\b',
    r'\bcognitive\s+function\b',
    r'\bcognitive\s+science\b',
]

NOT_MH_STRONG = [
    # Physical diseases without mental health
    r'\b(malaria|tuberculosis|tb)\b.*(?!.*(mental|psychological|depression))',
    r'\b(cancer|cardiovascular|diabetes)\b.*(?!.*(mental|psychological|depression))',
    
    # Basic science without mental health
    r'\bgenomics?\b.*(?!.*(mental|psychiatric|psychological))',
    r'\bvaccine\b.*(?!.*(mental|psychological))',
]

#===============================================================================
# CLASSIFICATION FUNCTIONS
#===============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for pattern matching."""
    if pd.isna(text):
        return ""
    return str(text).lower().strip()

def find_matches(text: str, patterns: List[str]) -> List[str]:
    """Find all pattern matches in text."""
    matches = []
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    return matches

def check_pattern_pair(text: str, pattern1: str, pattern2: str) -> bool:
    """Check if both patterns exist in text."""
    return bool(re.search(pattern1, text, re.IGNORECASE) and 
                re.search(pattern2, text, re.IGNORECASE))

def classify_grant(title: str, description: str) -> Tuple[str, float, str]:
    """
    Classify a single grant into mental health category.
    
    Returns:
        category: direct, integrated, adjacent, not_mh, uncertain
        confidence: 0-1 confidence score
        evidence: Comma-separated matched patterns/terms
    """
    title_norm = normalize_text(title)
    desc_norm = normalize_text(description)
    combined = f"{title_norm} {desc_norm}"
    
    # Track all matches for evidence
    all_matches = []
    
    # Priority 1: Direct Mental Health
    direct_strong_matches = find_matches(combined, DIRECT_MH_STRONG)
    direct_medium_matches = find_matches(combined, DIRECT_MH_MEDIUM)
    
    if direct_strong_matches:
        # Strong match in title or description
        title_matches = find_matches(title_norm, DIRECT_MH_STRONG)
        if title_matches:
            confidence = 0.95  # High confidence for title match
        else:
            confidence = 0.85  # High confidence for description match
        
        evidence = "; ".join(direct_strong_matches[:3])  # Top 3 matches
        return "direct", confidence, f"Direct MH: {evidence}"
    
    elif len(direct_medium_matches) >= 2:
        # Multiple medium signals
        confidence = 0.75
        evidence = "; ".join(direct_medium_matches[:2])
        return "direct", confidence, f"Direct MH: {evidence}"
    
    # Priority 2: Integrated Mental Health
    # Integrated requires: broader programme indicator AND mental health component
    # BUT not if already has strong direct MH signals
    for pattern1, pattern2 in INTEGRATED_MH_PATTERNS:
        if check_pattern_pair(combined, pattern1, pattern2):
            # Don't classify as integrated if title has strong direct MH terms
            title_has_direct_mh = find_matches(title_norm, DIRECT_MH_STRONG)
            if title_has_direct_mh:
                # This is direct MH, not integrated
                confidence = 0.90
                evidence = "; ".join(title_has_direct_mh[:2])
                return "direct", confidence, f"Direct MH (title): {evidence}"
            
            # True integrated: MH component within broader program
            confidence = 0.80 if check_pattern_pair(title_norm, pattern1, pattern2) else 0.70
            evidence = f"Broader program + MH component"
            return "integrated", confidence, f"Integrated MH: {evidence}"
    
    # Check if has medium mental health signal but not strong enough for direct
    if direct_medium_matches and len(direct_medium_matches) == 1:
        # Single weak signal - could be integrated or uncertain
        confidence = 0.60
        evidence = direct_medium_matches[0]
        return "uncertain", confidence, f"Weak MH signal: {evidence}"
    
    # Priority 3: Adjacent/Enabling
    neuro_matches = find_matches(combined, ADJACENT_NEUROSCIENCE)
    behavioral_matches = find_matches(combined, ADJACENT_BEHAVIORAL)
    
    # Ensure no mental health context with neuroscience/behavioral
    has_mh_context = find_matches(combined, DIRECT_MH_STRONG + DIRECT_MH_MEDIUM)
    
    if (neuro_matches or behavioral_matches) and not has_mh_context:
        confidence = 0.75 if (neuro_matches and behavioral_matches) else 0.70
        evidence = "; ".join((neuro_matches + behavioral_matches)[:2])
        return "adjacent", confidence, f"Adjacent: {evidence}"
    
    # Priority 4: Not Mental Health
    # If reached here and has strong non-MH indicators
    not_mh_matches = find_matches(combined, NOT_MH_STRONG)
    if not_mh_matches:
        confidence = 0.80
        evidence = not_mh_matches[0]
        return "not_mh", confidence, f"Not MH: {evidence}"
    
    # Priority 5: Uncertain/Not Mental Health Default
    # If no strong signals for any category, likely not mental health
    # but classify as uncertain for short titles/descriptions
    text_length = len(title_norm) + len(desc_norm)
    
    if text_length < 50:  # Very short text
        return "uncertain", 0.40, "Insufficient detail"
    elif text_length < 150:  # Short text
        return "not_mh", 0.65, "No MH indicators, limited text"
    else:  # Adequate text, no MH signals
        return "not_mh", 0.75, "No MH indicators"

def classify_population(input_path: str, output_path: str = None, version: str = CLASSIFIER_VERSION) -> pd.DataFrame:
    """
    Classify all grants in the population.
    
    Args:
        input_path: Path to input CSV with grants
        output_path: Optional path to save classifications
        version: Classifier version for tracking
    
    Returns:
        DataFrame with classifications added
    """
    print(f"Loading grants from {input_path}...")
    df = pd.read_csv(input_path)
    
    print(f"Classifying {len(df):,} grants...")
    
    results = []
    for idx, row in df.iterrows():
        category, confidence, evidence = classify_grant(row['title'], row['description'])
        results.append({
            'category': category,
            'confidence': confidence,
            'evidence': evidence,
        })
        
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1:,} grants...")
    
    # Add classification results to dataframe
    result_df = pd.DataFrame(results)
    df['mh_category_v1'] = result_df['category']
    df['mh_confidence_v1'] = result_df['confidence']
    df['mh_evidence_v1'] = result_df['evidence']
    df['classifier_version'] = version
    df['review_status'] = 'automated'  # All start as automated
    
    # Add comparison with existing keyword screening
    if 'mental_health_flag' in df.columns:
        df['keyword_candidate'] = df['mental_health_flag'].isin(['keyword_candidate_unreviewed', 'not_reviewed'])
    
    print(f"\nClassification summary:")
    print(df['mh_category_v1'].value_counts().sort_index())
    
    print(f"\nConfidence distribution:")
    print(df['mh_confidence_v1'].describe())
    
    if output_path:
        print(f"\nSaving to {output_path}...")
        df.to_csv(output_path, index=False)
    
    return df

#===============================================================================
# CLI
#===============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Mental Health Classification v1 - Rule-based classifier for Wellcome grants'
    )
    parser.add_argument(
        '--input',
        default='data/wellcome_full_imported_all.csv',
        help='Input CSV with grants (default: data/wellcome_full_imported_all.csv)'
    )
    parser.add_argument(
        '--output',
        default='data/wellcome_mh_classifications_v1.csv',
        help='Output CSV with classifications (default: data/wellcome_mh_classifications_v1.csv)'
    )
    parser.add_argument(
        '--version',
        default=CLASSIFIER_VERSION,
        help=f'Classifier version (default: {CLASSIFIER_VERSION})'
    )
    
    args = parser.parse_args()
    
    # Run classification
    classified_df = classify_population(args.input, args.output, args.version)
    
    print(f"\n{'='*80}")
    print("CLASSIFICATION COMPLETE")
    print('='*80)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Version: {args.version}")
    print(f"Total grants: {len(classified_df):,}")
    print("\nREMINDER: All classifications are automated and unreviewed.")
    print("Human validation required before any funding calculations or claims.")
