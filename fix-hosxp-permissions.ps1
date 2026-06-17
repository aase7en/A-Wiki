# HOSxPXE4 Permissions Fix Script
# แก้ปัญหา user aase7en ไม่สามารถเขียนไฟล์ configuration ได้

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "HOSxPXE4 Permissions Fix Script" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# ตัวแปร
$targetUser = "aase7en"
$configFiles = @()
$foundFolders = @()

# 1. ค้นหาไฟล์ Hos-WIM32.INI ทั้งหมดในเครื่อง
Write-Host "[1/4] ค้นหาไฟล์ Hos-WIM32.INI..." -ForegroundColor Yellow
$iniFiles = Get-ChildItem -Path "C:\" -Filter "Hos-WIM32.INI" -Recurse -ErrorAction SilentlyContinue -Force | Select-Object FullName, Length, LastWriteTime
if ($iniFiles) {
    Write-Host "✅ พบ $($iniFiles.Count) ไฟล์:" -ForegroundColor Green
    $iniFiles | ForEach-Object {
        Write-Host "   - $($_.FullName)" -ForegroundColor White
        $configFiles += $_.FullName
    }
} else {
    Write-Host "❌ ไม่พบไฟล์ Hos-WIM32.INI" -ForegroundColor Red
}

# 2. ค้นหาไฟล์ .INI ที่เกี่ยวกับ HOS ใน ProgramData
Write-Host "`n[2/4] ค้นหาไฟล์ .INI ใน ProgramData..." -ForegroundColor Yellow
$programDataIni = Get-ChildItem -Path "C:\ProgramData" -Filter "*.INI" -Recurse -ErrorAction SilentlyContinue -Force |
    Where-Object { $_.Name -like "*hos*" -or $_.Name -like "*HOS*" -or $_.Name -like "*Hos*" -or $_.Name -like "*bms*" -or $_.Name -like "*BMS*" } |
    Select-Object FullName, Length, LastWriteTime

if ($programDataIni) {
    Write-Host "✅ พบ $($programDataIni.Count) ไฟล์:" -ForegroundColor Green
    $programDataIni | ForEach-Object {
        Write-Host "   - $($_.FullName)" -ForegroundColor White
        $configFiles += $_.FullName
    }
} else {
    Write-Host "❌ ไม่พบไฟล์ .INI ที่เกี่ยวกับ HOS ใน ProgramData" -ForegroundColor Red
}

# 3. ค้นหาโฟลเดอร์ BMS/HOSxPXE4
Write-Host "`n[3/4] ค้นหาโฟลเดอร์ BMS/HOSxPXE4..." -ForegroundColor Yellow
$searchPaths = @(
    "C:\ProgramData",
    "C:\Program Files",
    "C:\Program Files (x86)",
    "C:\Users\Uthai2\AppData\Roaming",
    "C:\Users\Uthai2\AppData\Local",
    "C:\Users\aase7en\AppData\Roaming",
    "C:\Users\aase7en\AppData\Local"
)

$searchFolders = @("BMS", "HOSxPXE4", "HOSxP", "HOSxP_HD")

foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        foreach ($folder in $searchFolders) {
            $folders = Get-ChildItem -Path $path -Filter $folder -Directory -ErrorAction SilentlyContinue -Force
            if ($folders) {
                $folders | ForEach-Object {
                    $foundPath = $_.FullName
                    Write-Host "   - $foundPath" -ForegroundColor White
                    $foundFolders += $foundPath

                    # ค้นหาไฟล์ config ในโฟลเดอร์นี้
                    $subConfigs = Get-ChildItem -Path $foundPath -Recurse -ErrorAction SilentlyContinue -Force |
                        Where-Object { $_.Extension -in @('.INI', '.CFG', '.CONF', '.DAT') } |
                        Select-Object FullName, LastWriteTime, Length

                    if ($subConfigs) {
                        $subConfigs | ForEach-Object {
                            Write-Host "     ├─ $($_.Name)" -ForegroundColor Gray
                            $configFiles += $_.FullName
                        }
                    }
                }
            }
        }
    }
}

if ($foundFolders.Count -eq 0) {
    Write-Host "❌ ไม่พบโฟลเดอร์ BMS/HOSxPXE4" -ForegroundColor Red
} else {
    Write-Host "✅ พบ $($foundFolders.Count) โฟลเดอร์" -ForegroundColor Green
}

# 4. แก้ permissions
Write-Host "`n[4/4] แก้ permissions..." -ForegroundColor Yellow

$successCount = 0
$failCount = 0

# แก้ permissions ไฟล์ config
foreach ($file in $configFiles) {
    try {
        Write-Host "กำลังแก้: $file" -ForegroundColor Gray
        icacls $file /grant "${targetUser}:(W)" /T | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ แก้สำเร็จ" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ❌ แก้ไม่สำเร็จ (Exit code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ❌ แก้ไม่สำเร็จ: $_" -ForegroundColor Red
        $failCount++
    }
}

# แก้ permissions โฟลเดอร์
foreach ($folder in $foundFolders) {
    try {
        Write-Host "กำลังแก้: $folder" -ForegroundColor Gray
        icacls $folder /grant "${targetUser}:(OI)(CI)M" /T | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ แก้สำเร็จ" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ❌ แก้ไม่สำเร็จ (Exit code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ❌ แก้ไม่สำเร็จ: $_" -ForegroundColor Red
        $failCount++
    }
}

# สรุป
Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "สรุปผลการแก้ไข" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "แก้สำเร็จ: $successCount" -ForegroundColor Green
Write-Host "แก้ไม่สำเร็จ: $failCount" -ForegroundColor Red

# แสดง permissions สุดท้าย
Write-Host "`n--- Permissions สุดท้าย ---" -ForegroundColor Cyan
if ($configFiles.Count -gt 0) {
    Write-Host "ไฟล์ Config:" -ForegroundColor Yellow
    $configFiles | ForEach-Object {
        Write-Host "`n$_:" -ForegroundColor White
        icacls $_ | Select-String -Pattern $targetUser
    }
}

if ($foundFolders.Count -gt 0) {
    Write-Host "`nโฟลเดอร์:" -ForegroundColor Yellow
    $foundFolders | ForEach-Object {
        Write-Host "`n$_:" -ForegroundColor White
        icacls $_ | Select-String -Pattern $targetUser
    }
}

Write-Host "`n✅ เสร็จสิ้น! ลองเปิด HOSxPXE4 ในฐานะ user $targetUser ดูครับ" -ForegroundColor Green
Write-Host "`nหมายเหตุ: ถ้ายังไม่ได้ ให้แจ้ง error ที่เกิดขึ้นมาอีกทีครับ" -ForegroundColor Yellow