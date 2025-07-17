@echo off
REM --------------------------------------------------
REM  ClibDT Python Environment Setup Script
REM --------------------------------------------------

echo.
echo [INFO] Checking for Python...
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo [INFO] Please install Python 3.8+ and re-run this script.
    pause
    exit /b 1
)

echo [OK] Python found.
echo.

REM --------------------------------------------------
REM  Install required Python packages
REM --------------------------------------------------

echo [INFO] Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install colorama rich tqdm requests

echo.
echo [DONE] All required packages installed.
echo.
pause