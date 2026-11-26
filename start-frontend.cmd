@echo off
cd /d "%~dp0frontend-web"
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo Node.js 22 LTS not found. Install it, reopen the terminal, then run setup-windows.cmd.
  pause
  exit /b 1
)
call npm.cmd run dev
pause
