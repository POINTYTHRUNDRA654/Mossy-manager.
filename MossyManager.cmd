@echo off
setlocal
set SCRIPT_DIR=%~dp0

REM Try the Python launcher (py.exe) first, then fall back to python in PATH
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -m mossy_manager.cli.main %*
) else (
    python -m mossy_manager.cli.main %*
)
endlocal
