# route.ps1 — PowerShell wrapper for A-Wiki universal ingest harness.
# Calls Python via py -3 (preferred on Windows) or python on PATH.

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$routePy = Join-Path $scriptDir 'route.py'

$py = Get-Command 'py' -ErrorAction SilentlyContinue
if ($py) {
    & py -3 $routePy @args
    exit $LASTEXITCODE
}

$python = Get-Command 'python' -ErrorAction SilentlyContinue
if ($python) {
    & python $routePy @args
    exit $LASTEXITCODE
}

$python3 = Get-Command 'python3' -ErrorAction SilentlyContinue
if ($python3) {
    & python3 $routePy @args
    exit $LASTEXITCODE
}

Write-Error 'python3, python, or py launcher required on PATH'
exit 127
