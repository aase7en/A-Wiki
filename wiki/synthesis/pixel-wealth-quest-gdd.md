---
type: synthesis
title: "Pixel Wealth Quest — Game Design Document"
slug: pixel-wealth-quest-gdd
tags: [game-design, gamification, finance, pixel-art, phaser, pixellab, tide-and-tally, nong-sunday, cozy-game]
sources: [trading-rpg-project-brief-2026-05-30]
created: 2026-06-03
updated: 2026-06-03
---

# Pixel Wealth Quest — Game Design Document

## คำถามที่ตอบ

"จะออกแบบ *Pixel Wealth Quest* — เกม pixel-art cozy ที่แปลงพฤติกรรมการออม/ลงทุนจริงให้เป็น gamification loop — เป็นโมดูลในเว็บบริษัท Sunday Estate อย่างไร โดย reuse ของที่มีอยู่ (Tide & Tally + PixelLab pipeline + A-Wiki) ให้มากที่สุด เบา ปลอดภัย และต่อยอดขายได้?"

> เอกสารนี้ประมวลผลจาก prompt ต้นฉบับ (`~/Downloads/gemini-code-1780419550203.md`) แล้วปรับให้ตรงสถานะจริงของโค้ดเบส (ดู [[8-bit-trading-rpg-blueprint]]). แผน execution เต็ม + handoff อยู่ที่ `pixel-wealth-quest/HANDOFF.md` (repo `sunday-estate-webapp`).

## สรุป

[verified 2026-06-03] *Pixel Wealth Quest* (PWQ) = **โมดูลเกม cozy life-sim ใหม่** ใน `sunday-estate-webapp/pixel-wealth-quest/` (React + Vite + TS + Phaser + Zustand) แยกจากเกม **Tide & Tally** (เรือโจรสลัดเทรดบอท) แต่ **reuse asset/ธีม/logic เดิมหนัก** และเชื่อมเป็น "โลกเดียว" ทางพื้นที่: **บ้านหลายห้อง → ฟาร์มติดทะเล → (อนาคต) เรือโจรสลัด**. ตัวเอกคือ **น้องซันเดย์** เด็กชายชุดกั๊กกรมท่า (โทนแบรนด์ Sunday Estate).

**กฎเหล็ก (Iron Law) — ไม่ต่อรอง:** เกมเป็น **visualization/reward layer เท่านั้น** — ไม่ถือ API key, ไม่ส่ง order, ไม่ทำ trade. ตัวเลขการเงินทั้งหมดเป็น **mock** ก่อน แล้วต่อ **feed จริงแบบ read-only** ภายหลังหลัง compliance (สืบทอดจาก [[8-bit-trading-rpg-blueprint]]).

---

## 1. แนวคิดหลัก & วงจร Gamification (Core Concept & Loop)

### โลกเดียวที่เดินต่อกัน (Unified World)
```
[บ้านหลายห้อง: in]  →ประตู→  [ฟาร์มติดทะเล: out]  →ขอบฟ้า→  [เรือโจรสลัด = Tide & Tally]
 Portfolio/ออม          ปลูก-ขาย-จ้างบอท              บอทออก "ล่องเทรด" (อนาคต)
```

### วงจรการให้รางวัล (Reward / Dopamine Loop)
| พฤติกรรมจริง | กลไกในเกม | รางวัลพิกเซล |
|---|---|---|
| ออมเงินรายวัน (งดกาแฟ/ของฟุ่มเฟือย) | The Latte Factor | กราฟทบต้นพุ่ง + เหรียญในเกม |
| ลงทุนสม่ำเสมอ | พอร์ตโต (mock→real read-only) | มูลค่าพอร์ตในห้องเพิ่ม |
| ขายผลผลิตฟาร์ม | เศรษฐกิจในเกม | จ้าง/อัปเกรด Worker-Bot |
| มีวินัย-คุมความเสี่ยง | บอททำงาน, สถานะดี | บอท P&L + bounty (ไม่ใช่กำไรดิบ) |

