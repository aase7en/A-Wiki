---
name: a-wiki-commands
description: "A-Wiki slash commands — /wiki, /search, /backup, /status, /spec, /plan, /build, /test, /review, /code-simplify, /ship"
version: 1.0.0
author: A-Wiki + Hermes
tags: [awiki, commands, slash, wiki-search, lifecycle]
---

# A-Wiki Commands — Slash Command Registry

ลงทะเบียน 11 คำสั่งใน Hermes — ค้น wiki, วงจรพัฒนา, backup, status

## Registered Commands

| Command | Action | Phase |
|---------|--------|-------|
| `/wiki <query>` | ค้น A-Wiki FTS5 → ตอบกลับ | Research |
| `/search <query>` | Web search + wiki search | Research |
| `/backup` | Manual session backup → drive | Ops |
| `/status` | แสดง system status + model + sessions | Ops |
| `/spec` | DEFINE — เขียน spec ก่อนเขียนโค้ด | Lifecycle |
| `/plan` | PLAN — แตกงานเป็น tasks | Lifecycle |
| `/build` | BUILD — incremental implementation + TDD | Lifecycle |
| `/test` | VERIFY — debug + test | Lifecycle |
| `/review` | REVIEW — 5-axis review | Lifecycle |
| `/code-simplify` | Simplify code | Lifecycle |
| `/ship` | SHIP — pre-launch checklist | Lifecycle |

## Usage

```bash
# Register with Hermes
hermes skills install skills/awiki/a-wiki-commands/SKILL.md

# Or symlink
ln -sf $HOME/A-Wiki/skills/awiki/a-wiki-commands $HOME/.hermes/skills/awiki/a-wiki-commands
```
