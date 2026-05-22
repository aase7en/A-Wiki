# Skill: Ask NotebookLM (via Gemini API)

**Trigger**: user ถามคำถามที่ต้อง synthesize >3-5 หน้าใน domain เดียว, ขอ overview, เปรียบเทียบหลายแหล่ง — และไม่ต้องการ paste กลับเองจาก NotebookLM Pro

**Cost Pyramid**: Level 1 (free Gemini API)

---

## เมื่อไหร่ใช้ vs ทางเลือกอื่น

| สถานการณ์ | เครื่องมือ |
|----------|-----------|
| ถาม keyword "อยู่หน้าไหน" | `wiki-search-local` (FTS5) |
| ถามแบบ synthesize >3 หน้า, จะตอบกลับใน chat | **skill นี้** |
| ต้องการคำตอบคุณภาพ NotebookLM Pro + audio overview | NotebookLM manual (upload bundle เอง) |
| งานสำคัญ / production decision | Claude Sonnet ตรง (Level 4) |
| Cross-domain (>1 domain) | บอก user ว่ายังไม่ support, ให้เลือก domain หลัก |

---

## Setup

```bash
# 1. Get free Gemini API key
open https://aistudio.google.com/apikey

# 2. Export (ใส่ใน ~/.zshrc สำหรับ persist)
export GEMINI_API_KEY=AIza...

# 3. ตรวจว่ามี bundle ของ domain นั้น
python3 scripts/ask-notebooklm.py --list
```

---

## Workflow

```bash
# Quick ask (bundle ต้องสดอยู่)
python3 scripts/ask-notebooklm.py --domain iot --query "MQTT vs CoAP tradeoffs"

# Refresh bundle ก่อนถาม (หลังแก้ wiki หลายไฟล์)
python3 scripts/ask-notebooklm.py --domain pharmacy --query "..." --refresh-bundle

# เช็คขนาด context ก่อนยิง (Flash 1M token, bundle ใหญ่สุดที่ส่ง ~200k)
python3 scripts/ask-notebooklm.py --domain iot --show-context-size

# List bundles + ขนาด
python3 scripts/ask-notebooklm.py --list
```

## Output

- คำตอบจาก Gemini Flash + cite source `[wiki/path/to/file.md]`
- ภาษาตรงกับคำถาม (Thai → Thai, EN → EN)
- ตอบ "ไม่ครอบคลุม" ถ้า context ไม่มีข้อมูล (กัน hallucinate)

---

## ข้อจำกัด

- Bundle เกิน 800 KB → truncate (head + tail). หาก domain ใหญ่จริง พิจารณาแยก sub-domain ใน `export-to-notebooklm.sh`
- ไม่มี GEMINI_API_KEY → fallback ให้ใช้ NotebookLM manual paste (skill จะแนะนำอัตโนมัติ)
- ภาษาไทยใน FTS5 unicode61 tokenize อาจไม่ตัดคำเพอร์เฟกต์ — ถ้าคำตอบไม่ตรง ลอง rephrase
- Gemini Flash free tier มี rate limit (~15 RPM, 1500 RPD ณ ปี 2026) — ดูที่ aistudio.google.com

---

## ความสัมพันธ์

- `export-notebooklm` skill — สร้าง bundle (เรียก `scripts/export-to-notebooklm.sh`)
- `wiki-search-local` — keyword search (ใช้ก่อนถ้าคำถามเป็น lookup)
- `docs/protocols/notebooklm.md` — manual NotebookLM workflow (เก็บไว้สำหรับงานคุณภาพสูง)
- CLAUDE.md §📘 NotebookLM-first Protocol
