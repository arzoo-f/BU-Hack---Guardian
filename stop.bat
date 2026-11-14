@echo off
rem Stop a Guardian that was started with start.bat in another window.
cd /d "%~dp0"
".venv\Scripts\python.exe" scripts\run_guardian.py --stop
pause
