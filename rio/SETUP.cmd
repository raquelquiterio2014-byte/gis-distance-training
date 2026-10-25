@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv312\Scripts\python.exe" (
  py -3.12 -m venv .venv312
  if errorlevel 1 exit /b 1
)
.venv312\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
exit /b 0
