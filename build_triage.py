from pathlib import Path
import pandas as pd
from mental_health_triage import classify_awards
root = Path(__file__).parent / 'data'
df = pd.read_csv(root/'wellcome_awards_imported.csv',low_memory=False)
out = classify_awards(df)
out.to_csv(root/'wellcome_mental_health_triage.csv',index=False)
print(out.triage_category.value_counts().to_string())
