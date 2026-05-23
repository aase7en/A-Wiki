---
type: concept
tags: [ai-tools, claude-code, hooks, skills, plugins, automation]
sources: [ai-agents-integration-guide]
created: 2026-05-17
updated: 2026-05-17
last_verified: 2026-05-17
verify_tool: training
---

# Hooks, Skills, Plugins — Pattern การขยาย Claude Code

## นิยาม

สามกลไกหลักที่ขยายพฤติกรรมของ Claude Code โดยไม่ต้องแก้ตัว AI เอง:

| กลไก | ลักษณะ | ตัวอย่าง |
|------|--------|---------|
| **Hook** | รันอัตโนมัติตาม lifecycle event — AI ไม่รู้ตัว | format code หลัง Edit, block commit บน dirty WT |
| **Skill** | แพ็กเกจ `SKILL.md` — AI เรียกเองเมื่อ description ตรง | `ingest-source`, `lint-wiki`, `verify-before-done` |
| **Plugin** | bundle Hooks + Skills + MCP Servers ใน manifest | แชร์ชุด tool สำหรับทีม |

## Hooks — การควบคุมเชิงรับ

Hook คือ shell script (Bash หรือ Python) ที่ตั้งค่าใน `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "prettier --write $CLAUDE_TOOL_INPUT_FILE_PATH" }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/check-raw-immutable.sh" }]
      }
    ]
  }
}
```

### Lifecycle Events ที่รองรับ

| Event | ทริก |
|-------|------|
| `SessionStart` | เริ่ม session ใหม่ |
| `PreToolUse` | ก่อน AI ใช้ tool |
| `PostToolUse` | หลัง AI ใช้ tool เสร็จ |
| `Stop` | Claude หยุดตอบ |

### Hook จาก InW-Wiki (ตัวอย่างจริง)

- `check-raw-immutable.sh` — PreToolUse: block Edit/Write ใน `raw/`
- `check-claudemd-lock.sh` — PreToolUse: block แก้ CLAUDE.md ถ้าไม่ unlock
- `check-bash-destructive-git.sh` — PreToolUse: block `git reset --hard` / `clean -f` เมื่อ WT dirty
- `post-wiki-edit-gen-index.sh` — PostToolUse: auto-run `gen-index.py` หลัง wiki/ edit (debounce 120s)
- `session-start-binary-scan.sh` — SessionStart: scan raw/ หาไฟล์ใหญ่ที่ไม่อยู่ใน manifest

> Hook เขียนเป็น **Python แทน Bash** ได้ — ดีกว่าเมื่อต้องการ error handling ซับซ้อน

## Skills — การขยายความสามารถเชิงรุก

Skill คือไฟล์ `SKILL.md` ใน `.claude/skills/<skill-name>/`:

```markdown
---
name: review-pr
description: Review a pull request for security, tests, and style violations
---
# Pull Request Review
1. Read the diff of the current pull request.
2. Check for common security issues.
3. Verify that new functions have tests.
4. Flag style guide violations.
5. Post review comments on the PR.
```

Claude อ่าน `description` แล้วตัดสินใจเรียก skill เมื่อ context ตรง

### Skills จาก InW-Wiki (ตัวอย่างจริง)

- `ingest-source` — workflow ingest source ใหม่เข้า wiki
- `lint-wiki` — ตรวจสุขภาพ wiki (orphans, contradictions, frontmatter)
- `verify-before-done` — self-check 4 จุดก่อน declare งานเสร็จ
- `brainstorm-before-build` — force clarify-then-propose ก่อน implement
- `hook-suggest` — วิเคราะห์ pattern ซ้ำและเสนอสร้าง hook

## Plugins — Bundle แชร์ได้

Plugin รวม Skills + Hooks + MCP Servers ไว้ใน `plugin.json`:

```json
{
  "name": "code-quality",
  "version": "1.0.0",
  "skills": ["review-pr", "lint-code"],
  "hooks": { "PostToolUse": [...] },
  "mcp": [{ "server": "postgres", "config": {...} }]
}
```

ทำให้ทีมติดตั้ง toolset เดียวกันได้ง่ายโดยแชร์ plugin เดียว

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| ควบคุม AI behavior แบบ declarative | Hook ผิดพลาด = block การทำงาน |
| Hooks รันแน่นอน AI ไม่ข้ามได้ | Skills ต้องเขียน description ให้ชัด ไม่งั้น AI ไม่เรียก |
| Skills ทำให้ workflow ซ้ำๆ consistent | Plugin management ยังไม่มี marketplace อย่างเป็นทางการ |
| แยก policy ออกจาก prompt | Hooks ต้อง debug ผ่าน hook stdout ซึ่งยากกว่าปกติ |

## ความสัมพันธ์

- [[concepts/ai-tools/symlinks-ssot]] — ใช้ symlinks ให้ AI หลายตัวเห็น skill/hook เดียวกัน
- [[concepts/ai-tools/context-management]] — hooks ช่วยบังคับ context discipline (block ก่อนทำลาย)
- [[concepts/ai-tools/session-setup]] — SessionStart hooks คือส่วนหนึ่งของ session setup

## แหล่งข้อมูล

- [[sources/ai-agents-integration-guide]] — Section 2-4: Hooks, Skills, Plugins
