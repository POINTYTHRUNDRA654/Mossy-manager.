@echo off
setlocal
set SCRIPT_DIR=%~dp0
set PY_EXE=C:\Users\billy\AppData\Local\Programs\Python\Python314\python.exe
"%PY_EXE%" -m mossy_manager.cli.main %*
endlocal
