<#
.SYNOPSIS
    Diagnose and repair the Windows "User Profile Service service failed the
    sign-in / User profile cannot be loaded" error.

.DESCRIPTION
    The error means Windows authenticated the user (PIN/password OK) but failed
    to LOAD the user profile. The most common cause is a corrupted ProfileList
    registry key (a duplicate <SID>.bak, or wrong State/RefCount/ProfileImagePath).

    DIAGNOSE mode (default) is read-only: it dumps ProfileList, recent User
    Profile Service events, disk health, and domain status, then prints
    recommended actions. REPAIR mode (-Repair) backs up the ProfileList subtree
    to a .reg file, then fixes the common .bak case and resets State/RefCount.

    Companion runbook:
      wiki/concepts/it-support/windows-user-profile-service-failed-signin.md

.PARAMETER User
    Target user (SamAccountName). Defaults to the current user. Used only to
    locate the right SID via ProfileImagePath = C:\Users\<User>.

.PARAMETER Repair
    Perform the registry repair (requires Administrator). Without this switch
    the script only diagnoses.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\batch\fix-user-profile-service.ps1
    # Diagnose the current user (read-only)

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\batch\fix-user-profile-service.ps1 -User aase7en -Repair
    # Back up ProfileList, then repair the profile for user 'aase7en'

.NOTES
    ALWAYS runs a registry backup before any change. Conservative: ambiguous
    cases print manual steps instead of guessing. Run as Administrator for -Repair.
    If you cannot sign in at all, boot Safe Mode or use another admin account.
#>

[CmdletBinding()]
param(
    [string]$User = $env:USERNAME,
    [switch]$Repair
)

$ErrorActionPreference = 'Stop'
$ProfileListPath = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'
$ProfileListReg  = 'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'
$TargetPath      = Join-Path 'C:\Users' $User

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ProfileEntries {
    Get-ChildItem $ProfileListPath | ForEach-Object {
        $p = Get-ItemProperty $_.PSPath
        [pscustomobject]@{
            SID   = $_.PSChildName
            Path  = $p.ProfileImagePath
            State = $p.State
            Ref   = $p.RefCount
            Bak   = $_.PSChildName.EndsWith('.bak')
            Key   = $_.PSPath
        }
    }
}

Write-Host "=== User Profile Service repair tool ===" -ForegroundColor Cyan
Write-Host "Target user : $User"
Write-Host "Profile path: $TargetPath"
Write-Host "Admin       : $(Test-Admin)"
Write-Host ""

# ---------------------------------------------------------------- DIAGNOSE ----
Write-Host "--- ProfileList entries ---" -ForegroundColor Yellow
$entries = Get-ProfileEntries
$entries | Format-Table SID, Path, State, Ref, Bak -AutoSize

# Entries that point at this user's folder (matching <SID> and/or <SID>.bak)
$mine = $entries | Where-Object { $_.Path -eq $TargetPath }
if (-not $mine) {
    Write-Warning "No ProfileList entry has ProfileImagePath = $TargetPath."
    Write-Host   "  -> Check the 'Path' column above; the real SID may point elsewhere,"
    Write-Host   "     or the profile folder name differs from the username."
}

Write-Host "`n--- Recent User Profile Service events (1500/1511/1515/1530/1542) ---" -ForegroundColor Yellow
try {
    Get-WinEvent -FilterHashtable @{
        LogName      = 'Application'
        ProviderName = 'Microsoft-Windows-User Profiles Service'
    } -MaxEvents 15 -ErrorAction Stop |
        Select-Object TimeCreated, Id, LevelDisplayName,
            @{N='Msg';E={ ($_.Message -split "`r?`n")[0] }} |
        Format-Table -AutoSize
} catch {
    Write-Host "  (no matching events, or insufficient rights to read them)"
}

Write-Host "`n--- Disk health (corrupt NTUSER.DAT often comes from a failing/dirty disk) ---" -ForegroundColor Yellow
try {
    Get-PhysicalDisk | Get-StorageReliabilityCounter -ErrorAction Stop |
        Select-Object DeviceId, Wear, ReadErrorsTotal, WriteErrorsTotal |
        Format-Table -AutoSize
} catch {
    Write-Host "  (StorageReliabilityCounter unavailable; run 'chkdsk C: /scan' manually)"
}

