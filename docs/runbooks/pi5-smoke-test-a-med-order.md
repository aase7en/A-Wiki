# Smoke Test — Pi5 / Hermes Telegram + A-Med-Order

> **ทำครั้งเดียวหลัง deploy** เพื่อยืนยันว่าใช้จริงได้ตอนฉุกเฉิน (Claude ติด limit แล้วต้องรีบสั่งยา)
> สร้างเมื่อ 2026-07-30 · ครอบคลุม: `a-med-order` v1.2.0 ที่ยังไม่เคยรันบน Pi5 เลย
> และ `/spec /plan /build /review /ship` ที่ runbook ระบุว่า "deployed แต่ phone smoke **optional**" ตั้งแต่ 2026-07-07
>
> วิธีใช้: ทำจากบนลงล่าง **ห้ามข้าม** — รอบ 0 พังแล้วรอบ 3 พังตามแน่นอน
> บันทึกผลในตารางท้ายเอกสาร แล้ว commit กลับ

---

## 🔧 รอบ 0 — Prerequisite (SSH เข้า Pi5 · ~5 นาที)

รันในคอนเทนเนอร์ Hermes (ปรับชื่อคอนเทนเนอร์ตามจริง):

```bash
CT=hermes-agent_web_1
CLONE=/opt/data/A-Wiki          # ปรับตาม path ที่ pi5-brain-sync ใช้
D() { sudo -S -p '' docker exec -i "$CT" bash -lc "$1"; }
```

| # | ตรวจอะไร | คำสั่ง | ผลที่ต้องได้ | ✅/❌ |
|---|---|---|---|---|
| 0.1 | sync ล่าสุด | `bash scripts/hermes/auto-sync-from-git.sh` (บน host) | จบ exit 0 · เห็น `link-awiki-skills` และ `gateway-rescan` | ☐ |
| 0.2 | commit ตรงกับ Mac | `D "cd $CLONE && git log --oneline -1"` | `646afe5a` หรือใหม่กว่า | ☐ |
| 0.3 | symlink สกิลติดแล้ว | `D "ls -la /opt/data/skills/awiki/ \| grep a-med-order"` | เห็น symlink → `$CLONE/skills/awiki/a-med-order` | ☐ |
| 0.4 | references ตามไปด้วย | `D "ls /opt/data/skills/awiki/a-med-order/references/"` | 4 ไฟล์ (normalization, order-sheet, telegram-lane, data-sources) | ☐ |
| 0.5 | **drive/pharmacy เข้าถึงได้** | `D "cd $CLONE && python3 -c \"import sys;sys.path.insert(0,'scripts');from drive_path import get_pharmacy_dir;print(get_pharmacy_dir())\""` | path ที่ **มีอยู่จริง** ไม่ใช่ `drive/pharmacy` เปล่าๆ | ☐ |
| 0.6 | ไฟล์สต๊อกอยู่ไหม | `D "ls '$(ผลข้อ 0.5)/medi.list/'"` | เห็น `รายการยาทั้งหมด.xls` | ☐ |
| 0.7 | คลังคำพ้องมาถึงไหม | `D "ls -la '$(ผลข้อ 0.5)/order-aliases.json'"` | มีไฟล์ ~30-40 KB | ☐ |
| 0.8 | xlrd + openpyxl | `D "python3 -c 'import xlrd,openpyxl;print(xlrd.__version__,openpyxl.__version__)'"` | พิมพ์เวอร์ชันทั้งคู่ | ☐ |
| 0.9 | สร้าง medi_list.db | `D "cd $CLONE && python3 scripts/import_medi_list.py"` | `✅ นำเข้า 5,xxx รายการ` | ☐ |
| 0.10 | alias อ่านได้ | `D "cd $CLONE && python3 scripts/pharmacy_aliases.py stats"` | `alias ทั้งหมด : 71` (หรือมากกว่า) | ☐ |

**ถ้า 0.5 ล้มเหลว** = Pi5 ไม่เห็น Google Drive → เลน B ใช้ไม่ได้เลย ต้องแก้ก่อน
ทางแก้ที่เป็นไปได้: mount rclone, sync เฉพาะ `pharmacy/` ผ่าน `sync-secrets-from-drive.sh` แบบขยาย,
หรือย้าย 3 ไฟล์ที่จำเป็น (`medi.list/*.xls`, `order-aliases.json`) เข้า Drive path ที่ Pi5 เห็นอยู่แล้ว

**ถ้า 0.8 ล้มเหลว** → `D "pip install --break-system-packages xlrd openpyxl"`

---

## 📱 รอบ 1 — Baseline บน Telegram (ยืนยันว่าบอทยังดี · ~2 นาที)

ก๊อปวางใน Telegram ทีละบรรทัด

