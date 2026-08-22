# Getting Started — คู่มือใช้งานสมองที่สอง A-Wiki (User Guide)

> ฉบับผู้ใช้ ไม่ต้องเป็นโปรแกรมเมอร์ · สำหรับผู้ดูแลระบบ/developer ดู `AGENTS.md` และ `docs/runbooks/review-bus.md`

**หลักการเดียวที่ต้องจำ: พิมพ์ *สิ่งที่อยากให้เกิด* สมองหาวิธีเอง** — มีแค่ 2 ทางเข้า: `/A <objective>` สำหรับงานทั่วไป และปุ่มเฉพาะ 12 ตัวสำหรับงานเฉพาะตัวของคุณ

---

## 1. ติดตั้ง (ครั้งแรกต่อเครื่อง)

### ทางที่ 1 — Git clone (แนะนำ เหมาะกับใช้งานจริง)

```bash
git clone https://github.com/aase7en/A-Wiki.git
cd A-Wiki
bash scripts/setup-local.sh        # ติดตั้งครบ: ลิงก์ drive, keys, index, hooks
```

จากนั้นเปิด AI tool ที่คุณใช้ (Claude Code / Codex / Gemini CLI / Cursor / ZCode ฯลฯ) ที่โฟลเดอร์นี้ — สมองต่ออัตโนมัติ ไม่ต้องตั้งค่าเพิ่ม

### ทางที่ 2 — pip package (เร็ว เหมาะทดลอง/ใช้เฉพาะ CLI)

```bash
pip install git+https://github.com/aase7en/A-Wiki.git   # ได้คำสั่ง awiki ทันที
awiki status                       # ทดสอบ (รันในโฟลเดอร์ clone หรือตั้ง AWIKI_ROOT)
```

> `awiki` เป็น thin launcher — คำสั่งวิ่งเข้า repo จริง (หาอัตโนมัติจาก cwd หรือ env `AWIKI_ROOT`) ดังนั้นติดตั้งครั้งเดียวใช้ได้ทุก clone

**สิ่งที่ต้องมี**: Python 3.9+ · Git · (ถ้าจะใช้ vector search: `pip install -r requirements.txt`)

## 2. ใช้งานประจำวัน

### เริ่มงานใหม่ — พิมพ์อย่างเดียวจบ

```
/A ทำเว็บขายของให้ร้านกาแฟ
```

สิ่งที่เกิดขึ้นเองตามลำดับ:

1. **Route** — งานตรงกับ skill เฉพาะ (เช่น "เว็บ") ก็ส่งตรงนั้นทันที
2. ไม่ตรงตัวไหน → **เดิน spine เต็ม**: คิดวิเคราะห์ → **ถามคุณกลับ ≥3 ข้อ** (ขอบเขต/งบ/เกณฑ์สำเร็จ — ตอบสั้นๆ ได้) → ปรึกษาทีมใน (council) → ลงมือทำ → ตรวจ bug วนจนผ่าน → เปิดรีวิว → แก้ตามผล → ครบจึงปิดงาน
3. **สิ่งที่คุณต้องทำระหว่างทาง**: ตอบเมื่อถูกถาม + ตัดสินใจตรงจุดที่ถูกขอ เท่านั้น

### ปุ่มเฉพาะตัวของคุณ (12 ปุ่ม กดตรง)

| พิมพ์ | ได้อะไร |
|---|---|
| `/A-Doc <งาน>` | เอกสารราชการ 8 แบบ (หนังสือราชการ ประกาศ ญัตติ WI-SP PR-QT-PO ...) |
| `/A-Med-Order` | คำสั่ง รพ./เวชกรรม |
| `/A-Rabies-Report` | รายงานสัตว์พาหะนรก/วัคซีน (มี regression คุมความถูก) |
| `word-generator` | เอกสาร Word ไทย ฟอนต์ TH SarabunPSK |
| `assessment-generator` | แบบประเมินสมรรถนะ + Excel/PDF |
| `pharmacy-order-lookup` | ค้นออเดอร์เภสัช |
| `thai-government-form` · `thai-invoice` · `thai-resume` · `thai-festival-card` | ฟอร์มราชการ / ใบเสร็จ / เรซูเม่ / การ์ดเทศกาล |
| `monte-carlo-quant-analysis` | วิเคราะห์ portfolio ลงทุนส่วนตัว |

