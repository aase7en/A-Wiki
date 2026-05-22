# Knowledge Currency Protocol — รับมือข้อมูลล้าหลัง

> อ่านไฟล์นี้เมื่อต้องตอบข้อมูล time-sensitive หรือหลัง Aug 2025

---

## 🧠 Knowledge Currency Protocol (รับมือข้อมูลล้าหลัง)

> **กฎเหล็ก**: Claude training cutoff = สิงหาคม 2025 — ข้อมูลหลังจากนั้น **ห้ามเดา ห้ามมโน** → delegate เสมอ

### หมวดข้อมูลตาม Risk Level

| Risk | ประเภทข้อมูล | วิธีจัดการ |
|------|-------------|-----------|
| 🟢 ต่ำ | protocols พื้นฐาน (MQTT, HTTP), concepts ที่ stable, กฎหมายหลัก | Claude ตอบได้เลย — ระบุ "ข้อมูลจาก training" |
| 🟡 กลาง | ราคา hardware, version ซอฟต์แวร์, API spec | ระบุความไม่แน่ใจ → delegate ก่อนตอบ |
| 🔴 สูง | AI models/products ใหม่, ข่าวล่าสุด, ผลิตภัณฑ์ที่ออกหลัง Aug 2025 | **delegate ก่อนเสมอ ไม่มีข้อยกเว้น** |

### Decision Tree

```
คำถามมาถึง Claude
    ↓
ข้อมูลนี้อยู่ใน training + ไม่เปลี่ยนบ่อย?
    ├─ ใช่ → ตอบได้เลย (บอก user ว่าข้อมูลจาก training cutoff Aug 2025)
    └─ ไม่แน่ใจ / เปลี่ยนบ่อย / หลัง Aug 2025
           ↓
       เลือก delegate tool (auto-fallback ตาม environment):
           ├─ 1. Web Research Layer (Google AI Studio / Groq API)
           │    → ฟรี ไม่กิน Claude token — curl ส่งตรง API (ใช้ model default)
           ├─ 2. Gemini CLI (desktop only)
           │    → Google Search จริง — gemini -p (default model)
           ├─ 3. WebSearch (Claude built-in)
           │    → ใช้ได้ทุก env — กิน token Claude
           ├─ 4. WebFetch (ถ้ารู้ URL แน่นอน)
           │    → ดึง content จริงมาตรวจสอบ
           └─ 5. OpenRouter API (fallback สุดท้าย)
                → ใช้ openrouter/auto หรือ model ฟรีที่มี
           ↓
       รับผล → Claude review → ตรวจ hallucination → cite source → ตอบ user
```

### ตรวจ Environment ก่อนเลือก Tool (ทำอัตโนมัติ)

```
Claude อยู่บน cloud (iPhone/Web)?
  └─ Google AI Studio ❌ (ไม่มี key)       └─ Groq ❌ (ไม่มี key)
  └─ Gemini CLI ❌ ไม่มี                    └─ WebSearch ✅ primary

Claude อยู่บน local (Mac/Windows)?
  └─ Google AI Studio ✅ (ถ้ามี key)       └─ Groq ✅ (ถ้ามี key)
  └─ Gemini CLI ✅ (google_web_search)     └─ WebSearch ✅ fallback
  └─ OpenRouter ✅ (ถ้ามี key)
```

**วิธีตรวจ**: `echo ${GOOGLE_AI_STUDIO_KEY:+OK}` / `which gemini` / `echo ${GROQ_API_KEY:+OK}` — ถ้าไม่มี → fallback auto

### เครื่องมือ Delegate ทั้งหมด (Model-Agnostic)

**1. Web Research Layer** — ฟรี, ใช้ API key ตรง (ดู `tools/prompts/web-research.md`)
```bash
# ใช้ model default ของ provider — เปลี่ยนตาม provider ไม่ fix model name
```
- ข้อดี: ไม่กิน Claude token (Claude แค่ review + save)
- ข้อเสีย: ต้องมี API key, reasoning ตื้นกว่า Claude

**2. Gemini CLI** — local only, ฟรี (ใช้ default model)
```bash
gemini -p "ใช้ google_web_search หา <X>
ตอบภาษาไทย — ห้าม fabricate URL — อ้างอิง URL จริง 2-3 แหล่ง"
```

**3. WebSearch** (Claude built-in)
- ใช้ได้ทุก env (รวม mobile) — ใช้เมื่อ API ฟรี + Gemini CLI ไม่ available

**4. OpenRouter** — fallback สุดท้าย, ใช้ `openrouter/auto`
```bash
# ต้องการ OPENROUTER_API_KEY ใน env
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/auto",
    "messages": [{"role": "user", "content": "<prompt>"}]
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```
- `openrouter/auto` = ให้ OpenRouter เลือก model ให้ (เริ่มจากฟรี/ถูก)

**5. WebFetch** (Claude built-in)
- ใช้เมื่อรู้ URL ที่แน่นอน (official docs, changelog, GitHub release)

### Source Traceability (บังคับทุกครั้ง)

ทุกข้อมูลที่ได้จาก delegate ต้อง:
1. ระบุ URL แหล่งที่มาจริง (ห้าม fabricate)
2. ระบุวันที่สืบค้น
3. ถ้าบันทึกลง wiki → เพิ่ม note ท้ายย่อหน้า:
   ```
   > ข้อมูลตรวจสอบผ่าน [Gemini/OpenRouter/WebFetch/NotebookLM] เมื่อ YYYY-MM-DD | Source: <URL>
   ```

### ตัวอย่างที่ต้อง Delegate (ห้ามตอบจาก training อย่างเดียว)

- "Claude Design / Canva AI feature ใหม่คืออะไร?" → AI product หลัง Aug 2025 → delegate
- "iPhone 17 spec?" → ผลิตภัณฑ์หลัง Aug 2025 → delegate
- "ราคา ESP32 ปัจจุบัน?" → ราคาเปลี่ยนบ่อย → delegate
- "Gemini / GPT model ล่าสุดคืออะไร?" → AI race เปลี่ยนแทบทุกสัปดาห์ → delegate
- "open-source project X ยังมีคนดูแลอยู่ไหม?" → สถานะ project → delegate

---

---
