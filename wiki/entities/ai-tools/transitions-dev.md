---
type: entity
category: tool
title: "Transitions.dev (Jakubantalik)"
tags: [claude-skills, design-web, css, animation, motion, candidate]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-13
updated: 2026-07-13
last_verified: 2026-07-13
verify_tool: WebSearch
---

# Transitions.dev (Jakubantalik/transitions.dev)

**ประเภท**: Agent skill — curated CSS transitions collection + audit/apply workflow
**สถานะ**: ✅ **ติดตั้งแล้ว** — `skills/transitions-dev/` (vendored 2026-07-14, registry: domain `design,ux-ui`, category `design`)
**License**: open-source (repo public)

## ภาพรวม

ชุด **18 production-ready CSS transitions** (card resize, number pop-in, modal, panel reveal, page slide, success check, error shake ฯลฯ) แพ็กเป็น agent skill — source อยู่ที่ `skills/transitions-dev/` ในรูป SKILL.md + reference ต่อ transition + `_root.css` [verified 2026-07-13]

คำสั่งหลัก:
- `transitions reveal` — ลิสต์ทุก transition
- `transitions review` — **สแกนทั้งโปรเจกต์**หา ad-hoc transitions / hardcoded durations แล้วเสนอจุดที่ควรแทนที่ (audit loop — จุดขายเทียบ ECC)
- `transitions apply` — auto-detect ตัวที่เหมาะกับ context แล้วติดตั้งหลัง confirm
- มีเครื่องมือ **Transitions Refine** สำหรับ tune timeline ใน Cursor/Codex/Claude Code

## ตำแหน่งใน A-Wiki

- ECC มี `motion-patterns`/`motion-advanced`/`motion-ui` แต่**ผูก React/Next** — transitions.dev เป็น CSS framework-agnostic → ใช้เป็น default นอก React ได้ (รวมถึง UI ของเกม Phaser: เมนู/HUD/overlay ใน [[synthesis/game-lightweight-highend-capability-hub]])
- ติดตั้งเบาสุด: `npx skills add Jakubantalik/transitions.dev` + ลง registry

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[synthesis/claude-skills-gap-web-game-2026]], [[synthesis/design-web-capability-hub]]
- ทับซ้อนบางส่วน: [[entities/ai-tools/ecc]] (motion-* ใน React path)
- ใช้ร่วมกับ: [[entities/ai-tools/taste-skill]], [[entities/ai-tools/ui-ux-pro-max]]

## แหล่งข้อมูล

- GitHub: https://github.com/Jakubantalik/transitions.dev · transitions.dev/skill.html
- [[sources/charliejhills-claude-skills-org-chart-2026]]
- [verified 2026-07-13] WebSearch — 18 transitions, คำสั่ง reveal/review/apply, Refine tool
