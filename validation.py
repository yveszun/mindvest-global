"""Reproducible stratified human audit; no automatic ground-truth labels."""
import pandas as pd

CATEGORIES = ['priority_direct_review','priority_integration_review','priority_description_review','adjacent_or_ambiguous_review','no_rule_match']
LABELS = ['direct','integrated','not_mental_health','uncertain']

def draw_sample(df, per_stratum=30, seed=20261108):
    parts=[]
    for cat in CATEGORIES:
        group=df[df.triage_category.eq(cat)].sort_values('grant_id')
        if len(group):
            parts.append(group.sample(n=min(per_stratum,len(group)), random_state=seed).sort_values('grant_id'))
    sample=pd.concat(parts,ignore_index=True)
    fields=['grant_id','triage_category','triage_reason','title','description','recipient','award_date','amount_gbp','source_url']
    sample=sample[fields].copy()
    sample['reviewer_label']=''
    sample['reviewer_id']=''
    sample['review_notes']=''
    sample['second_reviewer_label']=''
    sample['adjudicated_label']=''
    return sample

def audit_report(sample, population):
    """Return stratum-wise rates and weighted estimated prevalence, only for completed adjudications."""
    if sample.grant_id.duplicated().any():
        raise ValueError('Duplicate grant IDs in audit sample')
    if population.grant_id.duplicated().any():
        raise ValueError('Duplicate grant IDs in population data')
    if 'adjudicated_label' not in sample:
        raise ValueError('Missing adjudicated_label')
    valid=sample[sample.adjudicated_label.isin(LABELS)].copy()
    pop=population.groupby('triage_category').size().to_dict()
    rows=[]
    for cat in CATEGORIES:
        s=sample[sample.triage_category.eq(cat)]
        v=valid[valid.triage_category.eq(cat)]
        n=int(pop.get(cat,0))
        if not n: continue
        pos=int(v.adjudicated_label.isin(['direct','integrated']).sum())
        known=int(v.adjudicated_label.ne('uncertain').sum())
        rows.append(dict(category=cat,population=n,sampled=len(s),adjudicated=len(v),known=known,positive=pos,positive_rate=(pos/known if known else None),estimated_positive=(n*pos/known if known else None)))
    result=pd.DataFrame(rows)
    complete=all((r['adjudicated']==r['sampled'] and r['known']==r['sampled']) for r in rows)
    estimate=float(result.estimated_positive.sum()) if complete else None
    return result,estimate,complete
