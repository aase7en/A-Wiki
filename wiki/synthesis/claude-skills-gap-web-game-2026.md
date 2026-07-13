---
type: synthesis
title: "Claude Skills Gap Analysis — Web Design + Game (จากโพสต์ charliejhills)"
slug: claude-skills-gap-web-game-2026
tags: [capability-lane, gap-analysis, design-web, game-design, claude-skills, brain-improvement]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-13
updated: 2026-07-13
---

# Claude Skills Gap Analysis — Web Design + Game (2026-07)

## คำถามที่ตอบ

จากโพสต์ [[sources/charliejhills-claude-skills-org-chart-2026]] (org chart 7 แผนก): **A-Wiki ยังขาด skill ไหนบ้าง และอะไรจำเป็นจริงต่อการทำให้ A-Wiki เก่งขึ้น โดยเฉพาะการออกแบบเว็บและการสร้างเกม**

## สรุป

1. **ฝั่ง official ไม่ขาดอะไรเลย** — 5 skills จาก `anthropics/skills` ที่โพสต์ชู (skill-creator, mcp-builder, webapp-testing, web-artifacts-builder, brand-guidelines) vendor อยู่ที่ `skills/anthropic-skills/` ครบแล้ว [wiki]
2. **Web design ขาดแค่ "taste + data layer" 3 ตัว** — [[entities/ai-tools/taste-skill]], [[entities/ai-tools/ui-ux-pro-max]], [[entities/ai-tools/transitions-dev]] — ส่วน pattern skills มีเพียบแล้วจาก ECC (registry รวม 365 skills)
3. **Game คือ gap จริงที่สุด** — A-Wiki ไม่มี game SKILL.md แม้แต่ตัวเดียว (grep phaser/pixellab ใน skills/ = 0) ทั้งที่มีโปรเจกต์ Pixel Wealth Quest + [[synthesis/game-lightweight-highend-capability-hub]] อยู่แล้ว — และ**โพสต์นี้ช่วยไม่ได้** (org chart ไม่มีแผนกเกม) ต้องหาจากที่อื่น [verified 2026-07-13]

## การวิเคราะห์

### Matrix: รายการในโพสต์ × สถานะ A-Wiki

| รายการโพสต์ | A-Wiki มี? | หลักฐาน / โน้ต |
|---|---|---|
| anthropics/skills (5 ตัวที่ชู) | ✅ ครบ | `skills/anthropic-skills/` 16 dirs — [[entities/ai-tools/anthropic-skills]] |
| Superpowers (253k★) | 🟡 ซ้ำเชิงหน้าที่ | ชน Iron Laws + debug-mantra + scrutinize + mattpocock tdd/grilling — นโยบายเดิม "keep ours" ใช้ได้ต่อ → [[entities/ai-tools/superpowers]] |
| Context7 (59k★) | ❌ ขาด | ไม่มี live library-docs layer; เสริม knowledge-currency protocol → [[entities/ai-tools/context7]] |
| Claude-Mem (87k★) | 🟡 ทับซ้อนปรัชญา | A-Wiki มี session-memory.md + FTS5/vec + [[entities/ai-tools/gbrain]] (opt-in) — claude-mem = auto-capture ต่างจาก explicit-curation → [[entities/ai-tools/claude-mem]] |
| UI UX Pro Max | ❌ ขาด | ไม่มี searchable design DB (palettes/font pairs/UX rules) → [[entities/ai-tools/ui-ux-pro-max]] |
| Taste / Frontend Design (59.4k★) | ❌ ขาด (บางส่วน) | ECC มี make-interfaces-feel-better, frontend-design-direction แต่ไม่ใช่ taste-EQ layer แบบ framework-agnostic → [[entities/ai-tools/taste-skill]] |
| Transitions | ❌ ขาด (บางส่วน) | ECC motion-patterns/advanced/ui ผูก React/Next — transitions.dev เป็น CSS framework-agnostic + มี audit (transitions review) → [[entities/ai-tools/transitions-dev]] |
| coreyhaines31/marketingskills (45) | ❌ นอก focus | ไม่เกี่ยว web/game — บันทึกใน source พอ ยังไม่ประเมิน gate |
| charlie947/social-media-skills (17) | ✅ มีหน้าแล้ว | [[entities/ai-tools/social-media-skills]] — เคย reject "Charlie Hills voice" style |
| claude.com/plugins Finance/SmallBiz/Legal | ❌ นอก focus | official directory — จดไว้เผื่ออนาคต ไม่เข้า gate รอบนี้ |

### Web design: มีอะไรแล้วบ้าง (ก่อนตัดสินว่า "ขาด")

Registry 365 skills มี design/frontend coverage หนาแล้ว [wiki]:

- **Official (vendored)**: frontend-design, theme-factory, canvas-design, web-artifacts-builder, brand-guidelines, webapp-testing
- **ECC**: design-system, frontend-design-direction, frontend-patterns, make-interfaces-feel-better, motion-patterns, motion-advanced, motion-ui, accessibility (WCAG 2.2), frontend-a11y, ui-demo, ui-to-vue, e2e-testing, liquid-glass-design, dashboard-builder
- **A-Wiki เอง**: [[entities/ai-tools/frontend-slides]], [[entities/ai-tools/react-doctor]], dataviz (built-in), [[synthesis/design-web-capability-hub]]

**สิ่งที่เพิ่มมูลค่าจริงจากโพสต์** = ชั้นที่ยังไม่มี:

