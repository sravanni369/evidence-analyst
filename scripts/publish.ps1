$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Run gh auth login -h github.com first. Never paste tokens into chat.' }
$account = gh api user --jq .login
if ($account -ne 'sravanni369') { throw 'Expected GitHub account sravanni369. Check the active account before publishing.' }
$dirty = git status --porcelain
if ($dirty) { throw 'Review and commit local changes before publishing.' }
# 'Not found' is the expected answer here; with ErrorActionPreference=Stop, Windows PowerShell would
# treat gh's stderr as fatal, so relax it just for this check.
$ErrorActionPreference = 'Continue'
gh repo view sravanni369/evidence-analyst --json nameWithOwner *> $null
$exists = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = 'Stop'
if ($exists) { throw 'Repository already exists. Inspect it before attaching or pushing; this script will not overwrite it.' }
gh repo create sravanni369/evidence-analyst --public --source . --remote origin --push --description 'Inspectable CSV analytics with Python, ML baselines, DSPy/E2B adapters and a native Power BI report'
if ($LASTEXITCODE -ne 0) { throw 'Publication failed. Inspect the error before retrying.' }
gh repo view sravanni369/evidence-analyst --json url --jq .url
