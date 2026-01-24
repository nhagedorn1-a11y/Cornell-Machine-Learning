#!/bin/bash
# Demand Forecasting Platform - Linux/Mac Startup Script

echo "============================================================"
echo "  DEMAND FORECASTING PLATFORM - STARTUP"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from https://www.python.org"
    exit 1
fi

echo "[1/4] Checking Python installation..."
python3 --version

echo ""
echo "[2/4] Installing dependencies..."
echo "This may take a minute on first run..."
pip3 install -q fastapi uvicorn streamlit pandas numpy plotly requests

echo ""
echo "[3/4] Starting API server on port 8001..."
python3 simple_api.py &
API_PID=$!

# Wait for API to start
sleep 3

echo ""
echo "[4/4] Starting web UI on port 8501..."
echo ""
echo "============================================================"
echo "  PLATFORM READY!"
echo "============================================================"
echo ""
echo "  API Server:  http://localhost:8001/docs"
echo "  Web UI:      http://localhost:8501"
echo ""
echo "  Press Ctrl+C to stop all servers"
echo "============================================================"
echo ""

# Trap Ctrl+C and kill API server
trap "kill $API_PID 2>/dev/null; exit" INT TERM

streamlit run app.py

# Cleanup
kill $API_PID 2>/dev/null
