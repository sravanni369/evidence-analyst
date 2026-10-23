$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Run gh auth login -h github.com first. Never paste tokens into chat.' }
$account = gh api user --jq .login
if ($account -ne 'sravanni369') { throw 'Expected GitHub account sravanni369. Check the active account before publishing.' }
$dirty = git status --porcelain
if ($dirty) { throw 'Review and commit local changes before publishing.' }
gh repo view sravanni369/evidence-analyst --json nameWithOwner 2>$null
if ($LASTEXITCODE -eq 0) { throw 'Repository already exists. Inspect it before attaching or pushing; this script will not overwrite it.' }
gh repo create sravanni369/evidence-analyst --public --source . --remote origin --push --description 'Inspectable CSV analytics with Python, ML baselines, DSPy/E2B adapters and a native Power BI report'
if ($LASTEXITCODE -ne 0) { throw 'Publication failed. Inspect the error before retrying.' }
gh repo view sravanni369/evidence-analyst --json url --jq .url
