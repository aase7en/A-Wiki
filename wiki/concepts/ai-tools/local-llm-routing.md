---
type: concept
tags: [llm, routing, ollama, cost-optimization, local-ai]
sources: [telegram-ai-router-design]
created: 2026-04-19
updated: 2026-04-19
---

# Local LLM Routing (Auto Model Switching)

## นิยาม
การตัดสินใจโดยอัตโนมัติว่า query ควรส่งไปประมวลผลที่ **local model** (ฟรี, latency สูงกว่า) หรือ **cloud API** (มีค่าใช้จ่าย, ฉลาดกว่า) โดยอิงจากความซับซ้อนของคำถาม

## ทำไมถึงสำคัญ
- Query ง่ายๆ ~70% ของการใช้งานทั่วไป ไม่จำเป็นต้องใช้ Claude/GPT
- ลดค่า API ได้มากโดยไม่ลดคุณภาพที่ผู้ใช้สังเกตเห็น
- รัน local model บน Mac Mini M1/M2 ได้จริง ไม่ต้องการ GPU แยก

## วิธีการทำงาน

```
Input query
     ↓
[Classifier] — ตรวจสอบ:
  • ความยาว (token count)
  • มีโค้ด/เทคนิคซับซ้อน?
  • เป็นงาน wiki (ingest/update)?
  • ต้องการ reasoning หลายขั้น?
     ↓
┌─────────────┬──────────────┬─────────────────┐
│ Simple      │ Wiki task    │ Complex/Code     │
│ Ollama      │ Gemini API   │ Claude API       │
│ (local/free)│ (ถูก)        │ (คุณภาพสูงสุด)  │
└─────────────┴──────────────┴─────────────────┘
```

## Routing Rules (ตัวอย่าง)

| เงื่อนไข | Model ที่เลือก | เหตุผล |
|---------|--------------|--------|
| query < 150 ตัวอักษร + ไม่มีโค้ด | Ollama local | คำถามทั่วไป |
| มีคำว่า ingest/wiki/สรุป | Gemini API | งาน wiki structured |
| มีโค้ด หรือ query > 500 ตัวอักษร | Claude API | ต้องการ reasoning |
| คำถามเกี่ยวกับ synthesis/วิเคราะห์ | Claude API | งาน cross-domain |

## Models ที่แนะนำสำหรับ Local (Ollama)

| Model | RAM | เหมาะกับ |
|-------|-----|---------|
| `llama3.2:3b` | 4 GB | คำถามทั่วไป, ไทย/อังกฤษ |
| `qwen2.5:7b` | 8 GB | ภาษาไทย ดีกว่า llama |
| `qwen2.5:14b` | 16 GB | เกือบเทียบ GPT-3.5 |
| `deepseek-r1:7b` | 8 GB | reasoning ดี |

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| ลดค่า API ~60-70% | latency local สูงกว่า 2-5 วินาที |
| Privacy — ข้อมูลไม่ออกจากบ้าน | ต้องมี Mac Mini เปิดตลอด |
| ปรับ route logic ได้เอง | classifier ต้อง tune เอง |
| รองรับ offline | local model ไม่ฉลาดเท่า cloud |

## ความสัมพันธ์
- ใช้ร่วมกับ: [[entities/ai-tools/telegram-ai-router]]
- ใช้ร่วมกับ: [[entities/ai-tools/ollama]]
- เกี่ยวข้องกับ: [[entities/ai-tools/hermes-agent]]

## แหล่งข้อมูล
- [[sources/telegram-ai-router-design]] — ออกแบบเอง 2026-04-19
