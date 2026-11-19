@echo off
REM Opens both demos, each in its own terminal window
start "FacePhys (deep)" cmd /k "%~dp0start-facephys.bat"
start "pulse (classical)" cmd /k "%~dp0start-pulse.bat"
