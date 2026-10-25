@echo off
setlocal
cd /d "%~dp0"
call SETUP.cmd
if errorlevel 1 goto failed
.venv312\Scripts\python.exe verify_project.py --api-url http://127.0.0.1:8002
if errorlevel 1 goto failed
pause
exit /b 0
:failed
echo Verification failed. Start RUN_API.cmd in a separate window and check the error above.
pause
exit /b 1
