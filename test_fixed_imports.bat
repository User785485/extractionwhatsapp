@echo off
echo Testing fixed imports...
echo.

REM Navigate to src directory
cd /d "%~dp0src"

REM Run the import test script
python test_imports.py

echo.
echo Press any key to exit...
pause > nul