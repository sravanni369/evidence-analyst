# Live AI check: DSPy (DeepSeek or another provider) generates code, E2B runs it, result is checked.
# Keys are typed here, held only in this PowerShell process, and never written to disk or the log.
# Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File scripts\live_check.ps1
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

function Read-Secret($prompt) {
    $secure = Read-Host $prompt -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

if (-not $env:LLM_MODEL) { $env:LLM_MODEL = 'deepseek/deepseek-flash' }
Write-Host "Model: $env:LLM_MODEL"
if ($env:LLM_MODEL -like 'deepseek/*' -and -not $env:DEEPSEEK_API_KEY) {
    $env:DEEPSEEK_API_KEY = Read-Secret 'DeepSeek API key (platform.deepseek.com/api_keys)'
}
if (-not $env:E2B_API_KEY) { $env:E2B_API_KEY = Read-Secret 'E2B API key (e2b.dev dashboard)' }

if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency install failed.' }

# Windows PowerShell turns any stderr line from a native program into a fatal error when
# ErrorActionPreference is Stop, hiding the real Python traceback. Let Python report its own errors.
$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = '1'
$env:LIVE_CHECK_LOG = (Join-Path (Get-Location) 'live_check.log')   # *.log is git-ignored
& .\.venv\Scripts\python.exe -u scripts\smoke_live.py
Write-Host "Exit code: $LASTEXITCODE (details in live_check.log)"
