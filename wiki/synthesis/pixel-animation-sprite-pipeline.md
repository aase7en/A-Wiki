---
type: synthesis
title: "Pixel Animation Sprite Pipeline"
tags: [pixel-art, animation, sprite-sheet, phaser, game-assets, sunday-invest-moon, codex-skill]
sources:
  - github-blendi-remade-sprite-sheet-creator
  - github-0x0funky-agent-sprite-forge
  - pixellab-asset-pipeline-for-trading-rpg
created: 2026-06-13
updated: 2026-06-13
confidence: "[verified 2026-06-13]"
---

# Pixel Animation Sprite Pipeline

## ใช้เมื่อไหร่

ใช้หน้านี้เมื่อ A-Wiki/Codex ต้องสร้างหรือแก้ **pixel animation** สำหรับเกม เช่น Sunday Invest Moon, Pixel Wealth Quest, NPC, สัตว์, market/town characters, projectiles, FX, prop packs หรือแผนที่ top-down ที่ต้องนำเข้า Phaser/Godot/Unity.

## สรุปสั้น

[verified 2026-06-13] pattern ที่ควรจำคือ **generate -> clean -> split -> QC -> preview -> import**. ห้ามข้าม QC เพราะ sprite sheet ที่ดูสวยในภาพเดียวมักพังเมื่อแยกเฟรม: scale drift, feet anchor ลอย, edge touch, body หดเพราะ FX กว้างเกิน, หรือ frame order อ่านไม่ออก.

## Decision Table

| ต้องการสร้าง | ใช้ workflow | Sheet default | หมายเหตุ |
|---|---|---:|---|
| ตัวละคร top-down 4 ทิศ | `player_sheet` / `npc_walk` | `4x4` | row = down/left/right/up; 4 frames ต่อทิศ |
| idle สั้น | `idle` | `2x2` | breathing/weight shift; ใช้ shared scale |
| run/walk side-view | `walk`/`run` | `2x2` หรือ `2x3` | ห้ามใช้ raw `1xN` ถ้าเป็น body character |
| attack hero | body-only attack + separate FX | `2x2`/`2x3` | slash/projectile/impact แยก sheet |
| spell | `spell_bundle` | cast `2x3`, projectile, impact | ทำ runtime layering |
| prop pack เล็ก | `prop_pack_3x3` | `3x3` | เฉพาะ compact props เช่น crate, sign, lamp |
| building/gate/bridge | one-by-one หรือ custom wide pack | custom | ไม่ใส่ใน square prop pack |
| top-down map | foundation base + separate props | map-specific | base ห้าม bake runtime props |

## Prompt Baseline สำหรับ Sunday Invest Moon

```text
Top-down 2D pixel art for a cozy 16-bit farming RPG, full body visible,
3/4 view from slightly above, crisp dark outline, warm readable palette,
same character identity in every frame, exact 4x4 sprite sheet grid,
row 1 down, row 2 left, row 3 right, row 4 up,
four walk frames per direction, stable feet anchor line,
same body scale and bounding box in every cell,
solid flat #FF00FF background, no text, no labels, no borders,
leave magenta margin on all sides, nothing crosses cell edges.
```

สำหรับ NPC/สัตว์ใน Sunday game ให้เพิ่ม identity lock เช่น สีผม เสื้อ หมวก ทรงตัว ขนาดตัว และ accessory ที่ต้องคงเดิม.

## QC Checklist

| Check | ผ่านเมื่อ |
|---|---|
| edge touch | ไม่มีเฟรมใดแตะขอบ cell |
| identity lock | หน้า/สี/ชุด/accessory ไม่ drift ระหว่างเฟรม |
| feet anchor | เท้าหรือฐานอยู่ y-position ใกล้กันทุกเฟรม |
| shared scale | body สูงใกล้กันทุกเฟรม; action body ไม่หดเกิน 10-15% จาก idle/run |
| frame order | animation อ่านซ้ายไปขวา/บนลงล่างได้ตรง action |
| alpha cleanup | background โปร่งใสสะอาด ไม่มี magenta fringe |
| runtime preview | เปิดใน Phaser/Canvas แล้ว scale/anchor ถูกจริง |

## A-Wiki Integration Plan

1. เก็บ raw source และ prompt ทุกครั้งใน `raw/` หรือ asset manifest.
2. สร้าง asset ทีละ action: idle/walk/run/attack/cast แยกกันก่อน.
3. ใช้ `#FF00FF` background สำหรับงานที่ต้อง cleanup แบบ deterministic.
4. ทำ postprocess: chroma-key, split frame, align bottom/feet, shared scale, export transparent PNG/GIF.
5. ตรวจ `pipeline-meta.json` หรือ metadata เทียบ checklist.
6. Import เข้า Phaser ด้วย stable keys เช่น `pwq_npc_market_lady_walk_down_000`.
7. ทำ runtime smoke: canvas ไม่ blank, frame loop เล่นได้, no console/network errors.

## ใช้กับ Sunday Invest Moon ทันที

| Asset backlog | แนวทาง |
|---|---|
| Town market lady animation | `npc_walk` 4 ทิศ, `4x4`, prompt ใช้ cozy Thai market vendor |
| Festival judge / quiz teacher | `npc` idle `2x2` + walk `4x4` ถ้าต้องเดิน |
| Chicken/cow polish | generate action แยก: idle/eat/walk; ห้ามรวมหลาย action ใน raw sheet เดียว |
| Market stall props | prop one-by-one หรือ compact `2x2`; building/gate ไม่ใส่ square pack |
| Festival FX | แยก `fx`/`impact` sheet เช่น confetti, sparkle, reward burst |

## Related

- [[sources/github-blendi-remade-sprite-sheet-creator]]
- [[sources/github-0x0funky-agent-sprite-forge]]
- [[synthesis/pixellab-asset-pipeline-for-trading-rpg]]
- [[synthesis/pixellab-phaser-asset-convention]]
