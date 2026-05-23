---
type: synthesis
tags: [pharmacy, web-app, claude-api, ocr, fuzzy-match, drug-ordering]
sources: [sp-drugstore-2020-catalog]
created: 2026-04-29
updated: 2026-04-30
---

# ระบบตรวจสอบรายการสั่งยา (Pharmacy Order Checker)

## บริบทโปรเจกต์
- **ชื่อร้าน**: ภูฟาร์มาซี (สมุทรปราการ)
- **เจ้าของ**: คุณAase7en
- **Supplier หลัก**: เอสพีดรักสโตร์ 2020

## คำถามที่ตอบ
"จะสร้างระบบ AI ที่ช่วยตรวจสอบรายการยาที่ลูกน้องส่งมาทาง Line ได้อย่างไร?"

## สรุป
รับ input เป็นข้อความหรือรูปภาพรายการยา (ที่มักสะกดผิดหรือใช้ชื่อเล่น) → AI วิเคราะห์และ match กับ drug database โดยใช้ [[wiki/concepts/pharmacy/drug-aliases]] → แสดงตารางสรุปข้อมูลที่ถูกต้องให้เจ้าของยืนยัน → export สั่งซื้อ

## Architecture

```
[ลูกน้อง ส่ง Line]
      ↓ copy-paste หรือ upload รูป
[Web App (FastAPI + React)]
      │
      ├─ Input: paste text หรือ upload image
      │         ↓ (ถ้าเป็นรูป)
      │     [Claude API — Vision/OCR]
      │         ↓
      │     extracted text
      │
      ├─ [Claude API — Drug Validation]
      │   system prompt: "คุณคือผู้ช่วยตรวจสอบรายการยา
      │                    ฐานข้อมูล: [drug database JSON]
      │                    ตรวจสอบชื่อยา ขนาด หน่วย"
      │         ↓
      │   JSON: [{name, strength, unit, confidence, matched_code}]
      │
      └─ [แสดง Form]
            ตาราง Output ที่ต้องการ:
            | ชื่อที่ลูกน้องส่งมา | ชื่อที่ถูกต้อง | ขนาด | หน่วยสั่งซื้อ | จำนวน |
            |-------------------|-------------|------|-------------|------|
            | อม็อก 500         | AMOXYCILLIN | 500mg| ก.50แผง     | 5    |
            | พารา              | PARACETAMOL | 500mg| ก.50แผง     | 3    |
            
            (ปุ่ม: [ยืนยันรายการ] [แก้ไข] [เพิ่มรายการด้วยมือ])
```

## Tech Stack

| Layer | เทคโนโลยี | หมายเหตุ |
|-------|-----------|---------|
| Frontend | React + Tailwind | เดิมมีแผนแล้ว |
| Backend | FastAPI (Python) | เดิมมีแผนแล้ว บน Pi5 |
| Database | JSON file หรือ PostgreSQL | drug catalog |
| AI | Claude API (claude-sonnet-4-6) | Vision + Text (High confidence matching) |
| OCR | Claude Vision API | รองรับลายมือและข้อความจากรูป Line |
| Logic | Fuzzy Matching | อ้างอิง [[wiki/concepts/pharmacy/drug-aliases]] |
| Host | Raspberry Pi 5 | เปิดตลอด |
| Access | Tailscale | เข้าจากมือถือ/โรงพยาบาล |

## Claude API Prompt สำหรับ Drug Validation

```python
SYSTEM_PROMPT = """
คุณคือผู้ช่วยตรวจสอบรายการสั่งซื้อยาสำหรับร้านขายยา "ภูฟาร์มาซี" (เจ้าของ: คุณAase7en)

ฐานข้อมูลยาหลัก (เอสพีดรักสโตร์ 2020):
{drug_database_sample}

กฎการทำงาน:
1. รับรายการยาที่อาจสะกดผิด (เช่น อม็อก, พารา), ตัวย่อ หรือชื่อไม่ชัดเจน
2. Match กับชื่อยาในฐานข้อมูล (ดูรายการ aliases ในระบบ)
3. ระบุ "หน่วยสั่งซื้อ" ให้ถูกต้องตามระบบร้าน:
   - "กล่อง": เช่น ก.10แผง, ก.50แผง
   - "ขวด": น้ำเชื่อม/ยาน้ำ
   - "กระปุก": ยาเม็ดขนาดใหญ่ (500-1000 เม็ด)
   - "แผง": กรณีสั่งแยก
4. แสดงผลเป็น JSON format สำหรับตารางตรวจสอบ

Output format:
[
  {
    "input": "อม็อก 500",
    "matched_name": "AMOXYCILLIN 500mg",
    "matched_code": "902500/1",
    "strength": "500mg",
    "unit": "ก.50แผง",
    "confidence": 0.95,
    "note": ""
  }
]
"""
```

## Drug Database JSON Format

```json
{
  "drugs": [
    {
      "code": "902500/1",
      "name": "AMOXYCILLIN 500",
      "generic": "Amoxicillin",
      "strength": "500mg",
      "form": "เม็ด",
      "unit": "ก.50แผง",
      "category": "J01",
      "aliases": ["amox", "อม็อก", "amoxil", "a.m.mox", "amoxycillin"]
    }
  ]
}
```

## Phases

| Phase | งาน | สถานะ |
|-------|-----|-------|
| 1 | สร้าง drug database JSON จาก PDF | ✅ ทำแล้ว (3,760 records) |
| 2 | สร้าง simple web page: paste text → Claude validate | 🔵 วางแผน |
| 3 | เพิ่ม image upload + OCR | 🔵 วางแผน |
| 4 | สร้าง order form + export | 🔵 วางแผน |
| 5 | ต่อกับ Pi5 FastAPI backend | 🔵 วางแผน |
| 6 | เพิ่ม supplier database อื่นๆ | 🔵 วางแผน |

## ความสัมพันธ์

- [[concepts/pharmacy/pharmacy-context]] — ข้อมูลร้านและหน่วยสั่งซื้อ (หัวใจหลักของ logic)
- [[concepts/pharmacy/drug-aliases]] — ฐานข้อมูลการแปลงชื่อ
- [[concepts/pharmacy/ordering-workflow]] — workflow ภาพรวม
- [[concepts/pharmacy/drug-classification]] — หมวดยา ATC
- [[synthesis/appsheet-to-webapp-pi5]] — Pi5 web app platform
- [[entities/ai-tools/telegram-ai-router]] — Telegram integration อนาคต
