# Delegation Protocols — Free Models, Subagent, Auto-Delegate

> อ่านไฟล์นี้เมื่อ root CLAUDE.md บอกให้ delegate — ไม่ auto-loaded

---

## Free Models & Cheap Paid (Level 1-2 ใน Cost-First Pyramid)

### Free Models ที่ใช้ได้ทันที (Level 1)
- **OpenRouter free**: `deepseek/deepseek-r1:free`, `meta-llama/llama-3.3-70b-instruct:free`, `qwen/qwen-2.5-72b-instruct:free`
- **Gemini Flash**: ฟรี 60 req/min — ใช้ `GOOGLE_AI_STUDIO_KEY`
- **Groq**: ฟรี 30 req/min — ใช้ `GROQ_API_KEY`

### Cheap Paid Models ที่คุ้มค่า (Level 2)
- **DeepSeek V3**: reasoning + code, ถูกกว่า Claude ~10x
- **Qwen2.5-72B**: multilingual (ไทย+อังกฤษ), ถูก
- **Gemini Flash 2.0**: เร็ว, ถูก, web grounding ดี

### กฎ Token เพิ่มเติม
- **Prompt ที่ส่งไป free/cheap model → ใช้ภาษาอังกฤษเสมอ** (ประหยัด ~30% vs ไทย)
- ตอบ user → ใช้ภาษาไทยตามปกติ

---

## 🤖 Delegate to Free Models (ประหยัด Claude token)

> **หลักการ**: งานเบาที่ verifiable (web search, lookup, สรุป URL) → โยน model ฟรีทำ
> Claude เป็น orchestrator + reviewer + writer ของ wiki

### เครื่องมือ (Model-Agnostic)

เครื่องมือ delegate แต่ละตัวใช้ model default ของ provider — model เปลี่ยนได้ตลอด อย่า fix model name ตายตัว

| Engine | ใช้เมื่อ | วิธีเรียก |
|--------|---------|----------|
| **Web Research Layer** | ค้นหา web หลายแหล่ง — priority สูงสุด | ตาม `tools/prompts/web-research.md` (auto-fallback) |
| **Gemini CLI** | desktop local — Google Search จริง | `gemini -p "prompt"` — ใช้ default model ของ Gemini CLI |
| **WebSearch** (built-in) | mobile / cloud env (กิน token Claude) | Tool `WebSearch` ของ Claude |
| **OpenRouter** | fallback สุดท้าย | `curl` ผ่าน API key, ใช้ `openrouter/auto` |

### ✅ เมื่อไหร่ควร Delegate

| งาน | ตัวอย่าง |
|---|---|
| Web search หลายแหล่ง | ค้นหาราคา X จาก Cytron, Shopee, Lazada |
| หา datasheet / spec | หา datasheet PDF ของ chip |
| สรุปบทความยาวจาก URL | สรุป URL 5 ข้อหลัก |
| ตรวจราคา hardware ปัจจุบัน | ราคา ESP32-S3 ปัจจุบันในไทย |
| เปรียบเทียบ alternatives | เทียบ MQTT broker free 3 ตัว |

### ❌ ห้าม Delegate เมื่อ
- งานต้อง reasoning ลึก (synthesis, contradiction check, lint)
- งานต้องเข้าใจ schema wiki แม่น (สร้าง entity page, edit wiki)
- งาน sensitive (auth, security review, แก้ CLAUDE.md)
- งานง่ายที่ Claude ทำเองเร็วกว่าโดยไม่เปลือง token มาก

### Workflow

```
1. Claude วิเคราะห์ task → ตรงกับ ✅ ข้างบน?
2. ตรวจ environment → เลือก engine ตาม priority:
   - Google AI Studio / Groq API key มี → ใช้ curl ส่ง (ฟรี ไม่กิน token)
   - Gemini CLI มี (desktop) → gemini -p "..."
   - ไม่มีทั้งคู่ → Claude WebSearch tool (กิน token Claude)
3. ส่ง prompt (ห้าม fabricate URL + ภาษาไทย)
4. รับ output → review:
   - URL จริงไหม? (verify สำคัญๆ ก่อน commit)
   - ตัวเลข/ข้อเท็จจริง make sense ไหม?
   - มี hallucination ไหม?
5. ถ้า OK → ใช้ข้อมูล / save raw / ตอบ user
6. ถ้าสงสัย → verify ด้วย WebFetch / ถาม user
```

