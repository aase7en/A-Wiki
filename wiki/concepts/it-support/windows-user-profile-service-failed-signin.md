---
type: concept
category: it-support
tags: [windows, user-profile, login, profilelist, registry, troubleshooting]
created: 2026-06-16
updated: 2026-06-16
---

# Windows — "User Profile Service failed the sign-in" (login profile โหลดไม่ขึ้น)

**ระบบปฏิบัติการ**: Windows 10 / 11
**ขอบเขต**: local + domain account
**ความเชื่อมั่น**: [training] — root cause + วิธีแก้เป็นแนวทางมาตรฐานของ Windows; ยืนยันตัวจริงด้วยขั้น "วินิจฉัย" บนเครื่อง

---

## อาการ

- ใส่ **PIN / รหัสผ่านถูกต้อง** แต่ขึ้น error:
  > The User Profile Service service failed the sign-in.
  > User profile cannot be loaded.
- เด้งกลับหน้า lock screen หรือเข้าได้แค่ profile ชั่วคราว (Temp)
- **เกิดทุกครั้งที่ start Windows** (ทุกวัน) — ไม่ใช่ครั้งเดียวจบ

> สำคัญ: PIN ผ่านแล้ว = **ไม่ใช่ปัญหา authentication** แต่เป็นขั้น "โหลด user profile" ที่ล้มเหลว

---

## สาเหตุ (เรียงตามโอกาสพบ)

1. **`ProfileList` registry เสีย (พบบ่อยสุด)**
   ที่ `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList`:
   - มี key ของ SID ซ้ำเป็น `<SID>` + `<SID>.bak` → Windows โหลดตัวผิด
   - `State` หรือ `RefCount` ไม่เป็น 0
   - `ProfileImagePath` ชี้ path ผิด (ไม่ใช่ `C:\Users\<user>`)
2. **`NTUSER.DAT` เสีย/ถูกล็อก** ใน `C:\Users\<user>\NTUSER.DAT` — มัก trigger จาก disk error หรือ shutdown ไม่สมบูรณ์ (ไฟดับ/กดปิดค้าง) → **อธิบายว่าทำไมเป็นทุกวัน**
3. **สิทธิ์ (ACL) บนโฟลเดอร์ profile ผิด** — SYSTEM / Administrators / ตัว user ต้องมีสิทธิ์ถูกต้อง
4. **เครื่อง domain ของบริษัท** — roaming profile sync ล้มเหลว หรือ GPO `Delete cached copies of roaming profiles` ลบ cache ทุก logoff → กลับมาเป็นซ้ำทุกวัน (registry edit ฝั่ง client จะถูก policy ทับ)

> ถ้า "เป็นทุกวัน" หลังเคยแก้แล้ว → โฟกัสสาเหตุ #2 (ดิสก์/shutdown) หรือ #4 (domain/GPO) เป็นหลัก

---

## วินิจฉัย (ก่อนแก้ — debug-mantra: หา root cause ก่อน)

รันใน **PowerShell (Run as administrator)** บน account ที่เข้าได้ (หรือ admin อื่น / Safe Mode):

```powershell
# 1) SID ของ user ปัจจุบัน
whoami /user

# 2) ดูทุก entry ใน ProfileList: SID, path, State, RefCount, ธง .bak
$pl = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'
Get-ChildItem $pl | ForEach-Object {
    $p = Get-ItemProperty $_.PSPath
    [pscustomobject]@{
        SID   = $_.PSChildName
        Path  = $p.ProfileImagePath
        State = $p.State
        Ref   = $p.RefCount
        Bak   = $_.PSChildName.EndsWith('.bak')
    }
} | Format-Table -Auto

# 3) Event log ของ User Profile Service (ดู ID 1500/1511/1515/1530/1542)
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Microsoft-Windows-User Profiles Service'} -MaxEvents 20 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-List

# 4) สุขภาพดิสก์ (สาเหตุ NTUSER.DAT เสียซ้ำ)
chkdsk C: /scan
Get-PhysicalDisk | Get-StorageReliabilityCounter | Select DeviceId, Wear, ReadErrorsTotal, WriteErrorsTotal

# 5) เครื่องนี้เป็น domain / Azure AD joined ไหม
dsregcmd /status
systeminfo | findstr /B /C:"Domain"
```

**ความหมาย Event ID**: `1511` = ล็อกอินด้วย temp profile · `1515` = ใช้ temp หลัง backup · `1500/1542` = โหลด profile ไม่ได้ · `1530` = registry hive ยังถูก process อื่นถือ (มัก = NTUSER.DAT ไม่ถูก unload ตอน logoff)

