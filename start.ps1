param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Run setup.ps1 to install the project dependencies first.'
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'dist\index.html'))) {
    throw 'Frontend build is missing. Run npm ci and npm run build.'
}
$env:PYTHONIOENCODING = 'utf-8'
Set-Location -LiteralPath $projectRoot
try {
    $currentService = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/health' -TimeoutSec 2
    if ($currentService.status -eq 'ok' -and $currentService.local_only) {
        Write-Host 'Scholar Workbench is already running: http://127.0.0.1:8765'
        if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765' }
        exit 0
    }
} catch { }
Write-Host 'Scholar Workbench: http://127.0.0.1:8765'
Write-Host 'Keep this window open. Press Ctrl+C to stop. Ollama runs separately.'
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765' }
& $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8765
