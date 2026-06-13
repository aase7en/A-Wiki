---
type: source
title: "GitHub: blendi-remade/sprite-sheet-creator"
tags: [github, pixel-art, sprite-sheet, animation, fal-ai, canvas, game-assets]
source_url: https://github.com/blendi-remade/sprite-sheet-creator
original_file: raw/github-blendi-remade-sprite-sheet-creator-2026-06-13/README.md
raw_archive: raw/github-blendi-remade-sprite-sheet-creator-2026-06-13/source-5af18208bef1ff989fedacbdf09c2184d0e7387a.tar.gz
commit: 5af18208bef1ff989fedacbdf09c2184d0e7387a
routed_via: harness@v1
routing_note: "Harness attempted; manual fallback because Tier 0 model call failed local SSL certificate verification."
confidence: "[verified 2026-06-13]"
created: 2026-06-13
updated: 2026-06-13
---

# GitHub: blendi-remade/sprite-sheet-creator

## สรุป

[verified 2026-06-13] `sprite-sheet-creator` เป็นเว็บ Next.js/React สำหรับสร้าง **sprite sheet (แผ่นเฟรมสไปรต์)** และ sandbox preview ของตัวละคร 2D โดยใช้ fal.ai เป็น image-generation backend. แนวคิดที่มีประโยชน์กับ A-Wiki คือ flow แบบครบวงจร: prompt/reference -> generate character -> generate action sheets -> remove background -> split frames -> preview animation -> test in sandbox.

## จุดที่ควรเรียนรู้

| หัวข้อ | ความรู้ที่นำไปใช้ |
|---|---|
| Game modes | รองรับ side-scroller และ isometric/RPG; ช่วยคิดแยก asset สำหรับเกมแนวนอนกับเกม top-down |
| Action coverage | side-scroller ใช้ walk, jump, attack, idle; isometric ใช้ walk/attack หลายทิศ + idle |
| Grid extraction | มีการ split frame จาก sprite sheet ด้วย grid dividers ที่ปรับได้ |
| Preview loop | มี animation preview ปรับ FPS ได้ ก่อนเอาเข้า runtime |
| Sandbox tuning | มี per-sprite scale sliders และ map/layer offset sliders เพื่อแก้ scale/alignment โดยไม่ต้อง regenerate |
| Model choice | เลือก model กลาง flow แล้วใช้ทั้ง pipeline เช่น Nano Banana Pro หรือ GPT Image 2 ผ่าน fal.ai |

## Architecture ที่เห็นจาก repo

```text
Prompt / uploaded reference
  -> fal.ai image generation
  -> background removal
  -> grid-based frame extraction
  -> canvas/Pixi-style preview sandbox
  -> scale / FPS / layer tuning
  -> game-ready frame assets
```

## ข้อควรใช้กับ Sunday Invest Moon

- ใช้เป็น reference pattern สำหรับสร้าง panel/เครื่องมือภายใน A-Wiki ที่ตรวจ sprite sheet หลัง generate.
- เก็บ concept "ปรับ scale ใน sandbox ก่อน regenerate" เพื่อลดค่า image generation.
- สำหรับตัวละคร Sunday/NPC/สัตว์ ให้ generate ทีละ action แล้ว preview FPS/anchor ก่อนนำเข้า Phaser.
- อย่าคัดลอก dependency/API key handling ตรง ๆ; A-Wiki ต้องเก็บ secret ใน external data layer เท่านั้น.

## คำศัพท์

| คำ | แปลไทย | ความหมาย |
|---|---|---|
| sprite | สไปรต์ / ภาพตัวละครแยกชิ้น | ภาพ 2D ที่ engine นำไปวางและขยับในฉาก |
| sprite sheet | แผ่นเฟรมสไปรต์ | ภาพเดียวที่รวมหลายเฟรมไว้ใน grid เพื่อใช้ทำ animation |
| frame extraction | การแยกเฟรม | ตัด sprite sheet ออกเป็นภาพย่อยตาม grid |
| sandbox | สนามทดลอง runtime | พื้นที่ทดสอบ asset ใน movement/animation จริงก่อนใช้ในเกม |

## Links

- Repo: https://github.com/blendi-remade/sprite-sheet-creator
- Raw snapshot: `raw/github-blendi-remade-sprite-sheet-creator-2026-06-13/`
- Related synthesis: [[synthesis/pixel-animation-sprite-pipeline]]
