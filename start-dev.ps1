$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Prefer backend/venv (has all dependencies installed)
$python = Join-Path $root "backend\venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    # Fall back to root .venv
    $python = Join-Path $root ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        throw "No Python venv found. Run: py -m venv backend\venv && backend\venv\Scripts\pip install -r backend\requirements.txt"
    }
}

Write-Host "Using Python: $python"

# Start backend — must cd into backend/ so 'app' package is on sys.path
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\backend'; & '$python' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

# Start frontend
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\frontend'; npm run dev -- --host 127.0.0.1"
)

Write-Host ""
Write-Host "Backend:          http://localhost:8000"
Write-Host "Backend Swagger:  http://localhost:8000/docs"
Write-Host "Frontend:         http://localhost:5173"
