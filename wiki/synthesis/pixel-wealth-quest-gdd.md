---
type: synthesis
title: "Pixel Wealth Quest — Game Design Document"
slug: pixel-wealth-quest-gdd
tags: [game-design, gamification, finance, pixel-art, phaser, pixellab, tide-and-tally, nong-sunday, cozy-game]
sources: [trading-rpg-project-brief-2026-05-30]
created: 2026-06-03
updated: 2026-06-04
---

# Pixel Wealth Quest — Game Design Document

> [verified 2026-06-05] Renamed user-facing product labels to **Sunday Invest Moon** in Phase 2c.1. The legacy `pixel-wealth-quest/` directory slug and this historical GDD filename remain unchanged to avoid breaking paths.

## คำถามที่ตอบ

"จะออกแบบ *Pixel Wealth Quest* — เกม pixel-art cozy ที่แปลงพฤติกรรมการออม/ลงทุนจริงให้เป็น gamification loop — เป็นโมดูลในเว็บของบริษัทเจ้าของ (private) อย่างไร โดย reuse ของที่มีอยู่ (Tide & Tally + PixelLab pipeline + A-Wiki) ให้มากที่สุด เบา ปลอดภัย และต่อยอดขายได้?"

> เอกสารนี้ประมวลผลจาก prompt ต้นฉบับ (`~/Downloads/gemini-code-1780419550203.md`) แล้วปรับให้ตรงสถานะจริงของโค้ดเบส (ดู [[8-bit-trading-rpg-blueprint]]). แผน execution เต็ม + handoff อยู่ที่ `pixel-wealth-quest/HANDOFF.md` ใน product repo.

## สรุป

[verified 2026-06-03] *Pixel Wealth Quest* (PWQ) = **โมดูลเกม cozy life-sim ใหม่** ใน `<product-repo>/pixel-wealth-quest/` (React + Vite + TS + Phaser + Zustand) แยกจากเกม **Tide & Tally** (เรือโจรสลัดเทรดบอท) แต่ **reuse asset/ธีม/logic เดิมหนัก** และเชื่อมเป็น "โลกเดียว" ทางพื้นที่: **บ้านหลายห้อง → ฟาร์มติดทะเล → (อนาคต) เรือโจรสลัด**. ตัวเอกคือ **น้องซันเดย์** เด็กชายชุดกั๊กกรมท่า (โทนแบรนด์ของบริษัท).

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
บ้านภายในเป็นหลายห้องแบบชีวิตจริง ไม่ใช่ห้องเดียว: **ห้องรับแขก+TV**, **ห้องทำงาน**, **ห้องนอน**, **ห้องครัว+โต๊ะกินข้าว**, และ **ห้องน้ำ**. ผู้เล่นเดินชน **ประตู/จุดวาร์ปโปร่งแสง** เพื่อเปลี่ยนห้องและ spawn ถูกฝั่งทางเข้า/ออก. [verified 2026-06-04] มี regression test กันเคส spawn ทับประตูย้อนกลับ และ `RoomScene` มี cooldown สั้น ๆ หลังเปลี่ยนห้องเพื่อกันเด้งกลับทันที. Logic room graph อยู่ใน `src/data/room.seed.ts` + `src/logic/house.ts`; state เก็บ `houseRoomId` + `playerCell`.

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
| **product webapp repo** (`<owner>/<product-repo>`) | ผลิตภัณฑ์: `prototype/` (เว็บบริษัท), `game/` (Tide & Tally), **`pixel-wealth-quest/`** (โมดูลใหม่) |

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

### House Room Navigation — [verified 2026-06-04 · Phase 2a.1-2a.4 built]
- 5 playable room backgrounds in `public/assets/room/`: living room, office, child bedroom, kitchen, and bathroom. Current active set uses wide straight-on images: `room-living-tv-wide-v002.png`, `room-office-wide-v002.png`, `room-bedroom-child-wide-v003.png`, `room-kitchen-wide-v002.png`, `room-bathroom-wide-v001.png`.
- Bedroom art was regenerated as a child room: reading desk + lamp, toy shelf, teddy/soft doll, wall frames, no computer/TV; family-photo frame overlay still opens the large photo modal.
- `HOUSE_ROOMS` defines door cells/fractional zones and target spawn points. Verified routes: living→office→living, living→kitchen→living, living→bathroom→living, living→bedroom→living, living→Farm→living. The living-room bottom middle now contains kitchen + bathroom routes; the baked back-wall door remains the Farm exit.
- UI polish: larger player scale, larger readable Plex Sans Thai HUD, translucent pulsing door markers with labels.
- PixelLab Phase 2a.1 spend: 3 pixflux room PNGs for about `$0.0287`; later child-bedroom polish spent about `$0.0230` and kept `room-bedroom-child-iso-v002.png`. Balance after bedroom polish was about `$4.8235`.

### Room Perspective + Free Movement — [verified 2026-06-03 · Phase 2a.3 built]
Phase 2a.3 แก้ปัญหา “ห้องนอนเป็นมุมมองแนวนอน แต่ control ยังเดินเฉียงแบบ iso grid” โดยเปลี่ยน `RoomScene` เป็น **continuous free movement** บนแกนจอจริง: กดขึ้น = เดินขึ้น, ลง = ลง, ซ้าย/ขวา = ซ้าย/ขวา, กดเฉียง = normalized diagonal แบบ joystick. Logic ทดสอบได้อยู่ใน `src/logic/roomFreeMovement.ts`. ห้องทั้ง 4 ถูก regenerate เป็นมุมกล้องเดียวกันแบบ wide straight-on cutaway: `room-living-tv-wide-v002.png`, `room-office-wide-v002.png`, `room-bedroom-child-wide-v003.png`, `room-kitchen-wide-v002.png`. การวาร์ปใช้ fractional door zones ที่วางบน **ประตูที่วาดอยู่ในภาพห้องเอง** พร้อม marker/label โปร่งแสงเท่านั้น; ลบ generated standalone door overlay แล้วเพราะ style ไม่เข้ากับภาพห้อง.

