---
type: entity
category: tool
tags: [claude-skills, engineering, productivity, upstream-tracked, git-subtree]
sources: [github-9arm-skills]
created: 2026-05-28
updated: 2026-05-28
last_verified: 2026-05-28
verify_tool: WebFetch
---

# thananon/9arm-skills

**ประเภท**: Upstream source ของ engineering+productivity skills ที่ A-Wiki ใช้
**สถานะ**: tracked via remote+refresh script at `agent-skills/_upstream/9arm-skills/` (local fork at `agent-skills/engineering/` and `productivity/`)
**License**: MIT

## ภาพรวม

repo จาก **thananon (9arm)** — รวม Claude Code skills 100% Shell — skills ที่ A-Wiki ใช้จริง (`agent-skills/engineering/`, `agent-skills/productivity/`) คัดลอกมาจาก repo นี้ **แต่เดิมไม่มี upstream link** → update ใหม่จาก thananon ไม่ได้ → แก้ด้วย `git subtree`

## Skills ที่ A-Wiki ใช้

| Category | Skill | Purpose |
|----------|-------|---------|
| engineering | **debug-mantra** | Four-mantra debugging — reproduce, trace, hypothesize, validate |
| engineering | **post-mortem** | Bug fix doc w/ root cause + validation record |
| engineering | **scrutinize** | Peer review of code plans + changes |
| productivity | **management-talk** | Adapt technical comm for leadership audiences |

## Setup & refresh

```bash
bash scripts/refresh-9arm.sh
```

Script ทำ:
1. `git remote add 9arm https://github.com/thananon/9arm-skills.git` (idempotent)
2. `git fetch 9arm main`
3. Extract latest tree → `agent-skills/_upstream/9arm-skills/` via `git archive | tar -x` (no merge, no clean-tree requirement)

**สำคัญ — A-Wiki ใช้ fork-aware tracking, ไม่ใช่ symlink**:

| Path | Role |
|------|------|
| `agent-skills/_upstream/9arm-skills/` | **read-only mirror** ของ upstream — refresh ทับได้ |
| `agent-skills/engineering/{debug-mantra,scrutinize,post-mortem}/` | **A-Wiki local fork** — เพิ่ม Iron Law enforcement blocks |
| `agent-skills/productivity/management-talk/` | A-Wiki local fork — simplified สำหรับ workflow ใน wiki |

หลัง refresh → ใช้ `diff` เพื่อดู upstream changes แล้ว cherry-pick:
```bash
diff -u agent-skills/_upstream/9arm-skills/skills/engineering/debug-mantra/SKILL.md \
        agent-skills/engineering/debug-mantra/SKILL.md
```

**เหตุผลที่ไม่ symlink:** A-Wiki ปรับ skill เพิ่ม Iron Law blocks (#1 "no code without failing test", #2 "no fix without root cause") + simplify management-talk จาก 173 → 33 บรรทัด → symlink ทับจะลบของพวกนี้

## โครงสร้าง upstream

```
9arm-skills/
├── engineering/
│   ├── debug-mantra/SKILL.md
│   ├── post-mortem/SKILL.md
│   └── scrutinize/SKILL.md
├── productivity/
│   └── management-talk/SKILL.md
├── misc/
├── personal/
├── in-progress/         ← drafts (ดูแต่ไม่ symlink)
└── deprecated/
```

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Track upstream — ได้ skill ใหม่อัตโนมัติ | git subtree mental model ซับซ้อนกว่า submodule |
| Skill ดี (debug-mantra ทำงาน 4 ขั้นชัด) | Shell-only — ไม่มี Python helper |
| MIT — ใช้ commercial ได้ | repo focus ส่วนตัวของ thananon |
| 2.5k stars — community พอใช้ได้ | personal/ category ไม่เหมาะกับ A-Wiki |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[ecc]] — ECC ก็มี engineering skills แต่ scope ต่างกัน
- ใช้ร่วมกับ: [[claude-skills]] — Claude Code skill system
- ใช้ร่วมกับ: [[git-subtree-workflow]] — refresh pattern
- Aligned กับ: A-Wiki's Iron Law #2 "no fix without root cause" — debug-mantra สอดคล้องโดยตรง

## แหล่งข้อมูล

- GitHub: https://github.com/thananon/9arm-skills
- Author: thananon (9arm)
- [verified 2026-05-28] WebFetch — 2.5k stars, Shell 100%
