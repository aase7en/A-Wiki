# ============================================================================
# setup-ide-env.ps1 - make every PowerShell session (incl. IDE-embedded) auto-
# source the global env from Drive. PowerShell port of setup-ide-env.sh.
# ============================================================================
# Strategy: inject ONE dot-source line into $PROFILE.CurrentUserAllHosts -
# the "all hosts" profile loaded by every PowerShell host for this user
# (console, ISE, VS Code's integrated terminal), mirroring how the bash
# version reaches every bash instance via .bashrc/.zshrc.
#
# The injected line is idempotent and guarded (try/catch) so it only sources
# when the loader exists and never breaks profile startup; safe to re-run.
#
# Usage:
#   powershell -File scripts\setup-ide-env.ps1              # inject (default)
#   powershell -File scripts\setup-ide-env.ps1 -Status      # show what's injected
#   powershell -File scripts\setup-ide-env.ps1 -Remove      # take the hook back out
#
# -ProfilePathOverride (or $env:A_WIKI_PROFILE_OVERRIDE) points the hook at a
# different profile file - used by tests so real user profiles are untouched.
# ============================================================================
param(
    [switch]$Status,
    [switch]$Remove,
    [switch]$Help,
    [string]$ProfilePathOverride = $env:A_WIKI_PROFILE_OVERRIDE
)

if ($Help) {
    Write-Host @"
setup-ide-env.ps1 - auto-source A-Wiki secrets/global.env into every PowerShell session.

Usage:
  powershell -File scripts\setup-ide-env.ps1              # inject (default)
  powershell -File scripts\setup-ide-env.ps1 -Status      # show status
  powershell -File scripts\setup-ide-env.ps1 -Remove      # remove the hook
"@
    return
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Loader = Join-Path $ScriptDir "load-global-env.ps1"

$MarkBegin = "# >>> A-Wiki global env (setup-ide-env.ps1) >>>"
$MarkEnd = "# <<< A-Wiki global env <<<"

$TargetProfile = if ($ProfilePathOverride) { $ProfilePathOverride } else { $PROFILE.CurrentUserAllHosts }

function Test-AWikiBlockPresent([string]$Path) {
    if (-not (Test-Path $Path)) { return $false }
    return [bool](Select-String -Path $Path -Pattern $MarkBegin -SimpleMatch -Quiet)
}

if ($Status) {
    Write-Host "IDE env hook status"
    $loaderStatus = if (Test-Path $Loader) { "present" } else { "MISSING" }
    Write-Host "  loader: $Loader ($loaderStatus)"
    Write-Host ""
    if (-not (Test-Path $TargetProfile)) {
        Write-Host "  [ -- ] $TargetProfile (not present)"
    } elseif (Test-AWikiBlockPresent $TargetProfile) {
        Write-Host "  [OK] $TargetProfile (hook injected)"
    } else {
        Write-Host "  [ -- ] $TargetProfile (no hook)"
    }
    return
}

if ($Remove) {
    if (-not (Test-Path $TargetProfile) -or -not (Test-AWikiBlockPresent $TargetProfile)) {
        Write-Host "No hook found in $TargetProfile."
        return
    }
    $lines = Get-Content -Path $TargetProfile -Encoding UTF8
    $out = New-Object System.Collections.Generic.List[string]
    $skip = $false
    foreach ($line in $lines) {
        if ($line -eq $MarkBegin) { $skip = $true; continue }
        if ($line -eq $MarkEnd) { $skip = $false; continue }
        if (-not $skip) { $out.Add($line) }
    }
    Set-Content -Path $TargetProfile -Value $out -Encoding UTF8
    Write-Host "Removed hook from $TargetProfile"
    return
}

# Default mode: inject.
if (-not (Test-Path $Loader)) {
    Write-Error "ERROR - loader not found at $Loader"
    return
}
$profileDir = Split-Path -Parent $TargetProfile
try {
    if ($profileDir -and -not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Force -Path $profileDir -ErrorAction Stop | Out-Null
    }
    if (-not (Test-Path $TargetProfile)) {
        New-Item -ItemType File -Path $TargetProfile -ErrorAction Stop | Out-Null
    }
} catch {
    Write-Error "ERROR - could not create profile path $TargetProfile : $_"
    return
}
if (Test-AWikiBlockPresent $TargetProfile) {
    Write-Host "Already injected in $TargetProfile -- nothing to do."
    return
}
$hookLine = "try { . `"$Loader`" -Quiet } catch { }"
$block = @(
    ""
    $MarkBegin
    "# Auto-source A-Wiki secrets/global.env (+ <repo>.env) into every"
    "# PowerShell session, including IDE-embedded (VS Code). Safe to"
    "# remove; re-run setup-ide-env.ps1 to restore."
    $hookLine
    $MarkEnd
)
try {
    Add-Content -Path $TargetProfile -Value $block -Encoding UTF8 -ErrorAction Stop
} catch {
    Write-Error "ERROR - could not write to $TargetProfile : $_"
    return
}
Write-Host "Injected hook into $TargetProfile"
Write-Host "Open a new PowerShell window (or dot-source `$PROFILE) to pick up global env."
