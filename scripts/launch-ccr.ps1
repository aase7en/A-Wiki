# Launch Claude Code through claude-code-router (ccr) — multi-provider backend.
# Regenerates ~/.claude-code-router/config.json from Drive secrets, then `ccr code`.
#
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\launch-ccr.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command ccr -ErrorAction SilentlyContinue)) {
    Write-Error "'ccr' not found. Install:  npm i -g @musistudio/claude-code-router"
    exit 1
}

# Find a REAL Python (skip the Microsoft Store execution-alias stub under WindowsApps)
$py = $null
foreach ($c in @("py", "python3", "python")) {
    $g = Get-Command $c -ErrorAction SilentlyContinue
    if ($g -and $g.Source -notmatch 'WindowsApps') { $py = $g.Source; break }
}
if (-not $py) { Write-Error "No real Python found (only the Microsoft Store alias). Install from python.org, or turn off the 'python' App execution alias in Settings."; exit 1 }

Write-Host "-> regenerating ccr config from Drive .secrets ..."
& $py scripts/gen-ccr-config.py
if ($LASTEXITCODE -ne 0) { Write-Error "config generation failed"; exit 1 }

Write-Host "-> starting Claude Code via ccr ..."
ccr code @args
