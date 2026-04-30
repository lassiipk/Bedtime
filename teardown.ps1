# teardown.ps1 — Bedtime teardown for Windows
# Run from the bedtime project directory:
#   .\teardown.ps1

Write-Host ""
Write-Host "🌙  Bedtime Teardown (Windows)" -ForegroundColor Magenta
Write-Host "───────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Host "✖  Python not found. Attempting manual cleanup..." -ForegroundColor Yellow
    # Manual: remove Task Scheduler entry
    schtasks /delete /tn "Bedtime" /f 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✔  Task Scheduler entry removed." -ForegroundColor Green
    } else {
        Write-Host "⚠  No Task Scheduler entry found." -ForegroundColor Yellow
    }
    exit 0
}

python teardown.py
