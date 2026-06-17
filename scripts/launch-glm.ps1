# Launch Claude Code on Z.ai GLM Coding Plan (subscription) — direct, no ccr.
# Points the Anthropic-compatible endpoint at Z.ai with the coding-plan key.
# Use this to run GLM instead of Opus (saves Anthropic quota).
#
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\launch-glm.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$py = "python"
if (Get-Command python3 -ErrorAction SilentlyContinue) { $py = "python3" }

$key = (& $py scripts/lib/drive_secrets.py ZHIPU_API_KEY).Trim()
if (-not $key) { Write-Error "ZHIPU_API_KEY not found in drive/.secrets"; exit 1 }

$env:ANTHROPIC_BASE_URL   = "https://api.z.ai/api/anthropic"
$env:ANTHROPIC_AUTH_TOKEN = $key
$env:ANTHROPIC_API_KEY    = $null   # avoid conflict with a logged-in Anthropic key
# Z.ai GLM Coding Plan official model mapping. Supported: GLM-5.2, GLM-5-Turbo,
# GLM-4.7, GLM-4.5-Air. Switch OPUS->GLM-5.2 for complex tasks (rivals Opus;
# costs 2-3x quota at peak 14:00-18:00 UTC+8). Defaults below = routine/cheap.
$env:ANTHROPIC_DEFAULT_OPUS_MODEL   = "GLM-4.7"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL = "GLM-4.7"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL  = "GLM-4.5-Air"

Write-Host "-> launching Claude Code on Z.ai GLM (subscription) ..."
claude @args
