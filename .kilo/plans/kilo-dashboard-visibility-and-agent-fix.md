# Plan — Kilo Dashboard Visibility + Fireworks Agent Fix

## สรุปการเปลี่ยนแปลง

### Fix 1: เพิ่ม Fireworks Provider
**ไฟล์:** `~/.config/kilo/kilo.jsonc`

เพิ่ม `fireworks-ai` provider ใน `provider` section:
```json
"fireworks-ai": {
  "options": {
    "apiKey": "fw_E2xLkk1Xy136j79uNg5Zsc"
  }
}
```

**ผล:** Code Skeptic + Test Engineer + Frontend Specialist จะใช้ `fireworks-ai/...` models ได้

### Fix 2: สร้าง /awiki-session-start Command
**ไฟล์ใหม่:** `.kilo/command/awiki-session-start.md`

Command ที่ emit session start event เข้า dashboard:
```markdown
---
description: Emit session start event to Live Dashboard
---
!`python3 scripts/live-dashboard/event_logger.py session_start agent=kilo model=fireworks-ai && echo "✅ Event emitted to dashboard"`
```

**ผล:** Kilo sessions จะเห็นใน Dashboard (agent ต้องเรียก command เองตอนเริ่ม session)

### Fix 3: เพิ่ม Session Start Instruction ใน Agents
**ไฟล์ที่จะแก้:**
- `.kilo/agents/code-skeptic.md`
- `.kilo/agents/test-engineer.md`
- `.kilo/agents/frontend-specialist.md`

เพิ่ม instruction:
```markdown
## Session Start Protocol
At the start of every session, run: `/awiki-session-start`
```

---

## ไฟล์ทั้งหมด

| ไฟล์ | Action |
|------|--------|
| `~/.config/kilo/kilo.jsonc` | แก้ไข — เพิ่ม `fireworks-ai` provider |
| `.kilo/command/awiki-session-start.md` | สร้างใหม่ |
| `.kilo/agents/code-skeptic.md` | แก้ไข — เพิ่ม session start instruction |
| `.kilo/agents/test-engineer.md` | แก้ไข — เพิ่ม session start instruction |
| `.kilo/agents/frontend-specialist.md` | แก้ไข — เพิ่ม session start instruction |

## Verification
1. `cat ~/.config/kilo/kilo.jsonc | python3 -m json.tool` — valid JSON
2. เปิด Kilo session ใหม่ → เรียก `/awiki-session-start` → ดู dashboard ว่ามี `session_start` event
3. เรียก Code Skeptic agent → ต้อง run ได้ (ไม่ error เรื่อง provider)
