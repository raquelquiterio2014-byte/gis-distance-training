@echo off
setlocal
cd /d "%~dp0"
call SETUP.cmd
if errorlevel 1 goto failed
.venv312\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 goto failed
.venv312\Scripts\python.exe -m unittest discover -s tests -v
if errorlevel 1 goto failed
echo Tests passed. QGIS measurements and positional validation remain separate.
pause
exit /b 0
:failed
echo Tests or setup failed. Read the error above.
pause
exit /b 1
