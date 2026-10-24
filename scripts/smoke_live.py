"""Opt-in paid integration check. Set service keys in your terminal, never in this file."""
import os
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LOG = os.getenv('LIVE_CHECK_LOG')
if LOG:  # mirror everything (including tracebacks) to a log file; keys are never printed
    class _Tee:
        def __init__(self, stream, handle):
            self.stream, self.handle = stream, handle
        def write(self, text):
            self.stream.write(text); self.handle.write(text); self.handle.flush()
        def flush(self):
            self.stream.flush(); self.handle.flush()
    _handle = open(LOG, 'w', encoding='utf-8')
    sys.stdout, sys.stderr = _Tee(sys.stdout, _handle), _Tee(sys.stderr, _handle)
    print(f"Live check started {datetime.now().isoformat(timespec='seconds')} with model {os.getenv('LLM_MODEL')}")
import pandas as pd
from ai import generate, execute

frame = pd.DataFrame({'region':['East','East','West'], 'revenue':[2,3,4]})
question = 'Sum revenue by region. Return columns region and revenue; one row per region.'
code = generate(frame, question)
print('Generated code (review before execution):\n', code)
print('Run this code in E2B using synthetic data? Type RUN and press Enter: ', end='', flush=True)
reply = input()
if LOG:
    _handle.write(reply + '\n'); _handle.flush()  # record the answer in the log only
if reply != 'RUN':
    raise SystemExit('Cancelled')
result = execute(frame, code)
assert set(result.columns) == {'region','revenue'}, 'Unexpected output columns'
actual = result.set_index('region')['revenue'].to_dict()
assert actual == {'East':5,'West':4}, f'Known-answer check failed: {actual}'
print('PASS: live DSPy -> E2B known-answer test')