### Prompt template (model-agnostic)

```
ค้นหา <X>
ตอบภาษาไทย สั้น กระชับ
ห้าม fabricate URL — ถ้าหาไม่ได้บอกตรงๆ
อ้างอิง 2-3 แหล่งพร้อม URL จริง
```

### ข้อจำกัดที่ต้องรู้
- Model ฟรี (Google AI Studio / Groq) อาจมี rate limit / reasoning ตื้น → ถ้าล้มเหลว fallback ไป engine ถัดไป
- เฉพาะ Claude Code เท่านั้นที่มี execute_command / write_file / edit tools → API ฟรีผ่าน curl ต้องให้ Claude save ไฟล์เอง
- Gemini CLI ถ้า env var GEMINI_API_KEY ถูก set → fallback ไป API tier (โควต้าน้อย) → unset ก่อนเรียก

---

---

## 🧩 Subagent Delegation (กัน context หลักไม่ให้บวม)

> **หลักการ**: งานที่ต้อง scan/อ่านไฟล์เยอะ → โยน subagent ทำ ส่งกลับมาแค่สรุป
> Claude หลักเก็บ context ไว้สำหรับ reasoning + writing — ลด token 30-50% ในงานใหญ่

### Subagent vs Gemini Delegate (อย่าสับสน)

| เลือก | งาน | ข้อมูลอยู่ที่ไหน |
|---|---|---|
| **Subagent** (Explore / general-purpose) | งานที่ต้องอ่านไฟล์ใน repo ของเรา | ใน wiki ของเรา |
| **Gemini CLI** | web search / external lookup | ภายนอก / web |
| **WebSearch** (Claude built-in) | mobile / cloud env ที่ Gemini ไม่มี | ภายนอก / web |
| **NotebookLM Pro** (user paste) | synthesize หลาย wiki page ที่ pre-indexed แล้ว | snapshot ของ wiki ใน NotebookLM |

### เครื่องมือ Subagent

| Subagent | ความสามารถ | เมื่อไหร่ใช้ |
|---|---|---|
| `Explore` (read-only) | ค้น/locate ในไฟล์เยอะ — ไม่แก้ไฟล์ได้ | "หาทุกหน้าที่กล่าวถึง MQTT QoS" |
| `general-purpose` | อ่าน + วิเคราะห์ + เขียนได้ครบ tools | สรุป source 3000+ บรรทัด, lint ทั้ง wiki |

### ✅ เมื่อไหร่ควร Delegate Subagent

- **`/lint`** → `general-purpose` สแกนทั้ง `wiki/` หา orphan/contradiction/stub → ส่งสรุปกลับ
- **คำถามที่ต้องอ่าน >5 หน้า** → `general-purpose` อ่าน+สรุป
- **Ingest source >2,000 บรรทัด** → `general-purpose` สรุป → Claude หลักเขียน wiki page
- **Cross-domain query** ที่ต้องอ่านหลาย index → `general-purpose`
- **ค้น "ที่ไหนกล่าวถึง X"** ที่ผลอาจกระจายหลายโฟลเดอร์ → `Explore`

### ❌ ห้ามใช้ Subagent เมื่อ

- คำถามที่อ่าน 1-2 หน้าก็ตอบได้ — overhead เกินคุ้ม
- งานเขียน wiki page เดียว — Claude หลักทำเองรักษา consistency กับ schema ดีกว่า
- งานที่ต้อง user approval ระหว่างทำ — subagent ถาม user ไม่ได้
- งาน sensitive (security review, แก้ CLAUDE.md, แก้ raw/) — Claude หลักเท่านั้น
- งานที่ต้องดูภาพรวม conversation — subagent ไม่เห็น history

