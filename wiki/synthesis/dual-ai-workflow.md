---
type: synthesis
tags: [gemini, claude, workflow, ai-tools, cost-optimization]
sources: [telegram-ai-router-design]
created: 2026-04-19
updated: 2026-04-19
---

# Dual AI Workflow — Gemini CLI + Claude

## คำถามที่ตอบ
จะใช้ Gemini CLI และ Claude ร่วมกันอย่างไรให้ประหยัด credit สูงสุด โดยไม่สูญเสียความต่อเนื่องของ context?

> หมายเหตุ: หน้านี้เน้น workflow ระหว่าง Gemini CLI กับ Claude เท่านั้น สำหรับการใช้งาน OpenRouter และ fallback free-model ให้ดู [[wiki/synthesis/openrouter-agent-routing]] และ [[concepts/ai-tools/openrouter-api]].

---

## ตาราง: งานไหนถาม Gemini / งานไหนถาม Claude

### ✅ ถาม Gemini CLI ก่อนเสมอ

| งาน | คำสั่งที่ใช้ |
|-----|------------|
| อ่านและสรุปไฟล์ใน `raw/` | "สรุปไฟล์ raw/ชื่อไฟล์.md ให้หน่อย" |
| สร้าง source page ใหม่ | "ingest raw/ชื่อไฟล์.md สร้าง wiki/sources/ ตาม GEMINI.md" |
| สร้าง entity/concept page (template ชัดเจน) | "สร้าง entity page สำหรับ [ชื่อ] ใน wiki/entities/iot/" |
| อัปเดต index-iot.md / index-env.md / index-ai.md | "อัปเดต index-iot.md เพิ่ม [ชื่อหน้า]" |
| append log.md | "เพิ่ม log entry สำหรับ [action] วันนี้" |
| ดูรายการไฟล์ใน wiki/ | "list ไฟล์ทั้งหมดใน wiki/entities/iot/" |
| ถามข้อมูลง่ายจากหน้าที่มีอยู่แล้ว | "ESP32 มีกี่ core?" / "LoRa ใช้ความถี่อะไรในไทย?" |
| นับหน้า / ตรวจ stats | "นับไฟล์ .md ใน wiki/ ทั้งหมด" |
| แก้ไขข้อความง่ายๆ ในหน้าเดียว | "แก้วันที่ updated ในไฟล์ X เป็น 2026-04-19" |
| **ค้นหา source ใหม่จาก web** | "ค้นหาข้อมูล [หัวข้อ] บันทึกลง raw/ ตาม Web Search Protocol" |

### 🧠 ถาม Claude เท่านั้น

| งาน | เหตุผล |
|-----|--------|
| `/lint` — ตรวจ contradiction + orphan pages | ต้องอ่านหลายหน้าพร้อมกันและ reason |
| Synthesis ข้ามโดเมน (IoT × Env) | ต้องเชื่อมโยง context ซับซ้อน |
| ออกแบบ schema / แก้ CLAUDE.md | ต้องเข้าใจ intent ทั้งระบบ |
| วิเคราะห์ contradiction ที่พบ | ต้องตัดสินว่าอันไหนถูก |
| ออกแบบระบบใหม่ (architecture) | ต้องการ reasoning หลายขั้น |
| คำถามที่ต้องการ "ความเห็น" หรือ tradeoff | Gemini ตอบ fact ได้ แต่ judgment ไม่เท่า |
| แก้ไขหลายไฟล์พร้อมกัน (atomic update) | Gemini อาจทำบางไฟล์พลาด |

---

## Handoff Protocol: Gemini → Claude

### Gemini ต้องทำเมื่อเสร็จงาน
เขียน entry ลงใน `handoff.md` format นี้:

```markdown
## [YYYY-MM-DD HH:MM] Gemini session

**งานที่ทำ:**
- สร้าง: wiki/sources/xxx.md
- อัปเดต: index-iot.md (เพิ่ม yyy)
- append: log.md

**context ที่ Claude ควรรู้:**
- [สิ่งที่น่าสนใจ / ข้อสังเกต / งานที่ค้างไว้]

**งานที่ยังไม่ทำ (ส่งต่อ Claude):**
- [ ] [งานที่ต้องการ Claude]
```

### Claude อ่าน handoff.md ก่อนเสมอ
เมื่อเริ่ม session ใหม่ Claude จะอ่าน handoff.md เพื่อรู้ว่า Gemini ทำอะไรไปแล้ว → ไม่ทำซ้ำ ต่อได้เลย

---

## Prompt Templates สำหรับ Gemini CLI

คัดลอกใช้ได้เลย:

### Ingest ไฟล์ใหม่
```
อ่านไฟล์ raw/[ชื่อไฟล์].md จาก repo ปัจจุบัน
สรุปประเด็นหลัก และสร้าง source page ใน wiki/sources/[slug].md
ตาม template ใน GEMINI.md
แล้วเพิ่ม log entry ใน log.md และ handoff.md
```

### อัปเดต entity page
```
อ่าน wiki/entities/iot/[ชื่อ].md จาก repo ปัจจุบัน
เพิ่มข้อมูล [X] ในหัวข้อ [Y]
อัปเดต updated date เป็น 2026-XX-XX
```

### ถามข้อมูลจาก wiki
```
อ่าน wiki/context/wiki-overview.md จาก repo ปัจจุบัน
แล้วตอบ: [คำถาม]
```

### บันทึก handoff หลังเสร็จงาน
```
เขียน entry ใหม่ใน handoff.md ของ repo ปัจจุบัน
สรุปสิ่งที่ทำในวันนี้ และงานที่ค้างไว้สำหรับ Claude
```

---

## ข้อจำกัดที่ต้องรู้ของ Gemini CLI (free tier)

| ข้อจำกัด | ผลกระทบ |
|---------|---------|
| shell ไม่ persist `cd` | ต้องใช้ absolute path เสมอ (แก้ใน GEMINI.md แล้ว) |
| ถูก restrict เป็น flash model | ตอบ reasoning ซับซ้อนได้ไม่ดี |
| ไม่มี memory ข้าม session | ต้องอ่าน wiki-overview.md ทุกครั้ง |
| อาจหยุดกลางคัน (context limit) | แบ่งงานเป็นชิ้นเล็ก |

---

## ความสัมพันธ์
- ใช้ร่วมกับ: [[entities/ai-tools/telegram-ai-router]]
- ใช้แนวคิด: [[concepts/ai-tools/local-llm-routing]]
- เกี่ยวข้องกับ: [[entities/ai-tools/hermes-agent]]
