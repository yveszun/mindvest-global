"""Transparent baseline. Not BehaviorGPT output."""
import pandas as pd

def rank_opportunities(funder_id, funders, investments, opportunities, links):
    funder = funders.set_index('funder_id').loc[funder_id]
    history = investments[investments.funder_id == funder_id].sort_values(['year','investment_id'])
    seen = set(history.theme)
    rows = []
    for _, op in opportunities.iterrows():
        relevant = set(links.loc[links.opportunity_id == op.opportunity_id, 'history_theme'])
        overlap = sorted(seen & relevant)
        eligible = funder['type'] in op.eligible_funder_types.split('|')
        rows.append({'opportunity_id':op.opportunity_id,'opportunity':op['name'],
                     'matching_themes':', '.join(overlap) or 'None',
                     'overlap_count':len(overlap),'eligible_type':eligible,
                     'baseline_score':len(overlap) if eligible else 0})
    return pd.DataFrame(rows).sort_values(['eligible_type','baseline_score','opportunity'], ascending=[False,False,True]).reset_index(drop=True)

def funding_gap(need, available):
    if pd.isna(need) or pd.isna(available) or need < 0 or available < 0:
        return None
    return max(need - available, 0)
