import json
from pathlib import Path
import requests
import jsonschema
cache={}
def fetch(uri):
    if uri not in cache:
        r=requests.get(uri,timeout=30);r.raise_for_status();cache[uri]=r.json()
    return cache[uri]
count=0
errors=[]
for p in (Path(__file__).resolve().parents[1] / 'powerbi/project').rglob('*.json'):
    d=json.loads(p.read_text())
    if '$schema' not in d:continue
    uri=d['$schema'];s=fetch(uri)
    resolver=jsonschema.RefResolver(base_uri=uri,referrer=s,handlers={'https':fetch})
    for e in jsonschema.Draft7Validator(s,resolver=resolver).iter_errors(d):
        errors.append(f'{p}: {list(e.path)} {e.message}')
    count+=1
print('\n'.join(errors) if errors else f'PASS: {count} PBIR documents validated against Microsoft schemas')
raise SystemExit(bool(errors))
