@echo off
REM Build script for creating Mossy Manager executable on Windows

echo Building Mossy Manager executable...
echo ====================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install -r requirements.txt
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the executable
echo Building executable...
pyinstaller mossy_manager.spec

REM Check if build was successful
if exist "dist\MossyManager.exe" (
    echo.
    echo ====================================
    echo Build successful!
    echo Executable location: dist\MossyManager.exe
    echo ====================================
) else (
    echo.
    echo ====================================
    echo Build failed! Check the output above for errors.
    echo ====================================
    exit /b 1
)
