---
name: token-optimization
description: Reduce context cost with compaction, clearing, and focused reload decisions before large wiki or agent tasks.
---

# Skill: Token Optimization

**Trigger**: ใช้เมื่อ user พูดว่า "ประหยัด token", "session หนัก/ช้า", "compact", "เริ่ม task ใหม่", หรือก่อน ingest source ขนาดใหญ่ (>1,000 บรรทัด)

---

## Step 1: ประเมิน Context ปัจจุบัน

ถามตัวเอง:
- session นี้ทำมาแล้วกี่ subtask?
- มีไฟล์ขนาดใหญ่ถูกโหลดเข้า context ไหม?
- task ต่อไปเกี่ยวข้องกับ task ปัจจุบันไหม?

---

## Step 2: เลือก Action

```
Task ต่อไปเกี่ยวกับ topic เดิม?
    ├─ ใช่ → /compact focus on <สิ่งที่ต้องจำ>
    └─ ไม่ → /rename <task-name> แล้ว /clear
```

### กรณี /compact — เลือก focus string

| สถานการณ์ | Focus string |
|----------|-------------|
| หลัง ingest source | `focus on entity/concept pages created and index todos` |
| หลัง edit wiki batch | `focus on pages modified, pending fixes, schema rules` |
| ก่อน ingest ขนาดใหญ่ | `focus on wiki schema rules and domain: <domain>` |
| งาน query/ตอบคำถาม | `focus on current question and relevant wiki pages` |
| หลัง lint | `focus on lint findings and fixes applied` |

### กรณี /clear — ทำตามลำดับ

```bash
/rename <ชื่อ task ใหม่>   # ตั้งชื่อก่อนเสมอ
/clear                      # reset
# → เริ่ม task ใหม่สะอาด
```

---

## Step 3: Plan Before Execute (ถ้างานกระทบ >3 ไฟล์)

ก่อน Edit/Write ใดๆ ให้ระบุ:

```
Plan:
- <file1> — <ทำอะไร>
- <file2> — <ทำอะไร>
- <file3> — <ทำอะไร>
ลำดับ: 1 → 2 → 3
```

ห้าม jump เข้า Edit ทันทีโดยไม่มี plan

---

## Step 4: เลือก Model ให้ถูกต้อง

| งาน | Model | เหตุผล |
|-----|-------|--------|
| วางแผน / synthesis / เขียน wiki | **Sonnet** (current) | ต้องการ reasoning ดี |
| Scan ไฟล์ / lint / grep | **Haiku subagent** | งานซ้ำ predictable |
| Web search / lookup / ราคา | **Free API** (OpenRouter/Gemini/Groq) | Level 1, ฟรี |
| อ่านไฟล์ >5 หน้า | **Explore subagent** | ไม่บวม main context |

> ⚠️ ห้ามใช้ Haiku เป็น main planner — plan ผิด → re-do ทั้งหมด = เสีย token 3-5x

---

## Step 5: Red Flags — สัญญาณว่าต้อง compact ตอนนี้

- Claude ตอบช้าลงเรื่อยๆ
- Claude เริ่ม "ลืม" สิ่งที่คุยไปก่อนหน้า
- มีไฟล์ขนาดใหญ่ (>500 บรรทัด) ถูกอ่านเข้า context >2 ครั้ง
- Session ยาวเกิน 2 ชั่วโมงโดยไม่ compact

---

## Step 6: Caveman Mode (บังคับตอบสั้น)

**Trigger**: user สั่ง `/caveman`, บ่นว่า "ตอบยาว", "ขอสั้นๆ", "เอาแค่คำตอบ" หรือเมื่อ session ใกล้ token limit

**กฎ Caveman**:
- ตัด preamble ("ผมจะ...", "ก่อนอื่น...", "let me...")
- ตัด recap ของสิ่งที่เพิ่งทำ (user เห็น tool calls แล้ว)
- Bullet ≤3 บรรทัดต่อ section
- ไม่ใส่ "หมายเหตุ" / "เพิ่มเติม" / "นอกจากนี้"
- ตอบคำถามตรงๆ — ถ้าใช่ ตอบ "ใช่ — <เหตุผล 1 บรรทัด>" จบ
- โค้ดให้ snippet ตรงประเด็น ไม่ต้อง wrap ด้วย explanation ยาว

**Output token ลดได้ ~60-65%** เทียบกับ default verbose mode

---

## Step 7: Strategic Compact (proactive timing)

**Default**: รอจน Claude Code auto-compact ที่ ~95% → คุณภาพตกแล้ว, สาย

**Strategic**: เสนอ /compact เองตามจุดเหล่านี้:

| Trigger | Focus string ที่แนะ |
|---------|---------------------|
| ✅ หลังจบ subtask (commit แล้ว ก่อนเริ่มอันถัดไป) | `focus on next subtask + relevant files` |
| 📥 ก่อน ingest source >2000 บรรทัด | `focus on wiki schema rules + domain: <X>` |
| 🔍 หลัง /verify ผ่าน | `focus on next planned change` |
| 🔄 ก่อนเปลี่ยน topic ใน session เดิม | `/rename <new> && /clear` (ดีกว่า compact) |
| 🤖 หลัง subagent return ผลกลับมา | `focus on subagent findings + integration plan` |
| 🐌 Claude เริ่มตอบช้า/ลืม | compact ทันที |

**ห้าม compact** ตอน:
- กลาง contradiction check ที่ต้องอ้างถึง history ทั้งหมด
- ก่อนรับ user input สำคัญที่ต้องเชื่อมโยงกลับ

---

## Quick Reference

```bash
# Compact แบบมี focus (แนะนำ)
/compact focus on wiki edits and pending todos

# Clear เมื่อเปลี่ยน task
/rename iot-hardware-query
/clear

# ตรวจ wiki-overview freshness (hook ทำอัตโนมัติแล้ว — SessionStart)
# ถ้าอยากตรวจด้วยตนเอง:
bash .claude/hooks/wiki-context-check.sh
```

---

## ความสัมพันธ์

- `wiki/concepts/ai-tools/context-management.md` — คำอธิบายเต็ม
- CLAUDE.md §💰 Cost-First Decision Pyramid — ระดับ 0-4
- CLAUDE.md §🧩 Subagent Delegation — เมื่อไหร่ delegate
- CLAUDE.md §📘 NotebookLM-first Protocol — synthesize แบบ 0 token
