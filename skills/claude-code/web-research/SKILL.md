---
name: web-research
description: Use this skill when the user asks you to find information from the web — price check, datasheet, alternatives, fact verification. Multi-engine auto-fallback. Model-agnostic.
---

# Web Research — Skill (Model-Agnostic)

> **วัตถุประสงค์**: ค้นหาข้อมูลจาก web — delegate ไปยัง model ฟรีที่เก่งเรื่องค้นหา
> **ทุก AI model อ่าน workflow นี้ได้** — ไม่เฉพาะ Claude Code
> **Last updated**: 2026-05-24

---

## ⚠️ กฎเหล็ก — ห้ามละเมิดเด็ดขาด

### 1. ❌ ห้ามใช้ training data — ต้องค้นหาจริงเท่านั้น
- ถ้า search engine / API ทั้งหมดใช้งานไม่ได้ → **ตอบว่า "ไม่สามารถค้นหาได้ในขณะนี้"**
- **ห้ามเดา ห้ามมโน ห้ามใช้ความรู้ภายใน AI** — ข้อมูลใหม่เปลี่ยนทุกวัน
- ข้อยกเว้น: ข้อมูล stable ที่ไม่เปลี่ยน เช่น protocol spec, กฎหมายหลัก → ระบุ `[training]`

### 2. ✅ ข้อมูลต้องใหม่ล่าสุดเท่านั้น
- ระบุวันที่ค้นหา + แหล่งที่มาทุกครั้ง
- ถ้าแหล่งเก่ากว่า 7 วัน → แจ้งผู้ใช้ว่าข้อมูลอาจล้าหลัง
- ถ้าเป็นราคา/version → ต้องค้นหาทุกครั้ง ไม่มีข้อยกเว้น

### 3. ✅ URL จริงเท่านั้น — ห้าม fabricate
- ทุก URL ต้องมาจากผลการค้นหาจริง
- ถ้าไม่แน่ใจว่า URL ถูกต้อง → ใช้ WebFetch ดึง content มาตรวจสอบ
- ถ้า WebFetch ก็ยืนยันไม่ได้ → ตัด URL นั้นทิ้ง

### 4. ✅ Source Traceability
- ทุกคำตอบต้องมี: `[source: <URL> | fetched: YYYY-MM-DD]`
- ถ้าบันทึกลง wiki → เพิ่ม note:
  ```
  > ข้อมูลตรวจสอบผ่าน [engine] เมื่อ YYYY-MM-DD | Source: <URL>
  ```

---

## เลือก Search Engine อัตโนมัติ (Auto-Fallback)

| Priority | Engine | API Key | Cost | ข้อดี |
|----------|--------|---------|------|-------|
| 1 | **OpenRouter Free** | `$OPENROUTER_API_KEY` | ฟรี (ต้องมี billing) | 28 free models — auto-select best |
| 2 | **Google AI Studio** | `$GOOGLE_AI_STUDIO_KEY` | ฟรี 60 req/min | ค้นหาเว็บได้ — ใช้ `gemini-2.5-flash` (model ล่าสุด) |
| 3 | **Groq** | `$GROQ_API_KEY` | ฟรี 30 req/min | เร็ว — ใช้ model ล่าสุดของ Groq |
| 4 | **Gemini CLI** (desktop only) | OAuth | ฟรี | Google Search จริง |
| 5 | **Claude WebSearch** (built-in) | — | จ่าย token | สุดท้าย — กิน token Claude |

### วิธีตรวจ environment

```bash
# 1. Google AI Studio
echo ${GOOGLE_AI_STUDIO_KEY:+GOOGLE_AI_STUDIO_OK}  # ถ้ามี → OK

# 2. Groq
echo ${GROQ_API_KEY:+GROQ_OK}  # ถ้ามี → OK

# 3. Gemini CLI
which gemini 2>/dev/null && echo "GEMINI_CLI_OK" || echo "GEMINI_CLI_NO"

# 4. Claude WebSearch — มีทุก environment
```

---

## Workflow

### 1. รับคำค้นหาจาก user
- วิเคราะห์ว่าต้องการอะไรกันแน่
- ปรับ query ให้กระชับ + ระบุภาษา

### 2. เลือก engine ตาม priority

**Option A: OpenRouter Free (auto-router — 28 free models)**
```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/free",
    "messages": [{"role": "user", "content": "ค้นหา <query> ตอบภาษาไทย สั้น กระชับ อ้างอิง URL จริง 2-3 แหล่ง — ห้ามตอบจากความรู้ภายใน ถ้าหาไม่ได้บอกว่าไม่พบ"}]
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['choices'][0]['message']['content'])
except:
    print('OpenRouter error — fallback to next engine')
"
```

