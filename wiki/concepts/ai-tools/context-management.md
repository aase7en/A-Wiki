---
type: concept
tags: [token-optimization, context-management, claude-code, compact, session-management]
sources: []
created: 2026-05-12
updated: 2026-05-12
last_verified: 2026-05-12
verify_tool: training
---

# Context Management — การจัดการ Context เพื่อลด Token

## นิยาม

แนวทางจัดการ context window ของ Claude Code ระหว่าง session เพื่อลดการสะสมของ token ที่ไม่จำเป็น โดยใช้คำสั่ง `/compact` และ `/clear` ควบคู่กับ pattern การทำงานแบบ plan-before-code

## ทำไมถึงสำคัญ

Claude Code ส่ง **context เดิมซ้ำทุกครั้ง** ที่รับคำสั่ง — session ยาวขึ้น = token เพิ่มแบบ compound เป็นต้นทุนแฝงที่ไม่เห็นชัดจนกว่า session จะหนักมากแล้ว

## Session Lifecycle

```
Session เริ่ม (context สะอาด)
    ↓
Subtask A เสร็จ
    → /compact focus on <ผลลัพธ์ที่ต้องจำ>   ← ลด 40-60%
    ↓
Subtask B เสร็จ
    → /compact focus on <ผลลัพธ์ใหม่>
    ↓
เปลี่ยน task ใหม่ (ไม่เกี่ยวกัน)
    → /rename <task-name> แล้ว /clear        ← reset สะอาด
    ↓
Session ใหม่
```

## คำสั่งหลัก

### `/compact [focus string]`
บีบอัด conversation history เก็บเฉพาะสิ่งที่ระบุใน focus — ประหยัด **40-60%** token

**ใช้เมื่อ:**
| สถานการณ์ | Focus string แนะนำ |
|----------|-------------------|
| จบ subtask ย่อย (ยังฟีเจอร์เดิม) | `focus on wiki edits and pending todos` |
| ก่อน ingest source ขนาดใหญ่ | `focus on wiki schema rules only` |
| Session เริ่มหนัก (รู้สึกช้า) | `focus on current task: <ชื่อ task>` |
| หลัง lint/batch edit หลายหน้า | `focus on pages modified and remaining fixes` |

**ห้าม compact เมื่อ:**
- กลาง contradiction check ที่ต้องอ้างถึง history
- กำลังรอ user input ที่ต้องเชื่อมโยงกลับ

### `/clear`
ล้าง context ทั้งหมด — ใช้เมื่อ **เปลี่ยน task ใหม่ที่ไม่เกี่ยวกัน**

**วิธีที่ถูกต้อง:**
```
1. /rename <ชื่อ task ใหม่>   ← ตั้งชื่อก่อน ไม่งั้น lost track
2. /clear                      ← reset context
3. เริ่ม task ใหม่
```

## Plan-Before-Code Pattern

ก่อน implement งานที่กระทบ >3 ไฟล์ ให้ระบุก่อนเสมอ:

```
"จะแก้:
- wiki/entities/iot/esp32.md — เพิ่ม section X
- wiki/concepts/iot/mqtt.md — อัปเดต version
- index-iot.md — เพิ่ม entry ใหม่
ทำตามลำดับนี้ก่อนนะ"
```

ประโยชน์: ป้องกัน Claude jump เข้า implementation ผิด → ลด re-edit iterations ที่เสีย token 2-3x

## Model Matching สำหรับ Planning vs Execution

| บทบาท | Model ที่เหมาะ | เหตุผล |
|-------|--------------|--------|
| **Planner** (วิเคราะห์, ออกแบบ, syntax) | Sonnet หรือ Opus | Haiku วางแผนผิด → เสีย token แก้งาน |
| **Executor** (scan ไฟล์, lint, search) | Haiku | งานซ้ำ predictable ไม่ต้อง reasoning ลึก |
| **Free tier** (web search, lookup, URL summary) | OpenRouter free / Gemini Flash / Groq | Level 1 ใน Cost-First Pyramid |

> ⚠️ **ห้ามใช้ Haiku เป็น main planner** — ถ้า plan ผิด ต้อง re-do ทั้งหมด = เสีย token มากกว่าประหยัด

## CLAUDE.md Minimalism Rule

CLAUDE.md โหลดทุก session — ทุก KB เพิ่มขึ้น = token ที่จ่ายซ้ำแบบ compound

**ใส่ใน CLAUDE.md ได้:**
- คำสั่ง (commands, build, test, lint)
- กฎที่ AI เดาเองไม่ได้ (naming convention, protected zones)
- Workflow ที่ต้องทำตามลำดับแน่นอน

**ห้ามใส่ใน CLAUDE.md:**
- คำอธิบาย architecture ยาวๆ ที่ไม่ต้องอ้างถึงบ่อย
- Context ชั่วคราวของ task ปัจจุบัน
- Code snippet ยาวๆ เป็นตัวอย่าง

## ความสัมพันธ์กับ Token Protocol อื่นๆ

| Protocol | Token Level | ใช้เมื่อ |
|---------|-------------|---------|
| **Context Management** (หน้านี้) | Level 4 (behavioral) | จัดการ session ที่ยาว |
| [[concepts/ai-tools/session-setup]] | Level 0 (hook) | setup อัตโนมัติทุก session |
| Cost-First Pyramid (CLAUDE.md) | Level 0-4 | เลือก engine ตาม cost |
| Subagent Delegation (CLAUDE.md §🧩) | Level 3 | งานที่ต้องอ่าน >5 ไฟล์ |
| NotebookLM Protocol (CLAUDE.md §📘) | Level 0 (external) | synthesize หลาย wiki page |

## ตัวอย่างการใช้งานจริง

```
# หลัง ingest source ใหม่ (subtask จบ):
/compact focus on entity pages created and index updates pending

# ก่อนเริ่ม batch lint:
/compact focus on wiki schema rules and lint criteria

# หลัง lint เสร็จ, อยากถามคำถาม IoT ต่อ:
/rename iot-query-session
/clear
```

## แหล่งข้อมูล

- บทความ "5 เคล็ดลับใช้ Claude Code ให้ Token อยู่ได้นานขึ้น 3 เท่า" — Siam Blockchain [training]
- [[concepts/ai-tools/agent-framework-tradeoffs]] — Lean vs Autonomous tradeoffs
