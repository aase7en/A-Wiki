---
type: entity
category: standard
tags: [agents-md, spec, multi-agent, claude-code, codex, cursor, aider, copilot]
sources: [github-agents-md]
created: 2026-05-28
updated: 2026-05-28
last_verified: 2026-05-28
verify_tool: WebFetch
---

# AGENTS.md Specification

**ประเภท**: Open format spec สำหรับ AI coding agents
**สถานะ**: A-Wiki's `AGENTS.md` follow spec แล้ว — เพิ่ม link/badge ใน header
**License**: MIT (spec)
**Adoption**: 21.8k stars, 1.6k forks

## ภาพรวม

AGENTS.md เป็น **open format** สำหรับ guide AI coding agent — เปรียบเหมือน README แต่สำหรับ AI: setup, build, test, code style, PR conventions, security — ให้ Claude Code, Codex, Cursor, Windsurf, Cline, Aider, GitHub Copilot อ่านได้แบบเดียวกัน

## โครงสร้างมาตรฐาน

| Section | Required | Purpose |
|---------|:--------:|---------|
| Dev Environment | ✅ | setup commands, deps |
| Build / Test | ✅ | how to run/test |
| Code Style | recommended | conventions, linters |
| Contribution / PR | recommended | PR conventions, commit format |
| Security | optional | secret handling, vuln workflow |
| Architecture | optional | high-level structure |

## การใช้งานใน A-Wiki

A-Wiki มี **`AGENTS.md`** (10.2 KB) ที่ครอบคลุมทุก section แล้ว + extra (Iron Laws, Swarm Protocol, Cost Pyramid, Repository Integration) — compliance ดี

**Patches ที่ทำตอน integration**:
- เพิ่ม badge/link ไปยัง spec ใน header
- Mirror Repository Integration table จาก CLAUDE.md
- ตรวจ section ordering ให้ตรง spec convention

## ข้อดีของการ comply spec

| ข้อดี | ผลกระทบ |
|-------|---------|
| Cursor/Aider/Windsurf อ่าน config เดียวกัน | switch agent ไม่ต้องเขียน config ใหม่ |
| Tool ใหม่ที่รองรับ AGENTS.md ใช้ A-Wiki ได้เลย | future-proof |
| Standard adoption สูง | 21.8k stars = de-facto spec |

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[claude-skills]], [[ecc]] — Claude-specific layer ที่อยู่บนนี้
- เปรียบเทียบกับ: `CLAUDE.md` — Claude-specific, AGENTS.md = universal
- ใช้ร่วมกับ: [[.cursorrules]], [[.codex/]], [[.gemini/]] — agent-specific configs

## แหล่งข้อมูล

- GitHub: https://github.com/agentsmd/agents.md
- Website: https://agents.md
- [verified 2026-05-28] WebFetch — 21.8k stars
