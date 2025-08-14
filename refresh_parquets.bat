@echo off
REM — activate your venv
call "C:\Users\betti\.spyder-py3\Market_Dashboards\env\Scripts\activate.bat"

REM — run the refresher and append stdout/stderr to a log
"C:\Users\betti\.spyder-py3\Market_Dashboards\env\Scripts\python.exe" ^
  "C:\Users\betti\.spyder-py3\Market_Dashboards\scripts\refresh_parquets.py" ^
  >> "C:\Users\betti\.spyder-py3\Market_Dashboards\logs\refresh.log" 2>&1