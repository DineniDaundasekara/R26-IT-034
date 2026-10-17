$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Create it first: python -m venv .venv"
    exit 1
}

. .\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
