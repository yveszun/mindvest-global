# Mental Health Classification v1 - Methodology

**Version:** 1.0  
**Date:** November 2026  
**Repository:** yveszun/mindvest-global  
**Status:** Automated classification - requires human validation

## Overview

This document defines a transparent, reproducible classification system for identifying mental health-related Wellcome grants from the complete dataset of 26,288 grants (2000-2026).

**Critical limitations:**
- All classifications are **automated** and **unreviewed**
- Classifications are **not verified** mental health funding
- No funding totals should be calculated from unreviewed classifications
- Human validation is required before any financial or policy claims

## Classification Categories

### 1. Direct Mental Health

**Definition:** Research or programmes explicitly addressing mental health conditions, services, prevention, treatment, or psychosocial support.

**Inclusion criteria:**
- Explicitly mentions mental health, mental illness, or mental disorders in objectives
- Primary focus on psychiatric conditions (depression, anxiety, schizophrenia, bipolar, PTSD, etc.)
- Mental health service delivery, treatment, or prevention programmes
- Psychological interventions or psychotherapies
- Mental health systems strengthening
- Suicide prevention or self-harm intervention
- Perinatal/maternal mental health programmes

**Examples:**
- "Improving access to mental health services in rural Kenya"
- "Cognitive behavioral therapy for depression in primary care"
- "Mental health consequences of conflict-related trauma"

**Exclusions:**
- Neuroscience without demonstrated mental health application
- General wellbeing or quality of life without mental health focus
- Behavioral interventions without mental health relevance

### 2. Integrated Mental Health

**Definition:** Mental health components embedded within broader health, social, or humanitarian programmes.

**Inclusion criteria:**
- Multi-component programmes with explicit mental health elements
- HIV/AIDS programmes addressing mental health comorbidities
- Maternal/child health including perinatal mental health
- Primary care integration of mental health screening/services
- Humanitarian response including psychosocial support
- Non-communicable disease programmes addressing mental health
- Education programmes with mental health components

**Examples:**
- "Integrated HIV and mental health care in urban clinics"
- "Maternal and child health with depression screening"
- "Primary care package including mental health training"

**Boundary with Direct:**
- Direct: Mental health is the primary objective
- Integrated: Mental health is one component among several

**Boundary with Adjacent:**
- Integrated: Mental health component is explicit and substantiated
- Adjacent: Mental health relevance is implied or indirect

### 3. Adjacent/Enabling

**Definition:** Research potentially relevant to mental health but without sufficiently demonstrated direct or integrated mental health objectives.

**Inclusion criteria:**
- Neuroscience research (brain imaging, neural mechanisms, neuroplasticity)
- Behavioral science without mental health focus
- General wellbeing, resilience, or quality of life research
- Cognitive science without clinical mental health application
- Social determinants research without mental health outcome
- Child development without mental health component

**Examples:**
- "Neural mechanisms of reward processing"
- "Wellbeing interventions in workplace settings"
- "Behavioral economics and health decision-making"

**Exclusions from Direct/Integrated:**
- No explicit mention of mental health conditions
- No demonstrable mental health service component
- Wellbeing != mental health unless specific conditions addressed

**Important distinction:**
- Neuroscience ≠ mental health research
- Behavioral science ≠ mental health investment
- These may enable future mental health applications but cannot be counted as verified mental health funding

### 4. Not Mental Health

**Definition:** No substantiated mental health relevance.

**Inclusion criteria:**
- Physical health conditions without mental health component
- Basic science without mental health application
- Infrastructure, capacity building, or methods without mental health focus
- Public health programmes without mental health element
- Communicable diseases without mental health comorbidity addressed

**Examples:**
- "Malaria vaccine development"
- "Tuberculosis treatment optimization"
- "Genomic sequencing methods"

### 5. Uncertain

**Definition:** Insufficient information or conflicting evidence to assign category with confidence.

**Inclusion criteria:**
- Ambiguous titles with inadequate descriptions
- Could be direct or integrated but evidence unclear
- Overlapping characteristics of multiple categories
- Requires human expert adjudication

**Examples:**
- Title: "Community health intervention" (no description of mental health)
- Title: "Trauma response" (could be physical or psychological)

## Classification Rules

### Rule-Based Classifier Logic

**Priority order:** Rules applied in sequence; first match determines category.

#### Direct Mental Health Rules (Priority 1)

**Strong indicators (title OR description):**
- Mental health, mental illness, mental disorder(s)
- Psychiatric, psychiatry, psychological therapy, psychotherapy
- Depression, anxiety, schizophrenia, bipolar, psychosis, PTSD
- Suicide, self-harm, suicidal
- Mental health service(s), mental health system(s)

**Medium indicators (require 2+ matches OR title match):**
- Psychological wellbeing (when combined with condition)
- Counseling/counselling (with mental health context)
- Trauma (when psychological trauma specified)

#### Integrated Mental Health Rules (Priority 2)

