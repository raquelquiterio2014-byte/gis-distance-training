@echo off
setlocal
cd /d "%~dp0"
call SETUP.cmd
if errorlevel 1 goto failed
.venv312\Scripts\python.exe main.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo Setup or launch failed. Check Python 3.12 and the error above.
pause
exit /b 1
