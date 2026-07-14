---
type: entity
category: tool
title: "UI UX Pro Max (nextlevelbuilder)"
tags: [claude-skills, design-web, ui-ux, design-database, candidate]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-13
updated: 2026-07-13
last_verified: 2026-07-13
verify_tool: WebSearch
---

# UI UX Pro Max (nextlevelbuilder/ui-ux-pro-max-skill)

**ประเภท**: Agent skill + searchable local design-intelligence database
**สถานะ**: ✅ **ติดตั้งแล้ว** — `skills/ui-ux-pro-max/` (vendored 2026-07-14, registry: domain `design,ux-ui`, category `design`)
**License**: open-source (repo public)

## ภาพรวม

Skill ให้ "design intelligence" ผ่านฐานข้อมูล local ที่ค้นได้: **50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, 25 chart types** ครอบคลุม 10 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, HTML/CSS) [verified 2026-07-13]

- v2.0 flagship = **Design System Generator** — reasoning engine วิเคราะห์ requirement แล้ว generate design system ทั้งชุด
- รองรับ harness กว้างมาก: Claude Code, Cursor, Windsurf, Antigravity, Codex CLI, Gemini CLI ฯลฯ — ตรงกับ multi-agent architecture ของ A-Wiki
- Activate อัตโนมัติเมื่อขอทำงาน UI/UX

## ตำแหน่งใน A-Wiki

- เป็น **data asset** ไม่ใช่แค่ prompt — ปรัชญาเดียวกับ local-first search ของ A-Wiki (FTS5/sqlite-vec)
- Gap ที่เติม: A-Wiki ไม่มี palette/font-pairing/UX-rule database เลย
- แนวติดตั้ง: vendored snapshot (pattern [[entities/ai-tools/mattpocock-skills]]: remote + refresh script) — **เช็คขนาด DB ก่อน vendor** (ใหญ่กว่า skill ปกติ)

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[synthesis/claude-skills-gap-web-game-2026]], [[synthesis/design-web-capability-hub]]
- ใช้ร่วมกับ: [[entities/ai-tools/taste-skill]] (taste layer) + [[entities/ai-tools/transitions-dev]] (motion layer)

## แหล่งข้อมูล

- GitHub: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- [[sources/charliejhills-claude-skills-org-chart-2026]]
- [verified 2026-07-13] WebSearch — repo structure (.claude/skills/ui-ux-pro-max/SKILL.md), DB scope, v2.0
