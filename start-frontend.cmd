@echo off
cd /d "%~dp0frontend-web"
where npm.cmd >nul 2>nul
if errorlevel 1 (
  node "%~dp0.tools\npm\bin\npm-cli.js" run dev
) else (
  call npm.cmd run dev
)
pause
