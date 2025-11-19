@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_windows_any.ps1"
endlocal