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
