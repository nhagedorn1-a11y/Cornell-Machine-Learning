@echo off
REM Demand Forecasting Platform - Windows Startup Script

echo ============================================================
echo   DEMAND FORECASTING PLATFORM - STARTUP
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version

echo.
echo [2/4] Installing dependencies...
echo This may take a minute on first run...
pip install -q fastapi uvicorn streamlit pandas numpy plotly requests

echo.
echo [3/4] Starting API server on port 8001...
start "API Server" cmd /k "python simple_api.py"

REM Wait for API to start
timeout /t 3 /nobreak >nul

echo.
echo [4/4] Starting web UI on port 8501...
echo.
echo ============================================================
echo   PLATFORM READY!
echo ============================================================
echo.
echo   API Server:  http://localhost:8001/docs
echo   Web UI:      http://localhost:8501
echo.
echo   Press Ctrl+C in each window to stop the servers
echo ============================================================
echo.

streamlit run app.py

pause
