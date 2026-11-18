$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$credentialPath = Join-Path $PSScriptRoot 'runtime\review-credentials.json'
if (-not (Test-Path -LiteralPath $credentialPath)) { throw 'Run tools/prepare_review.py first.' }
$reviewConfig = Get-Content -LiteralPath $credentialPath -Raw -Encoding UTF8 | ConvertFrom-Json
$env:PUBLIC_REVIEW_TOKEN = $reviewConfig.password
$env:SCHOLAR_DATA_DIR = Join-Path $PSScriptRoot 'data-judge'
$env:PYTHONIOENCODING = 'utf-8'
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --no-access-log
