"""Opt-in paid integration check. Set service keys in your terminal, never in this file."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from ai import generate, execute

frame = pd.DataFrame({'region':['East','East','West'], 'revenue':[2,3,4]})
question = 'Sum revenue by region. Return columns region and revenue; one row per region.'
code = generate(frame, question)
print('Generated code (review before execution):\n', code)
if input('Run this code in E2B using synthetic data? Type RUN: ') != 'RUN':
    raise SystemExit('Cancelled')
result = execute(frame, code)
assert set(result.columns) == {'region','revenue'}, 'Unexpected output columns'
actual = result.set_index('region')['revenue'].to_dict()
assert actual == {'East':5,'West':4}, f'Known-answer check failed: {actual}'
print('PASS: live DSPy -> E2B known-answer test')