```
/status
```
☐ ตอบ session / model / context — **ถ้าข้อนี้ไม่ตอบ หยุด** ปัญหาอยู่ที่ gateway ไม่ใช่สกิล

```
/wiki mqtt broker
```
☐ ตอบ 5 hits เป็น path + title + snippet (นี่คือข้อที่ verified ไว้เมื่อ 2026-07-07 — ใช้เทียบว่ายังไม่ regress)

---

## 🧪 รอบ 2 — 5 คำสั่ง lifecycle ที่ไม่เคยลองบนมือถือ (~5 นาที)

ส่งสั้นๆ พอให้เห็นว่า route ทำงาน ไม่ต้องรอผลลัพธ์คุณภาพสูง

```
/spec ระบบแจ้งเตือนยาใกล้หมดอายุในร้าน
```
☐ ตอบเป็นโครง spec (ไม่ใช่ `Unknown command`)

```
/plan แยกงาน spec ข้างบนเป็น task
```
☐ ตอบเป็นลิสต์ task

```
/build เริ่มทำ task แรก
```
☐ ตอบแนวทาง incremental + TDD

```
/review ตรวจ scripts/med_order_telegram.py
```
☐ ตอบเป็นรีวิว (persona fan-out) — อาจใช้เวลานาน/กิน token มาก ถ้าช้าเกิน 2 นาทีถือว่า ⚠️

```
/ship
```
☐ ตอบ go/no-go gate

> เจอ `Unknown command` → gateway ยังไม่ rescan
> แก้: restart Hermes ผ่าน Umbrel UI (Apps → Hermes Agent → Restart) แล้วลองซ้ำ

---

## 💊 รอบ 3 — A-Med-Order เลน B ครบวง (ข้อสำคัญที่สุด · ~10 นาที)

### 3.1 draft

ก๊อปทั้งก้อนนี้วางใน Telegram (ลิสต์ทดสอบออกแบบให้ครบทั้ง 3 เส้นทาง):

```
/a-med-order รายการยาหมด
TACTNOL 0.1% 15g
Allernix10s
ยาคุมมินนี่28เม็ด
ยาทดสอบสมมติ 99mg
```

**ผลที่ต้องได้** (บรรทัดสำคัญ — ตรวจให้ตรง):

```
1. ✅ TACINOL ครีม Triamcinolone acetonide 0.1% 15 g = ___ หลอด
2. ✅ Allernix Loratadine 10 mg 10 เม็ด/แผง = ___ แผง
3. ✅ ยาคุมมินนี่ (Minny) Ethinylestradiol 0.02 mg + Desogestrel 0.15 mg 28 เม็ด/แผง = ___ แผง
4. ❓ ยาทดสอบสมมติ 99mg  ← ยังไม่รู้จัก

✅ จากคำพ้องที่ยืนยันแล้ว 3 · 🟡 เดาจากสต๊อก 0 · ❓ ยังไม่รู้จัก 1
```

- ☐ ข้อ 1 ต้องเป็น **TACINOL** (ไม่ใช่ TACTNOL) ← พิสูจน์ว่าคลังคำพ้องทำงาน
- ☐ ข้อ 2 ต้องเป็น **Loratadine** (ไม่ใช่ Chlorpheniramine) ← พิสูจน์ว่าอ่านของที่แก้แล้ว
- ☐ ข้อ 4 ต้องขึ้น ❓ ← พิสูจน์ว่ามันไม่มโนชื่อยาเอง **ข้อนี้สำคัญที่สุด**
- ☐ บอทบอก session id กลับมา (เช่น `20260801-01`) — จดไว้ใช้ข้อถัดไป

> **ถ้าข้อ 4 ถูกเดาเป็นชื่อยาจริง = FAIL ร้ายแรง** หยุดทันที ห้ามใช้เลนนี้สั่งยาจริง
> แล้วแจ้งกลับมา (เป็นไปได้ว่าโมเดลข้ามสคริปต์ไปตอบเอง ไม่ได้เรียก `resolve`)

### 3.2 qty

```
/a-med-order qty <session-id> 1=12 2=10 3=40 4=6
```
☐ ตอบว่ากรอกแล้ว 4/4 และแสดงลิสต์ที่มีจำนวน

### 3.3 finish — ต้องถูกบล็อก

```
/a-med-order finish <session-id> --po PO-SMOKE-01
```
☐ **ต้อง error** ว่า `ข้อ [4] ยังไม่รู้จักชื่อยา — ใช้ set ยืนยันก่อน`
← พิสูจน์ guard ทำงาน ถ้ามันออกไฟล์เลย = FAIL

### 3.4 set แล้ว finish จริง

```
/a-med-order set <session-id> 4 --name "Nizoral ครีม" --strength "Ketoconazole 2%" --pack "10 g" --unit หลอด --category "3. ยาปฏิชีวนะ / ต้านเชื้อรา"
```
☐ ตอบ `✓ ข้อ 4 → Nizoral ครีม | Ketoconazole 2% | 10 g`

