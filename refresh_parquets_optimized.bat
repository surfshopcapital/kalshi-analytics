@echo off
REM Optimized Kalshi Parquet Refresh Script for Windows Task Scheduler
REM This script refreshes market data every 15 minutes

echo Starting Kalshi data refresh at %date% %time%

REM Change to the project directory
cd /d "C:\Users\betti\.spyder-py3\Market_Dashboards"

REM Activate virtual environment and run the optimized refresh script
call env\Scripts\activate.bat

REM Run the optimized refresh script with error handling
python scripts\refresh_parquets_optimized.py

REM Check if the script ran successfully
if %errorlevel% equ 0 (
    echo Refresh completed successfully at %date% %time%
    exit /b 0
) else (
    echo Refresh failed with error code %errorlevel% at %date% %time%
    exit /b %errorlevel%
)
