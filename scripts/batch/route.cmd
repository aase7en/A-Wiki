@echo off
:: route.cmd — cmd.exe shim that delegates to route.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0route.ps1" %*
exit /b %ERRORLEVEL%
