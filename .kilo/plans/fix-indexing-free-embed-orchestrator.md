# Plan: แก้ Indexing Error (Gemini free) + อธิบาย Orchestrator Deprecation

## สถานะ: พร้อม execute (รอ user วาง key ใน .env)

---

## ส่วนที่ 1: แก้ Indexing Error → Gemini free tier

### สาเหตุ
`.kilo/kilo.jsonc` ใช้ `provider: "kilo"` + `mistralai/mistral-embed-2312` = **Kilo Gateway ต้องการ credits (เสียเงิน)** → error

### การตรวจสอบที่ทำแล้ว
- **CPU**: Apple M1 arm64 → LanceDB ใช้ได้
- **`.kilo/kilo.jsonc`**: git-tracked (public repo) → **ห้ามใส่ API key ในไฟล์นี้**
- **`~/.config/kilo/kilo.jsonc`** (global, private): เก็บ **literal** API keys (openrouter/groq/deepseek) อยู่แล้ว → pattern ที่ใช้จริง
- **`.env`**: symlink → `drive/.secrets` (gitignored); ไม่มี `GEMINI_API_KEY` จริง (มีเฉพาะใน `.env.example`)
- **Kilo indexing อ่าน key อย่างไร**: จาก config block `indexing.<provider>.apiKey` ตรงๆ — **ไม่ได้อ่านจาก `.env` โดยตรง** (global config ปัจจุบันใช้ literal keys ทั้งหมด, ไม่มี env interpolation ที่ยืนยันได้จาก binary ที่ compile แล้ว)

### กลยุทธ์: .env เป็น single source of truth ของค่า key → mirror ไป global config
เนื่องจาก Kilo indexing ต้องการ key ใน config block (ไม่ใช่ env var):
1. **user วาง key ใน `.env`** (workflow secrets ที่คุ้นเคย — เหมือน key อื่นๆ)
2. **agent mirror ค่าเดียวกันไป global config** `~/.config/kilo/kilo.jsonc` ใต้ `indexing.gemini.apiKey` (สถานที่ private, pattern เดียวกับ openrouter/groq/deepseek ที่มีอยู่)
3. **project config** `.kilo/kilo.jsonc` เก็บเฉพาะ `provider/model/vectorStore` (ไม่ใช่ secret)

> ผลลัพธ์: key อยู่ใน .env (source of truth) + สะท้อนใน global config (ที่ Kilo อ่านจริง) + **ไม่มีใน repo สาธารณะ**

### การแก้ไข

**ไฟล์ 1 — `.kilo/kilo.jsonc`** (แก้ส่วน `indexing`, public, ไม่มี secret):
```json
"indexing": {
  "enabled": true,
  "provider": "gemini",
  "model": "gemini-embedding-001",
  "vectorStore": "lancedb",
  "lancedb": {}
}
```
(เดิม: `provider: "kilo"`, `model: "mistralai/mistral-embed-2312"`)

**ไฟล์ 2 — `~/.config/kilo/kilo.jsonc`** (เพิ่ม global indexing block, private — mirror จาก .env):
```json
"indexing": {
  "gemini": { "apiKey": "<ค่าเดียวกับ GEMINI_API_KEY ใน .env>" }
}
```

**ไฟล์ 3 — `.env`** (เพิ่มบรรทัด, single source of truth):
```
GEMINI_API_KEY=<key จาก Google AI Studio>
```

### สิ่งที่ user ต้องทำเอง (agent ทำแทนไม่ได้)
1. รับ **Google AI API key ฟรี** จาก https://aistudio.google.com/apikey (free tier เพียงพอ) → วางใน `.env` ที่ `GEMINI_API_KEY=` แล้วบอกค่าให้ agent mirror
2. หลังแก้ config → เปิด **Settings → Indexing → Enable for This Project** (หรือ Global Enable) ใน UI
3. รอ initial scan เสร็จ (สถานะ Complete)

---

## ส่วนที่ 2: Orchestrator "เลิกใช้" — คำอธิบาย (ไม่ต้องแก้ config เป็นหลัก)

### ยืนยันจาก docs ทางการ (หน้า "Orchestrator Mode (Deprecated)")
> ⚠️ **Deprecated — scheduled for removal**
> Orchestrator mode is deprecated and will be removed in a future release.

### ทำไมถึงเลิกใช้
- **ก่อน**: Orchestrator เป็นโหมดเดียวที่แบ่งงานซับซ้อนเป็น subtask แล้วมอบหมายให้โหมดอื่น
- **ตอนนี้**: ความสามารถ delegate (เรียก subagent) **ฝังในทุก agent ที่มี full tool access แล้ว** → **Code, Plan, Debug** (โหมด read-only เช่น Ask ไม่รองรับ)

### สิ่งที่มาแทน
1. **แค่ใช้ agent ปกติ** — Code (เขียน), Plan (ออกแบบ), Debug (แก้บั๊ก) → ประสาน subagent อัตโนมัติผ่าน `task` tool เมื่อคุ้มค่า
2. **Custom Subagents** (`.kilo/agents/*.md` หรือ key `agent`) สำหรับ delegation เฉพาะทาง — built-in มี `general` (งานทั่วไป) และ `explore` (สำรวจ code, read-only)
3. **หยุดสลับไปโหมด Orchestrator** ก่อนงานซับซ้อน

### สังเกตจาก global config ปัจจุบัน
`~/.config/kilo/kilo.jsonc` บรรทัด 160-164 มี:
```json
"orchestrator": { "model": "zai-coding-plan/glm-5.2", "disable": false, "variant": "high" }
```
→ user เปิด orchestrator ไว้ชัดเจน. **(optional)** ถ้าอยากซ่อนจากเมนูให้ตั้ง `"disable": true` — แต่ไม่จำเป็น, ปล่อยไว้ก็ใช้ได้จนกว่าจะถูกลบในเวอร์ชันอนาคต

---

## ขั้นตอน execute (หลัง user วาง key ใน .env)

1. แก้ `.kilo/kilo.jsonc` — อัปเดตส่วน `indexing` (provider → gemini, model → gemini-embedding-001, +vectorStore lancedb)
2. เพิ่ม `GEMINI_API_KEY=` ใน `.env` (user วางค่าจริง) — single source of truth
3. mirror ค่าเดียวกันไป `~/.config/kilo/kilo.jsonc` — เพิ่ม `indexing.gemini.apiKey` (ที่ Kilo อ่านจริง)
4. แจ้ง user ไปเปิด indexing ใน Settings UI → Enable for This Project

## ไฟล์ที่จะแก้
- `.kilo/kilo.jsonc` (ส่วน `indexing` เท่านั้น — public, ไม่มี secret)
- `.env` (เพิ่ม `GEMINI_API_KEY` — private symlink, single source of truth)
- `~/.config/kilo/kilo.jsonc` (เพิ่ม `indexing.gemini.apiKey` — private, mirror จาก .env)

## ไม่ต้องทำ
- ไม่ commit (รอ user สั่ง)
- ไม่แตะ AGENTS.md/CLAUDE.md/skills
- Orchestrator config ปล่อยไว้ (optional disable เท่านั้น)
