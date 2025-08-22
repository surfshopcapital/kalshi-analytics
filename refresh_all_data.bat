@echo off
echo ========================================
echo    Market Data Refresh - All Sources
echo ========================================
echo.

echo 🔄 Refreshing Kalshi data...
call python scripts\refresh_parquets.py
echo.

echo 🔄 Refreshing Polymarket data...
call python scripts\refresh_polymarket.py
echo.

echo ========================================
echo    Refresh Complete!
echo ========================================
echo.
echo Data sources updated:
echo - Kalshi markets
echo - Polymarket markets
echo.
echo You can now run the dashboard with:
echo   streamlit run Dashboard.py
echo.
pause
