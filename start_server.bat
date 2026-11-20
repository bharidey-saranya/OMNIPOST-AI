@echo off
title OmniPost AI Broadcasting Server (:4000)
cd /d "%~dp0"
echo ===================================================
echo   OmniPost AI - Automated Multi-Platform System
echo   Starting FastAPI Server on http://localhost:4000
echo ===================================================
echo.
"C:\Users\Admin\AppData\Local\Python\bin\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
pause