Write-Host "`n--- Domain / Azure AD join status ---" -ForegroundColor Yellow
try { (dsregcmd /status | Select-String 'DomainJoined|AzureAdJoined|WorkplaceJoined') -join "`n" }
catch { Write-Host "  (dsregcmd unavailable)" }

# Decide the situation for this user's SID
$bak    = $mine | Where-Object { $_.Bak }
$plain  = $mine | Where-Object { -not $_.Bak }

Write-Host "`n--- Recommendation ---" -ForegroundColor Green
if ($mine.Count -eq 0) {
    Write-Host "Cannot locate this user's SID by path. Inspect the table above and the"
    Write-Host "runbook before touching the registry."
} elseif ($bak -and $plain) {
    Write-Host "Found BOTH <SID> and <SID>.bak -> classic corruption."
    Write-Host "Fix: rename the non-.bak key aside, drop '.bak' from the backup key,"
    Write-Host "then set State=0 and RefCount=0 on it."
} elseif ($bak -and -not $plain) {
    Write-Host "Found only <SID>.bak -> drop '.bak' and set State=0, RefCount=0."
} elseif ($plain -and ($plain.State -ne 0 -or $plain.Ref -ne 0)) {
    Write-Host "Single key but State=$($plain.State) RefCount=$($plain.Ref)."
    Write-Host "Fix: set both to 0. If error persists, suspect NTUSER.DAT/permissions."
} else {
    Write-Host "ProfileList looks normal for this user. Likely NTUSER.DAT corruption,"
    Write-Host "folder ACLs, or a domain/GPO policy. See the runbook 'prevent recurrence'."
}

if (-not $Repair) {
    Write-Host "`n(Read-only diagnose. Re-run with -Repair as Administrator to apply the registry fix.)" -ForegroundColor Cyan
    return
}

# ------------------------------------------------------------------ REPAIR ----
if (-not (Test-Admin)) {
    Write-Error "Repair requires Administrator. Right-click PowerShell -> Run as administrator."
    return
}

# Backup first — always
$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path ([Environment]::GetFolderPath('Desktop')) "ProfileList-backup-$stamp.reg"
Write-Host "`nBacking up ProfileList -> $backup" -ForegroundColor Yellow
reg export $ProfileListReg $backup /y | Out-Null

if (-not $mine) {
    Write-Error "No SID matches $TargetPath. Aborting repair (nothing safe to do automatically)."
    return
}

if ($bak -and $plain) {
    # Park the broken (temp) non-.bak key, then promote the .bak key
    $parked = "$($plain.SID).corrupt-$stamp"
    Write-Host "Renaming temp key $($plain.SID) -> $parked" -ForegroundColor Yellow
    Rename-Item -Path $plain.Key -NewName $parked
    Write-Host "Promoting $($bak.SID) -> $($plain.SID)" -ForegroundColor Yellow
    Rename-Item -Path $bak.Key -NewName $plain.SID
    $fixKey = Join-Path $ProfileListPath $plain.SID
} elseif ($bak -and -not $plain) {
    $newName = $bak.SID.Substring(0, $bak.SID.Length - 4)   # strip ".bak"
    Write-Host "Renaming $($bak.SID) -> $newName" -ForegroundColor Yellow
    Rename-Item -Path $bak.Key -NewName $newName
    $fixKey = Join-Path $ProfileListPath $newName
} elseif ($plain) {
    $fixKey = $plain.Key
} else {
    Write-Error "Unexpected state. Inspect manually using the runbook."
    return
}

Write-Host "Setting State=0, RefCount=0 on $fixKey" -ForegroundColor Yellow
New-ItemProperty -Path $fixKey -Name 'State'    -PropertyType DWord -Value 0 -Force | Out-Null
New-ItemProperty -Path $fixKey -Name 'RefCount' -PropertyType DWord -Value 0 -Force | Out-Null

$final = Get-ItemProperty $fixKey
Write-Host "`n--- Result ---" -ForegroundColor Green
Write-Host "ProfileImagePath: $($final.ProfileImagePath)"
Write-Host "State           : $($final.State)"
Write-Host "RefCount        : $($final.RefCount)"
if ($final.ProfileImagePath -ne $TargetPath) {
    Write-Warning "ProfileImagePath != $TargetPath. Verify it points to the correct folder."
}
Write-Host "`nDone. RESTART the PC and sign in again." -ForegroundColor Cyan
Write-Host "If it returns tomorrow, the root cause is disk/shutdown/GPO — see 'prevent recurrence' in the runbook."
