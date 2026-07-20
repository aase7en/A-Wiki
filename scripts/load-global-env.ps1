# ============================================================================
# load-global-env.ps1 - source the universal secrets from Drive into this
# PowerShell session. PowerShell port of load-global-env.sh (same resolution
# order, same file format, same override semantics).
# ============================================================================
# Cross-platform: resolves Drive path via the same chain as drive_path.py
# (env override -> drive/ link -> .drive-path file -> ~/.a-wiki-data fallback).
#
# Loads:
#   1. <drive>/secrets/global.env           (universal AI keys etc.)
#   2. <drive>/secrets/<Repo>.env  (if -Repo NAME given)  (repo-specific)
#
# Repo-specific values override global ones (loaded second).
# Idempotent: re-sourcing is safe.
#
# Usage:
#   . scripts\load-global-env.ps1
#   . scripts\load-global-env.ps1 -Repo env-wastewater-webapp
#   powershell -File scripts\load-global-env.ps1 -Print -Repo X
#
# Flags:
#   -Repo NAME   also load secrets/<NAME>.env after global.env
#   -Quiet       suppress the "loaded N keys" message
#   -Print       print KEY=VALUE lines instead of setting env vars (for
#                debugging, values still shown -- never pipe this to a
#                committable file)
#   -Help        show this help and exit
# ============================================================================
param(
    [string]$Repo = "",
    [switch]$Quiet,
    [switch]$Print,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
load-global-env.ps1 - source the universal secrets from Drive into this PowerShell session.

Usage:
  . scripts\load-global-env.ps1
  . scripts\load-global-env.ps1 -Repo env-wastewater-webapp

Flags:
  -Repo NAME   also load secrets/<NAME>.env after global.env
  -Quiet       suppress the "loaded N keys" message
  -Print       print KEY=VALUE lines instead of setting env vars
  -Help        show this help and exit
"@
    return
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

function Resolve-AWikiDriveRoot {
    if ($env:A_WIKI_DRIVE_PATH) {
        return $env:A_WIKI_DRIVE_PATH
    }
    $driveLink = Join-Path $RepoRoot "drive"
    if (Test-Path $driveLink) {
        try {
            $target = (Get-Item -Path $driveLink -Force).Target
            if ($target) {
                if ($target -is [array]) { $target = $target[0] }
                return $target
            }
        } catch {}
        return $driveLink
    }
    $drivePathFile = Join-Path $RepoRoot ".drive-path"
    if (Test-Path $drivePathFile) {
        $p = (Get-Content -Path $drivePathFile -TotalCount 1 -Encoding UTF8).Trim()
        if ($p) { return $p }
    }
    return (Join-Path $HOME ".a-wiki-data")
}

function Read-AWikiEnvFile([string]$Path) {
    $result = [ordered]@{}
    if (-not (Test-Path $Path)) { return $result }
    foreach ($rawLine in Get-Content -Path $Path -Encoding UTF8) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith('#') -or $line.StartsWith(';')) { continue }
        if ($line.StartsWith('export ')) { $line = $line.Substring(7).Trim() }
        $idx = $line.IndexOf('=')
        if ($idx -lt 0) { continue }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        if ($val.Length -ge 2 -and $val.StartsWith('"') -and $val.EndsWith('"')) {
            $val = $val.Substring(1, $val.Length - 2)
        } elseif ($val.Length -ge 2 -and $val.StartsWith("'") -and $val.EndsWith("'")) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        if ($key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { continue }
        $result[$key] = $val
    }
    return $result
}

$DriveRoot = Resolve-AWikiDriveRoot
$SecretsDir = Join-Path $DriveRoot "secrets"
$GlobalPath = Join-Path $SecretsDir "global.env"

$merged = [ordered]@{}
$globalCount = 0
$repoCount = 0

if (Test-Path $GlobalPath) {
    $g = Read-AWikiEnvFile $GlobalPath
    foreach ($k in $g.Keys) { $merged[$k] = $g[$k] }
    $globalCount = $g.Count
} elseif (-not $Quiet) {
    Write-Warning "load-global-env: $GlobalPath not found"
    Write-Warning "  Drive root resolved to: $DriveRoot"
    Write-Warning "  Set A_WIKI_DRIVE_PATH or fix A-Wiki/.drive-path"
}

if ($Repo) {
    $repoPath = Join-Path $SecretsDir "$Repo.env"
    if (Test-Path $repoPath) {
        $r = Read-AWikiEnvFile $repoPath
        foreach ($k in $r.Keys) { $merged[$k] = $r[$k] }
        $repoCount = $r.Count
    }
}

foreach ($k in $merged.Keys) {
    if ($Print) {
        Write-Output "$k=$($merged[$k])"
    } else {
        Set-Item -Path "env:$k" -Value $merged[$k]
    }
}

if (-not $Quiet -and -not $Print) {
    $msg = "load-global-env: $globalCount keys from global.env"
    if ($Repo) { $msg += " + $repoCount from $Repo.env" }
    $msg += " (drive: $DriveRoot)"
    Write-Host $msg
}