> **หลักชนะ:** เปลี่ยน "ความน่าเบื่อของ dashboard การเงิน" ให้เป็น **behavioral feedback** ที่ cozy และเสพติดเชิงบวก — รางวัลผูกกับ *วินัย/ความสม่ำเสมอ* ไม่ใช่การเทรดบ่อยหรือกำไรวันเดียว

### ระบบในบ้าน (Cozy House Rooms) — [verified 2026-06-03 · Phase 2a.1 built]
บ้านภายในเป็นหลายห้องแบบชีวิตจริง ไม่ใช่ห้องเดียว: **ห้องรับแขก+TV**, **ห้องทำงาน**, **ห้องนอน**, **ห้องครัว+โต๊ะกินข้าว**. ผู้เล่นเดินชน **ประตูโปร่งแสง** เพื่อเปลี่ยนห้องและ spawn ถูกฝั่งทางเข้า/ออก. Logic room graph อยู่ใน `src/data/room.seed.ts` + `src/logic/house.ts`; state เก็บ `houseRoomId` + `playerCell`.

Hotspots ในบ้าน:
- **TV / โต๊ะทำงาน** → Portfolio dashboard (มูลค่าพอร์ต, day change, allocation)
- **ครัว / โต๊ะกินข้าว / ชั้นความรู้** → The Latte Factor (ทบต้น 8%/ปี → projection 10/20/30 ปี)
- **กรอบรูปครอบครัว** (รูปจริงของน้องซันเดย์) → ข้อความสร้างแรงจูงใจการออม

### ระบบนอกบ้าน (Cozy Compounding Farm) — [verified 2026-06-03 · Phase 2a built]
ฟาร์ม top-down: ประตูห้อง → ฟาร์ม → ประตูฟาร์มกลับห้อง. ผู้เล่นคลิกแปลงว่างเพื่อปลูก **แครอตทบต้น**, เวลาในฟาร์ม tick ตาม scene, crop โตเป็น `seed → sprout → ready`, แล้วคลิกเก็บเกี่ยว/ขายได้ **+24 เหรียญในเกม**. Logic อยู่ใน `src/logic/farm.ts` และ store action อยู่ใน `src/state/store.ts` จึงต่อ Phase 2b Worker-Bot ได้โดยไม่ผูกกับ Phaser.

ขั้นต่อไปของฟาร์ม: ใช้เหรียญจ้าง **Worker-Bot** (= เทรดบอท) มาทำงานฟาร์มอัตโนมัติ (1 บอท = 1 งาน) → ต่อสู้ความผันผวนตลาด (พายุ = เหตุการณ์ตลาด).

---

## 2. สถาปัตยกรรมซอฟต์แวร์ & Repositories

### 2 git repo แยกกัน
| Repo | บทบาท |
|---|---|
| **A-Wiki** (`github.com/aase7en/A-Wiki`) | สมอง: PixelLab scripts (`scripts/game/`), asset pipeline, GDD/wiki, drive secrets, **news generator** |
| **sunday-estate-webapp** (`github.com/aase7en/sunday-estate-webapp`) | ผลิตภัณฑ์: `prototype/` (เว็บบริษัท), `game/` (Tide & Tally), **`pixel-wealth-quest/`** (โมดูลใหม่) |

