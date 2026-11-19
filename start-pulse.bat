@echo off
REM Starts the pulse (classical POS) demo at http://localhost:5173/pulse/
cd /d "%~dp0apps\pulse-classical"
if not exist node_modules (
  echo Installing dependencies, first run only...
  call npm install
)
echo.
echo  pulse running at:  http://localhost:5173/pulse/
echo  Press Ctrl+C to stop.
echo.
call npm run dev -- --port 5173 --open /pulse/
