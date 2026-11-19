@echo off
REM Starts PulseLens Deep (state-space model) at http://localhost:8001
cd /d "%~dp0apps\pulselens-deep"
echo.
echo  PulseLens Deep running at:  http://localhost:8001
echo  Press Ctrl+C to stop.
echo.
start "" http://localhost:8001
python -m http.server 8001 || py -m http.server 8001 || npx --yes http-server -p 8001 -c-1
