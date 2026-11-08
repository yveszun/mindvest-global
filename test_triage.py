from mental_health_triage import triage

def test_direct_title():
    assert triage('Mental health services in Kenya','')['0' if False else 0] == 'priority_direct_review'

def test_integrated():
    assert triage('Community care','Integrating depression screening in maternal health')[0] == 'priority_integration_review'

def test_incidental():
    assert triage('Genomic research','Unrelated molecular biology')[0] == 'no_rule_match'
