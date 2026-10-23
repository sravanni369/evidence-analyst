"""Reproduce all offline artifacts without Streamlit, LLMs, or cloud accounts."""
import json
from pathlib import Path
from core import read_csv, clean, answer, regression, export_bundle

root = Path(__file__).parent
df, audit = clean(read_csv((root/'data/retail_demo.csv').read_bytes()))
result = answer(df, 'Revenue by region')
metrics, predictions = regression(df, 'revenue', ['units','unit_price','discount'])
out = root/'demo_output'
out.mkdir(exist_ok=True)
(out/'powerbi_bundle.zip').write_bytes(export_bundle(df, audit, result))
(out/'metrics.json').write_text(json.dumps(metrics, indent=2))
predictions.to_csv(out/'predictions.csv', index=False)
print(json.dumps({'quality': audit, 'evaluation': metrics}, indent=2))
