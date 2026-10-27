# Run StockQuote AI FastAPI Backend
Write-Host "Starting StockQuote AI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot/backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
