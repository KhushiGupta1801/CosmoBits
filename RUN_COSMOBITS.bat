@echo off
setlocal
cd /d "%~dp0"
title CosmoBits - Local Launcher

echo.
echo ============================================
echo       COSMOBITS - LOCAL LAUNCHER
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo Install Python 3.11 or 3.12 from https://www.python.org/downloads/
    echo During installation, tick "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating project virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Could not create virtual environment. Try installing Python 3.11 or 3.12.
        pause
        exit /b 1
    )
)

echo [2/3] Installing / checking required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [3/3] Starting CosmoBits...
echo Your browser should open at http://localhost:8501
echo Keep this window open while using the app.
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless false
if errorlevel 1 goto :error
goto :eof

:error
echo.
echo Something went wrong while setting up or starting CosmoBits.
echo Check the error above. Python 3.11 or 3.12 is recommended.
pause
exit /b 1
