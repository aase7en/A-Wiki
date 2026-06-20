# Hermes Auto-Sync — Windows PowerShell
# Run via Task Scheduler every 6 hours
# Usage: powershell -ExecutionPolicy Bypass -File auto-sync.ps1

$ErrorActionPreference = "Stop"
$RepoDir = "$env:USERPROFILE\A-Wiki"
$ExportPattern = "scripts\hermes\hermes-export-*.tar.gz"
$Profile = "tech_and_ai_architect"
$LockFile = "$env:TEMP\hermes-auto-sync.lock"
$LastImportFile = "$env:TEMP\hermes-last-import.txt"

# Prevent overlapping runs
if (Test-Path $LockFile) { Write-Host "Already running. Skipping."; exit 0 }
New-Item -ItemType File -Path $LockFile -Force | Out-Null

try {
    Write-Host "=== $(Get-Date): Hermes Auto-Sync (Windows) ==="

    # Step 1: Pull latest from GitHub
    Set-Location $RepoDir
    $before = git rev-parse HEAD
    git pull --ff-only
    $after = git rev-parse HEAD

    if ($before -eq $after) {
        Write-Host "No new commits."
        exit 0
    }

    Write-Host "New: $($before.Substring(0,7)) -> $($after.Substring(0,7))"

    # Step 2: Find latest export
    $latest = Get-ChildItem $ExportPattern | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { Write-Host "No export package found."; exit 0 }

    # Step 3: Check if already imported
    $pkgTime = $latest.LastWriteTime.ToFileTime()
    $lastTime = if (Test-Path $LastImportFile) { [int64](Get-Content $LastImportFile) } else { 0 }
    if ($pkgTime -le $lastTime) { Write-Host "Already imported."; exit 0 }

    # Step 4: Import profile
    Write-Host "Importing $($latest.Name)..."
    hermes profile import $latest.FullName

    # Step 5: Fix paths
    hermes -p $Profile config set terminal.cwd $RepoDir

    # Step 6: Record
    $pkgTime | Out-File -FilePath $LastImportFile
    Write-Host "=== Done ==="
}
finally {
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
}
