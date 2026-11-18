@echo off
echo ========================================================
echo Starting Automated Multi-Platform Posting System
echo http://localhost:4000
echo ========================================================
python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
pause
