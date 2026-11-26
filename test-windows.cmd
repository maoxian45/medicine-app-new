@echo off
cd /d "%~dp0"
if not exist ".venv-win\Scripts\python.exe" (
  echo Run setup-windows.cmd first.
  pause
  exit /b 1
)
echo Running backend tests...
".venv-win\Scripts\python.exe" -m pytest backend\tests -q
if errorlevel 1 goto failed
echo Building frontend...
call npm.cmd --prefix frontend-web run build
if errorlevel 1 goto failed
echo All checks passed.
pause
exit /b 0
:failed
echo Checks failed. See the output above.
pause
exit /b 1
