@echo off
REM Starts PulseLens Classical (POS signal processing) at http://localhost:5173/pulse/
cd /d "%~dp0apps\pulselens-classical"
if not exist node_modules (
  echo Installing dependencies, first run only...
  call npm install
)
echo.
echo  PulseLens Classical running at:  http://localhost:5173/pulse/
echo  Press Ctrl+C to stop.
echo.
call npm run dev -- --port 5173 --open /pulse/
