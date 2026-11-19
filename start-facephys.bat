@echo off
REM Starts the FacePhys (deep learning) demo at http://localhost:8001
cd /d "%~dp0apps\facephys-deep"
echo.
echo  FacePhys running at:  http://localhost:8001
echo  Press Ctrl+C to stop.
echo.
start "" http://localhost:8001
python -m http.server 8001 || py -m http.server 8001 || npx --yes http-server -p 8001 -c-1
