---
type: synthesis
tags: [env, ai-tools, ocr, claude-api, waste-report, hospital, vision]
sources: [infectious-waste-th-law]
domains: [Env, AI Tools]
created: 2026-05-14
updated: 2026-05-21
---

# ระบบอ่านภาพใบรายงานขยะทั่วไปโรงพยาบาล (Garbage Report OCR)

## คำถามที่ตอบ

"จะสร้างระบบอ่านภาพใบรายงานขยะทั่วไปของโรงพยาบาล (internal form) โดยอัตโนมัติได้อย่างไร?"

## สรุป

ใช้ **Claude Vision API** อ่านภาพถ่ายใบรายงานขยะทั่วไป (รับจาก LINE หรือ upload) แล้ว extract ข้อมูลออกมาเป็น JSON structured data เพื่อบันทึกลงระบบหรือตรวจสอบต่อ — เป็น pattern เดียวกับ [[synthesis/pharmacy-order-checker]] แต่ปรับ domain สำหรับงานอนามัยสิ่งแวดล้อม

## Architecture

```
[ภาพใบรายงานขยะ (ถ่ายจากมือถือ / LINE / scan)]
      ↓ base64 encode
[Claude Vision API (claude-sonnet-4-6)]
      ↓ system prompt: extract waste report fields
[JSON structured data]
      ↓
[ตรวจสอบ / แก้ไข / บันทึกฐานข้อมูล]
      ↓ (อนาคต)
[FastAPI endpoint บน Raspberry Pi 5]
```

## Fields ที่ extract จากใบรายงานขยะทั่วไป

ฟิลด์มาตรฐานที่พบในแบบฟอร์มภายในโรงพยาบาล:

| Field (JSON key) | ความหมาย | ตัวอย่าง |
|-----------------|----------|---------|
| `date` | วันที่บันทึก | "2026-05-14" |
| `department` | ตึก / แผนก / ward | "ตึกอายุรกรรม" |
| `waste_type` | ประเภทขยะ | "มูลฝอยติดเชื้อ" / "ขยะทั่วไป" |
| `color_code` | สีถุง/ภาชนะ | "แดง" / "เหลือง" / "น้ำตาล" / "ดำ" |
| `weight_kg` | น้ำหนัก (กิโลกรัม) | 12.5 |
| `quantity` | จำนวนถุง/กล่อง/ภาชนะ | 4 |
| `unit` | หน่วย | "ถุง" / "กล่อง" |
| `recorder` | ชื่อผู้บันทึก | "นายสมชาย ใจดี" |
| `supervisor` | ผู้ตรวจสอบ / หัวหน้า | "นางสาวมาลี สุขใส" |
| `notes` | หมายเหตุ (ถ้ามี) | null |

> ระบบสีถุงอ้างอิงจาก [[concepts/env/infectious-waste-management]] — แดง = ติดเชื้อทั่วไป, เหลือง = sharps, น้ำตาล = เคมี, ดำ = ทั่วไป

### Fields จริงในฟอร์ม "รายงานขยะทั่วไป" [verified 2026-05-20]

ฟอร์มนี้มีเพียง 6 คอลัมน์ (ไม่มี waste_type / color_code / quantity):

| Field (JSON key) | คอลัมน์ในฟอร์ม | ตัวอย่าง |
|-----------------|---------------|---------|
| `row_number` | ลำดับ | 1, 2, 3 … |
| `date` | วัน/เดือน/ปี (พ.ศ.) | "2026-04-30" |
| `time` | เวลา | "15:00", "07:35น." |
| `weight_kg` | น้ำหนักขยะ /kg. | 17 |
| `location` | สถานที่เก็บ | "OPD", "วอร์ด", "ER" |
| `recorder` | เจ้าหน้าที่จดขยะ | "อ้อย+อ้อย", "ปลา+เพ็ญ" |

> หมายเหตุ: เซลล์วันที่ที่ใช้ "น" หรือ "ง" = ditto (ซ้ำจากแถวบน) → ต้อง resolve ให้เป็นวันที่จริงก่อน output

## Claude API Prompt Design

