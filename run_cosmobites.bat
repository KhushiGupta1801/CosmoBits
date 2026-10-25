@echo off
setlocal enabledelayedexpansion
title Cosmo Bites — Orbital Command Center Launcher
cd /d "%~dp0"

echo.
echo ============================================================
echo         COSMO BITES — ORBITAL COMMAND CENTER (WINDOWS)
echo ============================================================
echo.

:: 1. Detect Python command
set "PYCMD="
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYCMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYCMD=py -3"
    )
)

if "%PYCMD%"=="" (
    echo [X] ERROR: Python is not installed or not in your PATH!
    echo.
    echo   Kripya Python 3.10, 3.11 ya 3.12 install karein:
    echo   1. Visit: https://www.python.org/downloads/
    echo   2. Installer download karke chalayein.
    echo   3. IMPORTANT: "Add python.exe to PATH" checkbox par tick zaroor karein!
    echo.
    pause
    exit /b 1
)

echo [*] Python detected:
%PYCMD% --version
echo.

:: 2. Check / Create Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Windows virtual environment (.venv) create ho raha hai...
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo [X] Virtual environment banane me error aaya.
        echo Make sure Python 3.10, 3.11 or 3.12 is properly installed.
        pause
        exit /b 1
    )
    echo [✓] Virtual environment ready.
) else (
    echo [1/3] Existing virtual environment (.venv) found.
)

:: 3. Install Requirements
echo [2/3] Dependencies check aur install ho rahi hain...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [X] Dependencies install karne me error aaya. Internet connection check karein.
    pause
    exit /b 1
)
echo [✓] Sabhi packages successfully installed!

:: 4. Launch Application
echo.
echo [3/3] Cosmo Bites launch ho raha hai...
echo ============================================================
echo   Browser me open hoga: http://localhost:8501
echo   App chalte samay is Command Prompt window ko band na karein.
echo ============================================================
echo.

start "" "http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false

if errorlevel 1 (
    echo.
    echo [X] Cosmo Bites run karne me koi error aaya.
    pause
)
