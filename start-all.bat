@echo off
REM Opens both PulseLens apps, each in its own terminal window
start "PulseLens Deep" cmd /k "%~dp0start-deep.bat"
start "PulseLens Classical" cmd /k "%~dp0start-classical.bat"
