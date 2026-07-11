# Context Compaction Protocol

> Claude Code ส่ง context เดิมซ้ำทุก turn — session ยาว = token เพิ่มแบบ compound.
> จัดการ context ตรงเวลา = ตัด "interest" ของ token. ลดได้ 40-60% กลาง session.
>
> รายละเอียดเต็ม: `wiki/concepts/ai-tools/context-management.md`
> Skill ที่เกี่ยวข้อง: `.claude/skills/token-optimization/SKILL.md` (Step 6 Caveman mode + Step 7 Strategic triggers)

## เมื่อไหร่ให้ /compact

| สถานการณ์ | คำสั่ง |
|----------|--------|
| จบ subtask ย่อย (ยังอยู่ฟีเจอร์เดิม) | `/compact focus on wiki edits and pending todos` |
| เปลี่ยน task ใหม่ (ไม่เกี่ยวกัน) | `/rename <task-name>` แล้ว `/clear` |
| ก่อน ingest source ขนาดใหญ่ | `/compact focus on wiki schema rules` |
| ก่อน ingest source >2000 บรรทัด | `/compact focus on wiki schema + domain: <X>` |
| session เริ่มหนัก / Claude ตอบช้า | `/compact focus on current task` |
| หลัง /verify pass | `/compact focus on next planned change` |
| หลัง subagent return | `/compact focus on subagent findings + integration plan` |

## ❌ ห้าม compact เมื่อ

- กลาง contradiction check ที่ต้องอ้างถึง history ทั้งหมด
- ก่อนรับ user input สำคัญที่ต้องเชื่อมโยงกลับ
- กลาง /verify หรือ skeptical review

## Strategic vs Auto

**Default (Claude Code auto)**: รอจน ~95% ค่อย auto-compact → คุณภาพตกแล้ว สาย.
**Strategic (แนะนำ)**: Claude เสนอ /compact เองตามจุดในตารางข้างบน ก่อนถึง 95%.

## 🗜️ Compaction-Suggest Hook (enforcement ของ Strategic)

Hook `scripts/hooks/check_compaction_suggest.py` ทำให้ตาราง strategic ข้างบนไม่ใช่แค่ prose:

- Wired บน **UserPromptSubmit** ใน `.claude/settings.json` แบบ direct (ไม่ผ่าน `hooks_runner.py` — runner กลืน stdout ที่ต้อง inject เป็น context)
- อ่าน `usage` ล่าสุดจาก transcript JSONL → context จริง = input + cache_read + cache_creation tokens
- เตือนเมื่อ ≥ **75%** ของ window (default 200k) → พิมพ์คำแนะนำ `/compact focus on <งาน>` เข้า context
- เตือนซ้ำทุก **+10pp** เท่านั้น (ไม่ spam); context หดเกิน 1 step (= compact แล้ว) → reset ladder
- Fail-soft ทุกกรณี: exit 0 เสมอ ไม่มีทาง block prompt

| Env flag | Default | ความหมาย |
|----------|---------|----------|
| `AWIKI_COMPACT_SUGGEST` | `1` | `0` = ปิด hook |
| `AWIKI_COMPACT_SUGGEST_PCT` | `75` | threshold % ของ window ที่เริ่มเตือน |
| `AWIKI_COMPACT_SUGGEST_STEP` | `10` | เตือนซ้ำทุก +N percentage points |
| `AWIKI_CONTEXT_WINDOW` | `200000` | ขนาด context window (tokens) |

Tests: `pytest tests/test_compaction_suggest.py -v`

## 🍃 Lean SessionStart (token-save คู่กัน)

ทุกบรรทัดที่ SessionStart hooks พิมพ์ = token ที่ฉีดเข้า context ทุก session. เปิด lean mode เพื่อตัดส่วน informational:

```jsonc
// .claude/settings.local.json (config flag ไม่ใช่ secret — cache ได้)
{ "env": { "AWIKI_LEAN_SESSION_START": "1" } }
```

| ยังทำใน lean mode | ข้ามใน lean mode |
|-------------------|------------------|
| git pull (multi-device sync) | wiki freshness check + auto-rebuild |
| Active TODOs (sticky rule — ต้องเห็นทุก session) | API key checks (ทั้ง python + shell) |
| cost-gate cleanup (functional, ไม่มี output) | model intel refresh + tier hint + scout warn |
| dashboard autostart + drive link check | vendor upstream-watch |
| initial-context (standing prompt ส่วนตัว) | binary scan (raw/ manifest) |
| | pharmacy DB rebuild check |

ของที่ข้ามจะกลับมาทำเองใน session ถัดไปที่ไม่ใช่ lean — flag นี้เหมาะกับช่วงทำงานถี่ ๆ หลาย session/วัน บนเครื่องเดิม.

Tests: `pytest tests/test_lean_session_start.py -v`

## Quick Reference

```bash
# Compact + focus (แนะนำ)
/compact focus on wiki edits and pending todos

# Clear เมื่อเปลี่ยน task ใหม่
/rename <new-task-name>
/clear

# ตรวจ wiki-overview freshness (SessionStart hook auto)
bash .claude/hooks/wiki-context-check.sh
```

## ความสัมพันธ์

- CLAUDE.md §💰 Cost-First Decision Pyramid — context compaction = Level 0 (ฟรี)
- `.claude/skills/token-optimization/SKILL.md` — workflow ละเอียด + Caveman mode
- `wiki/concepts/ai-tools/context-management.md` — ทฤษฎีและ benchmark
