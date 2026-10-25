@echo off
setlocal
cd /d "%~dp0"
call SETUP.cmd
if errorlevel 1 goto failed
echo Rio API: http://127.0.0.1:8002/docs
echo Keep this window open. Press Ctrl+C to stop.
.venv312\Scripts\python.exe api.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo API setup or launch failed. Check Python 3.12 and the error above.
pause
exit /b 1
