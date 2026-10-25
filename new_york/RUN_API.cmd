@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv312\Scripts\python.exe" (
  echo Run RUN_DASHBOARD.cmd first to install the environment.
  pause
  exit /b 1
)
echo New York API documentation: http://127.0.0.1:8003/docs
echo Keep this window open while comparing from the dashboard.
.venv312\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8003
pause