### บทบาท repo ในเอกสาร Gemini (ตัดสินใจจริง)
| Repo อ้างอิง | บทบาทที่ตั้งใจ | ตัดสินใจ |
|---|---|---|
| [Phaser 3](https://github.com/phaserjs/phaser) | game engine + grid/iso | ✅ ใช้อยู่แล้ว |
| [Pixel Agents](https://github.com/pixel-agents-hq/pixel-agents) | agent sprite + speech bubble | ⏸ reference — pattern crew-sprite + gameBus มีแล้ว |
| [TradingGym](https://github.com/Yvictor/TradingGym) | RL trading env | ❌ ขัด mock-only; offline backtest Phase 5+ เท่านั้น |
| [Local LLM NPC](https://github.com/code-forge-temple/local-llm-npc) | Gemma 3n/Ollama NPC dialogue | ⏸ Phase 3 (ก่อนนั้น canned + free-model) |
| [Turbovec](https://github.com/RyanCodrai/turbovec) | vector index RAG | – ของ A-Wiki opt-in, ไม่เกี่ยวเกมตรง |
| [SkillOpt](https://github.com/microsoft/SkillOpt) | bot decision (no weight tuning) | ❌ research, เลื่อน |
| OmegaWiki | multi-agent + compression | ❌ A-Wiki ครอบ niche แล้ว |

> **นโยบาย:** ไม่ clone repo หนัก — **เสริม A-Wiki** แทน (GDD + handoff + free-model news generator + harden PixelLab pipeline). ผ่าน `docs/protocols/brain-improvement-gate.md`.

### Stack & Frontend (mirror Tide & Tally)
Phaser 3.80 (HTML5 + iso grid) · React 18 (HUD overlay) · Zustand vanilla (store เดียว Phaser อ่าน 60fps / React subscribe) · Vite 5 · Vitest (logic test-first). โมดูลฝังเข้าเว็บบริษัทผ่าน **iframe** (คุม 2 build system ไม่ชนกัน).

---

## 3. พิมพ์เขียว PixelLab API (V2 Integration) — สถานะจริง

[verified 2026-06-03] Tide & Tally **มี PixelLab asset pack เต็มชุดแล้ว** ที่ `game/public/assets/trading-rpg-pirate-prototype/` (ตัวละคร 8 ทิศ 10 archetype, นก `news_gull_courier`, กรอบ UI parchment, props, tiles, ฉาก). PWQ **reuse** ของเหล่านี้.

| ความต้องการ (Gemini) | Endpoint | สถานะใน repo |
|---|---|---|
| ตัวละคร/บอท 8 ทิศ + animation | `/create-character-v3`, `/create-character-with-8-directions`, `/animate-character` | ✅ wrap แล้ว: `scripts/game/pixellab_character.py`; น้องซันเดย์ clean 8 rotations + south-facing idle/walk/run/sit/lie/eat/cry integrated in Phase 1.5 |
| ฉาก/พื้นผิว (scene art) | `/create-image-pixflux` (sync ≤400px) | ✅ wrap แล้ว: `scripts/game/pixellab_generate_image.py` (+ `--upscale` NEAREST) |
| กระเบื้อง iso/พื้นดิน | `/create-isometric-tile`, `/create-tiles-pro` | async — Phase 2 (Phase 1 ใช้ placeholder + pixflux) |
| ATM/กระปุก/map objects | `/map-objects`, `/create-8-direction-object` | async — Phase 2/3 |
| ป๊อปอัป/เฟรม UI JRPG | `/generate-ui-v2` | async — reuse กรอบ parchment ที่มีแล้ว |

**Secret:** `PIXELLAB_API_TOKEN` ดึง on-demand จาก Drive secrets (`scripts/lib/drive_secrets.py`) — ไม่ hardcode/commit. **Workflow มาตรฐาน:** skill `skills/claude-code/pixellab-asset-ingest/SKILL.md` + [[pixellab-phaser-asset-convention]] + [[pixellab-api-endpoint-matrix]] + [[pixellab-asset-pipeline-for-trading-rpg]].

**งบ:** เริ่ม $5 และใช้จริงต่ำมากเพราะ reuse หนัก. Phase 1.5 ใช้ jobs ที่ Claude ยิงไว้แล้ว (transcript ระบุประมาณ $0.065 USD หลัง trial generations) → ยิงเพิ่มเฉพาะเมื่อ visual QA ต้องการ 8-dir walk/run หรือ props ใหม่.

---

## 4. Harness, การคุมความเสี่ยง & Event Hooks (5-Layer)

| Layer | บทบาท | ใน PWQ/A-Wiki |
|---|---|---|
| **L1 Memory** | `CLAUDE.md` + `Risk.md` คุมพฤติกรรม | Iron Law ใน CLAUDE.md + ADR `0001-pwq-stack-and-iron-law` |
| **L2 Knowledge (Playbooks/Skills)** | กลยุทธ์เป็นชุดความสามารถ progressive disclosure | strategies seed + skills ECC/9arm |
| **L3 Guardrail (Event Hooks)** | ดักพฤติกรรมการเงินไม่พึงประสงค์ | **`validateBriefingSafe`** (regex บล็อก buy/sell/order/ซื้อ/ขาย) เป็นตัวอย่างจริง; `PortfolioFeed` interface ไม่มี method เขียน/order → Iron Law บังคับด้วย type system; hooks A-Wiki (secret leak, no-branch) |
| **L4 Delegation (Subagents)** | แยกงานประมวลผลข่าว/คำนวณ ไม่เปลือง context หลัก | **free-model news generator** (`generate-briefing.mjs` → Gemini Flash/OpenRouter ฟรี) ผลิต `briefings/latest.json` แบบ read-only |

---

## 5. ฟังก์ชันการเงินเชิงลึก (Gameplay Mechanics)

### The Latte Factor — [verified 2026-06-03 · Phase 1 built]
กรอกค่าใช้จ่ายฟุ่มเฟือยรายวัน → แปลงเป็นเงินออม/ปี → ทบต้น **8%/ปี** → แสดง projection 10/20/30 ปี. (เช่น ฿120/วัน → ~฿4.96M ใน 30 ปี). Logic บริสุทธิ์ test-first (`logic/compounding.ts`, `logic/latteFactor.ts`).

### น้องซันเดย์ Animation — [verified 2026-06-03 · Phase 1.5 + 2a.2 built]
PixelLab สร้าง clean 8 rotations จาก `character_id=58be20a8-ee08-4432-bb43-3627f69e12ac` และ action frames south-facing 7 ชุด: idle, walk, run, sit, lie, eat, cry. `normalize_pwq_anims.py` แปลง raw export เป็น `anim_clean/` + `src/phaser/playerAnims.ts`; Phaser preload/register แล้วเล่นจริงใน `RoomScene` และ `FarmScene`. Phase 2a.2 เพิ่ม **8-direction walk cycle** ครบ front/front-right/right/back-right/back/back-left/left/front-left; เมื่อตัวละครเดินเปลี่ยนช่อง ขาจะขยับตามทิศเดินจริง. ข้อจำกัดที่ยังเหลือ: run/sit/lie/eat/cry ยังเป็น south/front-facing; running ใช้ 8-dir walk cycle ที่ tween เร็วขึ้นจนกว่าจะคุ้มยิง run 8 ทิศ.

### Farm Economy — [verified 2026-06-03 · Phase 2a built]
- `src/data/farm.seed.ts`: layout ฟาร์ม 10x8, spawn/door, 4 plots, `DEFAULT_CROP` = `carrot`, growth 6 ticks, sell price 24 coins.
- `src/logic/farm.ts`: pure test-first `plantPlot`, `refreshPlotStage`, `harvestPlot`, `refreshPlots`, `replacePlot`.
- `src/phaser/scenes/FarmScene.ts`: top-down grid via `cellToScreenTopDown`, green programmatic floor, PixelLab plot/crop overlays, plant/harvest pointer zones, 1-second farm tick, Room<->Farm transition.
- PixelLab Phase 2a spend: 4 pixflux PNGs in `public/assets/farm/` for about `$0.029`; `farm-soil-plot-v001.png` is kept as candidate because it returned as a veggie sprite sheet rather than clean soil.

### House Room Navigation — [verified 2026-06-03 · Phase 2a.1 built]
- 4 room backgrounds in `public/assets/room/`: `room-living-tv-iso-v001.png`, `room-office-iso-v001.png`, `room-bedroom-child-iso-v002.png` (bedroom), `room-kitchen-iso-v001.png`.
- Bedroom art was regenerated as a child room: reading desk + lamp, toy shelf, teddy/soft doll, wall frames, no computer/TV; family-photo frame overlay still opens the large photo modal.
- `HOUSE_ROOMS` defines door cells and target spawn cells. Verified routes: living→office→living, living→kitchen→living, living→bedroom→living, living→Farm→living.
- UI polish: larger player scale, larger readable Plex Sans Thai HUD, translucent pulsing door markers with labels.
- PixelLab Phase 2a.1 spend: 3 pixflux room PNGs for about `$0.0287`; later child-bedroom polish spent about `$0.0230` and kept `room-bedroom-child-iso-v002.png`. Balance after bedroom polish was about `$4.8235`.

### Worker-Bot Economy / Bot Trading Command Center — [wiki · Phase 2b]
- ปลูก/ขายผัก → เหรียญ → **จ้าง Worker-Bot** (reuse 9 บอท NPC 8-ทิศจาก Tide & Tally)
- **1 บอท = 1 งานฟาร์ม** (รดน้ำ/พรวนดิน/ตัดไม้/เลี้ยงสัตว์)
- คลิกบอท → panel status + **กำไรขาดทุน (P&L)** (mock → real read-only)
- บอทตัวเดียวกันมีตัวตนคู่ (ลูกจ้างฟาร์ม + เทรดบอท) = **สะพานเชื่อม Tide & Tally**

### The Debt Dungeon — [wiki · Phase 3]
เปรียบเทียบสินทรัพย์ vs หนี้สินตามเวลา: หนี้ดี (ผ่อนเพื่อสร้างสินทรัพย์) = เครื่องผลิตเหรียญ; หนี้เสีย = ปรสิตสีแดงดูดพลังเมือง.

### News Bird (Morning Briefing) — [wiki · Phase 2c, ~80% reuse]
นก `news_gull_courier` บินมา **8 โมงเช้า** (in-game time) ส่งจดหมาย parchment = สรุปข่าว **ธุรกิจ/การเงิน/ลงทุน/เทคโนโลยี/คริปโต** จาก **Gemini Flash ฟรี** (ต่อยอด `generate-briefing.mjs` + เพิ่ม web-search) ผ่าน safety gate. (มี: นก, จดหมาย UI, `advisor.ts`, fallback chain, `latest.json`).

---

## สถานะการพัฒนา (Phase status)

| Phase | สถานะ | สาระ |
|---|---|---|
| **0 Foundations** | ✅ [verified 2026-06-03] | ingest น้องซันเดย์ (8 ทิศ + family) · scaffold โมดูล (build เขียว) · GDD นี้ · ADR · game-assets/manifests |
| **1 Room + Portfolio** | ✅ [verified 2026-06-03] | ห้อง iso เดินได้ · คลิกเฟอร์นิเจอร์ · Portfolio + Latte Factor + Family panel · ธีม parchment · mock feed seam |
| **1.5 Animation Reconcile** | ✅ [verified 2026-06-03] | PixelLab character wrapper + normalize script · 51 clean action frames · `PLAYER_ANIMS`/Phaser Sprite integration |
| **2a Farm + Economy** | ✅ [verified 2026-06-03] | FarmScene top-down · Room↔Farm door · pure farm logic · plant/grow/harvest/sell · coins HUD |
| **2a.1 House Rooms + Door UX** | ✅ [verified 2026-06-03] | 4 house rooms · transparent door markers · correct room spawn routing · bigger player/readable font · 46 unit tests เขียว |
| **2a.2 House/Pets + 8-dir Walk** | ✅ [verified 2026-06-03] | modern solar house v002 · 3-dog pet pack wandering · น้องซันเดย์ walk animates all 8 directions · 53 unit tests เขียว |
| **2b Worker-Bots** | ⬜ | hire/assign bot logic + status/P&L panel |
| **2c News Bird** | ⬜ | gull courier + briefing safety gate + free model generator |
| **3 Debt Dungeon + animation polish** | ⬜ | Debt mechanic, NPC coach, optional 8-dir run/emotes หลัง visual QA |
| **4 Sea + ลิงก์ Tide & Tally** | ⬜ | รวม roster บอท 2 เกม |
| **5 Feed จริง read-only + ขาย** | ⬜ | compliance gate, packaging |

## แหล่งข้อมูล / Related
- [[8-bit-trading-rpg-blueprint]] — architecture + Iron Law ต้นทาง
- [[pixellab-phaser-asset-convention]] · [[pixellab-asset-pipeline-for-trading-rpg]] · [[pixellab-api-endpoint-matrix]]
- [[sources/trading-rpg-project-brief-2026-05-30]]
- Implementation + handoff: `sunday-estate-webapp/pixel-wealth-quest/` + `HANDOFF.md`
