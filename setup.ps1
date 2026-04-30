# setup.ps1 — Bedtime setup for Windows
# Run from the bedtime project directory:
#   .\setup.ps1

Write-Host ""
Write-Host "🌙  Bedtime Setup (Windows)" -ForegroundColor Magenta
Write-Host "─────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── Check Python ──────────────────────────────────────────────────────────────
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "✖  Python is not installed or not on PATH." -ForegroundColor Red
    Write-Host "   Download Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

$version = & python --version 2>&1
Write-Host "✔  Found: $version" -ForegroundColor Green

# ── Run Python setup ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "→  Running Python setup script..." -ForegroundColor Cyan
python setup.py
