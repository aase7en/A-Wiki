# A-Med-Order · references/telegram-lane.md — เลนไม่ใช้ browser (Pi5 / Hermes / ZCode)

> เปิดไฟล์นี้เมื่อ: ทำงานผ่าน Telegram หรือบนเครื่องที่ไม่มีเบราว์เซอร์

ใช้เมื่อ Claude ติด limit, ไม่มีเบราว์เซอร์, หรือรีบสั่งจากมือถือ
**ตัด Google Sheet ออกทั้งหมด จบใน 3 ข้อความ**

## 4 คำสั่ง

```bash
# 1) ลิสต์ยาหมด → session + ข้อความถามจำนวน (ส่งกลับผู้ใช้ทาง Telegram)
python3 scripts/med_order_telegram.py draft list.txt --session 20260801-01

# 2) เฉพาะรายการ ❓ unknown — จุดเดียวที่ต้องใช้ LLM/คนตัดสิน
python3 scripts/med_order_telegram.py set 20260801-01 5 \
        --name "Nizoral ครีม" --strength "Ketoconazole 2%" --pack "10 g" \
        --unit หลอด --category "3. ยาปฏิชีวนะ / ต้านเชื้อรา"

# 3) ผู้ใช้ตอบจำนวนมา → อัปเดต
python3 scripts/med_order_telegram.py qty 20260801-01 "1=12 2=10 3=40"

# 4) ปิดงาน
python3 scripts/med_order_telegram.py finish 20260801-01 --po PO-2026-08-01
```

คำสั่งเสริม: `status <id>` (ดูสถานะ) · `list --limit 10` (session ล่าสุด)

## `finish` ทำ 3 อย่างพร้อมกัน

1. เขียน `.xlsx` ลง `<drive>/pharmacy/order-history/<po>_<session>.xlsx`
2. พิมพ์ข้อความ LINE ออก **stdout** (ส่งต่อให้ผู้ใช้ได้เลย)
3. เรียน alias จากรายการ `alias` + `manual` → รอบหน้าไม่ต้องถามซ้ำ (ปิดด้วย `--no-learn`)

metadata (path, จำนวน, ผลการเรียน) ออก **stderr** เป็น JSON — บอทไม่ต้องส่งต่อ

## รูปแบบคำตอบจำนวนที่รองรับ

| รูปแบบ | ตัวอย่าง |
|---|---|
| เท่ากับ | `1=12 2=5 7=3` |
| ทวิภาค + คอมมา | `1:12, 2:5` |
| เว้นวรรค / บรรทัดละคู่ | `1 12`↵`2 5` |
| ลูกศร | `1->12` · `1→12` |
| ทั้งหมดเท่ากัน | `all 12` · `ทั้งหมด 12` · `ทุกตัว 12` |

- ข้อที่ไม่ตอบ = **ไม่สั่ง** (ไม่เข้าใบสั่งซื้อ)
- ระบุข้อเดิมซ้ำ → ใช้ค่าหลัง + เตือน
- ระบุข้อที่ไม่มี → เตือน แล้วข้าม
- อ่านไม่ออกเลย → เตือน `ใช้รูปแบบ 1=12 2=5` ไม่แก้ไขอะไร

## สถานะรายการ

| ไอคอน | status | หมายถึง |
|---|---|---|
| ✅ | `alias` | คลังคำพ้องเคยยืนยันแล้ว — เชื่อถือได้ ไม่ต้องใช้ LLM |
| 🟡 | `stock` | เดาจากสต๊อกจริง — **ตรวจความแรง/ขนาดบรรจุอีกครั้ง** |
| ❓ | `unknown` | ไม่รู้จัก — ต้อง `set` ก่อน |
| ✍️ | `manual` | คน/LLM ยืนยันแล้วใน session นี้ |

`finish` จะ **บล็อก** ถ้ายังมีรายการ ❓ ที่ใส่จำนวนไว้ (ข้ามด้วย `--force` = สั่งด้วยชื่อดิบ)

## ทำไมเลนนี้ปลอดภัยกับโมเดลเล็ก

| ข้อ | เหตุผล |
|---|---|
| สคริปต์ไม่มี secret ไม่ต่อเน็ต ไม่เรียก LLM | เป็น state machine ล้วน — บอทแค่ pipe ข้อความ |
| LLM แตะจุดเดียว = คำสั่ง `set` | ที่เหลือ deterministic ทั้งหมด |
| รายการที่ hit alias ไม่ผ่าน LLM เลย | ยิ่งใช้ ยิ่งเหลืองานให้โมเดลน้อยลง |

Session เก็บที่ `<drive>/pharmacy/order-sessions/<id>.json`

บอท Telegram ตัวจริงอยู่ใน `scripts/telegram-bot/` (private, gitignored, symlink ไป
`drive/personal-tools/`) — เรียกสคริปต์นี้ผ่าน subprocess แล้ว pipe stdout กลับเข้าแชท

## ⚠️ ข้อจำกัดจริงบน Pi5 (ยังไม่ได้แก้ — ตรวจก่อนใช้ครั้งแรก)

1. **LLM อยู่ใน path เสมอ** — Hermes ใช้ Skills-as-Commands: dir `a-med-order` →
   `/a-med-order` อัตโนมัติ แล้ว **LLM อ่าน SKILL.md ก่อนแล้วค่อยเรียกสคริปต์**
   ทางเลี่ยง LLM (`quick_commands type:exec`) ยังติด upstream bug #44718
   (`{args}` placeholder ไม่ substitute) → เลี่ยงไม่ได้จนกว่าจะแก้ที่ต้นทาง
   นี่คือเหตุผลที่ SKILL.md ต้องบาง และรายละเอียดอยู่ใน `references/` แบบนี้
2. **Pi5 ต้องเข้าถึง `<drive>/pharmacy/` ได้** — sync ปัจจุบันเป็น
   `sync-secrets-from-drive.sh` (secrets เท่านั้น) ยังไม่ยืนยันว่าครอบคลุม pharmacy
   ตรวจด้วย `python3 -c "import sys;sys.path.insert(0,'scripts');from drive_path import get_pharmacy_dir;print(get_pharmacy_dir())"`
3. **ต้องมี `xlrd` + `openpyxl` ในคอนเทนเนอร์** — `.xls` แบบเก่า (cp874) pandas/openpyxl อ่านไม่ได้
4. **`medi_list.db` ถูก gitignore** — รัน `import_medi_list.py` หนึ่งครั้งบนเครื่องนั้น

## การ deploy บน Pi5

ไม่ต้องทำมือ — cron ทุก 6 ชม. `auto-sync-from-git.sh` → `pi5-brain-sync.py --apply`
เรียก `link_awiki_skills.py --apply` ซึ่งอ่าน `hermes.skills.json` แล้ว symlink
ทุก entry ที่ path ขึ้นต้น `skills/awiki/` เข้า `/opt/data/skills/awiki/` → gateway rescan

`a-med-order` แท็ก `agents: [all, hermes]` แล้ว จึงติดไปด้วยอัตโนมัติ
เร่งได้ด้วย `bash scripts/hermes/auto-sync-from-git.sh` บน Pi5
