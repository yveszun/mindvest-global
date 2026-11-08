import pandas as pd
from wellcome_import import import_awards

def test_import_and_dedup(tmp_path):
 p=tmp_path/'sample.csv'
 pd.DataFrame({'Grant Reference':['A1','A1','A2'],'Title':['Mental health','Mental health','HIV'],'Award Date':['2024-01-02','2024-01-02','2025-01-03'],'Amount Awarded':['£1,200','£1,200','300'],'Organisation':['Org','Org','Other']}).to_csv(p,index=False)
 result=import_awards(p)
 assert len(result)==2
 assert result.amount_gbp.sum()==1500
 assert set(result.classification)=={'unclassified'}

def test_reject_unknown_schema(tmp_path):
 p=tmp_path/'bad.csv';pd.DataFrame({'wrong':[1]}).to_csv(p,index=False)
 try:import_awards(p)
 except ValueError:return
 assert False
