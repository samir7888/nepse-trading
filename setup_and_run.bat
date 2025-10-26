@echo off
echo ============================================================
echo NEPSE Trading System - Setup and Run
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found. Checking version...
python --version

echo.
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo Error installing packages. Please check your internet connection.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Starting NEPSE Trading System...
echo ============================================================
echo.

python run_system.py

echo.
echo ============================================================
echo System execution completed.
echo ============================================================
pause