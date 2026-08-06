#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Register the awiki:// custom URL protocol so a click in the browser can
  launch the A-Wiki dashboard server (and the browser) on this machine.

.DESCRIPTION
  Browser security forbids a web page from starting a local process. The
  workaround is an OS-level custom protocol: the web page navigates to
  awiki://start, the OS resolves it to this launcher, which boots the
  dashboard server and opens the browser.

  Run ONCE per machine (per user — no admin needed because it writes only
  HKCU). After registration, the "เปิด Dashboard ตอนนี้" button on the
  offline overlay works from any browser.

.PARAMETER Uninstall
  Remove the protocol registration instead of adding it.

.EXAMPLE
  pwsh scripts/install-dashboard-protocol.ps1
  pwsh scripts/install-dashboard-protocol.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$repoRoot   = Split-Path -Parent $PSScriptRoot
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { $pythonCmd = Get-Command pythonw -ErrorAction SilentlyContinue }
$pythonExe = if ($pythonCmd) { $pythonCmd.Source } else { 'pythonw.exe' }
$serverPy   = Join-Path $repoRoot 'scripts\live-dashboard\server.py'
$launcherB  = Join-Path $repoRoot 'scripts\start-dashboard.bat'

if (-not (Test-Path $serverPy)) {
    Write-Error "server.py not found at: $serverPy"
    exit 1
}

# --- Build the launcher batch file (the protocol target) ---
# Uses single-quoted here-string so PowerShell does not interpolate, then
# substitutes __PYTHON__ and __SERVER__ placeholders. This avoids the -f
# format operator, which mis-parses batch-file braces and percent signs.
$launcherTemplate = @'
@echo off
setlocal
set "PYTHON=__PYTHON__"
set "SERVER=__SERVER__"
set "URL=http://localhost:7790/"

rem Boot server detached (pythonw = no console window)
start "" /B "%PYTHON%" "%SERVER%" --no-browser

rem Wait for the port to come up (max ~16 tries ~= 16s)
set /a tries=0
:waitloop
set /a tries+=1
powershell -NoProfile -Command "try{(Invoke-WebRequest -Uri '%URL%status' -UseBasicParsing -TimeoutSec 1 ^| Out-Null);exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 (
    if %tries% lss 16 (
        timeout /t 1 /nobreak >nul
        goto waitloop
    )
)

start "" "%URL%"
endlocal
'@
$launcherContent = $launcherTemplate.Replace('__PYTHON__', $pythonExe).Replace('__SERVER__', $serverPy)

Set-Content -Path $launcherB -Value $launcherContent -Encoding ASCII
Write-Host ('Launcher written: ' + $launcherB) -ForegroundColor Green

# --- Register or unregister the awiki:// protocol in HKCU ---
$protoKey = 'HKCU:\Software\Classes\awiki'

if ($Uninstall) {
    if (Test-Path $protoKey) {
        Remove-Item -Path $protoKey -Recurse -Force
        Write-Host 'Removed awiki:// protocol registration.' -ForegroundColor Yellow
    } else {
        Write-Host 'awiki:// not registered — nothing to remove.' -ForegroundColor DarkGray
    }
    exit 0
}

if (-not (Test-Path $protoKey)) {
    New-Item -Path $protoKey -Force | Out-Null
}
Set-ItemProperty -Path $protoKey -Name '(Default)' -Value 'URL:A-Wiki Dashboard'
Set-ItemProperty -Path $protoKey -Name 'URL Protocol' -Value '' -Type String

$cmdKey = Join-Path $protoKey 'shell\open\command'
if (-not (Test-Path $cmdKey)) {
    New-Item -Path $cmdKey -Force | Out-Null
}
# %1 will be replaced by the OS with the full awiki://... URL
$cmdValue = '"' + $launcherB + '"'
Set-ItemProperty -Path $cmdKey -Name '(Default)' -Value $cmdValue -Type ExpandString

Write-Host ''
Write-Host 'awiki:// protocol registered.' -ForegroundColor Green
Write-Host ('   Launcher: ' + $launcherB)
Write-Host ''
Write-Host 'Now clicking awiki://start from any browser will boot the dashboard.'
Write-Host 'Reload http://localhost:7790/ and click the new button on the'
Write-Host 'offline overlay, or type this in the browser address bar:'
Write-Host ''
Write-Host '    awiki://start' -ForegroundColor Cyan
Write-Host ''
Write-Host 'To remove:  pwsh scripts/install-dashboard-protocol.ps1 -Uninstall'