| Candidate | เพิ่มอะไรที่ไม่มี | รูปแบบเบาสุด (gate) | เสี่ยง |
|---|---|---|---|
| taste-skill | aesthetic-judgment layer กัน generic slop, 3-parameter EQ, 11 variants | skill files — npx skills add Leonxlnx/taste-skill --skill "design-taste-frontend" แล้วลง registry | v2 ยัง experimental; ทับ ECC 2 ตัวบางส่วน — ต้องกำหนด precedence |
| ui-ux-pro-max | local searchable DB: 50+ styles / 161 palettes / 57 font pairs / 99 UX rules / 25 chart types, 10 stacks | vendored snapshot (pattern เดียวกับ mattpocock: remote + refresh script) | ก้อนใหญ่กว่า skill ปกติ (มี DB) — เช็คขนาดก่อน vendor |
| transitions-dev | 18 CSS transitions + transitions reveal/review/apply audit loop, framework-agnostic | npx skills add Jakubantalik/transitions.dev | ทับ motion-* ของ ECC ใน React path — ใช้ transitions-dev เป็น default นอก React |

### Game: gap ที่แท้จริง + ทางไป

**สถานะ**: PWQ (Phaser + Vite + TS + PixelLab) มี knowledge ครบใน [[synthesis/game-lightweight-highend-capability-hub]], [[synthesis/8-bit-trading-rpg-blueprint]], [[synthesis/pixellab-asset-pipeline-for-trading-rpg]], [[synthesis/pixellab-phaser-asset-convention]] — **แต่ไม่ถูก package เป็น SKILL.md เลย** ทำให้ agent ต้อง re-read synthesis ทุกครั้ง (ขัด gate ข้อ "ถ้าใช้ซ้ำได้ ให้มัดเป็น reusable unit")

**คำแนะนำ (เรียงตาม gate)**:

1. **สร้าง skill ของตัวเอง game-phaser-pipeline** (เบาสุด, ตรง stack สุด) — distill route + asset convention + safety gate (client = visualization-only ตาม Iron Law #7) จาก synthesis 4 หน้าข้างบนเป็น SKILL.md เดียว + ลง registry — ไม่มี dependency ภายนอก ใช้ได้ทุก agent ทันที
2. **Vendored subset ของ gamedev-skills/awesome-gamedev-agent-skills** [verified 2026-07-13 via search] — 66 version-pinned skills + master router, ครอบคลุม Phaser/PixiJS/three.js/Godot/Unity, SKILL.md format เดียวกัน — ใช้ pattern remote+refresh เหมือน mattpocock, cherry-pick เฉพาะ web-game (Phaser/PixiJS/three.js) ไม่เอาทั้ง 66
3. ตัวเลือกเสริมถ้าขยับ engine อื่น: Randroids-Dojo/Godot-Claude-Skills (Godot 4.x + GdUnit4), htdt/godogen (autonomous Godot/Bevy/Babylon) — ยังไม่จำเป็นตอนนี้ [verified 2026-07-13 via search]
4. 3D preview ใน Cowork session มี Three.js MCP (show_threejs_scene) ให้ใช้อยู่แล้ว — จดเป็น capability ไม่ต้องติดตั้งอะไร

### Infra candidates (นอก design/game แต่กระทบ brain)

| Candidate | คุ้มไหม | เหตุผล |
|---|---|---|
| context7 | ✅ ควร (opt-in MCP) | ลด wrong-API loop = ลด token retry — เข้า setup-optional-mcp.sh pattern เหมือน gitnexus/graphify |
| claude-mem | 🟡 ประเมินก่อน | ทับ session-memory + gbrain; auto-capture ขัด explicit-curation + เสี่ยง private data ไหลเข้า DB — ถ้าลอง ให้ sandbox แบบ gbrain (tool-shaped, ไม่ auto-install) |
| superpowers | 🟡 track เฉย ๆ | 253k★ แต่ชนของที่ "keep ours" ทั้งแถว — เพิ่ม upstream remote ไว้ diff หา idea ใหม่พอ ไม่ vendor |

### ลำดับติดตั้งที่แนะนำ (รอไฟเขียว — ทำบนเครื่องหลักที่มี drive/)

```bash
# 1. game-phaser-pipeline (เขียนเอง — งาน authoring + registry + regen, ไม่มีคำสั่งติดตั้ง)
# 2. taste-skill
npx skills add Leonxlnx/taste-skill --skill "design-taste-frontend"
# 3. transitions-dev
npx skills add Jakubantalik/transitions.dev
# 4. ui-ux-pro-max — vendored: git remote add uiuxpromax https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git + refresh script
# 5. context7 — เพิ่มใน scripts/setup-optional-mcp.sh (--context7)
# ทุกตัว: เพิ่ม entry ใน skills-registry.json → python scripts/regen-skill-surfaces.py → commit (Iron Law #10)
```

## แหล่งข้อมูลที่ใช้

- [[sources/charliejhills-claude-skills-org-chart-2026]] — โพสต์ต้นเรื่อง (ลิงก์ verified ครบ)
- [[synthesis/design-web-capability-hub]] / [[synthesis/game-lightweight-highend-capability-hub]] — lane เดิม
- skills-registry.json (365 skills) + skills/anthropic-skills/ + skills/ecosystem/ — inventory จริง ณ 2026-07-13 [wiki]
- Game candidates: github.com/gamedev-skills/awesome-gamedev-agent-skills, github.com/Randroids-Dojo/Godot-Claude-Skills, github.com/htdt/godogen [verified 2026-07-13 via search]
