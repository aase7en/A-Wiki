---
type: source
title: "GitHub: 0x0funky/agent-sprite-forge"
tags: [github, codex-skill, pixel-art, sprite-sheet, animation, game-assets, godot, unity]
source_url: https://github.com/0x0funky/agent-sprite-forge
original_file: raw/github-0x0funky-agent-sprite-forge-2026-06-13/README.md
raw_archive: raw/github-0x0funky-agent-sprite-forge-2026-06-13/source-fff651a89223b044ccfc0b75ed9f3754c6d739b1.tar.gz
commit: fff651a89223b044ccfc0b75ed9f3754c6d739b1
routed_via: harness@v1
routing_note: "Manual fallback after local harness network SSL issue; raw-first provenance preserved."
confidence: "[verified 2026-06-13]"
created: 2026-06-13
updated: 2026-06-13
---

# GitHub: 0x0funky/agent-sprite-forge

## สรุป

[verified 2026-06-13] `agent-sprite-forge` เป็นชุด Codex skills สำหรับสร้าง 2D game assets: sprite sheets, transparent PNG frames, animated GIFs, layered maps, prop packs, collision/zones metadata และ engine handoff สำหรับ Godot/Unity/raw 2D workflow.

Repo นี้สำคัญกับ A-Wiki มากกว่าเครื่องมือ preview ทั่วไป เพราะแยกบทบาทชัด: **agent ตัดสิน asset plan + image generation สร้าง raw art + local scripts ทำ cleanup/export/QC**.

## หลักที่ควรยึด

| หลัก | เหตุผล |
|---|---|
| Generate raw art ด้วย image generation | ไม่ใช้ Canvas/SVG/PIL วาด placeholder เป็น final sprite art |
| ใช้ solid magenta `#FF00FF` background | ทำ chroma-key removal ได้ deterministic |
| แยก body sheet กับ FX | ป้องกัน slash/projectile/impact ทำให้ตัวละครหดใน fixed cell |
| ใช้ multi-row grid สำหรับ body animation | ลด drift/crop ที่เจอบ่อยใน single-row sheet |
| QC ก่อน assemble atlas | ตรวจ edge touch, scale drift, feet anchor, silhouette ก่อนรวมเป็น engine atlas |
| Map base ต้อง foundation-only | props/collision/interactables ต้องแยก layer เพื่อ runtime ควบคุมได้ |

## Sprite modes ที่ใช้ซ้ำได้

| Request | Plan |
|---|---|
| 4-direction overworld hero | `player_sheet`, raw `4x4`, rows = down/left/right/up |
| Side-view hero multiple actions | `hero_action_bundle`, generate idle/run/attack/jump แยก sheet |
| Spell | `spell_bundle`: caster cast + projectile + impact |
| NPC walk | `npc` + `walk`, usually compact grid |
| Projectile | `projectile`, often strip or `2x2` depending runtime |
| Impact/explosion | `impact` / `explode`, usually `2x2` |

## Output contract

```text
raw-sheet.png
raw-sheet-clean.png
sheet-transparent.png
frames/*.png
animation.gif
prompt-used.txt
pipeline-meta.json
```

สำหรับ player sheet ควรมี direction strips และ GIF แยกทิศด้วย เพื่อ QC movement ในเกม top-down.

## คำศัพท์

| คำ | แปลไทย | ความหมาย / รากคำ |
|---|---|---|
| chroma-key | การตัดพื้นหลังด้วยสีคีย์ | `chroma` มาจากกรีกแปลว่าสี; ใช้สีเฉพาะ เช่น magenta เพื่อลบพื้นหลัง |
| atlas | แผนที่รวมภาพ / texture atlas | รวม asset หลายชิ้นในภาพเดียวเพื่อลดโหลด texture |
| anchor | จุดยึด | จุดอ้างอิงของ sprite เช่น center, bottom, feet |
| QC | ตรวจคุณภาพ (Quality Control) | ตรวจว่าเฟรมไม่แตะขอบ scale ไม่เพี้ยน และ animation อ่านชัด |
| engine handoff | ส่งต่อเข้า game engine | ส่งออกพร้อม metadata ที่ engine ใช้ต่อได้ เช่น collision, zone, frame order |

## Links

- Repo: https://github.com/0x0funky/agent-sprite-forge
- Raw snapshot: `raw/github-0x0funky-agent-sprite-forge-2026-06-13/`
- Related synthesis: [[synthesis/pixel-animation-sprite-pipeline]]