**Indicators (title OR description):**
- "integrated" AND (mental health OR psychosocial OR psychological)
- (HIV OR AIDS OR tuberculosis) AND (mental health OR depression OR psychological)
- (maternal health OR perinatal OR postnatal) AND (depression OR mental health OR psychosocial)
- (primary care OR community health) AND (mental health screening OR psychological)
- humanitarian AND (psychosocial support OR mental health)

#### Adjacent/Enabling Rules (Priority 3)

**Neuroscience indicators:**
- Neuroscience, neuroimaging, brain imaging, fMRI, neuroplasticity
- Neural mechanisms, brain function, neural circuits
- (WITHOUT mental health/psychiatric/psychological in same context)

**Behavioral/wellbeing indicators:**
- Behavioral economics, behavioral science, behavior change
- Wellbeing, well-being, quality of life, resilience
- Cognitive function, cognitive science
- (WITHOUT mental health conditions specified)

#### Not Mental Health Rules (Priority 4)

**Strong indicators:**
- Physical disease focus without mental health comorbidity mentioned
- Laboratory/basic science without clinical mental health application
- Infrastructure/capacity building without mental health component

#### Uncertain Rules (Priority 5 - Default)

**Triggers:**
- Contradictory signals from multiple categories
- Insufficient title/description detail
- Edge cases requiring human judgment

## Confidence Scoring

Confidence levels assigned based on:

- **High (0.8-1.0):** Clear category indicators, unambiguous language, strong evidence
- **Medium (0.5-0.79):** Mixed signals, moderate evidence, some ambiguity
- **Low (<0.5):** Weak signals, high ambiguity, requires review

Confidence ≠ verification. Even high-confidence automated classifications require human validation.

## Evidence Recording

For each classification, record:
- **Matched rules:** Which rules triggered the classification
- **Matched terms:** Specific keywords/phrases found
- **Context:** Title vs description matches
- **Confidence score:** Numeric confidence (0-1)
- **Review status:** `automated` (default), `human_verified`, `human_rejected`
- **Classifier version:** `v1.0` for reproducibility

## Human Validation Protocol

### Stratified Review Sample

**IMPORTANT: The stratified sample is NOT representative of population category prevalence.**

The sampling strategy deliberately **oversamples rare categories** (integrated, uncertain) and **undersamples common categories** (not_mh) to ensure adequate evaluation coverage across all categories.

**Implications:**
- Sample category distribution ≠ population category distribution
- Unweighted sample metrics cannot be extrapolated to population estimates
- To estimate population-level performance, apply inverse probability weights
- Sampling metadata includes population sizes, sample sizes, and sampling probabilities for each stratum

Generate stratified sample of 200-300 grants:

**Strata:**
1. **Direct MH (automated):** ~40 grants
2. **Integrated MH (automated):** ~40 grants (oversampled - rare category)
3. **Adjacent/Enabling (automated):** ~40 grants
4. **Not MH (automated):** ~40 grants (undersampled - common category)
5. **Uncertain (automated):** ~40 grants (oversampled - requires review)
6. **Keyword-negative (baseline):** ~60 grants randomly sampled from non-candidates

**Sampling method:**
- Stratified sampling with fixed sample sizes per stratum
- Random sampling within each stratum
- Confidence-based diversity sampling (mix of high/medium/low confidence)
- Fixed seed (42) for reproducibility
- Sampling metadata saved with population sizes and probabilities

**Weighting for population estimates:**
```
weight[stratum] = (population_proportion[stratum]) / (sample_proportion[stratum])
```

Where:
- population_proportion = stratum_size / total_population
- sample_proportion = stratum_sample_size / total_sample_size

### Review CSV Format

**Columns:**
- `grant_id`: Unique grant identifier
- `title`: Grant title (full text)
- `description`: Grant description (truncated if >500 chars, with "...")
- `amount_gbp`: Award amount
- `award_date`: Award date
- `automated_category`: Classifier's proposed category
- `confidence_score`: Classifier confidence (0-1)
- `matched_evidence`: Keywords/rules that triggered classification
- `human_category`: *[BLANK - for reviewer to fill]*
- `reviewer_confidence`: *[BLANK - for reviewer: high/medium/low]*
- `reviewer_notes`: *[BLANK - for reviewer comments]*
- `reviewer_id`: *[BLANK - reviewer initials/ID]*
- `review_date`: *[BLANK - date of review]*

### Review Instructions for Humans

**Category assignment:**
- Assign one primary category: direct, integrated, adjacent, not_mh, uncertain
- Use `uncertain` only when genuinely unable to decide
- Document reasoning in reviewer_notes for uncertain cases
- Flag disagreements with automated classification

**Confidence:**
- High: Clear, unambiguous evidence
- Medium: Reasonable inference but some uncertainty
- Low: Weak evidence, needs more information

**Inter-rater reliability:**
- Subset of grants should be reviewed by 2+ reviewers
- Track agreement rates
- Adjudicate disagreements through discussion

