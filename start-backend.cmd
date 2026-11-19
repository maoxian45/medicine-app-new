@echo off
cd /d "%~dp0"
if not exist ".venv-win\Scripts\python.exe" (
  echo Run setup-windows.cmd first.
  pause
  exit /b 1
)
cd backend
"..\.venv-win\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