### Workflow

```
1. Claude ประเมิน task → match ✅ ข้างบน?
2. ถ้าใช่ → เรียก subagent พร้อม prompt self-contained:
   - context ที่ subagent ต้องรู้ (paths, schema สั้น ๆ)
   - คำถาม/งานที่ต้องทำ
   - format output ที่ต้องการ (เช่น "ตอบเป็น bullet ไม่เกิน 10 ข้อ")
   - ขอบเขตห้าม (ห้ามเขียนไฟล์ใหม่ / ห้ามแก้ raw/)
3. รับสรุปกลับ → review ความน่าเชื่อถือ → ใช้ตอบ user / เขียน wiki
```

### Prompt Template สำหรับ Subagent (Wiki)

```
[context]
- Wiki schema: kebab-case .md ใน wiki/{entities,concepts,sources,synthesis}/{iot,env,ai-tools,pharmacy}
- Fast-load: wiki/context/wiki-overview.md (อ่านก่อนเสมอ)
- ห้ามแก้: raw/, CLAUDE.md, .claude/

[งาน]
<task ชัดเจน — เป้าหมาย + ขอบเขต + criteria สำเร็จ>

[output]
<format ที่ต้องการ — bullet / table / Markdown section>
ตอบเป็นภาษาไทย กระชับ ไม่เกิน <X> ข้อ

[ห้าม]
- เขียนไฟล์ใหม่ (ให้ Claude หลักทำ)
- แก้ raw/ หรือ CLAUDE.md
- ตอบจาก training อย่างเดียวเรื่อง time-sensitive
```

### ตัวอย่างจริง

- User: `/lint` → Claude เรียก `general-purpose`:
  > "scan `wiki/` ทั้งหมด รายงาน orphan pages, contradictions, stub concepts ที่ถูก link แต่ยังไม่มีหน้า, stale pages (last_verified > 90 วัน) — ตาม CLAUDE.md > Workflow: Lint Wiki ตอบเป็น 5 sections — ห้ามแก้ไฟล์"

- User: "สรุปบทความใน `raw/articles/long-iot-paper.md`" (3,500 บรรทัด) → Claude เรียก `general-purpose`:
  > "อ่าน `raw/articles/long-iot-paper.md` สรุปประเด็นหลัก 5 ข้อ + entities ที่ปรากฏ + concepts ที่ปรากฏ + ข้อมูลขัดแย้งกับ wiki ปัจจุบัน — ห้ามเขียนไฟล์"

- User: "หาทุกหน้าที่พูดถึง LoRa ใน wiki" → Claude เรียก `Explore`:
  > "หา .md ใน wiki/ ที่กล่าวถึง 'LoRa' หรือ 'LoRaWAN' — ส่ง path + 1 บรรทัด context ของแต่ละ match"

---

---

## 🎯 Auto-Delegate Trigger Rules (ประหยัด token อัตโนมัติ)

> **หลักการ**: คำถามบางประเภท → Claude delegate ไปยัง model ฟรีให้ตอบก่อน → Claude review → ตอบ user
> **เป้าหมาย**: ลด token Claude 60-80% สำหรับงาน lookup/search

### Auto-Fallback Chain (5 Engines — ตรวจสอบ environment อัตโนมัติ)

```
1. OpenRouter Free (`openrouter/free` auto-router)
   → 28 free models — auto-select best
   → ล้มเหลว / rate limit?

2. Google AI Studio (`gemini-1.5-flash`)
   → ฟรี 60 req/min — ใช้ GOOGLE_AI_STUDIO_KEY
   → ล้มเหลว?

3. Groq (model ล่าสุดที่มี)
   → ฟรี 30 req/min — ใช้ GROQ_API_KEY
   → ล้มเหลว?

4. Gemini CLI (`gemini -p`)
   → Google Search จริง — desktop only
   → ล้มเหลว?

5. Claude WebSearch (built-in) ← สุดท้าย กิน token Claude
```

