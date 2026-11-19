@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.11+ with Python Launcher first.
  pause
  exit /b 1
)
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo Install Node.js 22 LTS, then reopen this script.
  pause
  exit /b 1
)
if not exist ".venv-win\Scripts\python.exe" py -3 -m venv .venv-win
if errorlevel 1 goto failed
".venv-win\Scripts\python.exe" -m pip install -r backend\requirements-lock.txt
if errorlevel 1 goto failed
cd frontend-web
call npm.cmd ci
if errorlevel 1 goto failed
echo Setup complete. Run start-backend.cmd and start-frontend.cmd.
pause
exit /b 0
:failed
echo Setup failed. Check the error above.
pause
exit /b 1