### ถามสมอง / ค้นความรู้

- **ในแชท agent ใดก็ได้**: พิมพ์ถามปกติ — ระบบดึงความจำเกี่ยวข้องมาช่วยตอบเอง
- **คำสั่งตรง** (หรือ `awiki ...` ถ้าติดตั้งแบบ pip):

```bash
awiki search "esp32 lora"      # ค้นความรู้ในสมอง
awiki related --page <path>    # หน้าที่เกี่ยวข้องบนกราฟความรู้
awiki hubs                     # ประเด็นศูนย์กลางที่เชื่อมมากที่สุด
awiki recall "zcode"           # ความจำเก่า (decisions/lessons)
awiki status                   # สถานะสมอง + งานที่ถูกจองอยู่
awiki plan "ทำ dashboard ขาย"  # แปลงความต้องการเป็นแผนงาน
```

## 3. ความจำ — ไม่ต้องทำอะไรเลย

ทุกการตัดสินใจ/บทเรียน/ผลงานถูกจดอัตโนมัติ · ซิงค์ข้ามเครื่อง (Windows/Mac/Pi5) · **ลบ secret ก่อนจดและก่อนส่งเสมอ** — ครั้งหน้าถามเรื่องเดิม สมองนึกออกเอง

## 4. เกราะที่ทำงานเบื้องหลัง (รู้ไว้ ไม่ต้องสั่ง)

| เหตุการณ์ | ผล |
|---|---|
| แก้ไฟล์ต้นฉบับใน `raw/` | ถูกขวาง (ต้นทางสงวนไว้) |
| พิมพ์ secret / ชื่อจริง รพ. | ถูกขวางก่อนขึ้น git เสมอ |
| แก้ skill โดยไม่จดทะเบียน | ถูกขวาง |
| สอง agent ทำงานชนกัน | ระบบกันเอง (claims + gates) |
| งานที่ไม่มี test | ห้ามเขียนโค้ดก่อน test (Iron Law #1) |

## 5. ดูสถานะรีวิวงาน (review bus)

```bash
cat .tmp/review-bus/P8-c1.json     # ดูรอบรีวิวล่าสุด (ถ้ามีงานกำลังรีวิว)
```

สนใจ 3 ช่อง: `status` (READY = ผ่านครบ · CHANGES_REQUIRED = กำลังแก้) · `findings` (ปัญหา id คงที่ + สถานะ) · `head_sha` (commit ที่ approval ผูกอยู่ — commit ใหม่ = รีวิวใหม่โดยอัตโนมัติ)

## 6. ขยายความสามารถ (optional)

อยากให้สมองรู้เรื่องข่าว/เหตุการณ์โลก (การลงทุน/สิ่งแวดล้อม/สาธารณภัย ฯลฯ): ตั้ง env `WORLD_INTEL_MCP_CMD` ชี้ไป MCP server ภายนอกที่คุณเลือกเอง — ไม่ตั้งก็ไม่มีอะไรพัง (ปิดไว้ default)

## 7. ดูแลรักษา

**ไม่ต้องทำ**: rebuild index / regen surfaces / privacy scan — hooks กับ CI ทำเองทุก commit
**ควรทำบ้าง**: เครื่องใหม่ → `bash scripts/setup-local.sh` · ก่อนงานใหญ่และอยากชัวร์ → `python -m pytest tests/ -q`

## 8. มีปัญหา?

- ค้นความรู้เดิมก่อน: `awiki search "<อาการ>"` หรือดู `wiki/context/session-memory.md`
- งานรีวิวค้าง: ดู `status` ใน `.tmp/review-bus/` — blocker ที่เปิดอยู่คือสิ่งที่ต้องแก้ก่อน
- Operator guide เต็ม: `docs/runbooks/review-bus.md` · สถาปัตยกรรม: `docs/architecture/SYSTEM-ARCHITECTURE.md`
