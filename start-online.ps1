$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$reviewCredential = Join-Path $PSScriptRoot 'runtime\review-credentials.json'
$tunnelExe = Join-Path $PSScriptRoot '.cache\cloudflared.exe'
if (-not (Test-Path -LiteralPath $reviewCredential)) { throw 'Prepare the isolated reviewer dataset with tools/prepare_review.py first.' }
if (-not (Test-Path -LiteralPath $tunnelExe)) { throw 'Install cloudflared.exe into .cache first; see docs/online-review.md.' }
$reviewListener = Get-NetTCPConnection -State Listen -LocalPort 8766 -ErrorAction SilentlyContinue
if (-not $reviewListener) {
    Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $PSScriptRoot -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'start-review.ps1')) -RedirectStandardOutput (Join-Path $PSScriptRoot 'runtime\review-service.log') -RedirectStandardError (Join-Path $PSScriptRoot 'runtime\review-service-error.log') | Out-Null
}
$existingTunnel = Get-CimInstance Win32_Process -Filter "name = 'cloudflared.exe'" | Where-Object { $_.CommandLine -like '*127.0.0.1:8766*' }
if ($existingTunnel) {
    Write-Host 'Reviewer tunnel is already running. Read runtime/cloudflared.log for its URL.'
    exit 0
}
$tunnelLog = Join-Path $PSScriptRoot 'runtime\cloudflared.log'
Start-Process -FilePath $tunnelExe -WindowStyle Hidden -WorkingDirectory $PSScriptRoot -ArgumentList @('tunnel','--url','http://127.0.0.1:8766','--protocol','http2','--no-autoupdate','--logfile',$tunnelLog) -RedirectStandardOutput (Join-Path $PSScriptRoot 'runtime\tunnel-stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'runtime\tunnel-stderr.log') | Out-Null
Write-Host 'Starting temporary reviewer tunnel. Open runtime/cloudflared.log for the NEW trycloudflare.com URL.'
Write-Host 'The hostname can change on restart. Update the submission URL and verify login. Keep this computer awake with Ollama running.'
