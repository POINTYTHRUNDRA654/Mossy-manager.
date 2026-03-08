@echo off
REM =====================================================================
REM  Mossy Manager - Windows Install Script
REM  Run this script after cloning the repository to install from source.
REM
REM  NOTE: If Windows gave you an empty folder when cloning, it is likely
REM  because the repository name ends with a period, which Windows does
REM  not allow as a folder name.
REM
REM  WORKAROUND:
REM    1. Open Command Prompt (Win+R, type cmd, press Enter)
REM    2. Run: git clone https://github.com/POINTYTHRUNDRA654/Mossy-manager. MossyManager
REM    3. Run: cd MossyManager
REM    4. Run: install.bat
REM =====================================================================

setlocal

echo ========================================================
echo  Mossy Manager - Install from Source
echo ========================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.8 or later from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo.

REM Install Mossy Manager
echo Installing Mossy Manager...
python -m pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install Mossy Manager.
    pause
    exit /b 1
)
echo.

echo ========================================================
echo  Installation complete!
echo ========================================================
echo.
echo You can now use Mossy Manager by running:
echo   mossy --help
echo   mossy auto --profile "Default"
echo.
echo To build a standalone executable (no Python required):
echo   build.bat
echo.
pause
endlocal
