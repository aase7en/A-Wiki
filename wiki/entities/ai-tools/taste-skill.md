---
type: entity
category: tool
title: "Taste Skill (Leonxlnx/taste-skill)"
tags: [claude-skills, design-web, frontend, anti-slop, candidate]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-13
updated: 2026-07-13
last_verified: 2026-07-13
verify_tool: WebSearch
---

# Taste Skill (Leonxlnx/taste-skill)

**ประเภท**: Agent skill suite — frontend design taste ("anti-slop")
**สถานะ**: **candidate — ยังไม่ติดตั้ง** (ผ่าน gap analysis 2026-07-13, รอไฟเขียว + Brain Improvement Gate)
**License**: open-source (repo public)

## ภาพรวม

Skill ที่ให้ AI agent มี "รสนิยม" ด้าน frontend — หยุด output แบบ generic/boring ด้วย rules ที่เจาะ design intent ไม่ผูก framework ใดเฉพาะ ใช้ได้กับ Cursor/Claude Code/Codex [verified 2026-07-13] 59.4k★ (+347% vs มี.ค. 2026)

- ไม่ใช่ skill เดียว — เป็น suite **11 variants + 3 image-gen skills** พร้อมระบบ 3 พารามิเตอร์ทำงานเหมือน EQ เสียงกับ design output
- Install name คงที่: `design-taste-frontend` (v2 experimental เป็น default ตั้งแต่ 2026, ดีกว่า v1 แต่ยัง iterate อยู่)
- ในโพสต์ charliejhills ถูกลิสต์ 2 ช่อง ("Taste" + "Frontend Design") ชี้ repo เดียวกัน

## ตำแหน่งใน A-Wiki

- เติมชั้น aesthetic-judgment ที่ [[synthesis/design-web-capability-hub]] ยังไม่มี — ECC `make-interfaces-feel-better` + `frontend-design-direction` ทับบางส่วนแต่เป็น pattern/detail ไม่ใช่ taste-EQ layer
- ถ้าติดตั้ง: ต้องกำหนด precedence กับ 2 ตัวนั้น + ลง `skills-registry.json` (Iron Law #10)
- ติดตั้งแบบเบาสุด: `npx skills add Leonxlnx/taste-skill --skill "design-taste-frontend"`

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[synthesis/claude-skills-gap-web-game-2026]] — ที่มาของ candidate นี้
- ใช้ร่วมกับ: [[entities/ai-tools/ui-ux-pro-max]], [[entities/ai-tools/transitions-dev]] — ชุด design 3 ตัวจาก gap เดียวกัน
- ทับซ้อนบางส่วน: [[entities/ai-tools/ecc]] (make-interfaces-feel-better, frontend-design-direction)

## แหล่งข้อมูล

- GitHub: https://github.com/Leonxlnx/taste-skill · Docs: tasteskill.dev
- [[sources/charliejhills-claude-skills-org-chart-2026]]
- [verified 2026-07-13] WebSearch — repo/stars/variant structure
