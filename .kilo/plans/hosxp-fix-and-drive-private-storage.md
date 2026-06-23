# Plan: ย้าย fix-script ไป private drive + แก้ syntax + สร้างคู่มือ "อะไรเก็บใน drive" สำหรับ AI agents

## สถานการณ์ปัจจุบัน (จากการสำรวจ)

| ข้อ | สถานะ |
|-----|-------|
| `fix-hosxp-permissions.ps1` / `.bat` | อยู่ที่ **root ของ repo public** (`A:\GitHub\A-Wiki\`) |
| `.gitignore` | **ไม่** ignore ไฟล์ทั้งสอง → ถ้า `git add` จะถูก commit เข้า public repo (อันตราย) |
| `drive/` | เป็น Junction → `L:\My Drive\A-Wiki-Data` ✅ (ใช้งานได้) |
| `.drive-path` | **ไม่มี** บนเครื่องนี้ (gitignore รองรับแต่ยังไม่สร้าง) |
| `drive/private-tools/` | มีอยู่ (เก็บ `shopee-buyer-assistant/` ฯลฯ) — pattern: 1 tool = 1 subfolder |
| `drive/personal-tools/scripts/` | มีอยู่ |
| `wiki/context/session-memory.md` | เป็น stub 1 บรรทัดชี้ Mac path เก่า และ **ถูก git track** (ไม่เหมาะใส่ path เครื่องนี้) |

## Root cause ของ PowerShell syntax error (วิเคราะห์แล้วชัดเจน)

1. **Encoding**: Write tool บันทึกเป็น UTF-8 *without BOM*; PowerShell 5.1 อ่านเป็น ANSI (cp874 ไทย) → อักขระ box-drawing `├─` (byte `0x94` ใน UTF-8) ถูกอ่านเป็น `"` → ปิด double-quoted string กลางอากาศ → cascade "Unexpected token `}`" ที่บรรทัด 77-81 + 84/85 (emoji ✅❌ ก็พัง)
2. **`"`n$_:"` (บรรทัด 143, 151)**: PowerShell อ่าน `$_:` เป็น scope variable → "Variable reference is not valid"

→ **แก้โดย**: เขียนใหม่เป็น ASCII-only (message ภาษาอังกฤษ ละ avoid emoji/box-drawing), แก้ `$_:` → `${_}:`, save เป็น **UTF-8 with BOM** (ป้องกัน cp874 mojibake)

---

## งานที่จะทำ (3 ส่วน)

### ส่วน A — ย้าย script ไป private drive + แก้ syntax + ลบจาก repo root

**ปลายทาง** (ตามที่เลือก): `L:\My Drive\A-Wiki-Data\uthai-hospital\hosxp\`
- เหตุผล: จัดเป็นงานด้านโรงพยาบาล (HOSxP) — `uthai-hospital/` มีอยู่แล้ว (`env-evaluations/` ฯลฯ)
- อ้างผ่าน repo: `drive/uthai-hospital/hosxp/`

ขั้นตอน:
1. สร้างโฟลเดอร์ `drive\uthai-hospital\hosxp\` (ผ่าน junction หรือ path L: ตรงๆ)
2. เขียน `fix-hosxp-permissions.ps1` ใหม่ที่นั่น — เวอร์ชัน **ASCII-only + UTF-8 BOM + แก้ `$_:` bug**, เนื้อหาเดิม (ค้นหา Hos-WIM32.INI → grant write/modify ให้ $USER)
3. เขียน `run-as-admin.bat` ที่นั่น — ใช้ `%~dp0` อ้างตัวเอง รัน ps1 แบบ `-ExecutionPolicy Bypass`
4. **ลบ** `A:\GitHub\A-Wiki\fix-hosxp-permissions.ps1` และ `.bat` ออกจาก repo root (ยังไม่ได้ commit อยู่แล้ว → ลบได้สบาย)

### ส่วน B — บันทึก machine path ของเครื่องนี้

1. สร้าง `A:\GitHub\A-Wiki\.drive-path` ใส่เนื้อหา:
   ```
   L:\My Drive\A-Wiki-Data
   ```
   - gitignore รองรับ `.drive-path` อยู่แล้ว → private, ไม่ขึ้น public
   - ทำให้ script/agent รู้ drive resolution ของเครื่องนี้โดยไม่ hardcode

### ส่วน C — คู่มือ "อะไรควรเก็บใน drive" สำหรับ AI ทุกตัว

วางที่ **2 ที่** (ตามที่เลือก — ได้รับอนุญาตแก้ AGENTS.md แล้วตาม Iron Law #5):

#### C1. `drive/README.md` (private, gitignored) — ฉบับเต็ม + path เครื่องนี้
- **Path resolution ของเครื่องนี้**: `L:\My Drive\A-Wiki-Data` (= repo `drive/` junction)
- **ตาราง "อะไรเก็บที่ไหน"** (ขยายจากตาราง AGENTS.md External Data Layer):
  | เก็บใน drive (private) | เก็บใน repo (public) |
  |---|---|
  | script/IT-fix ส่วนตัว, secrets, raw files, journal ส่วนตัว, DB หนัก, ข้อมูลลูกค้า/คนไข้ | wiki knowledge, protocol docs, ADR, hook/skill สาธารณะ, `.example` template |
- **กฎตัดสินใจสำหรับ agent** (decision rule):
  - มี personal data / secret / ข้อมูลคนไข้ / path เครื่องเฉพาะ → **drive** (gitignored)
  - เป็นความรู้/rule ที่ใช้ร่วมข้ามเครื่อง → **repo** (public)
  - ไม่แน่ใจ → ใส่ใน drive ก่อน (ปลอดภัยกว่า)
- แมป subfolder ที่มี: `raw/` `personal/` `personal-tools/` `private-tools/` `uthai-hospital/` `individual-tasks/` `.secrets/` `batch-state/`

#### C2. แก้ `AGENTS.md` (public) — เพิ่มส่วน "Storage Decision Rule" แบบ public-safe
- วางใต้ส่วน "## 🗄️ External Data Layer" ที่มีอยู่
- เน้น: **abstract rules เท่านั้น** ห้าม hardcode path `L:\...` (public-safe + cross-device policy)
- เนื้อหาที่จะเพิ่ม:
  - กฎ "Drive vs Repo" decision checklist (3 ข้อเดียวกับ C1)
  - เตือน: ห้ามเขียน path เครื่องเฉพาะ / personal artifact / IT-fix ส่วนตัว ลง repo โดยตรง — ใช้ `drive/` (junction) หรือ `A_WIKI_DRIVE_PATH`
  - ชี้ไป `drive/README.md` (private) สำหรับรายละเอียด path แต่ละเครื่อง + แมป subfolder
- รักษาโทน/มาร์กดาวน์ให้กลมกลืนกับส่วนที่มี

### ส่วน D — วิธีรันหลังย้าย

```
1. เข้าโฟลเดอร์:  L:\My Drive\A-Wiki-Data\uthai-hospital\hosxp\
2. คลิกขวา run-as-admin.bat → Run as administrator
   (หรือ: powershell -ExecutionPolicy Bypass -File "<path>\fix-hosxp-permissions.ps1")
3. Log out → login เป็น $USER → เปิด HOSxPXE4 ตามปกติ (ไม่ต้อง admin)
```

---

## ผลลัพธ์ที่คาดหวัง

- ไฟล์ IT-fix **ไม่ตกไปใน public repo** อีก (อยู่ใน `drive/uthai-hospital/hosxp/`)
- `.ps1` รันได้จริง (ไม่มี syntax error แล้ว)
- AI ทุก platform ที่เข้า drive/ จะเจอ `README.md` → รู้ path + กฎการจัดเก็บ
- AI ทุก platform อ่าน `AGENTS.md` → เห็น Storage Decision Rule (public-safe, ไม่มี path เครื่องเฉพาะ)
- `.drive-path` บอกตำแหน่ง drive ของเครื่องนี้โดยไม่ hardcode

## การตรวจทาน

- `git -C A:\GitHub\A-Wiki status` ยืนยันว่าไม่มี fix-hosxp-* ค้างอยู่ และมีแค่ AGENTS.md ที่เปลี่ยน
- `git -C A:\GitHub\A-Wiki check-ignore .drive-path drive/README.md drive/uthai-hospital/hosxp/` คืนค่า (ignored = private แน่นอน)
- รัน `.bat` จริง → ไม่มี ParseException → แสดงผล permission

## ข้อยืนยัน Iron Law

- **Iron Law #5 (ห้ามแก้ AGENTS.md โดยไม่ได้รับอนุญาต)**: ✅ ได้รับอนุญาตจาก user แล้วในแพลนนี้
- **Public-safe policy**: ส่วนที่เพิ่มใน AGENTS.md เป็น abstract rule เท่านั้น — **ห้าม** ใส่ path `L:\My Drive\A-Wiki-Data` หรือ personal data ลงใน AGENTS.md (ไปไว้ใน `.drive-path` + `drive/README.md` ที่เป็น private)
