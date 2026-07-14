---
name: delegate-subagent
description: Use this skill when the user asks for /lint, asks a wiki question that requires reading 5+ files, asks to ingest a source longer than 2000 lines, or asks a cross-domain question spanning multiple index files. Delegates the read-heavy work to an Explore (search) or general-purpose (analyze + summarize) subagent so the main context stays small. Skip for 1-2 page queries, single page edits, or sensitive tasks (security review, schema edits).
---

# delegate-subagent

ทริกเกอร์การ delegate งานอ่านไฟล์เยอะ ๆ ให้ subagent เพื่อกัน context ของ Claude หลักไม่ให้บวม

## เมื่อไหร่ใช้

ใช้ skill นี้เมื่อ task **อ่านไฟล์ใน repo เยอะ**:

- `/lint` หรือ health check ทั้ง wiki → `general-purpose`
- คำถามที่ต้องอ่าน >5 หน้าเพื่อตอบ → `general-purpose`
- Ingest source >2,000 บรรทัด → `general-purpose` สรุปก่อนเขียน
- Cross-domain query ที่ต้องอ่านหลาย `index-*.md` → `general-purpose`
- ค้น "ที่ไหนกล่าวถึง X" ใน wiki → `Explore` (read-only ประหยัดสุด)

## เมื่อไหร่ห้ามใช้

- คำถามอ่าน 1-2 หน้า → Claude หลักทำเอง overhead น้อยกว่า
- เขียน wiki page เดียว → Claude หลักรักษา schema consistency ได้ดีกว่า
- งาน sensitive (security review, แก้ CLAUDE.md, แก้ raw/) → Claude หลักเท่านั้น
- งานที่ subagent ต้องถาม user ระหว่างทาง → subagent ถามไม่ได้

## เลือก Subagent

| Subagent | ใช้เมื่อ |
|---|---|
| `Explore` (read-only) | ต้องค้น/locate ไฟล์เท่านั้น ไม่ต้องวิเคราะห์ลึก |
| `general-purpose` | ต้องอ่าน + วิเคราะห์ + สรุป + เขียนได้ครบ tools |

## Prompt Template (Wiki context)

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

## ตัวอย่าง

### `/lint` → general-purpose

```
Subagent prompt:
[context] Wiki schema ตาม CLAUDE.md > Workflow: Lint Wiki
[งาน] scan wiki/ ทั้งหมด รายงาน:
  1. orphan pages (ไม่มี inbound link)
  2. contradictions ระหว่างหน้า
  3. stub concepts (ถูก link แต่ยังไม่มีหน้า)
  4. stale pages (last_verified > 90 วัน)
[output] 4 sections ตามข้างบน — ภาษาไทย bullet ข้อสั้น
[ห้าม] เขียน/แก้ไฟล์
```

### Ingest source ยาว → general-purpose

```
Subagent prompt:
[context] ดู CLAUDE.md > Workflow: Ingest
[งาน] อ่าน raw/articles/<file>.md (3,500 บรรทัด)
สรุป:
  1. ประเด็นหลัก 5 ข้อ
  2. entities ที่ปรากฏ (พร้อม domain)
  3. concepts ที่ปรากฏ
  4. ข้อขัดแย้งกับ wiki ปัจจุบัน
[output] Markdown 4 sections
[ห้าม] เขียนไฟล์ — Claude หลักจะ map ไป wiki/sources/<slug>.md เอง
```

### ค้น "ที่ไหนกล่าวถึง LoRa" → Explore

```
Subagent prompt:
หา .md ใน wiki/ ที่กล่าวถึง 'LoRa' หรือ 'LoRaWAN'
ส่ง path + 1 บรรทัด context ของแต่ละ match
```

## Parallel Fan-out Rules (Anti Rate-Limit)

เมื่อ delegate หลาย subagent ในข้อความเดียว (parallel fan-out) ต้องกระจาย model/provider เพื่อไม่ให้ชน rate limit ของ free tier — ดูรายละเอียด `docs/protocols/subagent-model-routing.md`

**กฎ:** ห้าม fan-out ≥3 subagent ไปที่ provider/bucket เดียวกันพร้อมกัน

| N parallel | ตัวที่ 1 | ตัวที่ 2 | ตัวที่ 3 | ตัวที่ 4 |
|---|---|---|---|---|
| 2 | DeepSeek v4-flash | GLM-5.2 | — | — |
| 3 | DeepSeek v4-flash | GLM-5.2 | OpenRouter free | — |
| 4 | DeepSeek v4-flash | GLM-5.2 | OpenRouter free | DeepSeek v4-pro |

**อย่า:** 3× Gemini Flash, 3× free-tier key เดียวกัน — bucket เดียวกัน = ชนแน่นอน

> Pattern อ้างอิง FinRobot Director Agent ที่หน้าที่คือ "ensuring model diversity" ตอน fan-out

## Rate-Limit Fallback

ถ้า subagent คืน `Provider rate limited the model request` (HTTP 429) ให้ retry ผ่าน fallback chain:

```bash
bash scripts/swarm/subagent_fallback.sh "<subagent_type>" "<prompt>"
```

chain: DeepSeek → OpenRouter free → GLM-5.2 → Gemini (last resort, single call)

หรือ primary agent จัดการเอง: รับ error → สลับ `model` ของ subagent นั้นเป็น provider ถัดไป → re-invoke

## ตัวชี้วัดความสำเร็จ

- Token main context ลดลง 30-50% ในงาน lint/ingest ใหญ่
- Claude หลักยังเป็นคนเขียน wiki ทั้งหมด (รักษา consistency)
- Subagent output ส่งกลับเป็น summary ไม่ใช่ raw file content
- Parallel fan-out ≥3 ตัวไม่ชน rate limit (กระจาย provider หรือใช้ fallback)

ดูรายละเอียดเต็มใน [CLAUDE.md > 🧩 Subagent Delegation](../../../CLAUDE.md) และ `docs/protocols/subagent-model-routing.md`