> มีสคริปต์ช่วย: `scripts/batch/fix-user-profile-service.ps1` (โหมด diagnose เป็น default)

---

## วิธีแก้ถาวร — ซ่อม ProfileList registry

> ⚠️ **Backup registry ก่อนเสมอ** และทำเป็น **admin**. ถ้าเข้า account ไม่ได้เลย → boot **Safe Mode** (กด Shift ค้างตอน Restart → Troubleshoot → Advanced → Startup Settings → Safe Mode) หรือใช้ **admin account อื่น** / เปิด built-in Administrator

```powershell
# Backup ทั้ง subtree ProfileList ก่อนแตะ
reg export "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" "$env:USERPROFILE\Desktop\ProfileList-backup.reg" /y
```

หา SID ของ user (จาก `ProfileImagePath = C:\Users\<user>`) แล้ว:

1. **มี 2 key — `<SID>` และ `<SID>.bak`**
   - key ที่ **ไม่มี** `.bak` = ตัว temp/เสีย → เปลี่ยนชื่อเติม `.ba` (เก็บไว้ชั่วคราว)
   - key `<SID>.bak` → ลบ `.bak` ออกให้เหลือ `<SID>` ล้วน (ตัวนี้คือ profile จริง)
2. **มี key `.bak` อันเดียว** → ลบ `.bak` ออกให้เหลือ `<SID>` ล้วน
3. บน key `<SID>` ที่ถูกต้อง ตั้งค่า (DWORD):
   - `RefCount` = `0`
   - `State` = `0`
   - ยืนยัน `ProfileImagePath` = `C:\Users\<user>` (ไม่มี `.bak`/เลขต่อท้าย)
4. **Restart** แล้ว login ใหม่

> ทำผ่าน `regedit` ด้วยมือก็ได้ หรือใช้ `scripts/batch/fix-user-profile-service.ps1 -Repair` (จะ backup + จัดการเคส `.bak` ที่พบบ่อยให้)

---

## ป้องกันไม่ให้กลับมา (ส่วน "ถาวร" จริง)

แก้ registry อย่างเดียวไม่พอถ้า root cause คือดิสก์/shutdown/policy — ทำเพิ่ม:

```powershell
sfc /scannow
DISM /Online /Cleanup-Image /RestoreHealth
chkdsk C: /f          # ขอ schedule รอบ reboot ถ้าถาม Y
```

- **ดิสก์ใกล้พัง** (SMART Wear สูง / มี error) → สำรองข้อมูล + เปลี่ยน SSD
- **ปิดเครื่องให้ถูกวิธี** — เลี่ยงกดปิดค้าง/ไฟดับ; ปิด **Fast Startup** ถ้า hive ค้างบ่อย
  (Control Panel → Power Options → Choose what the power buttons do → ปลด "Turn on fast startup")
- ตรวจ **antivirus / Storage Sense / scheduled task** ที่อาจลบหรือล็อก profile
- **เครื่อง domain บริษัท** → registry edit จะถูก GPO ทับ ⇒ **แจ้ง IT** ให้ตรวจ roaming profile / folder redirection / GPO `Delete cached copies of roaming profiles`

---

## ถ้าซ่อม registry แล้วยังไม่หาย

1. สร้าง **local account ใหม่** (admin): Settings → Accounts → Other users → Add account
2. login เข้า account ใหม่ 1 ครั้งให้สร้าง profile
3. copy ข้อมูลจาก `C:\Users\<old>` → `C:\Users\<new>` (ยกเว้นไฟล์ระบบ `NTUSER.DAT*`, `AppData\Local\Temp`)
4. ตั้ง account ใหม่เป็นตัวหลัก แล้วค่อยลบ profile เก่าหลังยืนยันว่าข้อมูลครบ

---

## หมายเหตุ (public-safe)

- ใช้ placeholder `<user>` / `<SID>` ในเอกสาร — สคริปต์ auto-detect SID เอง ไม่ hardcode ชื่อ user
- ทุกขั้นที่แตะ registry/disk ต้องเป็น **admin** + **backup ก่อน**
- คอมที่ทำงานที่ถูก IT จัดการ อาจต้องให้ IT ดำเนินการ (ห้ามฝืน policy องค์กร)

---

## ความสัมพันธ์

- IT troubleshooting ในที่ทำงาน — ดู index รวม `[[index-it]]`
- สคริปต์ช่วย: `scripts/batch/fix-user-profile-service.ps1`
