"""Conservative importer for Wellcome's publicly downloadable award spreadsheet.
No network calls. Preserve source rows; never infer unobserved behavior.
"""
from pathlib import Path
import re
import pandas as pd

SOURCE = 'https://wellcome.org/research-funding/funding-portfolio'
ALIASES = {
 'grant_id':['grant reference','internal id','identifier','grant id','grant number','reference','identifier','id'],
 'title':['title','project title','grant title'],
 'description':['description','summary','project summary','abstract'],
 'date':['award date','planned dates start date','date awarded','date of award','start date','date'],
 'amount':['amount awarded','amount awarded from wellcome','award amount','amount'],
 'recipient':['recipient org name','organisation','organization','recipient organisation','lead organisation','host organisation','recipient'],
}

def clean(x):
 return re.sub(r'[^a-z0-9]+',' ',str(x).lower()).strip()

def select_columns(columns):
 norm={clean(c):c for c in columns}
 found={}
 for key,choices in ALIASES.items():
  for alias in choices:
   if clean(alias) in norm:
    found[key]=norm[clean(alias)];break
 return found

def import_awards(path, max_rows=None, include_raw=False, audit_mode=False):
 """Import Wellcome awards with comprehensive audit trail.
 
 Args:
  path: Path to Wellcome Excel workbook or CSV
  max_rows: Optional row limit for testing
  include_raw: If True, return (processed, raw, exclusions) tuple
  audit_mode: If True, return detailed exclusion reasons
 
 Returns:
  DataFrame or tuple depending on include_raw parameter
 """
 path=Path(path)
 if path.suffix.lower() in ('.xlsx','.xls'):
  book=pd.ExcelFile(path)
  sheets=[pd.read_excel(path,sheet_name=s) for s in book.sheet_names]
  raw=max(sheets,key=lambda d:len(select_columns(d.columns))*100000+len(d))
 elif path.suffix.lower()=='.csv':raw=pd.read_csv(path)
 else:raise ValueError('Supply Wellcome CSV or Excel (.xlsx/.xls) export')
 
 # Store original for audit trail
 raw_original = raw.copy()
 source_row_count = len(raw)
 
 cols=select_columns(raw.columns)
 missing={'grant_id','title','date','amount'}-set(cols)
 if missing:raise ValueError(f'Unrecognized source columns: {sorted(missing)}. Available: {list(raw.columns)}')
 out=pd.DataFrame({k:raw[v] for k,v in cols.items()})
 for k in ('description','recipient'):
  if k not in out:out[k]=''
 
 # Track exclusion reasons with source row index
 exclusions = pd.DataFrame({
  'source_row_index': range(len(raw)),
  'grant_id': raw[cols['grant_id']].astype(str).str.strip(),
  'title': raw[cols['title']],
  'exclusion_reason': '',
  'excluded': False
 })
 
 # Date parsing - handle both Excel datetime and string formats
 dates=out['date']
 if pd.api.types.is_datetime64_any_dtype(dates):
  # Already parsed by pandas from Excel
  out['award_date'] = dates
 else:
  # String dates from CSV - need parsing
  numeric=pd.to_numeric(dates,errors='coerce')
  out['award_date']=pd.to_datetime(dates.where(numeric.isna()),errors='coerce',dayfirst=True)
  out['award_date']=out['award_date'].fillna(pd.to_datetime(numeric,unit='D',origin='1899-12-30',errors='coerce'))
 
 # Track invalid dates
 invalid_dates = out['award_date'].isnull()
 exclusions.loc[invalid_dates, 'exclusion_reason'] = 'invalid_date'
 exclusions.loc[invalid_dates, 'excluded'] = True
 
 # Amount parsing
 out['amount_gbp']=pd.to_numeric(out['amount'].astype(str).str.replace(r'[£, ]','',regex=True),errors='coerce')
 
 # Track invalid/zero amounts
 invalid_amounts = out['amount_gbp'].isnull()
 zero_amounts = (out['amount_gbp'] == 0)
 exclusions.loc[invalid_amounts & ~exclusions['excluded'], 'exclusion_reason'] = 'invalid_amount'
 exclusions.loc[invalid_amounts & ~exclusions['excluded'], 'excluded'] = True
 exclusions.loc[zero_amounts & ~exclusions['excluded'], 'exclusion_reason'] = 'zero_amount'
 exclusions.loc[zero_amounts & ~exclusions['excluded'], 'excluded'] = True
 
 out['grant_id']=out['grant_id'].astype(str).str.strip()
 
 # Track empty grant IDs
 empty_ids = (out.grant_id == '') | (out.grant_id == 'nan')
 exclusions.loc[empty_ids & ~exclusions['excluded'], 'exclusion_reason'] = 'missing_grant_id'
 exclusions.loc[empty_ids & ~exclusions['excluded'], 'excluded'] = True
 
 # Currency filter - track non-GBP exclusions
 if 'Currency' in raw.columns:
  non_gbp = ~raw['Currency'].astype(str).str.upper().eq('GBP')
  exclusions.loc[non_gbp & ~exclusions['excluded'], 'exclusion_reason'] = 'non_gbp_currency'
  exclusions.loc[non_gbp & ~exclusions['excluded'], 'excluded'] = True
  out=out[~non_gbp]
 
 # Apply filters
 out=out.dropna(subset=['award_date','amount_gbp'])
 out=out[(out.grant_id!='')&(out.grant_id!='nan')]
 
 # Track duplicates before removing (mark only the duplicate rows, not the first occurrence)
 duplicates_mask = out['grant_id'].duplicated(keep='first')
 if duplicates_mask.any():
  # Get the indices of duplicate rows in the original dataframe
  dup_indices = duplicates_mask[duplicates_mask].index.tolist()
  exclusions.loc[dup_indices, 'exclusion_reason'] = 'duplicate_grant_id'
  exclusions.loc[dup_indices, 'excluded'] = True
 
 out=out.drop_duplicates(subset=['grant_id'],keep='first').sort_values(['award_date','grant_id'])
 out['funder']='Wellcome'
 out['currency']='GBP'
 out['source_url']=SOURCE
 out['classification']='unclassified'
 out['mental_health_flag']='not_reviewed'
 out['record_type']='awarded_grant'
 if max_rows:out=out.head(max_rows)
 
 result = out[['grant_id','funder','title','description','recipient','award_date','amount_gbp','currency','classification','mental_health_flag','record_type','source_url']].reset_index(drop=True)
 
 if include_raw:
  return result, raw_original, exclusions
 return result

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--output',default='data/wellcome_awards_imported.csv');a=p.parse_args()
 df=import_awards(a.source);Path(a.output).parent.mkdir(parents=True,exist_ok=True);df.to_csv(a.output,index=False)
 print(f'Imported {len(df)} awarded-grant records to {a.output}. All themes unclassified pending review.')
