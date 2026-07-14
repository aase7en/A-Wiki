---
type: entity
category: tool
title: "gamedev-skills/awesome-gamedev-agent-skills (web-engines subset)"
tags: [claude-skills, game-design, phaser, pixijs, threejs, vendored]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-14
updated: 2026-07-14
last_verified: 2026-07-14
verify_tool: WebFetch
---

# gamedev-skills/awesome-gamedev-agent-skills (web-engines subset)

**ประเภท**: Agent skill catalog — 66 version-pinned game-dev skills + router across 10 engines
**สถานะ**: ✅ **ติดตั้งบางส่วนแล้ว** — cherry-pick เฉพาะ 6 skills จาก `web-engines/` (ไม่เอาทั้ง 66)
**License**: Apache-2.0 [verified 2026-07-14]

## ภาพรวม

Upstream repo ให้ความรู้ engine-specific ระดับ API สำหรับ Godot/Unity/Unreal/Phaser/PixiJS/
three.js/Bevy/pygame/LÖVE/Roblox พร้อม router ที่เลือก skill ให้อัตโนมัติ — A-Wiki ไม่ใช้ router
ของเขา (มี `skills-registry.json` ของตัวเองอยู่แล้ว) และไม่ต้องการ engine อื่นนอกเว็บ จึง
cherry-pick เฉพาะ `skills/web-engines/*` มา 6 ตัว: `phaser-arcade-physics`, `phaser-core`,
`pixijs-rendering`, `threejs-gltf-loading`, `threejs-materials-lighting`, `threejs-scene-setup`

## ตำแหน่งใน A-Wiki

- เสริม [[entities/ai-tools/game-lightweight-highend-capability-hub]] chain — `skills/awiki/game-phaser-pipeline/`
  (route/convention/safety ของ A-Wiki เอง) ชี้มาที่นี่เมื่อต้องการรายละเอียดระดับ engine API
- Path: `skills/gamedev-skills/{skill-name}/SKILL.md` — verbatim จาก upstream, ไม่แก้เนื้อหา
- Attribution: `skills/gamedev-skills/NOTICE.md`
- Refresh: `bash scripts/refresh-gamedev-skills.sh` (snapshot 66-skill เต็มไป `skills/_upstream/gamedev-skills/` เพื่อ diff/cherry-pick เพิ่มในอนาคต)

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/ai-tools/a-wiki-skill-architecture]] (game-phaser-pipeline เป็น route, ตัวนี้เป็น engine-depth reference)
- เกี่ยวข้องกับ: [[synthesis/claude-skills-gap-web-game-2026]] — คำแนะนำ #2 (gap analysis 2026-07-13)
- ทางเลือกอื่นถ้าขยับ engine: Randroids-Dojo/Godot-Claude-Skills, htdt/godogen (ยังไม่ vendor)

## แหล่งข้อมูล

- GitHub: https://github.com/gamedev-skills/awesome-gamedev-agent-skills
- [[sources/charliejhills-claude-skills-org-chart-2026]]
- [verified 2026-07-14] shallow clone — repo structure, license, web-engines subdir contents