### 🛠️ Production Wrapper: `scripts/delegate.sh`

ทุก agent (Claude / Codex / Gemini CLI) เรียก **wrapper เดียว** แทน craft curl เอง:

```bash
scripts/delegate.sh <task_type> "<english_prompt>"
# task_type: search | lookup | summarize | reason | compare | scan
# stdout: response text
# exit:   0=ok, 1=engines failed, 2=no API keys, 3=bad args
```

Wrapper routing:
- `search/lookup/summarize` → tier 1 (free): OpenRouter free → Gemini → Groq
- `reason/compare` → tier 2 (cheap paid): OpenRouter auto → DeepSeek → Gemini Flash
- `scan` → tier 3 (subagent): GPT-4o-mini → DeepSeek → Claude Haiku

ดู [.codex/AGENTS.md](../../.codex/AGENTS.md) สำหรับ task_type table + examples (ใช้ได้กับทุก agent ไม่เฉพาะ Codex)

### ตรวจ Environment

```bash
# OpenRouter
echo ${OPENROUTER_API_KEY:+OPENROUTER_OK}

# Google AI Studio
echo ${GOOGLE_AI_STUDIO_KEY:+GOOGLE_AI_STUDIO_OK}

# Groq
echo ${GROQ_API_KEY:+GROQ_OK}

# Gemini CLI
which gemini 2>/dev/null && echo "GEMINI_CLI_OK"
```

### Trigger Patterns — คำถามไหนควร delegate

| คำถามต้นแบบ | ตรวจเจอจาก | Delegate ไป | เพราะ |
|------------|------------|-------------|-------|
| "ราคา X ในไทย" / "ล่าสุดกี่บาท" | คำ: ราคา, ล่าสุด, ตอนนี้, กี่บาท | OpenRouter Free → Groq → Gemini CLI | time-sensitive ต้อง search |
| "หา datasheet / spec X" | คำ: datasheet, spec, data sheet | Gemini CLI (Google Search จริง) | ต้อง search engine |
| "สรุปบทความ / URL นี้" | คำ: สรุป, อ่าน, เนื้อหา, URL | OpenRouter Free → Google AI Studio | long context — free ทำได้ |
| "ตรวจสอบข้อเท็จจริง / verify" | คำ: ตรวจ, จริงไหม, verify, fact-check | OpenRouter Free → Google AI Studio | fact-check |
| "เปรียบเทียบ A vs B" | คำ: เปรียบเทียบ, ต่างกัน, vs | OpenRouter Free → Groq | table — simple |
| "รุ่นใหม่ของ X มีอะไร" | คำ: รุ่นใหม่, อัปเดต, version, new | OpenRouter Free → Gemini CLI | time-sensitive |

### ❌ ห้าม Delegate (ให้ Claude คิดเอง)

- งาน reasoning ซับซ้อน (synthesis, architecture design)
- เขียน/แก้ไข wiki page
- งาน sensitive (แก้ CLAUDE.md, raw/)
- งานที่ต้อง tools (write_file, edit) — model ฟรีไม่มี tools
- คำถามที่ตอบจาก wiki/ ของเราได้เลย (ข้อมูลมีอยู่แล้ว)

### Workflow Auto-Delegate

```
User ถาม → Claude วิเคราะห์
    ↓
ตรงกับ Trigger Pattern?
    ├─ ใช่ → ตรวจ environment:
    │         OpenRouter key? → curl openrouter/free
    │         Google AI Studio key? → curl gemini-flash
    │         Groq key? → curl Groq
    │         Gemini CLI? → gemini -p
    │         ไม่มีเลย → Claude WebSearch (กิน token)
    │    → model ฟรีตอบกลับ → Claude review + ตรวจ URL จริง
    │    → ตอบ user พร้อม [source: engine | verified YYYY-MM-DD]
    │
    └─ ไม่ → Claude ตอบจากความรู้ + wiki + tools
```

