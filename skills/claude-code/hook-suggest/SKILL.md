---
name: hook-suggest
description: >
  วิเคราะห์ pattern ซ้ำๆ ในงานปัจจุบัน แล้วเสนอหรือสร้าง hook อัตโนมัติ
  SAFE hooks (read-only) → สร้างเลย | RISKY hooks (write/commit/delete) → ถามก่อน
  Trigger: /hook-suggest | Claude สังเกตว่าทำ step เดิม ≥2 ครั้งใน session | ผู้ใช้บ่นว่า "ต้องทำซ้ำ" หรือ "ทำอีกครั้ง"
---

# hook-suggest

**Trigger**: `/hook-suggest` | step เดิม ≥2 ครั้ง | "ต้องทำซ้ำ" / "ทำอีก" / "ทุกครั้ง"

## 1. อ่าน context ก่อนวิเคราะห์

```
อ่าน .claude/settings.json → hooks section (รู้ว่ามีอะไรแล้ว ห้าม duplicate)
อ่าน wiki/context/session-memory.md → งานซ้ำข้าม session
ดู session context → งานที่ทำซ้ำใน session นี้
```

## 2. Safety classification

| SAFE → auto-create โดยไม่ต้องถาม | RISKY → ต้อง approve ก่อน |
|-----------------------------------|---------------------------|
| python3 scripts/*.py (read-only) | git commit / push / pull |
| cat / grep / stat / find (no -delete) | rm / delete / mv ข้าม folder |
| echo / printf / wc / jq | git reset / clean / restore |
| bash scripts (read-only output) | write to config files |
| gen-index, export scripts | chmod ที่ไม่ชัดเจน |

ถ้าไม่แน่ใจ → classify RISKY

## 3. flow

### SAFE hook — สร้างเลย
1. เขียน `.claude/hooks/<name>.sh` ด้วย debounce template
2. `chmod +x` ไฟล์นั้น
3. เพิ่ม entry ใน `.claude/settings.json` ใน event ที่เหมาะ
4. แจ้งผู้ใช้: "สร้าง hook <name> แล้ว — trigger เมื่อ <event>, ประหยัด <step>"

### RISKY hook — แสดง + ถามก่อน
1. แสดง proposed script + settings.json diff
2. ถาม: "สร้าง hook นี้ได้ไหม?"
3. รอ "ใช่" / "ok" / "approve" → ค่อยสร้างตาม SAFE flow

## 4. Debounce template (บังคับใช้ทุก PostToolUse hook)

```bash
#!/usr/bin/env bash
# <Event>: <description> (debounced <N>s)
LAST="/tmp/wiki-<name>-lastrun"
LOCK="/tmp/wiki-<name>-lock"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

[ -f "$LAST" ] && DIFF=$(( $(date +%s) - $(cat "$LAST" 2>/dev/null || echo 0) )) \
  && [ "$DIFF" -lt 120 ] && exit 0
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
date +%s > "$LAST"
cd "$REPO"
# งานจริง ↓
```

## 5. Event เลือกอย่างไร

| ต้องการ trigger เมื่อ | ใช้ event |
|-----------------------|-----------|
| หลังแก้ไขไฟล์ | PostToolUse (matcher: Edit\|Write\|MultiEdit) |
| ก่อนแก้ไขไฟล์ | PreToolUse (matcher: Edit\|Write\|MultiEdit) |
| ก่อน bash command | PreToolUse (matcher: Bash) |
| เริ่ม session ใหม่ | SessionStart |
| จบ session | Stop |
| หลัง /compact | PostCompact |
| ผู้ใช้ส่งข้อความ | UserPromptSubmit |

## 6. กฎเหล็ก
- ตรวจ settings.json ก่อนเสมอ — ห้าม duplicate hook
- hook ต้อง exit 0 เสมอ (ห้าม block Claude ด้วย error ที่ไม่จำเป็น)
- debounce ทุก PostToolUse hook (≥60s แนะนำ 120s)
- บันทึก hook ใหม่ใน log.md ทุกครั้ง: `## [DATE] update | hook-suggest: <name>`
- ถ้า hook ซับซ้อน (>20 บรรทัด) → ถามก่อนสร้างแม้ SAFE
