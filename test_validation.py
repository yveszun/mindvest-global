import pandas as pd
from validation import draw_sample, audit_report

def test_reproducible_and_unlabelled():
    df=pd.DataFrame({'grant_id':[str(i) for i in range(50)],'triage_category':['no_rule_match']*50,'triage_reason':['none']*50,'title':['x']*50,'description':['']*50,'recipient':['r']*50,'award_date':['2020']*50,'amount_gbp':[1]*50,'source_url':['url']*50})
    a=draw_sample(df,10); b=draw_sample(df,10)
    assert a.grant_id.tolist()==b.grant_id.tolist()
    assert len(a)==10 and a.adjudicated_label.eq('').all()
    report,estimate,complete=audit_report(a,df)
    assert not complete and estimate is None