```
/a-med-order finish <session-id> --po PO-SMOKE-01
```
☐ ตอบเป็นข้อความ LINE จัดกลุ่มตามหมวด 4 รายการ ลงท้าย `รบกวนแจ้งราคาและกำหนดส่งด้วยครับ ขอบคุณครับ`
☐ ข้อความสั้นพอที่ Telegram ส่งได้ในข้อความเดียว (< 4096 อักษร)

---

## 📂 รอบ 4 — ตรวจ artifact ที่ตกลงจริง (SSH · ~2 นาที)

```bash
PH=$(D "cd $CLONE && python3 -c \"import sys;sys.path.insert(0,'scripts');from drive_path import get_pharmacy_dir;print(get_pharmacy_dir())\"")
```

| # | ตรวจ | คำสั่ง | ผลที่ต้องได้ | ✅/❌ |
|---|---|---|---|---|
| 4.1 | ไฟล์ xlsx เกิดขึ้น | `D "ls -la '$PH/order-history/' \| grep SMOKE"` | เห็น `PO-SMOKE-01_*.xlsx` | ☐ |
| 4.2 | session ปิดแล้ว | `D "python3 -c \"import json;print(json.load(open('$PH/order-sessions/<id>.json'))['state'])\""` | `done` | ☐ |
| 4.3 | **alias เรียนเพิ่ม** | `D "cd $CLONE && python3 scripts/pharmacy_aliases.py resolve 'ยาทดสอบสมมติ 99mg'"` | ✅ → Nizoral ครีม | ☐ |
| 4.4 | ราคาทุนถูกเติม | `D "cd $CLONE && python3 -c \"from openpyxl import load_workbook as L;w=L('$PH/order-history/PO-SMOKE-01_<id>.xlsx')['ใบสั่งซื้อ'];print([w.cell(row=r,column=8).value for r in range(7,14)])\""` | มีตัวเลขบางช่อง (ไม่ต้องครบ) | ☐ |
| 4.5 | ไฟล์ sync ขึ้น Drive | เปิด Google Drive บนมือถือ → `A-Wiki-Data/pharmacy/order-history/` | เห็นไฟล์ SMOKE | ☐ |

### 🧹 เก็บของทดสอบ

```bash
D "cd $CLONE && python3 scripts/pharmacy_aliases.py forget 'ยาทดสอบสมมติ 99mg'"
D "rm -f '$PH/order-history/PO-SMOKE-01_'*.xlsx '$PH/order-sessions/<id>.json'"
```
☐ `pharmacy_aliases.py stats` กลับมาเป็น 71

---

## 📊 บันทึกผล

| รอบ | วันที่ | ผล | หมายเหตุ |
|---|---|---|---|
| 0 Prerequisite | | ☐ PASS ☐ FAIL | |
| 1 Baseline | | ☐ PASS ☐ FAIL | |
| 2 Lifecycle ×5 | | ☐ PASS ☐ FAIL | |
| 3 A-Med-Order | | ☐ PASS ☐ FAIL | |
| 4 Artifact | | ☐ PASS ☐ FAIL | |

**Token ที่ใช้ทั้งรอบ (จาก `/status` ก่อน-หลัง):** ______
← ตัวเลขนี้สำคัญ: ถ้าเกิน ~15k จาก 8 ข้อความ แปลว่า SKILL.md ยังหนาเกินไปสำหรับ free-tier pool
และควรบางลงอีก (ปัจจุบัน 8.8 KB ลดจาก 23.7 KB แล้วรอบหนึ่ง)

---

## เกณฑ์ตัดสิน

| ผล | หมายถึง |
|---|---|
| รอบ 0-4 PASS ทั้งหมด | ใช้เลน B สั่งยาจริงได้ ✅ |
| รอบ 3.1 ข้อ 4 ถูกเดาเป็นยาจริง | **ห้ามใช้** — โมเดลไม่ได้เรียกสคริปต์ ตอบเองจาก SKILL.md |
| รอบ 3.3 ไม่บล็อก | **ห้ามใช้** — guard ไม่ทำงาน |
| รอบ 0.5 FAIL | เลน B ใช้ไม่ได้จนกว่าจะแก้ Drive access |
| รอบ 2 FAIL แต่รอบ 3 PASS | ใช้สั่งยาได้ แต่ lifecycle command เสีย (แยกปัญหากันได้) |

## See also

- `skills/awiki/a-med-order/references/telegram-lane.md` — ข้อจำกัด 4 ข้อบน Pi5
- `docs/runbooks/hermes-raspberry-pi5.md` §"Slash Commands" — ตารางสถานะคำสั่ง
- `docs/architecture/hermes-cross-agent-handoff.md` §"CHUNK E Phase 4 RESULTS"