### Evaluation Metrics

**Treatment of Uncertain Predictions:**
- Uncertain predictions are **abstentions**, not negative classifications
- **Abstention rate** = fraction of predictions classified as "uncertain"
- **Classification coverage** = 1 - abstention rate
- Performance metrics (precision, recall, F1) computed only on classified samples (excluding uncertain)
- Abstention rate and coverage reported separately

**When Human Labels Available:**

**Overall Performance:**
- Precision: True positives / (True positives + False positives)
- Recall: True positives / (True positives + False negatives)
- F1 Score: 2 × (Precision × Recall) / (Precision + Recall)
- Accuracy: Correct classifications / Total classifications

#### Binary Mental Health Relevance:**

**Abstention/Coverage Metrics:**
- Abstention rate: proportion of predictions = "uncertain"
- Classification coverage: 1 - abstention rate  
- Human labeled uncertain: count of human "uncertain" labels

**Performance on Classified Samples:**
(excluding uncertain predictions)
- Combine Direct + Integrated as "relevant"
- Adjacent + Not MH as "not relevant"
- Report precision, recall, F1 for relevance

**Multi-class Performance:**
- Confusion matrix: Automated vs Human categories
- Per-category precision, recall, F1
- Most frequent misclassifications

**Keyword Screening Baseline:**
- Compare classifier performance to keyword screening
- Does classifier improve on keyword-only approach?
- False positive and false negative rates by keyword status

### Without Human Labels

**Report only:**
- Classification distribution (counts per category)
- Confidence score distribution
- Keyword overlap analysis
- Sample records for manual inspection

**DO NOT REPORT:**
- Verified mental health funding totals
- Claims of accuracy or performance
- Population-level mental health investment estimates

## Safeguards and Limitations

### What This Classifier DOES NOT Do

❌ **Does not verify mental health funding amounts**
- Automated classifications are unreviewed
- Financial totals cannot be calculated without human validation

❌ **Does not equate neuroscience with mental health**
- Neuroscience is adjacent/enabling, not direct mental health
- Potential future mental health applications ≠ current mental health investment

❌ **Does not allocate full grant value to mental health**
- Integrated grants have multiple components
- Cannot assume 100% of integrated grant is mental health funding
- Component financial allocation requires manual review

❌ **Does not make verified claims without evidence**
- "Unreviewed" means unverified
- Automated ≠ validated
- High confidence ≠ human verification

### What This Classifier DOES Do

✅ **Provides transparent categorization**
- Rule-based logic, no black boxes
- Reproducible classifications
- Documented methodology

✅ **Enables systematic review**
- Prioritizes grants for human validation
- Stratified sampling for efficient review
- Tracks review progress and agreement

✅ **Improves on keyword-only screening**
- More nuanced categories than binary flag
- Context-aware rules
- Confidence scoring

## Reproducibility

### Classification Version Control

- **Version:** v1.0 (November 2026)
- **Rules file:** `mental_health_classifier_v1.py`
- **Population:** All 26,288 Wellcome grants (2000-2026)
- **Baseline:** Existing keyword candidates (2,489 grants)
- **Sample seed:** 42 (for validation sample reproducibility)

### Regenerating Classifications

```bash
PYTHONPATH=./lib python mental_health_classifier_v1.py \
    --input data/wellcome_full_imported_all.csv \
    --output data/wellcome_mh_classifications_v1.csv \
    --version v1.0
```

### Regenerating Review Sample

```bash
PYTHONPATH=./lib python generate_review_sample_v1.py \
    --classifications data/wellcome_mh_classifications_v1.csv \
    --output data/wellcome_mh_review_sample_v1.csv \
    --sample_size 250 \
    --seed 42
```

### Changelog

### v1.0.1 (November 2026 - Methodological Corrections)
- **Fixed:** Uncertain predictions now treated as abstentions, not negatives
- **Fixed:** Evaluation correctly reports abstention rate and classification coverage separately
- **Fixed:** Integrated MH pattern matching tightened (reduced false positives from generic "screening")
- **Fixed:** Direct MH signals take precedence over integrated classification
- **Added:** Streamlit validation upload with comprehensive validation (grant IDs, categories, duplicates)
- **Added:** Sampling metadata file documenting population sizes, sampling probabilities, stratum weights
- **Documented:** Stratified sample is NOT representative of population prevalence
- **Documented:** Sample metrics require weighting for population estimates

### v1.0 (November 2026)
- Initial rule-based classifier
- 5-category framework
- Stratified validation sampling
- Evaluation framework
- Streamlit integration

## References

- Source data: Wellcome Trust grants database (CC BY 4.0)
- Import audit: `data/FULL_WELLCOME_IMPORT_AUDIT.md`
- Baseline keyword screening: `import_full_wellcome.py`

---

**Important:** This is an automated classification system requiring human validation. Do not use for verified funding calculations or policy claims without expert review.
