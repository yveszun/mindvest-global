from pathlib import Path
import pandas as pd
from validation import draw_sample
root=Path(__file__).parent/'data'
frame=pd.read_csv(root/'wellcome_mental_health_triage.csv',low_memory=False)
sample=draw_sample(frame)
sample.to_csv(root/'wellcome_validation_sample.csv',index=False)
print(f'Created {len(sample)} unlabelled audit records in 5 strata')
