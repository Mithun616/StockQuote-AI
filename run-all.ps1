# Launch both Backend and Frontend in separate PowerShell jobs/windows
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting StockQuote AI Full-Stack Environment" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$backendPath = Join-Path $PSScriptRoot "backend"
$frontendPath = Join-Path $PSScriptRoot "frontend"

Write-Host "1. Spawning FastAPI backend process (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "2. Spawning React/Vite frontend process (port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

Write-Host "`n✓ Backend running at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "✓ Frontend running at: http://localhost:5173" -ForegroundColor Green
Write-Host "✓ API Docs available at: http://127.0.0.1:8000/docs" -ForegroundColor Green