```python
SYSTEM_PROMPT = """
You are a data extraction assistant for hospital waste reports (Thai hospital internal forms).
Extract all visible fields from the waste report image and return a JSON array — one object per row.

This form has 6 columns per row:
- row_number: sequence number (integer)
- date: recording date in YYYY-MM-DD (convert Thai Buddhist Era: subtract 543; "น" or "ง" = same as row above)
- time: time string as written (e.g. "15:00", "07:35น.")
- weight_kg: weight as float, null if blank
- location: collection point in Thai — see known values below
- recorder: staff name(s) as written, multiple people joined with "+"

LOCATION VOCABULARY (handwritten Thai shorthand — read carefully):
- วอร์ด  = Ward (inpatient area) — WARNING: often misread as จอดรถ (parking lot)
- เวช    = เวชกรรม (medical ward) — WARNING: often misread as ลาว
- OPD   = ผู้ป่วยนอก (outpatient)
- ER     = ห้องฉุกเฉิน (emergency)
- OPD+ER = both areas
- แผนไทย+ฝังเข็ม = Thai Traditional Medicine + Acupuncture (same zone)
- ฝังเข็ม = Acupuncture only
- โรงครัว = Kitchen

STAFF CONTEXT (use as confirmation hint, not override):
- OPD (afternoon)       → อ้อย + อ้อย (two staff with identical name)
- OPD (no date/time)    → กลอยใจ (special shift or coverage)
- วอร์ด                → ปลา and/or เพ็ญ (order may vary: ปลา+เพ็ญ or เพ็ญ+ปลา)
- แผนไทย+ฝังเข็ม       → หนึ่ง + เพ็ญ
- ER                   → กลอยใจ or ณฐอร; เพ็ญ covers ER night shifts (19:30น.+)
- โรงครัว              → ก (single character nickname)

DITTO RESOLUTION: When date cell contains "น", "ง", or a long dash/line,
copy the date from the nearest row above that has an explicit date.

If a field is illegible, set it to null.
Return ONLY a valid JSON array, no explanations, no markdown.
"""
```

## Python Code Sample

