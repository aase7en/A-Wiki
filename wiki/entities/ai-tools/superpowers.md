---
type: entity
category: tool
title: "Superpowers (obra)"
tags: [claude-skills, engineering, workflow, tdd, upstream-watch]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-13
updated: 2026-07-13
last_verified: 2026-07-13
verify_tool: WebFetch
---

# Superpowers (obra/superpowers)

**ประเภท**: Agentic skills framework + software development methodology
**สถานะ**: **track upstream เฉย ๆ — ไม่ vendor** (ชนของเดิมที่นโยบาย "keep ours" คุ้มครอง)
**License**: open-source · ผู้สร้าง: Jesse Vincent (obra) · **253k★** [verified 2026-07-13]

## ภาพรวม

Framework skills สำหรับ coding agents ที่ดังที่สุดในสาย methodology — TDD, systematic debugging, brainstorming, planning, code review ฯลฯ ติดตั้งได้ผ่าน official Claude plugin marketplace, ใช้ข้ามหลาย agent [verified 2026-07-13] ("Skill Forge — 14-skill power pack" ตาม org chart ในโพสต์)

## ทำไม A-Wiki ไม่ vendor (keep ours)

| หน้าที่ | A-Wiki มีแล้ว | Superpowers |
|---|---|---|
| Debugging discipline | `debug-mantra` (4-step root cause — Iron Law #2) | systematic debugging |
| TDD | Iron Law #1 + mattpocock `tdd` | TDD skills |
| Review | `scrutinize` (outsider perspective) + `two-axis-code-review` | code review |
| Plan sharpening | mattpocock `grill-me`/`grilling` | brainstorming/planning |

ตารางเดียวกับเหตุผลที่เคยเลือก A-Wiki skills เหนือ agent-skills upstream (ดู CLAUDE.md §A-Wiki Overlap) — 253k★ ไม่เปลี่ยนข้อเท็จจริงว่า scope ทับเกือบ 100%

**Action ที่คุ้ม**: เพิ่ม upstream remote ไว้ `diff` หา idea/skill ใหม่เป็นระยะ (เหมือน `_upstream/9arm-skills`) — ไม่ integrate ทั้งชุด

## ความสัมพันธ์

- ทับซ้อน: [[entities/ai-tools/9arm-skills]], [[entities/ai-tools/mattpocock-skills]], agent-skills/engineering ของ A-Wiki
- เกี่ยวข้องกับ: [[synthesis/claude-skills-gap-web-game-2026]]

## แหล่งข้อมูล

- GitHub: https://github.com/obra/superpowers
- [[sources/charliejhills-claude-skills-org-chart-2026]]
- [verified 2026-07-13] WebFetch — 253k★, marketplace install, skill scope
