@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv312\Scripts\python.exe" (
  py -3.12 -m venv .venv312
  if errorlevel 1 goto failed
)
.venv312\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
.venv312\Scripts\python.exe main.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Setup or launch failed. Check that Python 3.12 is installed and internet is available for setup.
pause
exit /b 1
