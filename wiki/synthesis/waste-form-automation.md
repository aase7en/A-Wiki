---
type: synthesis
tags: [env, ai-tools, automation, playwright, ocr, claude-api, waste-report, hospital, web-form]
sources: [infectious-waste-th-law]
domains: [Env, AI Tools]
created: 2026-05-21
updated: 2026-05-21
---

# Automation: กรอกฟอร์มรายงานขยะโรงพยาบาลอัตโนมัติ

## คำถามที่ตอบ

"จะ automate การกรอกฟอร์มน้ำหนักขยะทั่วไปบนเว็บโรงพยาบาลจากภาพถ่ายได้อย่างไร?"

## สรุป

Pipeline เดียว: **ภาพถ่ายใบรายงาน → OCR (Claude Vision) → aggregate → Playwright กรอกฟอร์มเว็บ** — ลดเวลากรอกข้อมูลจากหลายนาทีต่อวันเหลือ ~30 วินาที ใช้ scripts สองตัวที่เก็บในโฟลเดอร์ `scripts/`:

| Script | วัตถุประสงค์ |
|--------|-------------|
| `scripts/save-waste-cookie.py` | ครั้งแรกครั้งเดียว: บันทึก session cookie หลัง login |
| `scripts/fill-waste-form.py` | งานหลัก: OCR → aggregate → กรอกฟอร์ม |

## Architecture

```
[ภาพใบรายงานขยะทั่วไป (.jpg / .png)]
    ↓ base64 encode
[Claude Vision API (claude-sonnet-4-6)]
    ↓ JSON array (6 fields per row)
[Aggregation: parse weight, resolve location → form rows]
    ↓ {row_num: kg} dict
[Playwright + saved cookie]
    ↓ fill header + weight rows
[เว็บฟอร์ม https://10779.gtwoffice.com/env/manage/trash_add]
    ↓ user confirms → submit
[Screenshot: waste_submit_YYYY-MM-DD.png]
```

## Setup (ครั้งแรกครั้งเดียว)

```bash
pip install playwright anthropic
playwright install chromium

# Login และบันทึก cookie
python scripts/save-waste-cookie.py
# → เปิด browser → login เอง → กด ENTER → บันทึกที่ .claude/waste-form-cookies.json
```

> `.claude/waste-form-cookies.json` ถูก gitignore อยู่แล้ว (อยู่ใต้ `.claude/*` rule)

## การใช้งานประจำวัน

```bash
# Preview ก่อน (ไม่เปิด browser)
python scripts/fill-waste-form.py รายงาน_พค_2569.jpg --dry-run

# กรอกจริง — ถ้า image มีหลายวันจะถามให้เลือก
python scripts/fill-waste-form.py รายงาน_พค_2569.jpg

# ระบุวันที่โดยตรง (CE)
python scripts/fill-waste-form.py รายงาน_พค_2569.jpg --date 2026-05-14
```

## Location → Form Row Mapping [verified 2026-05-21]

| OCR `location` | Form row # | Label ในฟอร์ม | หมายเหตุ |
|---|---|---|---|
| OPD | 12 | ขยะทั่วไป OPD | — |
| วอร์ด | 14 | ขยะทั่วไป Ward | — |
| ER | 8 | ขยะทั่วไป ER | — |
| OPD+ER | 8, 12 | ทั้งสอง | split weight equally |
| โรงครัว | 9 | ขยะทั่วไป โรงครัว | — |
| เวช | 13 | ขยะทั่วไป เวชฯ | — |
| แผนไทย+ฝังเข็ม | 18, 11 | แพทย์แผนไทย + ฝังเข็ม | split weight equally |
| ฝังเข็ม | 11 | ขยะทั่วไป ฝังเข็ม | — |

> Rows อื่นๆ ในฟอร์ม (1–7, 10, 15–25) = ไม่มีข้อมูลจากใบรายงานนี้ → script ปล่อยว่าง

## Data Aggregation Rules

| กรณี | วิธีจัดการ |
|------|-----------|
| `weight_kg = "5+5"` | sum → 10.0 |
| `location = "OPD+ER"` | map ไป rows 8 + 12, แบ่ง weight เท่ากัน |
| `location = "แผนไทย+ฝังเข็ม"` | map ไป rows 18 + 11, แบ่ง weight เท่ากัน |
| วันเดียวกัน + location เดิม | sum weight รวม |
| เวลา | ใช้ time แรกสุดของวัน (min sort) |

