@echo off
echo ====================================
echo HOSxPXE4 Permissions Fix Script
echo ====================================
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0fix-hosxp-permissions.ps1"

echo.
echo Press any key to exit...
pause >nul