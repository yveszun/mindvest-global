from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scoring import rank_opportunities, funding_gap
D=Path(__file__).resolve().parents[1]/'data'
def read(n): return pd.read_csv(D/f'{n}.csv')
def test_rank():
    r=rank_opportunities('F01',read('funders'),read('investments'),read('opportunities'),read('theme_links'))
    assert r.iloc[0].opportunity_id == 'O01'
    assert r.iloc[0].baseline_score == 3
def test_gap():
    assert funding_gap(10,4)==6
    assert funding_gap(3,4)==0
    assert funding_gap(None,4) is None
