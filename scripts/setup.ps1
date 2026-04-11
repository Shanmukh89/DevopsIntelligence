$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Installing frontend dependencies..."
Set-Location (Join-Path $Root "frontend")
npm install

Write-Host "Installing realtime service dependencies..."
Set-Location (Join-Path $Root "services\realtime")
npm install

Set-Location $Root
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Creating Python venv and installing backend deps..."
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    pip install -r backend\requirements.txt
}

Write-Host "Done. Copy .env.example to .env if you have not already."
