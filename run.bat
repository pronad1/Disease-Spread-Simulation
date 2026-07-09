@echo off
title EpiSim — Disease Spread Simulation
echo.
echo  ====================================================
echo   EpiSim — Disease Spread Simulation
echo  ====================================================
echo.

:: Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo  [1/2] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo  [!] No .venv found — using system Python.
    echo      Run: python -m venv .venv ^& pip install -r requirements.txt
    echo.
)

echo  [2/2] Starting Streamlit dashboard...
echo.
streamlit run ui\app.py
pause