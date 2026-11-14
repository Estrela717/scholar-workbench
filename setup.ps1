$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.cache\uv'
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    uv venv --python 3.13 .venv
    if ($LASTEXITCODE -ne 0) { throw '创建虚拟环境失败' }
}
uv pip install --python .venv\Scripts\python.exe -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python 依赖安装失败' }
npm ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw '前端依赖安装失败' }
npm run build
if ($LASTEXITCODE -ne 0) { throw '前端构建失败' }
Write-Host '依赖就绪。请确保 Ollama 正在运行，再运行 start.cmd。'