```python
import anthropic
import base64
import json
from pathlib import Path


def read_waste_report(image_path: str) -> dict:
    client = anthropic.Anthropic()

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    ext = Path(image_path).suffix.lower()
    media_type_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                      ".png": "image/png", ".webp": "image/webp"}
    media_type = media_type_map.get(ext, "image/jpeg")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract all fields from this hospital waste report form."
                    }
                ],
            }
        ],
        system=SYSTEM_PROMPT,
    )

    raw = message.content[0].text.strip()
    return json.loads(raw)


# ตัวอย่างใช้งาน
if __name__ == "__main__":
    result = read_waste_report("waste_report_2026_05_14.jpg")
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### ตัวอย่าง Output

```json
{
  "date": "2026-05-14",
  "department": "ตึกอายุรกรรมชาย",
  "waste_type": "มูลฝอยติดเชื้อ",
  "color_code": "แดง",
  "weight_kg": 8.5,
  "quantity": 3,
  "unit": "ถุง",
  "recorder": "นายสมชาย ใจดี",
  "supervisor": "นางสาวมาลี สุขใส",
  "notes": null
}
```

## Confidence Handling

กรณีที่ภาพไม่ชัด / ตัวเขียนยาก → เพิ่ม field `_confidence` ใน prompt:

```python
# เพิ่มใน SYSTEM_PROMPT
"""
Also include a "_confidence" field (0.0-1.0) indicating overall extraction confidence.
If confidence < 0.7, add "_unclear_fields" list with field names that were hard to read.
"""
```

## OCR Learning — Contextual Knowledge [verified 2026-05-21]

Pattern ที่เรียนรู้จากการตรวจสอบใบรายงานจริง (หน้า 1–3 ช่วง 30 เม.ย. – 14 พ.ค. 2569)

### สถานที่เก็บ — OCR Confusion Traps

| เขียนในฟอร์ม | ความหมาย | อ่านผิดเป็น | เหตุผล |
|---|---|---|---|
| วอร์ด | Ward (ผู้ป่วยใน) | จอดรถ | ลายมือ ว ≈ จ, อักษรท้ายคล้ายกัน |
| เวช | เวชกรรม | ลาว | ว-เ-ช กับ ล-า-ว รูปใกล้เคียงในลายมือ |
| แผนไทย+ฝังเข็ม | แพทย์แผนไทย + ฝังเข็ม | แผนไทย+ฝ่ายแม่ | สองแผนกในโซนเดียวกัน — ไม่ใช่ฝ่ายสูตินรี |

### เจ้าหน้าที่ประจำแผนก (Staff Directory)

| แผนก/โซน | เจ้าหน้าที่หลัก | หมายเหตุ |
|---|---|---|
| OPD (บ่าย) | อ้อย + อ้อย | สองคนชื่อเหมือนกัน ทำงานคู่กัน |
| วอร์ด | ปลา + เพ็ญ | มักคู่กัน บางรอบเพ็ญคนเดียว ลำดับสลับได้ (ปลา+เพ็ญ หรือ เพ็ญ+ปลา) |
| แผนไทย + ฝังเข็ม | หนึ่ง + เพ็ญ | ชั่งรวมทั้งสองแผนกในครั้งเดียว |
| ER | กลอยใจ, ณฐอร | สลับกันตามเวร; เพ็ญ cover ER กะดึก (19:30น.+) ได้ด้วย |
| OPD (ไม่มีวันที่/เวลา) | กลอยใจ | แถวที่ไม่ระบุวัน/เวลา อาจเป็นเวรพิเศษหรือแทนเวร |
| โรงครัว | ก | บันทึกเป็นอักษรเดียว (ชื่อย่อ) |
| เวช | ยังไม่ระบุ | ลายเซ็นที่ไม่รู้จัก — รอข้อมูลเพิ่ม |

### ชื่อเล่นที่ OCR อ่านผิดบ่อย

| ชื่อจริง | อ่านผิดเป็น |
|---|---|
| เพ็ญ | เพิ่ง |
| กลอยใจ | กอยง, กอวง |
| ณฐอร | แสงอร, อรจอร |
| อ้อย+อ้อย | บอนตลิ้ง (อ่านรวมเป็นคำเดียว) |

## Integration Points

- **IoT cross-check**: นำค่า `weight_kg` ไปเปรียบเทียบกับ sensor data จาก [[synthesis/waste-weight-monitoring]] (load cell บนถังขยะ)
- **Database**: บันทึกลง PostgreSQL / PocketBase บน Raspberry Pi 5 ([[entities/ai-tools/pocketbase]])
- **FastAPI endpoint**: รับ multipart image upload → return JSON → frontend แสดงผลตรวจสอบ
- **LINE integration**: webhook รับรูปจาก LINE → ส่ง OCR → ตอบกลับตาราง (อนาคต)
- **Web form auto-fill**: JSON output จาก OCR → aggregate → Playwright กรอกฟอร์มเว็บอัตโนมัติ → `scripts/fill-waste-form.py` | ดู [[synthesis/waste-form-automation]]

## ข้อจำกัด

| ปัญหา | วิธีรับมือ |
|-------|-----------|
| ลายมือแย่มาก | Claude Vision รับมือได้ดี แต่เพิ่ม `_unclear_fields` ให้ user ตรวจ |
| แบบฟอร์มแต่ละตึกต่างกัน | Prompt แบบ flexible (ไม่ผูกกับ layout เฉพาะ) |
| ภาพมืด/เบลอ | แจ้ง user ถ่ายใหม่ถ้า confidence < 0.6 |
| วันที่ พ.ศ. / ค.ศ. | Prompt สั่งให้ convert เป็น CE เสมอ |
| "วอร์ด" อ่านเป็น "จอดรถ" | ใส่ Location Vocabulary + OCR warning ใน SYSTEM_PROMPT |
| "เวช" อ่านเป็น "ลาว" | เช่นเดียวกัน — เพิ่ม known-value list |
| ditto mark (น/ง/—) | Prompt สั่ง resolve จากแถวบน ก่อน output |
| ชื่อเล่นสั้น (ก, ร, ส) | ยอมรับ null / unclear — ไม่ force guess |
| สองคนชื่อเหมือนกัน (อ้อย+อ้อย) | เก็บ string "อ้อย+อ้อย" ทั้งคู่ ไม่ตัดซ้ำ |
| น้ำหนัก 2 รายการในช่องเดียว (5+5) | เก็บเป็น string "5+5" ไม่บวกรวม — ให้ user ตัดสินใจ |
| ตัวเลขคล้ายกันที่อ่านผิดบ่อย | 2↔9, 6↔5, 1↔4 — double-check เสมอเมื่อน้ำหนักดูผิดปกติ |

## ความสัมพันธ์

- [[concepts/env/infectious-waste-management]] — ประเภทขยะ ระบบสีถุง กฎการบันทึกปริมาณ (ประกาศกรมอนามัย 2565)
- [[synthesis/waste-weight-monitoring]] — IoT weight sensor cross-check
- [[synthesis/pharmacy-order-checker]] — OCR architecture pattern ต้นแบบ (Claude Vision + JSON output)
- [[synthesis/appsheet-to-webapp-pi5]] — Platform: FastAPI + Raspberry Pi 5 สำหรับ deployment

## แหล่งข้อมูล

- [[sources/infectious-waste-th-law]] — กฎกระทรวงว่าด้วยการกำจัดมูลฝอยติดเชื้อ พ.ศ. 2545, 2564
- [training] Anthropic Claude Vision API documentation