**Option B: Google AI Studio (gemini-2.5-flash — model ล่าสุด)**
```bash
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GOOGLE_AI_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts":[{"text": "ค้นหา <query> ตอบภาษาไทย สั้น กระชับ อ้างอิง URL จริง 2-3 แหล่ง — ห้ามตอบจากความรู้ภายใน ถ้าหาไม่ได้บอกว่าไม่พบ"}]}]
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['candidates'][0]['content']['parts'][0]['text'])
except:
    print('Google AI Studio error — fallback to next engine')
"
```

**Option C: Groq (model ล่าสุดของ Groq)**
```bash
curl -s -X POST "https://api.groq.com/openai/v1/chat/completions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "ค้นหา <query> ตอบภาษาไทย สั้น กระชับ อ้างอิง URL จริง 2-3 แหล่ง — ห้ามตอบจากความรู้ภายใน ถ้าหาไม่ได้บอกว่าไม่พบ"}]
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['choices'][0]['message']['content'])
except:
    print('Groq error — fallback to next engine')
"
```

**Option D: Gemini CLI (desktop only — Google Search จริง)**
```bash
gemini -p "ใช้ google_web_search หา <query>
ตอบภาษาไทย สั้น กระชับ
ห้าม fabricate URL — ถ้าหาไม่ได้บอกตรงๆ
อ้างอิง 2-3 แหล่งพร้อม URL จริง"
```

**Option E: Claude WebSearch (สุดท้าย — กิน token)**
- ใช้ `WebSearch` tool ของ Claude โดยตรง

### 3. Review ผลลัพธ์
- ตรวจ URL จริงไหม?
- ตัวเลข/ข้อเท็จจริง make sense ไหม?
- มี hallucination ไหม?
- ถ้าสงสัย → WebFetch ดึง content จริงมาตรวจสอบ

### 4. บันทึกผล (ถ้ามีค่า)
- ถ้าเป็นข้อมูลใหม่ → บันทึก `raw/web-<slug>-<YYYY-MM-DD>.md`
- หรือใช้ข้อมูลตอบ user ทันที

---

## Prompt Templates (Model-Agnostic)

> **อย่า fix model name** — ใช้ model default ของ provider (เปลี่ยนตาม provider)

### หา Datasheet / Spec
```bash
# Google AI Studio
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GOOGLE_AI_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text": "หา datasheet PDF ของ <chip/module> spec: voltage, current, interface, frequency, package URL จริงจาก manufacturer หรือ distributor ตอบภาษาไทย"}]}]}'

# หรือ OpenRouter Free
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "openrouter/free", "messages": [{"role": "user", "content": "หา datasheet PDF ของ <chip/module> ตอบภาษาไทย"}]}'
```

### หาราคา Hardware
```bash
# Google AI Studio
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GOOGLE_AI_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text": "ราคา <device> ในไทยปัจจุบัน แหล่ง: Shopee, Lazada, Cytron, ThaiEasyElec ราคาเป็นบาท — อัปเดตล่าสุดเมื่อไหร่ URL จริง"}]}]}'

# หรือ Gemini CLI (Google Search จริง)
gemini -p "ราคา <device> ในไทยปัจจุบัน อ้างอิง URL จริง"
```

### เปรียบเทียบ Alternatives
```bash
# OpenRouter Free
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "openrouter/free", "messages": [{"role": "user", "content": "เปรียบเทียบ <A> vs <B> 5 มิติ: ราคา, ประสิทธิภาพ, ความง่าย, ecosystem, community URL จริงของแต่ละตัว ตอบภาษาไทย ตาราง"}]}'
```

### Verify Fact
```bash
# Google AI Studio
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GOOGLE_AI_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text": "ตรวจสอบข้อเท็จจริง: <claim> หาแหล่งที่มายืนยันหรือคัดค้าน URL จริง 2-3 แหล่ง ตอบภาษาไทย"}]}]}'
```

---

## ตัวอย่างการใช้งานจริง

### User: "หาราคา ESP32-S3 DevKit ในไทย"
```
→ ตรวจ environment → มี GOOGLE_AI_STUDIO_KEY
→ ส่ง curl ไป gemini-2.5-flash
→ ได้ผลลัพธ์: 280-350 บาท พร้อม URL (ThaiEasyElec, Gravitechthai, ArduinoAll)
→ review → ตอบ user พร้อม URL
→ ประหยัด Claude token: ~200 tokens (แค่ review)
```

### User: "DX-LR02 datasheet"
```
→ ตรวจ environment → GOOGLE_AI_STUDIO_KEY ล้มเหลว
→ Fallback ไป Groq → สำเร็จ
→ ได้ URL → WebFetch ดึง datasheet จริง
→ สรุป spec → ตอบ user
```

---

## ห้าม
- fabricate URL หรือข้อมูล
- ใช้ Claude WebSearch ถ้า Google AI Studio / Groq / Gemini CLI ใช้ได้
- ให้ AI ภายนอกเขียนไฟล์ลง wiki โดยตรง (Claude ต้อง review + save เอง)
- ใช้ skill นี้กับข้อมูลที่ stable และมีใน wiki อยู่แล้ว