## Header Fields ที่กรอกอัตโนมัติ

| ช่อง | ค่าที่กรอก | วิธีหา |
|------|-----------|--------|
| วันที่บันทึก | DD/MM/YYYY (พ.ศ.) | convert จาก OCR date |
| เวลา | เวลาแรกสุดของวัน | min(times) |
| Supplies | อบต.อุทัย | hardcoded constant |
| ผู้บันทึก | ศุภศิษฎิ์ คงสุวรรณ | hardcoded constant |

## Cookie Management

Session cookie บันทึกด้วย Playwright `storage_state` — เก็บ cookies + localStorage ทั้งหมดของ session นั้น:

```bash
# บันทึก cookie ใหม่ (ทำเมื่อ session หมดอายุ / login ใหม่)
python scripts/save-waste-cookie.py

# ระบุ path custom
python scripts/fill-waste-form.py image.jpg --cookie /path/to/custom-cookie.json
```

> Cookie หมดอายุตาม session ของเว็บ (ปกติ 1–7 วัน) — ถ้า script error 403/redirect login → รัน `save-waste-cookie.py` ใหม่

## Alternative: Userscript Edition (no-install) [2026-05-26]

Lightweight option ที่ไม่ต้อง Python/Playwright — ใช้ **Tampermonkey userscript** + **Gemini 2.5 Flash** (ฟรี 1500 req/วัน) inject ปุ่ม "📷 OCR & Fill" ลงในหน้า `trash_add` โดยตรง

| Aspect | Python + Playwright | Userscript ✅ ใหม่ |
|---|---|---|
| ติดตั้ง | pip + chromium 200MB + save-cookie | Tampermonkey ext + paste 1 ไฟล์ |
| Login | จัดการ cookie แยก | ใช้ session ที่เปิดอยู่ในเบราว์เซอร์ |
| OCR | Claude Vision (paid ~$0.003/รูป) | Gemini Flash (ฟรี) |
| Submit | กรอก + รอ user คลิก submit | กรอก + รอ user คลิก submit (เหมือนกัน) |
| Cross-platform | Mac/PC + dep diff | ทุก OS ที่มี Chrome |

ไฟล์:
- `scripts/userscripts/waste-form-ocr-fill.user.js` — userscript ~400 บรรทัด
- `scripts/userscripts/README.md` — install + debug

DOM strategy: **label-based** ไม่ใช่ name-attribute → robust ต่อ form refactor (หา `<td>` ที่ text = "ขยะทั่วไป OPD" แล้วเอา `<input>` ใน row เดียวกัน)

> Python+Playwright spec ในเอกสารนี้ยังเก็บไว้เป็น fallback หาก userscript ใช้ไม่ได้

## ข้อจำกัด

| ปัญหา | วิธีรับมือ |
|-------|-----------|
| Row selectors ไม่ตรง | script ลอง `input[name="amount[N]"]`, `qty[N]`, `weight[N]` และ table fallback ตามลำดับ |
| Submit button ไม่พบ | script แจ้ง warning แต่ไม่ปิด browser — user คลิก submit เองได้ |
| Cookie หมดอายุ | รัน `save-waste-cookie.py` ใหม่ |
| Location ใหม่ที่ไม่รู้จัก | script แจ้ง warning ใน console — เพิ่มใน `LOCATION_ROW_MAP` ในไฟล์ script |
| เว็บ internal network | ต้อง run บนเครื่อง local (Mac/PC) ที่เชื่อมต่อกับ network โรงพยาบาล |

## ความสัมพันธ์

- [[synthesis/garbage-report-ocr]] — OCR system prompt + field definitions (ต้นน้ำของ pipeline นี้)
- [[synthesis/waste-weight-monitoring]] — IoT weight sensor cross-check (เปรียบเทียบค่าจาก sensor กับใบรายงาน)
- [[synthesis/appsheet-to-webapp-pi5]] — Platform บน Raspberry Pi 5 สำหรับ deploy ต่อ

## แหล่งข้อมูล

- [training] Playwright Python API — `storage_state`, `page.fill`, `select_option`
- [training] Anthropic Claude Vision API — image OCR via Messages API
- [[sources/infectious-waste-th-law]] — กฎกระทรวงขยะติดเชื้อ (context domain)
