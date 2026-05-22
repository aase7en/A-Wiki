---
name: web-research
description: Use this skill when the user asks to search for information on the web, find datasheets/prices/specs, or verify facts that require up-to-date data. Full workflow in docs/protocols/delegation.md (model-agnostic).
---

# web-research

ใช้เมื่อต้องการค้นหาข้อมูลจาก web — delegate ไปยัง API/model ฟรี หลีกเลี่ยงการใช้ Claude WebSearch (กิน token)

## Auto-Route (Cost Pyramid — ทำก่อนใช้ Claude tools เสมอ)

```
bash scripts/delegate.sh search "<query in English>"
```
- ถ้าได้ผลลัพธ์ → ใช้เลย ไม่ต้องเรียก Claude WebFetch/WebSearch
- ถ้า delegate.sh ไม่พร้อม → fall back ไป engine ด้านล่าง
- รายละเอียด engine chain: `docs/protocols/delegation.md`

## ขั้นตอนย่อ

1. รัน `bash scripts/delegate.sh search "<query>"` ก่อนเสมอ (Tier-1 free)
2. ถ้า delegate.sh ไม่พร้อม → เลือก engine: OpenRouter Free → Gemini → Groq → Gemini CLI → Claude WebSearch
   - **อย่า fix model name** — provider อัปเดต model ตลอด ใช้ default
3. ส่ง search → review ผลลัพธ์ (ตรวจ URL จริง, hallucination, make sense?)
4. ตอบ user หรือบันทึก `raw/web-<slug>-<date>.md`

## กฎ
- prompt ส่งออก → ภาษาอังกฤษเสมอ (ประหยัด ~30%)
- ห้าม fabricate URL — ถ้าหาไม่ได้บอกตรงๆ
- verified ด้วย WebFetch ก่อน commit สำคัญ