Follow-up: ประตูบานกลางขวาบนผนังหลังของห้องรับแขกถูกเปลี่ยนเป็นทางออกไป **ฟาร์ม** (`living-farm`) และลบจุดฟาร์มล่างโซฟาที่ไม่ตรงกับประตูจริงแล้ว.

### Household Dogs — [verified 2026-06-04 · Phase 2a.4 built]
จากเดิมหมา 3 ตัวถูก bake เป็น sprite กลุ่มเดียว ตอนนี้แยกเป็น 3 actor (`black`, `red`, `cream`) ใน `PET_DOGS` และ `PetPack` ให้เดินอิสระคนละจังหวะในบ้าน/ฟาร์ม. Asset อยู่ที่ `public/assets/character/pets/individual/{black,red,cream}/` รวม 48 PNG (3 ตัว x 8 ทิศ x 2 walking frames). ข้อจำกัด: เฟรมชุดนี้ derive จากภาพกลุ่มเดิม จึงอาจมี artifact บางมุม; ถ้าต้อง production-grade ให้ยิง PixelLab character แยก 3 ตัวจาก reference หน้าตรง.

### Worker-Bot Economy / Bot Trading Command Center — [verified 2026-06-05 · roadmap Phase 2d built]
- ปลูก/ขายผัก → เหรียญ → **จ้าง Worker-Bot** ด้วย mock/local economy เท่านั้น
- **1 บอท = 1 งานฟาร์ม** และ 1 แปลงเป้าหมาย: till/plant/water/harvest/tend ผ่าน pure `workerBotFarmTick`
- คลิกบอท → responsive hire/assign/status panel; P&L/trading bot status ยังเป็น mock visualization แยกจาก Worker-Bot state
- บอทมีตัวตนเป็นลูกจ้างฟาร์มก่อน ส่วน trading-bot/feed จริงยังต้องผ่าน read-only/compliance gate ในอนาคต

### The Debt Dungeon — [verified 2026-06-05 · roadmap Phase 3 built]
เปรียบเทียบสินทรัพย์ vs ภาระหนี้ตามเวลาแบบไม่ตีตราผู้เล่น: หนี้สร้างสินทรัพย์ = ภาระที่มี asset backing; หนี้ดอกเบี้ยสูง = แรงกดดันที่ต้องทำให้เห็นผลของดอกเบี้ย. Phase 3 เพิ่ม mock liabilities + pure projection, derived store state, read-only HUD panel, encounter cards, deterministic NPC coach lines, และ Farm portal. Runtime QA ผ่าน desktop/iPhone/iPad โดยไม่มี horizontal overflow และไม่มีปุ่มสมัคร/กู้/จ่ายเงินจริง.

### News Bird (Morning Briefing) — [verified 2026-06-05 · roadmap Phase 2e built]
นก `news_gull_courier` ส่งจดหมาย parchment เวลา **8 โมงเช้า** ตาม in-game clock. Client อ่านเฉพาะ static `/briefings/latest.json` หรือ fallback canned ที่ safety-gate แล้ว; ไม่มี API key, generation request, หรือคำสั่งซื้อขายใน bundle. `npm run briefing:generate` เป็น author-time tool นอก Vite สำหรับสร้าง dated JSON + `latest.json` และ preserve last good file เมื่อไม่มี key. Runtime smoke พิสูจน์ 08:00 → gull visible → click opens letter → 3 cards render → console clean.

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
| **2a.3 Room Perspective + Free Movement** | ✅ [verified 2026-06-03] | 4 wide rooms same camera · living back-wall door exits to farm · joystick-like continuous control · 60 unit tests เขียว |
| **2a.4 Door/Bathroom/Pet Reconcile** | ✅ [verified 2026-06-04] | กันเด้งกลับหลังเปลี่ยนห้อง · เพิ่มห้องน้ำ · living ลงล่างไปครัว/ห้องน้ำ · หมา 3 ตัวเดินแยก · 64 unit tests เขียว |
| **2b/2d Worker-Bots** | ✅ [verified 2026-06-05] | hire/assign logic, farm automation, sprites, responsive status UI |
| **2c/2e News Bird** | ✅ [verified 2026-06-05] | gull courier, safe briefing domain/feed/UI, author-time generator, runtime smoke |
| **3 Debt Dungeon + animation polish** | ✅ [verified 2026-06-05] | Debt domain/projection, store/HUD, encounter cards, NPC coach, Farm portal, responsive QA; optional animation polish remains future polish |
| **4 Sea + ลิงก์ Tide & Tally** | 🟨 [started 2026-06-05] | Read-only future visual bridge contract built; UI/portal still next |
| **5 Feed จริง read-only + ขาย** | ⬜ | compliance gate, packaging |

## แหล่งข้อมูล / Related
- [[8-bit-trading-rpg-blueprint]] — architecture + Iron Law ต้นทาง
- [[pixellab-phaser-asset-convention]] · [[pixellab-asset-pipeline-for-trading-rpg]] · [[pixellab-api-endpoint-matrix]]
- [[sources/trading-rpg-project-brief-2026-05-30]]
- Implementation + handoff: `<product-repo>/pixel-wealth-quest/` + `HANDOFF.md`
