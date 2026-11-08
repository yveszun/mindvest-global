"""Reproducible keyword triage, NOT verified mental-health grant classification."""
import re
import pandas as pd
DIRECT = re.compile(r'\b(mental health|mental illness|mental disorder|psychiatr\w*|psychosis|schizophren\w*|bipolar disorder|depression|depressive disorder|anxiety disorder|suicid\w*|self.harm|psychological treatment|psychotherapy|perinatal depression|postpartum depression)\b', re.I)
ADJACENT = re.compile(r'\b(psychosocial|wellbeing|well.being|stress|trauma|addiction|substance use|neurodevelopment|autis\w*|dementia|sleep|cognitive|behavioral health|behavioural health)\b', re.I)
INTEGRATION = re.compile(r'\b(maternal|perinatal|pregnan\w*|primary care|community health|HIV|tuberculosis|school|adolescen\w*|refugee|humanitarian|workforce|climate|digital health)\b', re.I)

def triage(title, description):
    title = str(title) if pd.notna(title) else ''
    description = str(description) if pd.notna(description) else ''
    t = bool(DIRECT.search(title)); d = bool(DIRECT.search(description))
    a = bool(ADJACENT.search(title + ' ' + description))
    integrated = bool(INTEGRATION.search(title + ' ' + description))
    if t:
        return ('priority_direct_review', 'direct mental-health term in title')
    if d and integrated:
        return ('priority_integration_review', 'mental-health term and adjacent-sector term in description')
    if d:
        return ('priority_description_review', 'mental-health term in description only')
    if a:
        return ('adjacent_or_ambiguous_review', 'broad adjacent term; relevance unconfirmed')
    return ('no_rule_match', 'no specified terms matched')

def classify_awards(df):
    out = df.copy()
    vals = [triage(t,d) for t,d in zip(out.title, out.description)]
    out['triage_category'] = [v[0] for v in vals]
    out['triage_reason'] = [v[1] for v in vals]
    out['human_review_status'] = 'not_reviewed'
    return out
