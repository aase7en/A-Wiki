---
name: a-game
description: "สร้างเกม (Phaser/PixiJS/Three.js) — bind game-phaser-pipeline, phaser-core, phaser-arcade-physics, pixijs-rendering, threejs-scene-setup, threejs-gltf-loading, threejs-materials-lighting. Dispatcher ล้วน. Trigger: 'เกม', 'game', 'phaser', 'pixijs', 'threejs', 'webgl'."
version: 1.0.0
author: A-Wiki
domain: [code, media]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Game"
a_phase: any
---

# A-Game — งานพัฒนาเกม (Phaser / PixiJS / Three.js)

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง

## เมื่อไหร่ใช้

✅ ใช้:
- สร้างเกม 2D (Phaser/PixiJS) หรือ 3D (Three.js) บน web
- แกะ/แก้ scene setup, physics, rendering
- โหลด GLTF model / ทำ materials & lighting

❌ ข้าม:
- แค่ CSS animation → `motion-patterns`
- เว็บทั่วไป → `/A-Web`
- งาน 3D นอกเกม (product viewer) → `threejs-*` ตรงๆ

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ**

```
focus_set({"skill": "a-game", "goal": "<done criteria>", "phase": "ask"})
```

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` · `grill-with-docs` | 2D/3D? genre? platform? target FPS? |
| DESIGN | `game-phaser-pipeline` (สำหรับ 2D Phaser) · **`a-design`** (menu/HUD/onboarding UI — ใช้ grammar sequential-story สำหรับ tutorial, consumer-service สำหรับ settings/menu) · scene structure | วาง scene graph + asset list + loop shape + game UI composition |
| PLAN | `a-plan` | แตกเป็น slice (boot → preload → main scene → physics → polish) |
| IMPLEMENT (2D) | `phaser-core` · `phaser-arcade-physics` · `pixijs-rendering` | โค้ดจริง |
| IMPLEMENT (3D) | `threejs-scene-setup` · `threejs-gltf-loading` · `threejs-materials-lighting` | โค้ดจริง |
| REVIEW | `a-council` | รีวิว perf + scene structure |
| DEBUG | `a-debug` · `blender-motion-state-inspection` (ถ้า export จาก Blender) | repro → root cause |
| TEST | `e2e-testing` · `browser-qa` | smoke + ตรวจ FPS/leak |

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ใช้ threejs-* ตรงๆ ก็ได้" | ได้ — แต่ยังต้อง `focus_set` และเลือก 2D vs 3D stack ก่อน |
| "เกมไม่ต้อง test" | ผิด — regression ของ physics/rendering พบบ่อย; smoke test จำเป็น |

## Invocation

```
/A-Game "<งาน>"
```
