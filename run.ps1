Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting Automated Multi-Platform Posting System API" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:4000" -ForegroundColor Yellow
Write-Host "API Docs:  http://localhost:4000/docs" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
