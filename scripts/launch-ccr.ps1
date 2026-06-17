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

$py = "python"
if (Get-Command python3 -ErrorAction SilentlyContinue) { $py = "python3" }

Write-Host "-> regenerating ccr config from Drive .secrets ..."
& $py scripts/gen-ccr-config.py
if ($LASTEXITCODE -ne 0) { Write-Error "config generation failed"; exit 1 }

Write-Host "-> starting Claude Code via ccr ..."
ccr code @args
