@echo off
rem Start Guardian: server, room agent (camera) and dashboard, then open the dashboard.
rem Options: --no-telegram  --mock  --demo   (see scripts\run_guardian.py)
rem Close this window or press Ctrl+C to stop Guardian.
cd /d "%~dp0"
".venv\Scripts\python.exe" scripts\run_guardian.py %*
pause
