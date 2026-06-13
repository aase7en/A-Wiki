---
> 2026-06-13 codex-poppy-javis: 13.3 done -- AnimalPanel + FarmScene animal render/click bridge + placeholder chicken/cow textures; targeted 53 tests + typecheck green. RESUME HERE -> 12.6 / 13.4 asset tickets.
type: synthesis
title: "Sunday Invest Moon — Cross-Agent Roadmap"
slug: sunday-invest-moon-roadmap
tags: [game-design, handoff, cross-agent, roadmap, sunday-invest-moon, phaser]
sources: [pixel-wealth-quest-gdd]
created: 2026-06-04
updated: 2026-06-13
---

# Sunday Invest Moon — Roadmap (cross-agent handoff)

> [verified 2026-06-05] **Cross-agent contract.** This file is the single source of truth for the Sunday Invest Moon refactor (formerly Pixel Wealth Quest). It lives in A-Wiki so Codex / Antigravity / Manus / Cursor / Claude can pick up where the previous agent left off without context-loss.
>
> **Source-of-truth policy**:
> 1. Edit only `A-Wiki/wiki/synthesis/sunday-invest-moon-roadmap.md` — canonical, git-tracked, FTS5-indexed (`python3 scripts/wiki/search-wiki.py "sunday invest moon"`).
> 2. `<product-repo>/pixel-wealth-quest/ROADMAP.md` is a product-repo mirror for agents working there. Do not edit it independently.
> 3. After every roadmap edit, run `python3 scripts/game/sync_sunday_invest_moon_roadmap.py --sync`, then run the same command without `--sync` to verify both copies match.
>
> **Code module**: `<product-repo>/pixel-wealth-quest/` · **GDD**: `A-Wiki/wiki/synthesis/pixel-wealth-quest-gdd.md` (rename header to Sunday Invest Moon when Phase 2c.1 ships).

---

## 60-second cold start (any Agent / IDE)

1. Read `## RESUME HERE`; it overrides stale TODOs in `HANDOFF.md`, chat transcripts, and local Claude plan files.
2. Read only the named ticket plus `Context`, `Cross-cutting reuse map`, and `Iron-Law guardrails`.
3. From A-Wiki, run `python3 scripts/agent-preflight.py` and `python3 scripts/game/sync_sunday_invest_moon_roadmap.py`.
4. From `<product-repo>`, confirm `git status --short --branch` before editing because another Agent may have unfinished work.
5. Claim the ticket by changing its status to `[~]` in the canonical roadmap and syncing the mirror before implementation.

`~/.claude/plans/...` is archival input only. It is machine-local and must never be treated as the current handoff source.

---

## How to use this file (agent protocol)

1. **Read the section `## RESUME HERE`** — it names the next ticket and the last-touched file.
2. **Open the matching `### Ticket 2c.X.Y` block** — it has a Goal, exact files to touch, the patterns to reuse, and a Done-when checklist.
3. **Do the work in a single focused pass.** Don't merge tickets — each ticket is sized for ~1 hour / one chat session.
4. **Update the ticket status checkbox**: `[ ]` → `[~]` (started) → `[x]` (done). Append a one-line note under the ticket: `> 2026-MM-DD <agent-name>: <what you did, what to verify next>`.
5. **Move the `## RESUME HERE` anchor to the next ticket.**
6. **Sync the product mirror** with `python3 scripts/game/sync_sunday_invest_moon_roadmap.py --sync`, verify with the same command without `--sync`, then commit both repos as applicable.
7. If you can't finish a ticket: leave it `[~]`, write a `> blocker:` note, and move RESUME HERE to the next *independent* ticket. Don't half-finish silently.

**Status legend** in this file:
- `[ ]` not started
- `[~]` in progress / blocked (read the note below the ticket)
- `[x]` done + verified

**Iron Law (non-negotiable for every ticket)**:
1. No production code without a failing test first.
2. No bug fix without root cause documented.
3. No API keys, secrets, or order-execution in the client. Period.
4. `raw/` is immutable. `CLAUDE.md`/`AGENTS.md` need explicit approval to edit.

---

## RESUME HERE

**Next ticket**: **Ticket 15.9 — Readability pass on existing finance panels**
**Last touched**: `src/feeds/instrumentFeed.ts`; `backend/routers/market.py`; read-only screener/funds contract docs; 591 tests green (session 2026-06-14)
**Branch policy**: commit straight to `main` of both repos (A-Wiki + <product-repo>) — no PR, no worktree (per `A-Wiki/CLAUDE.md` rule #6).

---

## Context (what's already shipped)

Phase 2a/2b complete: 5 baked house rooms, top-down farm, น้องซันเดย์ with 8-dir walk + idle/run/sit/lie/eat/cry, **three real chihuahuas (red/black/cream) with PixelLab walk+sit+wag in all 8 directions**, parchment HUD, family-photo modal, click-to-move free vector inside rooms via `roomFreeMovement.ts`. Build is **green** (typecheck clean, 64 vitest tests, no console errors, React Doctor ≈100).

**Confirmed scope decisions** (user picked these in plan mode, locked):
| Decision | Choice |
|---|---|
| Bot trading | **MOCK first** + adapter seam for a future backend service (no live orders in client) |
| Open-world farm | **Bigger grid + camera scrolls with player** (~30×20 cells, single FarmScene) — not chunk streaming |
| Title screen | **1 button "เริ่มเกม"** (no Continue/Settings yet) |
| Click-to-move | **A* pathfinding** around obstacles |

---

## Theme palette (locked — every UI ticket pulls from here)

Sampled from the user-supplied splash art `Gemini_Generated_Image_251ghe251ghe251g.png`. New tokens are added to `src/styles/tokens.css` **in addition to** the existing parchment vars (parchment stays for FamilyPanel/PetBioPanel text-heavy modals; lawn/wood is for chips, buttons, title).

```css
:root {
  --sim-lawn:       #86c34a; /* primary green */
  --sim-lawn-dark:  #5b8a2f;
  --sim-wood:       #8b5a2b; /* sign body */
  --sim-wood-dark:  #3a2010; /* sign outline */
  --sim-cream:      #fff4da; /* highlight text */
  --sim-cream-2:    #f4e9c8;
  --sim-red:        #c92828; /* "AI Market Ventures" red */
  --sim-sky:        #a3d4ee; /* subtle UI backdrop */
}
```

---

## Phase 2c.1 — Rename + Theme + Title + Logo + Responsive shell

Foundation. Every later phase depends on this.

### Ticket 2c.1.1 — Ingest title splash + logo images  · `[x]`
**Goal**: Title art + small logo live in the product repo + archived in A-Wiki references.
**Source files** (user-provided, in `~/Downloads/`):
- `Gemini_Generated_Image_251ghe251ghe251g.png` — splash background (lawn + sign + characters)
- `Gemini_Generated_Image_cy1pv5cy1pv5cy1p.png` — sign logo, transparent
**Destinations**:
- Product: `<product-repo>/pixel-wealth-quest/public/assets/title/sunday-invest-moon-splash-v001.jpg` (downscaled 1280×720 + JPEG q85 = 208 KB)
- Product: `<product-repo>/pixel-wealth-quest/public/assets/title/sunday-invest-moon-logo-v001.png` (88 KB, transparent)
- Archive (A-Wiki): `game-assets/references/sunday-invest-moon/title/{splash,logo}-v001.png` (full-res originals 6.1 MB + 88 KB)
**Done when**:
- [x] Files exist at the destinations
- [x] `du -h` both files → splash 208 KB (JPG), logo 88 KB — both well under 1 MB
- [x] Note: splash is `.jpg` (no transparency needed); Ticket 2c.1.3 preload path uses `.jpg`
> 2026-06-04 claude-opus-4-7: ingested via Bash cp + PIL downscale (NEAREST to preserve pixel art). Original 2730×1536 PNG kept as A-Wiki ref. **RESUME** → 2c.1.2.

---

### Ticket 2c.1.2 — Rename "Pixel Wealth Quest" → "Sunday Invest Moon" (user-facing only)  · `[x]`
**Goal**: Every label the user sees says "Sunday Invest Moon". The directory slug `pixel-wealth-quest/` does NOT change (would break iframe URL + dozens of import paths).
**Files to touch** (use `grep -rln "Pixel Wealth Quest" <product-repo>/ A-Wiki/wiki/` to verify the full set):
- `<product-repo>/prototype/src/data.jsx` — nav entry `pwq: { th, en }`
- `<product-repo>/prototype/src/app.jsx` — `PwqFrame` title
- `<product-repo>/pixel-wealth-quest/index.html` — `<title>`
- `<product-repo>/pixel-wealth-quest/src/App.tsx` — visible headings
- `<product-repo>/pixel-wealth-quest/HANDOFF.md` — update game name section
- `A-Wiki/wiki/synthesis/pixel-wealth-quest-gdd.md` — add "Renamed to **Sunday Invest Moon** in Phase 2c.1" note
- New copy: `<product-repo>/pixel-wealth-quest/ROADMAP.md` ← copy this file
- New copy: `A-Wiki/wiki/synthesis/sunday-invest-moon-roadmap.md` ← copy this file
**Tagline**: "AI Market Ventures" · **Footer**: "© 2006 Sunday Estate Co.,Ltd"
**Done when**:
- [x] No user-visible label still says "Pixel Wealth Quest"
- [x] `grep -rln "Pixel Wealth Quest"` only matches internal comments / legacy ADR / historical headers
- [x] `npm --prefix <product-repo>/pixel-wealth-quest run typecheck` green
> 2026-06-05 codex-poppy-javis: Renamed nav, iframe, and document-title labels; added tagline/footer plus `branding.test.ts`. Verified 66 tests, typecheck/build, prototype JSX parse, React Doctor 100/100. Browser localhost QA was blocked by Browser URL policy. **RESUME** → 2c.1.3.

---

### Ticket 2c.1.3 — TitleScene + "เริ่มเกม" button  · `[x]`
**Goal**: Game opens to a title screen. One button starts the room.
**New file**: `<product-repo>/pixel-wealth-quest/src/phaser/scenes/TitleScene.ts`
- `preload`: `this.load.image('sim_title_splash', 'assets/title/sunday-invest-moon-splash-v001.jpg')`
- `create`: full-bleed image (cover), then a DOM/HTML button "เริ่มเกม" centred-bottom. Click → `scene.start('Room')`.
**Edit**: `<product-repo>/pixel-wealth-quest/src/phaser/PhaserGame.ts` — scene array becomes `[BootScene, PreloadScene, TitleScene, RoomScene, FarmScene]`. `PreloadScene.create()` → `scene.start('Title')` (was `'Room'`).
**Reuse**: existing `Phaser.Scale.RESIZE` config (no change). Style the button using `var(--sim-wood)` for bg, `var(--sim-cream)` text, `var(--sim-wood-dark)` border.
**Done when**:
- [x] Opening the iframe shows splash + button
- [x] Click/tap button → Room renders
- [x] No console errors
- [x] Runtime screenshots captured + added to HANDOFF.md
> 2026-06-05 codex-poppy-javis: Playwright verified splash/button, title→Room, clean console, and recorded screenshot evidence in HANDOFF.md. **RESUME** → 2c.1.4.

---

### Ticket 2c.1.4 — Top-left HUD logo chip  · `[x]`
**Goal**: While playing, the small wooden sign sits top-left of the HUD.
**Edit**: `<product-repo>/pixel-wealth-quest/src/components/HudOverlay.tsx` — add `<img className="sim-hud-logo" src="assets/title/sunday-invest-moon-logo-v001.png" alt="Sunday Invest Moon" />`
**Edit**: `<product-repo>/pixel-wealth-quest/src/styles/hud.css` — `.sim-hud-logo { position: absolute; top: 12px; left: 12px; width: clamp(80px, 12vw, 140px); image-rendering: pixelated; z-index: 10; pointer-events: none; }`
**Done when**:
- [x] Logo visible top-left in Room + Farm
- [x] Logo does not block click zones (`pointer-events: none`)
- [x] Logo scales sanely on mobile widths
> 2026-06-05 codex-poppy-javis: Added shared HUD logo + collision-free chip offset; regression test verifies asset/alt and CSS verifies pointer-events/clamp. Verified 70 tests, typecheck/build, React Doctor 100. **RESUME** → 2c.1.5.

---

### Ticket 2c.1.5 — Theme tokens (add `--sim-*` palette)  · `[x]`
**Goal**: New lawn-green/wood-brown palette available app-wide as CSS vars, without removing existing parchment tokens.
**Edit**: `<product-repo>/pixel-wealth-quest/src/styles/tokens.css` — append the `--sim-*` block from the "Theme palette (locked)" section of this file.
**Edit**: `<product-repo>/pixel-wealth-quest/src/styles/hud.css` — change `.pwq-chip` bg to `var(--sim-wood)`, text to `var(--sim-cream)`, border to `var(--sim-wood-dark)`. **Keep** `.pwq-family`, `.pwq-panel` on parchment (text readability).
**Done when**:
- [x] HUD chip reads warm wood-brown, not parchment
- [x] FamilyPanel still parchment-style
- [x] No CSS lint warnings
> 2026-06-05 codex-poppy-javis: Added locked `--sim-*` palette and moved only `.pwq-chip` to wood/cream while preserving parchment panels. Verified CSS contracts, 70 tests, typecheck/build, React Doctor 100. **RESUME** → 2c.1.6.

---

### Ticket 2c.1.6 — Responsive shell (mobile breakpoints)  · `[x]`
**Goal**: PWQ usable on iPhone 12 (390×844) and iPad (768×1024).
**Pattern to copy**: `<product-repo>/game/src/styles/hud.css` (Tide & Tally), lines ~144–750 (`@media (max-width: 920px)`, `@media (orientation: portrait)` blocks). Adapt to PWQ class names (`.pwq-*`, `.sim-*`).
**Edit**: `<product-repo>/pixel-wealth-quest/index.html` — confirm `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` present.
**Add**: `src/logic/platform.ts` (test-first) — `isTouchDevice()` returning `'ontouchstart' in window || navigator.maxTouchPoints > 0`. Used in Phase 2c.2 to swap on-screen control hints. Tests in `src/logic/platform.test.ts`.
**Done when**:
- [x] Runtime resize 390×844 → no horizontal scroll, no overlap
- [x] Runtime resize 768×1024 → same
- [x] `npm test` green (platform.test.ts passes)
> 2026-06-05 codex-poppy-javis: Playwright verified title, Room/inventory, and Farm/IoT layouts at 390×844 and 768×1024 without horizontal overflow or overlap. **RESUME** → 2c.2.1.

---

## Phase 2c.2 — Click/tap-to-move with A* pathfinding

### Ticket 2c.2.1 — `src/logic/pathfind.ts` + test  · `[x]`
**Goal**: Pure A* implementation, no Phaser deps, deterministic.
**New file**: `src/logic/pathfind.ts` — `aStar(start: Cell, goal: Cell, grid: RoomGrid): Cell[] | null`
- 8-neighbour expansion (diag costs √2)
- Manhattan heuristic for axis-aligned, Octile for diagonal
- Returns `null` if unreachable
- Prevents corner-cut through diagonal blocked cells
**Reuse**: `Cell`, `RoomGrid` types from `src/types/domain.ts` + `src/logic/movement.ts`; `nextCell` for neighbour iteration.
**New file**: `src/logic/pathfind.test.ts` — cases: open grid, blocked corridor, unreachable, corner-cut guard, 1-cell path.
**Done when**:
- [x] All test cases pass
- [x] Path length matches expected (octile distance)
> 2026-06-05 codex-poppy-javis: Added deterministic pure A* with octile heuristic and diagonal corner-cut guards. Verified 5 focused cases, 78 total tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.2.2.

---

### Ticket 2c.2.2 — `screenToCell` inverse projection  · `[x]`
**Goal**: A pointer event in world coords → a grid cell.
**Edit**: `src/logic/grid.ts` — add `screenToCell(p: {x:number;y:number}, origin: GridOrigin): Cell` for both iso (rooms) and top-down (farm) projections. Write the inverse of the existing `cellToScreenIso` / `cellToScreenTopDown`.
**Tests**: `grid.test.ts` — round-trip `cellToScreen(c) → screenToCell(p) === c` for both projections.
**Done when**:
- [x] Round-trip tests pass for all 4 corners + centre
> 2026-06-05 codex-poppy-javis: Added discriminated `GridOrigin` + `screenToCell()` inverse for iso/top-down projections. Verified 5-point round trips per projection, 80 total tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.2.3.

---

### Ticket 2c.2.3 — `playerController` (path-driven walk)  · `[x]`
**Goal**: Player walks a precomputed path one cell at a time, with correct facing.
**New file**: `src/phaser/playerController.ts` — owns `targetPath: Cell[] | null`. Each scene update: if path non-empty, tween to `path[0]`, compute facing via `dir8FromVector`, play `playerMoveAnimKey('walk', dir)`. On arrival: shift path. On empty: idle.
**Reuse**: `dir8FromVector` (playerFrames.ts), `cellToScreenIso` (grid.ts), `screenDepth` (grid.ts), tween-walk pattern from `objects/PetPack.step()`.
**Edit**: `RoomScene.ts` + `FarmScene.ts` — register `this.input.on('pointerdown', e => { const cell = screenToCell({x: e.worldX, y: e.worldY}, origin); const path = aStar(this.player.cell, cell, this.grid); this.playerController.setPath(path); })`.
**Cancel logic**: any keyboard input → `setPath(null)`; reuse existing `movementVector()` for keyboard freeform.
**Done when**:
- [x] Click an empty cell → player walks there
- [x] Click the sofa → path-finds around it to the nearest free cell
- [x] Keyboard input mid-path cancels and takes over
- [x] Mobile tap = same behaviour (no separate code path)
> 2026-06-05 codex-poppy-javis: Calibrated the living sofa footprint against the 16:10 runtime frame, moved the initial spawn from blocked `3,3` to free `2,3`, and added regressions protecting obstacle/spawn/door cells. Playwright proved a sofa-centre click requests blocked `3,3`, builds a path, and stops at nearest free `3,2`. Verified 156 tests, typecheck/build, React Doctor 100, and console 0 errors/warnings. **RESUME** → 2c.3.3.

---

## Phase 2c.3 — Player action menu (click น้องซันเดย์)

### Ticket 2c.3.1 — Player click zone + modal state  · `[x]`
**Goal**: Tapping the player opens an action strip.
**Edit**: `RoomScene.ts` + `FarmScene.ts` — add a Phaser Zone on the player sprite (size = sprite bounds + 8px padding), `setInteractive`, on `pointerdown` → `pwqStore.setOpenModal('player-actions')`.
**Edit**: `pwqStore.ts` — extend modal union with `'player-actions'`.
**Done when**:
- [x] Tap player → store `openModal === 'player-actions'`
- [x] No conflict with tap-to-move (zone consumes the event)
> 2026-06-05 codex-poppy-javis: Added reusable player hit zone that follows the sprite, opens `player-actions`, and stops pointer propagation before scene tap-to-move. Verified 87 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.3.2.

---

### Ticket 2c.3.2 — `PlayerActionStrip.tsx` UI  · `[x]`
**Goal**: 5 chips: นั่ง / นอน / ร้องไห้ / วิ่งเล่น / กิน.
**New file**: `src/components/PlayerActionStrip.tsx` — render when `openModal === 'player-actions'`. Each chip → `gameBus.emit('player-action', action)`; closing → `setOpenModal(null)`.
**Edit**: `HudOverlay.tsx` — render the strip in the modal slot.
**Reuse**: `pwq-chip` styling already in `hud.css`, gameBus already wired.
**Done when**:
- [x] Strip appears below player when modal open
- [x] Buttons fire actions
> 2026-06-05 codex-poppy-javis: Playwright visually verified the action strip beside/below the player and exercised the sit action without tap-to-move click-through. **RESUME** → 2c.3.3.

---

### Ticket 2c.3.3 — Action playback with hold/loop rules  · `[x]`
**Goal**: Each action plays per the user's exact frame rules.
**Edit**: `playerController.ts` — handle `gameBus.on('player-action', action)`:
- `sit` → play `sit_south_000..006`, on `animationcomplete` → `sprite.setTexture(playerAnimFrameKey('sit', 6))`. Hold until next walk or action.
- `lie` → same pattern, hold on `lie_south_006`.
- `cry` → play `cry_south_000..006` with `repeat: -1` (loop). Need to change `cry.repeat` from `0` → `-1` in `playerAnims.ts` (auto-generated). Either edit the generator's `REPEAT` map in `scripts/game/normalize_pwq_anims.py` and re-run, or override locally in `playerController` (`scene.anims.create` with same key but `repeat: -1`).
- `run` → play 8-dir run anim + wander randomly within walkArea for ~4s.
- `eat` → play `eat_south_000..006` once, return to idle.
**Cancel**: any tap-to-move click or keyboard input → stop animation + return to walk.
**Done when**:
- [x] นั่ง holds on frame 6 visibly
- [x] นอน holds on frame 6
- [x] ร้องไห้ loops forever until interrupted
- [x] วิ่งเล่น picks random cell and runs there
- [x] กิน plays once and returns to idle
> 2026-06-05 codex-poppy-javis: Extended the source-of-truth normalizer so run registers 8 directional keys: front uses real run art; missing directions reuse matching locomotion frames at 12 FPS. PlayerController now selects run by facing. Playwright verified `lie_006` hold plus live `run_back_left`/`run_front_right`; console stayed clean. Verified A-Wiki 253 tests, product 157 tests/typecheck/build, and React Doctor 100. **RESUME** → 2d.1.

---

## Phase 2c.4 — Pet click → bio popup

### Ticket 2c.4.1 — `pets.bios.ts` data table  · `[x]`
**New file**: `src/data/pets.bios.ts` — exported `PET_BIOS: Record<PetDogId, PetBio>`. Bio strings per the user's spec (verbatim Thai):

```ts
red (สุขใจ):
  portrait: 'assets/character/pets/individual/red/dog_red_front_001.png'
  sex: 'เมีย', born: 'ธันวาคม 2561'
  personality: 'หวงเจ้าของ เห่าเก่ง เห่าได้ทั้งวัน ดุร้ายเมื่อเจอคนแปลกหน้า'
  abilities: 'สั่งตายได้ ขอมือได้ หมุนตัวได้ หยิบของมาให้ได้'
  history: 'เป็นแม่ของ มั่งมี และ ศรีสุข ผ่าคลอดเพราะไปซื้อกินจนท้องไม่มีพ่อ ลูกเลยตัวใหญ่กว่าตัวเอง'

black (ศรีสุข):
  portrait: 'assets/character/pets/individual/black/dog_black_front_001.png'
  sex: 'ผู้', born: 'กุมภาพันธ์ 2564'
  personality: 'ขี้กลัว ปล่อยออกนอกบ้านก็หนีเข้าบ้าน ไม่เคยโดนหมาที่ไหนกัด เพราะซ่อนเก่ง ชอบกระเด้าขา เห่าตามแม่'
  history: 'เป็นลูกของ สุขใจ เป็นพี่น้องกับ มั่งมี'

cream (มั่งมี):
  portrait: 'assets/character/pets/individual/cream/dog_cream_front_000.png'
  sex: 'ผู้', born: 'กุมภาพันธ์ 2564'
  personality: 'ขี้เก่าเหมือนแม่ ใจกล้ามาก ไล่กัดหมาใหญ่ จนตัวเองโดนกัด'
  history: 'เป็นลูกของ สุขใจ เป็นพี่น้องกับ ศรีสุข'
  status: 'rip', statusNote: 'ปัจจุบัน: ตายแล้ว 🙏'
```

**Done when**:
- [x] File exports the typed record
- [x] All three portrait paths exist on disk
> 2026-06-05 codex-poppy-javis: Added verbatim typed bios for red/black/cream dogs with RIP metadata for มั่งมี; verified all portrait files, 95 tests, typecheck/build. **RESUME** → 2c.4.2.

---

### Ticket 2c.4.2 — `PetBioPanel.tsx`  · `[x]`
**Goal**: Parchment modal like FamilyPanel; shows portrait + bio. `cream` gets a soft RIP treatment.
**New file**: `src/components/PetBioPanel.tsx` — mirror `FamilyPanel` (HudOverlay.tsx lines ~167–184). Title = ชื่อหมา, large portrait at top, meta grid below, RIP badge if `status === 'rip'` (small black/grey ribbon, not heavy).
**Edit**: `HudOverlay.tsx` — render when `openModal` matches `pet:red|pet:black|pet:cream`.
**Edit**: `pwqStore.ts` modal union — add `'pet:red'|'pet:black'|'pet:cream'`.
**Done when**:
- [x] Each dog opens its own panel
- [x] Cream shows RIP badge
- [x] Close button works
> 2026-06-05 codex-poppy-javis: Added responsive parchment pet bio panel, typed pet modal routing, soft RIP badge, and close flow. Verified 98 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.4.3.

---

### Ticket 2c.4.3 — Pet click zones in `PetPack`  · `[x]`
**Edit**: `src/phaser/objects/PetPack.ts` — in `PetActor` setup, `sprite.setInteractive()` and `on('pointerdown', () => gameBus.emit('pet-clicked', dog.id))`.
**Edit**: gameBus listener in HudOverlay or App level → `pwqStore.setOpenModal(\`pet:\${id}\`)`.
**Caveat**: depth + tweens — the sprite is moving; verify the hit-area follows. Use `useHandCursor: true` on desktop only.
**Done when**:
- [x] Click each of the three dogs in the room → correct bio modal
- [x] Click works in farm scene too
> 2026-06-05 codex-poppy-javis: Made shared Room/Farm PetPack sprites interactive, consumed pointer propagation, added typed `pet-clicked` bridge + explicit HUD cleanup, and verified modal routing. Passed 100 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.5.1.

---

## Phase 2c.5 — Bug fixes

### Ticket 2c.5.1 — Player walk-west uses south-west art  · `[x]`
**Goal**: When walking horizontally left, use `walk_south-west_000..008.png` instead of `walk_west_*` (user said the SW frames read better at the game's 3/4 angle).
**Approach A (recommended, reversible)**: Edit `scripts/game/normalize_pwq_anims.py` — add a constant `WALK_LEFT_USES_SW = True`; in the walk emit logic, when `dir8 === 'left'`, point its frames at the `south-west` slice instead of `west`. Re-run normalize.
**Approach B (hand override)**: In `playerAnims.ts` (auto-generated), replace the `walk.left.frames` array with the `south-west` paths. Add a comment so the next normalize doesn't clobber it (or set the flag in A).
**Done when**:
- [x] Player walking left visibly uses SW frames
- [x] No regression on other directions
- [x] `playerAnims.test.ts` green
> 2026-06-05 codex-poppy-javis: Playwright runtime evidence confirmed west movement plays `pwq_player_walk_left` on the expected SW-backed texture key. **RESUME** → 2c.5.2.

---

### Ticket 2c.5.2 — Dogs wander truly omnidirectional (free vector)  · `[x]`
**Goal**: Today dogs step cell-by-cell, which reads as snapped/diagonal. Switch to free-vector wander while keeping the directional walk anim correct.
**Edit**: `src/logic/pet.ts` (+test) — replace `pickWander(): StepDir|null` with `pickWanderTarget(from, walkArea, rng): {dx:number, dy:number, distance:number}` returning a vector offset (1.5–3 tiles, any angle). Test new shape deterministically.
**Edit**: `src/phaser/objects/PetPack.ts` — replace cell-step tween with a free tween toward the vector target. Recompute `facing = dir8FromVector(velocity)` each tick → swap walk anim via `petMoveAnimKey(id, 'walk', facing)`. Respect grid bounds.
**Done when**:
- [x] Dogs walk smooth arcs, not diagonal jumps
- [x] Facing matches direction of motion in all 8 sectors
- [x] Bounds enforced (no walking through walls)
- [x] `pet.test.ts` updated + green
> 2026-06-05 codex-poppy-javis: Playwright before/after runtime samples confirmed live free-direction position, texture, and facing changes with smooth tweened wander. **RESUME** → 2c.6.1.

---

## Phase 2c.6 — Equal-size rooms

### Ticket 2c.6.1 — Normalize room viewport  · `[x]`
**Goal**: น้องซันเดย์'s sprite size doesn't visibly jump between rooms.
**Edit**: `RoomScene.ts` — backdrop scaling. Today: 98% × 90% of canvas. Add `ROOM_VIEWPORT_ASPECT = 16/10`; letterbox each backdrop to that aspect. Adjust grid origin per room so the playable floor area lines up across rooms.
**Done when**:
- [x] Walk room → room, player sprite size unchanged
- [x] No black bars wider than 2% of canvas in any room
> 2026-06-05 codex-poppy-javis: Playwright visually checked living↔office transitions plus desktop/mobile room layouts; player scale stayed consistent. **RESUME** → 2c.7.1.

---

## Phase 2c.7 — Inventory + Shop

### Ticket 2c.7.1 — `items.ts` registry  · `[x]`
**New file**: `src/data/items.ts` — `Item = { id, nameTh, category: 'seed'|'iot'|'food-human'|'food-dog', priceCoins, iconPath, descTh }`.
Initial roster:
- Seeds: carrot, tomato, basil, sunflower
- IoT (7): soil-moisture-watering, pm25-sensor, light-switch-sensor, harvest-robot, scale, water-drone, fertilizer-drone
- Human food: ข้าว, ลาเต้, ขนม
- Dog food: เม็ดอาหารหมา, ขนมหมา
**Done when**:
- [x] File compiles
- [x] All `iconPath` strings reference paths that will exist after 2c.7.2
> 2026-06-05 codex-poppy-javis: Added typed 16-item registry, inferred ItemId/lookup map, positive prices, Thai descriptions, and versioned public icon paths. Verified registry contracts, 117 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.7.2.

---

### Ticket 2c.7.2 — Generate IoT + item icons (PixelLab)  · `[x]`
**Goal**: 64×64 transparent PNGs in parchment-pixel style for every item.
**Tool**: extend `scripts/game/pixellab_generate_image.py` with `--icon` mode (passes `image_size: 64×64`, `pixelation_style: 'medium'`). Reference real-world devices in the prompt so it nails the IoT look:
- soil-moisture-watering: "pixel art icon of a tiny garden sprinkler with a soil moisture probe, top-down view, transparent background"
- pm25-sensor: "pixel art icon of a small white air quality sensor with a digital display"
- harvest-robot: "pixel art icon of a small wheeled harvest robot with a basket"
- ... (similar concrete prompts for the rest)
**Output**: `public/assets/items/iot/<slug>-v001.png`, `public/assets/items/seeds/<slug>-v001.png`, etc.
**Budget guard**: cap at $1.50 for this ticket. Echo balance via `python3 scripts/game/pixellab_gen.py balance` before/after.
**Done when**:
- [x] All `iconPath`s in `items.ts` resolve to files
- [x] Icons visible in browser at 1:1
> 2026-06-05 codex-poppy-javis: Added tested `--icon` mode and generated/visually checked all 16 transparent 64x64 item icons. Current PixelLab OpenAPI rejects roadmap's obsolete `pixelation_style`; wrapper uses supported `detail: "medium detail"` instead. Verified all paths, A-Wiki 252 tests, product 117 tests/typecheck/build. Cost: $0.11185 of $1.50 cap. **RESUME** → 2c.7.3.

---

### Ticket 2c.7.3 — Inventory state + persistence  · `[x]`
**Edit**: `pwqStore.ts` — `inventory: Record<ItemId, number>`, `addItem(id, qty)`, `removeItem(id, qty)`. Persist to `localStorage` under key `sim:inventory`.
**Tests**: `pwqStore.test.ts` for add/remove edge cases.
**Done when**:
- [x] Reload preserves inventory
- [x] removeItem clamps at 0
> 2026-06-05 codex-poppy-javis: Added complete typed inventory, defensive `sim:inventory` loading/persistence, and positive-whole add/remove actions with zero clamp. Verified reload + edge cases, 119 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.7.4.

---

### Ticket 2c.7.4 — `BackpackButton` + `InventoryPanel`  · `[x]`
**New files**: `src/components/BackpackButton.tsx` (fixed bottom-right), `src/components/InventoryPanel.tsx` (parchment grid, tabs by category, qty badges).
**Edit**: `HudOverlay.tsx` — render button; render panel when `openModal === 'inventory'`.
**Icon**: school-backpack 64×64 from PixelLab or hand-drawn.
**Done when**:
- [x] Button bottom-right, doesn't block movement
- [x] Tap → panel opens; tabs filter; counts match store
> 2026-06-05 codex-poppy-javis: Added fixed pointer-isolated backpack button, generated/checked its 64x64 icon, and added responsive parchment inventory panel with category tabs + live quantity badges. Verified integration flow, 122 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.7.5.

---

### Ticket 2c.7.5 — Office-computer hotspot + ShopPanel  · `[x]`
**Edit**: `RoomScene.ts` — in the office room, add a hotspot on the computer; `opens: 'shop'`.
**New file**: `src/components/ShopPanel.tsx` — category tabs, grid of items with price + buy button. On buy: check coins → decrement → addItem → toast.
**Edit**: `pwqStore.ts` modal union — add `'shop'`. Add `buy(itemId)` action that returns `{ok:boolean, reason?:string}` for testability.
**Tests**: `shop.test.ts` for buy logic (insufficient coins, valid buy).
**Done when**:
- [x] Click office computer → shop opens
- [x] Buy decreases coins + increases inventory
- [x] Insufficient coins → toast, no state change
> 2026-06-05 codex-poppy-javis: Added office computer shop hotspot, atomic tested buy action, responsive category shop grid, balance display, and success/insufficient toast. Verified 127 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.8.1.

---

## Phase 2c.8 — Farm expansion + Harvest-Moon plant/water + IoT slots

### Ticket 2c.8.1 — Bigger farm grid + camera follow  · `[x]`
**Edit**: `FarmScene.ts` — grid 30×20 (from 10×8). Camera: `this.cameras.main.startFollow(this.player, true, 0.1, 0.1)`, set `world bounds = (0, 0, worldPxW, worldPxH)`. Verify minimap not needed yet.
**Edit**: `farm.seed.ts` — split plots into biome zones (planting field centre, IoT slot row south, paths, sea horizon eye-candy).
**Done when**:
- [x] Player exits house → wide farm, camera scrolls
- [x] No edge-of-world artifacts
- [x] Performance ≥ 55 FPS on mid laptop
> 2026-06-05 codex-poppy-javis: Playwright verified wide-farm entry, bounded camera scroll, clean world edges, and Phaser runtime FPS at 60. **RESUME** → 2c.8.2.

---

### Ticket 2c.8.2 — Harvest-Moon-style plot lifecycle  · `[x]`
**Edit**: `src/data/farm.seed.ts` — `FarmPlot.stage` enum becomes `untilled|tilled|seeded|growing|wet|ready|withered`.
**New file**: `src/logic/farm.ts` (+test) — pure stage-transition functions: `till(plot)`, `seed(plot, seedId)`, `water(plot)`, `harvest(plot)`. Wither rule: water level 0 for >N ticks → withered.
**New file**: `src/phaser/objects/ToolWheel.ts` — show when player adjacent to a plot; chips: hoe / seed / water / scythe. Tap → calls farm logic.
**Edit**: `FarmScene.ts` — render plot by stage (reuse existing carrot art; add tilled/wet/withered placeholder tints).
**Done when**:
- [x] Walk to plot → wheel appears
- [x] Hoe → tilled; seed (from inventory) → seeded; water → wet; wait → growing → ready; harvest → coins + remove inventory seed
- [x] `farm.test.ts` all transitions covered
> 2026-06-05 codex-poppy-javis: Playwright visibly verified adjacent ToolWheel and completed hoe→seed→water→ready→harvest, raising coins from 8 to 32. **RESUME** → 2c.8.3.

---

### Ticket 2c.8.3 — IoT slot system  · `[x]`
**Goal**: Slots scattered through the farm where the user drops a purchased IoT device. Placement gates Phase 2c.9.
**New file**: `src/logic/iotSlots.ts` (+test) — `IoTSlot = { id, cell, occupiedBy: ItemId|null }`; functions `placeDevice(slot, item)`, `removeDevice(slot)`.
**Edit**: `pwqStore.ts` — `iotSlots: IoTSlot[]`, `placeDevice`, persisted to localStorage.
**Edit**: `FarmScene.ts` — render slot markers (small pixel base plate); on click → open `IoTPlacePanel` with the user's IoT inventory; on confirm → call store action; render device sprite.
**Done when**:
- [x] Slots visible
- [x] Click empty slot + own a device → place
- [x] Placed device shows + reduces inventory by 1
> 2026-06-05 codex-poppy-javis: Playwright verified visible slots, placed `light-switch-sensor` in `iot-3`, inventory decrement, localStorage persistence, and configured-device mini sparkline. **RESUME** → 2c.9.1.

---

## Phase 2c.9 — Bot trading (MOCK + seam)

### Ticket 2c.9.1 — `tradingStrategies.ts`  · `[x]`
**New file**: `src/data/tradingStrategies.ts` — strategies referenced from popular retail-bot platforms (Grid, DCA, Momentum/RSI, Mean-Reversion/Bollinger, Scalping, Pairs-Arb). Each: `{ id, nameTh, descTh, defaultParams, riskNote }`. No exchange names, no API keys.
**Done when**: file compiles; 6 strategies listed.
> 2026-06-05 codex-poppy-javis: Added exchange-neutral typed registry for Grid, DCA, Momentum/RSI, Mean-Reversion/Bollinger, Scalping, and Pairs-Arb with defaults + explicit Thai risk notes. Verified registry contracts, 141 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.9.2.

---

### Ticket 2c.9.2 — `botSim.ts` (deterministic mock P&L)  · `[x]`
**New file**: `src/logic/botSim.ts` (+test) — `simulate(strategy, capital, windowSec, rng) → { equityCurve: number[], trades: Trade[] }`. Pure, tested. No live network.
**Done when**: snapshot tests stable; sane equity ranges per strategy.
> 2026-06-05 codex-poppy-javis: Added pure injected-RNG simulator with per-strategy profiles, positive equity clamp, deterministic trade records, replay test, sane-range test, and stable cross-strategy summary snapshot. Verified 144 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.9.3.

---

### Ticket 2c.9.3 — `tradingBotFeed` adapter seam  · `[x]`
**New file**: `src/feeds/tradingBotFeed.ts` — `interface BotFeed { getStatus(deviceId): Promise<BotStatus>; setStrategy(deviceId, cfg): Promise<void> }`. Two impls:
- `MockBotFeed` (uses `botSim`)
- `RemoteBotFeed` (throws "not implemented"; doc-comment describes the future backend contract: endpoint, auth-via-server, no client secrets)
**Done when**: app uses `MockBotFeed` by default; swapping to remote later = 1-line change.
> 2026-06-05 codex-poppy-javis: Added typed BotFeed seam, deterministic in-memory MockBotFeed as the one-line default, and explicit RemoteBotFeed not-implemented stub with server-session/no-client-secret contract. Verified 146 tests, typecheck/build, and React Doctor 100. **RESUME** → 2c.9.4.

---

### Ticket 2c.9.4 — `BotConfigPanel` + `BotStatusOverlay`  · `[x]`
**New files**: `BotConfigPanel.tsx` (pick strategy + params), `BotStatusOverlay.tsx` (mini equity sparkline above a placed IoT device).
**Edit**: `pwqStore.ts` — `bots: Record<DeviceId, BotState>`, actions.
**Edit**: `FarmScene.ts` — click placed device → open BotConfigPanel.
**Done when**:
- [x] Pick strategy on a placed device → equity curve animates
- [x] No real network calls
- [x] No secret-looking env vars reachable from `window`
> 2026-06-05 codex-poppy-javis: Added placed-device bot config routing, mock-feed-backed bot state/actions, strategy/default-param picker, animated React SVG sparkline, and Phaser mini sparkline above configured devices. Verified 149 tests, typecheck/build, React Doctor 100, no real network path, and client secret-env scan clean (only the safe `DEV` flag). **RESUME** → 2c.9.5.

---

### Ticket 2c.9.5 — Iron Law ADR  · `[x]`
**New file**: `docs/protocols/bot-trading-iron-law.md` — document the seam, the future backend contract (auth-via-server, request signing, idempotency), and what each agent must NOT do in the client. Cross-link from `A-Wiki/CLAUDE.md` "Iron Laws" section.
**Done when**: ADR exists; CLAUDE.md links to it.
> 2026-06-05 codex-poppy-javis: Added the mock/visualization-only client Iron Law, future server-session/signing/idempotency/risk-control contract, and a `CLAUDE.md` cross-link. Verified A-Wiki 252 tests, product 149 tests/typecheck/build, React Doctor 100, cross-platform, and generated-index checks. Privacy scan still reports 12 pre-existing/out-of-scope codename findings in four files. **RESUME** → Phase 2c full-game runtime smoke.

---

## Verification (full game, after every phase)

### Verification checkpoint — Phase 2c full-game smoke  · `[x]`

- [x] Product tests (157), typecheck, build, and React Doctor 100
- [x] A-Wiki tests (253), cross-platform check, generated-index check, and handoff mirror integrity
- [x] Client secret-env scan clean; only safe `import.meta.env.DEV` exposure
- [x] Run the full desktop end-to-end smoke below and capture runtime/console evidence
- [x] Repeat critical layout checks at 390×844 and 768×1024
- [x] Record current PixelLab balance: `$3.57846708981859`

> 2026-06-05 codex-poppy-javis: Full Playwright smoke passed with 0 console errors/warnings, 60 Phaser FPS, mobile/tablet layout evidence, and external hosts limited to Google Fonts. Test-first runtime fixes removed the zero-coin economy deadlock, backdrop-modal click-through into Phaser, and stale PlayerController action listener. **RESUME** → 2c.2.3 furniture collision calibration.

Standard checks before marking RESUME HERE to the next phase:

```bash
# 0. Handoff integrity (from A-Wiki)
python3 scripts/game/sync_sunday_invest_moon_roadmap.py

# 1. Static
npm --prefix <product-repo>/pixel-wealth-quest run typecheck
npm --prefix <product-repo>/pixel-wealth-quest test
npx react-doctor@latest <product-repo>/pixel-wealth-quest --verbose --diff

# 2. Runtime
# (via mcp__Claude_Preview__ tools, in your IDE if available)
preview_start pixel-wealth-quest
preview_screenshot
preview_resize 390 844 && preview_screenshot   # iPhone
preview_resize 768 1024 && preview_screenshot  # iPad
preview_console_logs --level error

# 3. PixelLab budget
python3 A-Wiki/scripts/game/pixellab_gen.py balance
```

End-to-end smoke (run after Phase 2c.9 finishes):
1. Parent shell → PWQ tab → TitleScene shows.
2. Tap "เริ่มเกม" → Room.
3. Tap a walkable cell → A* path; player walks around obstacles.
4. Tap player → action strip; pick นั่ง → holds on frame 6; tap to move → cancels.
5. Tap each dog → bio modal; cream shows RIP.
6. Walk through south door → Farm (camera scrolls).
7. Buy a seed at the office computer, till + plant + water + harvest.
8. Buy an IoT device, place in a slot, pick a strategy → mock equity animates.

---

## Phase 2d — Worker-Bots (mock farm automation)

Promoted from `HANDOFF.md` historical Phase 2b backlog after Phase 2c completed. Keep this separate from IoT trading-bot state: Worker-Bots automate farm tasks; trading bots remain mock visualization only.

### Ticket 2d.1 — Worker-Bot domain + seed registry  · `[x]`
**Goal**: Typed, deterministic catalog for hireable human/IoT farm workers.
**Files**: `src/types/domain.ts`, new `src/data/workerBots.seed.ts` + test.
**Shape**: `WorkerBotKind = 'human'|'iot'`; tasks `water|till|plant|harvest|tend`; catalog entries include `id`, Thai name, kind, cost, supported tasks, sprite key/path.
**Done when**:
- [x] Registry has at least 4 workers and both kinds
- [x] Every cost is positive; IDs/tasks unique and typed
- [x] Asset paths exist or have an explicit placeholder contract
> 2026-06-05 codex-poppy-javis: Added typed WorkerBot/FarmTask contracts plus a six-worker catalog: 2 human planned-reuse sources and 4 ready IoT assets. Tests cover kinds, unique IDs/tasks, positive costs, full task coverage, and asset contracts; shell verification confirmed all 6 source/ready files. Verified 160 tests, typecheck/build, and React Doctor 100. **RESUME** → 2d.2.

### Ticket 2d.2 — Pure hire + assign logic  · `[x]`
**Goal**: Spend coins to hire once; assign one supported task to one plot.
**Files**: new `src/logic/workerBots.ts` + test.
**Done when**:
- [x] Insufficient coins/duplicate hire/unsupported task fail without mutation
- [x] Successful hire deducts exact cost
- [x] Assignment keeps 1 bot = 1 task + 1 optional plot
> 2026-06-05 codex-poppy-javis: Added immutable pure hire/assign functions backed by the catalog source of truth. Exact-cost hire, duplicate/insufficient failures, supported-task assignment, and missing/unsupported failures are regression-covered. Verified 164 tests, typecheck/build, and React Doctor 100. **RESUME** → 2d.3.

### Ticket 2d.3 — Pure `workerBotFarmTick` automation  · `[x]`
**Goal**: One deterministic farm action per assigned worker per tick.
**Files**: `src/logic/workerBots.ts` + test; reuse `src/logic/farm.ts`.
**Done when**:
- [x] till/plant/water/harvest transitions use existing farm rules
- [x] Harvest credits coins; plant consumes seed inventory
- [x] No worker can mutate more than one plot per tick
> 2026-06-05 codex-poppy-javis: Added deterministic `workerBotFarmTick` using existing farm transitions. Tests prove sequential till→plant→water, seed consumption, harvest coins, one-step tend, and assigned-plot-only mutation. Replaced repeated plot scans with a per-tick Map after React Doctor caught it. Verified 167 tests, typecheck/build, and React Doctor 100. **RESUME** → 2d.4.

### Ticket 2d.4 — Store integration  · `[x]`
**Goal**: Wire worker roster, hire/assign actions, and automation into Zustand.
**Files**: `src/state/store.ts` + test.
**Done when**:
- [x] `workerBots[]`, `hireWorkerBot`, `assignWorkerBot` exposed
- [x] `advanceFarmTime()` applies worker automation atomically
- [x] Trading `bots` record remains unchanged and mock-only
> 2026-06-05 codex-poppy-javis: Wired separate `workerBots[]` + hire/assign actions into Zustand and applied one automation pass per elapsed farm tick inside one store emission. Tests prove failure no-ops, atomic automation, and unchanged trading-bot state. Verified 170 tests, typecheck/build, and React Doctor 100. **RESUME** → 2d.5.

### Ticket 2d.5 — Farm sprites + click bridge  · `[x]`
**Goal**: Render hired workers near assigned plots and open their status.
**Files**: `PreloadScene.ts`, `FarmScene.ts`, assets under `public/assets/farm/bots/` or reused Tide & Tally previews.
**Done when**:
- [x] Hired worker appears and follows assigned-plot position
- [x] Click/tap worker consumes propagation and opens its own status
- [x] No new PixelLab spend unless existing assets are insufficient
> 2026-06-05 codex-poppy-javis: Ingested two Tide & Tally human previews beside the four existing IoT sprites, preloaded the complete six-worker catalog, rendered hired workers at assigned plots/staging cells, and added a propagation-safe click bridge to the selected-worker modal state. Verified 173 tests, typecheck/build, and React Doctor 100 with $0 new PixelLab spend. **RESUME** → 2d.6.

### Ticket 2d.6 — Worker status/hire/assign UI + runtime smoke  · `[x]`
**Goal**: Complete the playable hire → assign → automated farm loop.
**Files**: new Worker-Bot panel(s), `HudOverlay.tsx`, `hud.css`, tests.
**Done when**:
- [x] User can hire, assign supported task/plot, and see status
- [x] Runtime proves one automated action/tick and correct coins/inventory
- [x] Desktop/mobile layouts, clean console, tests/typecheck/build/React Doctor pass
> 2026-06-05 codex-poppy-javis: Added responsive Worker-Bot center + HUD entry, catalog hire/assignment/status flow, and selected-sprite status highlighting. Playwright proved hire 200→20 coins, one-action ticks, seed 1→0, automated harvest 20→44 coins, assigned Farm sprite + propagation-safe click, desktop/mobile/tablet layouts, and 0 console errors/warnings. Fixed a runtime-found mobile logo-over-modal stacking bug test-first. Verified 177 tests, typecheck/build, and React Doctor 100. **RESUME** → 2e.1.

## Phase 2e — News Bird (safe daily briefing)

Promoted from `HANDOFF.md` after Phase 2d completed. Reuse Tide & Tally's advisor/news system, gull art, and parchment letter while keeping all generation out of the client and all copy coaching-only.

### Ticket 2e.1 — News Bird briefing domain + safety gate  · `[x]`
**Goal**: Define a Sunday Invest Moon briefing contract and reject trade/order instructions before display.
**Files**: new `src/types/briefing.ts`, `src/logic/briefing.ts` + test; adapt Tide & Tally `types/advisor.ts` and `logic/advisor.ts`.
**Done when**:
- [x] Typed daily briefing supports news, technical, and sentiment cards with provenance
- [x] Unsafe Thai/English execution copy is rejected
- [x] Safe live → cached → canned selection is deterministic
> 2026-06-05 codex-poppy-javis: Added runtime-validated News Bird contracts for news/technical/sentiment cards, provenance/confidence/signals, and strategy hints. The pure safety gate rejects Thai/English trade or execution instructions, validates unknown JSON metadata, resolves safe live→cached→canned deterministically, and throws if the controlled canned floor is unsafe. Verified 181 tests, typecheck/build, and React Doctor 100. **RESUME** → 2e.2.

### Ticket 2e.2 — Canned floor + static briefing feed  · `[x]`
**Goal**: The client always has safe content and can optionally read pre-generated static JSON without secrets.
**Files**: new canned briefing data, briefing feed/adapter + test, `src/state/store.ts`.
**Done when**:
- [x] Canned Thai briefing renders offline
- [x] Safe `/briefings/latest.json` replaces canned; malformed/unsafe/network failure does not
- [x] No API key or generation request exists in the client bundle
> 2026-06-05 codex-poppy-javis: Added a safe Thai canned floor, same-day static JSON feed with safe in-memory cache, a validating store action, and an App hook that reads only `/briefings/latest.json`. Tests prove safe live replacement and malformed/unsafe/network fallback; client scan found no API key or generation endpoint. Verified 186 tests, typecheck/build, and React Doctor 100. **RESUME** → 2e.3.

### Ticket 2e.3 — In-game clock + 08:00 once-daily trigger  · `[x]`
**Goal**: Pure deterministic game-time logic schedules one News Bird delivery per day.
**Files**: new `src/logic/gameClock.ts` + test, store integration.
**Done when**:
- [x] Clock advances deterministically across day boundaries
- [x] Crossing 08:00 emits exactly one delivery per game day
- [x] Reload/state updates cannot duplicate the same day's delivery
> 2026-06-05 codex-poppy-javis: Added pure absolute-minute game clock logic plus persisted `sim:game-clock` store state. Tests prove deterministic rollover, exactly one 08:00 delivery per crossed day (including long jumps), pending delivery persistence, acknowledgement persistence, and no same-day duplicate after reload. Verified 190 tests, typecheck/build, and React Doctor 100. **RESUME** → 2e.4.

### Ticket 2e.4 — Gull assets + Farm click/trigger bridge  · `[x]`
**Goal**: Reuse the Tide & Tally News Gull and letter art; show/click the courier in FarmScene.
**Files**: reused assets under `public/assets/news-bird/`, `PreloadScene.ts`, `FarmScene.ts` + tests.
**Done when**:
- [x] Gull and parchment assets are product-local and preloaded
- [x] 08:00 delivery makes the gull visible; click consumes propagation
- [x] Click opens the current briefing letter
> 2026-06-05 codex-poppy-javis: Reused product-local Tide & Tally gull/letter assets, preloaded them, connected each Farm tick to 10 game minutes, rendered the interactive courier for pending 08:00 deliveries, and acknowledged/opened `news-bird` on a propagation-safe click. Playwright proved the real 07:50→08:00 trigger, visible interactive gull, modal bridge, bird removal, and clean console. Runtime QA also exposed and test-first fixed UTC-vs-Bangkok daily briefing dates. Verified 193 tests, typecheck/build, and React Doctor 100 with $0 PixelLab spend. **RESUME** → 2e.5.

### Ticket 2e.5 — Briefing letter UI  · `[x]`
**Goal**: Responsive parchment letter showing coaching-only daily news, technical signal, and sentiment.
**Files**: new News Bird panel(s), `HudOverlay.tsx`, `hud.css`, tests.
**Done when**:
- [x] All three cards show source/confidence and no execution controls
- [x] Safe fallback/source state is understandable
- [x] Desktop/mobile layouts and modal input gating pass
> 2026-06-05 codex-poppy-javis: Added read-only News Bird letter UI with three cards, source/confidence badges, optional technical/sentiment/strategy-learning signals, parchment styling, and HudOverlay routing. Tests prove there are no execution controls. Playwright verified desktop three-column layout, mobile single-column layout, no horizontal overflow, local date display, and clean console. Verified 196 tests, typecheck/build, and React Doctor 100. **RESUME** → 2e.6.

### Ticket 2e.6 — Out-of-band generator + runtime smoke  · `[x]`
**Goal**: Generate sanitized static JSON outside Vite and verify the complete 08:00 → gull → letter flow.
**Files**: product-local generator adapted from `game/tools/generate-briefing.mjs`, docs/handoff, runtime evidence.
**Done when**:
- [x] Generator reads server/author-time secret only, safety-checks output, and preserves last good JSON on failure
- [x] Runtime smoke covers canned + safe static JSON + unsafe fallback
- [x] Tests/typecheck/build/React Doctor, clean console, and client secret scan pass
> 2026-06-05 codex-poppy-javis: Added author-time `npm run briefing:generate` backed by `tools/generate-briefing.mjs`; it reads only `OPENROUTER_API_KEY`/A-Wiki secrets outside Vite, safety-converts unknown model JSON, writes dated + `latest.json` atomically, and preserves existing static files when no key is available. Seeded safe 2026-06-05 static briefing with `source: live`. Playwright proved the full 08:00 Farm trigger: pending gull visible, click opened `news-bird`, pending cleared, `source=live`, 3 cards rendered, and console had 0 errors/0 warnings. Client scan found no key/generation strings in `src` or `public`. Verified 200 tests, typecheck/build, and React Doctor 100. Phase 2e complete. **RESUME** → 3.1.

## Phase 3 — Debt Dungeon (safe liabilities mechanic)

Promoted from the GDD after Phase 2e completed. Keep this as a coaching/visualization mechanic: no credit-product advice, no loan applications, no real account writes, and no shaming copy. Debt data starts mock/local only.

### Ticket 3.1 — Debt Dungeon domain + pure balance math  · `[x]`
**Goal**: Define the debt/liability model and pure monthly projection rules before any UI or scene work.
**Files**: new debt types/data/logic + tests; update GDD/HANDOFF status if needed.
**Done when**:
- [x] Mock liability entries distinguish good debt vs bad debt without moralizing language
- [x] Pure projection calculates balance, interest cost, minimum-payment progress, and payoff month estimate deterministically
- [x] Tests cover zero/overpayment, high-interest debt, asset-building debt, and Thai coaching labels without execution/financial-product advice
> 2026-06-05 codex-poppy-javis: Added `Liability`/pressure types, non-shaming mock liabilities, and pure `projectLiability`/`summarizeLiabilities` logic. Test-first coverage proves high-interest vs asset-building classification, first-month interest/principal, payoff month estimates, overpayment closeout, under-interest stuck state, and safe Thai labels with no loan/product advice. Verified 206 tests, typecheck/build, React Doctor 100, and clean client secret scan. **RESUME** → 3.2.

### Ticket 3.2 — Debt Dungeon store state + HUD entry point  · `[x]`
**Goal**: Make Debt Dungeon data available in app state and expose a safe read-only HUD entry without building the full dungeon scene yet.
**Files**: `src/state/store.ts`, `HudOverlay.tsx`, small `DebtDungeonButton`/panel placeholder if needed, tests.
**Done when**:
- [x] Store initializes mock liabilities and exposes derived debt summary/projections without mutating source data
- [x] HUD has a clearly labeled read-only Debt Dungeon entry point
- [x] Tests prove no real credit application/order/write path exists
> 2026-06-05 codex-poppy-javis: Added derived Debt Dungeon state (`debtLiabilities`, `debtProjections`, `debtSummary`), a bottom HUD entry button, and a read-only Debt Dungeon panel with aggregate balance/minimum-payment/high-interest/equity cards plus per-liability projection rows. Tests prove derived state is cloned, no debt pay/apply/borrow action exists, and the modal exposes no forbidden action buttons. Playwright proved start→open Debt Dungeon, heading/read-only copy visible, forbidden buttons=0, no horizontal overflow, and console 0 errors/0 warnings. Screenshot: `.playwright-cli/page-2026-06-04T23-28-28-681Z.png`. Verified 208 tests, typecheck/build, React Doctor 100, and production client scan clean. **RESUME** → 3.3.

### Ticket 3.3 — Debt Dungeon encounter cards + coaching copy  · `[x]`
**Goal**: Convert debt projections into non-shaming, read-only encounter cards that can later feed a dungeon scene/NPC coach.
**Files**: new pure encounter logic/data + tests; optional panel wiring after logic passes.
**Done when**:
- [x] Projection rows map deterministically to asset-building, high-pressure, stuck, and neutral encounter cards
- [x] Thai coaching copy explains interest pressure without shame, credit-product advice, or payment/order commands
- [x] Tests cover all pressure levels and prove cards contain no apply/borrow/pay-now language
> 2026-06-05 codex-poppy-javis: Added pure `buildDebtEncounterCards` and derived `debtEncounterCards` state. Debt projections now map to `asset-guardian`, `interest-specter`, `principal-lock`, and `steady-path` encounter cards with support/warning/danger/neutral severity and safe Thai coaching copy. Wired cards into the read-only Debt Dungeon panel. Tests prove all pressure levels and no shame/apply/borrow/pay-now language; Playwright proved guardian/specter visible, 4 cards rendered, forbidden buttons=0, no overflow, and console 0 errors/0 warnings. Screenshot: `.playwright-cli/page-2026-06-04T23-33-55-114Z.png`. Verified 209 tests, typecheck/build, React Doctor 100, and production client scan clean. **RESUME** → 3.4.

### Ticket 3.4 — Debt Dungeon scene shell + entry bridge  · `[x]`
**Goal**: Add the lightest possible in-world scene/bridge for Debt Dungeon without changing debt data or adding real financial actions.
**Files**: Phaser scene/preload/entry bridge tests; optional reused local art only.
**Done when**:
- [x] A deterministic entry point can open the existing read-only Debt Dungeon panel from the game world
- [x] Scene/bridge has tests for input gating and no pay/apply/borrow side effects
- [x] Runtime smoke proves entry works, panel still read-only, and console is clean
> 2026-06-05 codex-poppy-javis: Added a lightweight programmatic Debt Dungeon entry in FarmScene at a deterministic farm cell. The entry consumes pointer propagation and opens the existing read-only `debt-dungeon` modal; no debt data mutation or financial action was added. Scene test proves bridge behavior. Playwright proved a real canvas click on the portal opens Debt Dungeon, modal visible, forbidden buttons=0, and console 0 errors/0 warnings. Screenshot: `.playwright-cli/page-2026-06-04T23-37-30-720Z.png`. Verified 210 tests, typecheck/build, React Doctor 100, and production client scan clean. **RESUME** → 3.5.

### Ticket 3.5 — Debt Dungeon NPC coach canned lines  · `[x]`
**Goal**: Add deterministic canned coach lines for Debt Dungeon encounters without LLM calls or personalized financial advice.
**Files**: pure coach copy/data + tests; optional panel display after logic passes.
**Done when**:
- [x] Each encounter type has short Thai coaching text and a neutral learning prompt
- [x] Copy avoids shame, loan application language, and payment/order commands
- [x] Tests prove deterministic mapping and no external generation/API path
> 2026-06-05 codex-poppy-javis: Added pure `buildDebtCoachLines`, derived `debtCoachLines` state, and a read-only coach section in the Debt Dungeon panel. Each encounter card now has deterministic Thai NPC coaching copy from `โค้ชดันเจี้ยน` plus neutral `ลองสังเกต...` prompts. Tests prove source projection mapping, no LLM/API/generation strings, and no apply/borrow/pay-now language. Playwright proved 4 coach lines rendered, prompt visible, forbidden buttons=0, no overflow, and console 0 errors/0 warnings. Screenshot: `.playwright-cli/page-2026-06-04T23-41-36-037Z.png`. Verified 211 tests, typecheck/build, React Doctor 100, and production client scan clean. **RESUME** → 3.6.

### Ticket 3.6 — Debt Dungeon mobile/tablet QA + Phase 3 closeout smoke  · `[x]`
**Goal**: Verify the complete Debt Dungeon flow across critical viewports and decide whether Phase 3 is shippable or needs polish tickets.
**Files**: runtime evidence, roadmap/HANDOFF/session-memory only unless QA exposes a bug.
**Done when**:
- [x] Desktop, iPhone-size, and iPad-size Debt Dungeon panel have no horizontal overflow
- [x] Farm portal click and HUD button both open the same read-only panel
- [x] Console clean, tests/build/React Doctor pass, and Phase 3 resume anchor moves to the next backlog
> 2026-06-05 codex-poppy-javis: Closed the Phase 3 Debt Dungeon slice with runtime QA. HUD button flow passed at desktop 1440×900, iPhone 390×844, and iPad 768×1024: heading/read-only copy visible, 4 coach lines rendered, forbidden buttons=0, and no horizontal overflow. Farm portal closeout smoke also passed via real canvas click: modal visible, `openModal=debt-dungeon`, forbidden buttons=0, and console 0 errors/0 warnings. Screenshots: `.playwright-cli/debt-dungeon-desktop-2026-06-05.png`, `.playwright-cli/debt-dungeon-iphone-2026-06-05.png`, `.playwright-cli/debt-dungeon-ipad-2026-06-05.png`, `.playwright-cli/debt-dungeon-portal-closeout-2026-06-05.png`. Latest verification remains 211 tests, typecheck/build, React Doctor 100, and production client scan clean. Phase 3 Debt Dungeon complete. **RESUME** → 4.1.

## Phase 4 — Sea + Tide & Tally Bridge

Promoted from the GDD after the Phase 3 Debt Dungeon slice completed. Keep this read-only and boundary-first: Sunday Invest Moon can point toward Tide & Tally/pirate ships, but must not import live trading, exchange keys, order actions, or shared mutable bot state into the client.

### Ticket 4.1 — Sea bridge read-only contract + Tide & Tally boundary  · `[x]`
**Goal**: Define the minimal type/logic contract for linking Sunday Invest Moon's farm/sea edge to Tide & Tally without crossing the mock-only/client-safety boundary.
**Files**: new pure bridge contract + tests; update GDD/HANDOFF if needed.
**Done when**:
- [x] Contract exposes read-only roster/route metadata only
- [x] Tests prove no exchange key, order, trade, or writable bot method exists
- [x] Copy clearly labels the sea bridge as a future/visual connection, not live trading
> 2026-06-05 codex-poppy-javis: Added minimal Sea/Tide & Tally bridge contract: `SeaBridgeRoute`, visual roster metadata, safe seed data, `resolveSeaBridgeRoute`, and `describeSeaBridge`. Contract is read-only and labels the connection as a future visual link, not a live system. Tests prove route/roster metadata only and scan serialization for no exchange/key/order/trade/buy/sell copy. Verified 213 tests, typecheck/build, React Doctor 100, and targeted sea bridge boundary scan clean. **RESUME** → 4.2.

### Ticket 4.2 — Sea bridge store state + read-only panel  · `[x]`
**Goal**: Expose the Sea/Tide & Tally bridge metadata in app state and display a read-only panel without adding any live integration.
**Files**: `src/state/store.ts`, new panel/button or existing HUD routing + tests.
**Done when**:
- [x] Store derives a read-only sea bridge summary from static route/roster metadata
- [x] UI clearly says future visual link / read-only and has no action buttons beyond close
- [x] Tests prove no exchange key, order, trade, buy, sell, or writable method path
> 2026-06-05 codex-poppy-javis: Added derived `seaBridge` state, read-only HUD button, and parchment-style Sea/Tide & Tally panel. Store tests prove cloned read-only route/roster metadata and no writable sea action path. HUD tests prove the panel opens and exposes no exchange/order/trade/buy/sell action button. Runtime smoke passed at 1440x900: heading visible, read-only copy count=2, forbidden buttons=0, no horizontal overflow, console 0 errors/0 warnings. Screenshot: `.playwright-cli/sea-bridge-panel-2026-06-05.png`. Verified 215 tests, typecheck/build, React Doctor 100, and targeted sea bridge boundary scan clean. **RESUME** -> 4.3.

### Ticket 4.3 — Sea bridge Farm edge marker + click bridge  · `[x]`
**Goal**: Add a deterministic in-world Farm sea-edge marker that opens the existing read-only Sea bridge panel without adding a live scene transition or shared mutable Tide & Tally state.
**Files**: `src/phaser/scenes/FarmScene.ts`, scene tests, maybe farm seed/constants.
**Done when**:
- [x] FarmScene renders a clear sea-edge/pier/boat marker at a deterministic farm position
- [x] Clicking the marker opens `sea-bridge` and consumes pointer propagation
- [x] Tests/runtime smoke prove no live Tide & Tally transition, no exchange/order/trade/buy/sell path, and clean console
> 2026-06-05 codex-poppy-javis: Added a deterministic Farm sea-horizon `Sea Bridge` marker that opens the existing read-only `sea-bridge` modal and consumes pointer propagation. Scene regression test proves the marker behavior. Runtime smoke started Farm via the dev seam, clicked the real canvas marker, and confirmed `openModal=sea-bridge`, heading visible, forbidden buttons=0, no horizontal overflow, and console 0 errors/0 warnings. Screenshot: `.playwright-cli/sea-bridge-farm-marker-2026-06-05.png`. Verified 216 tests, typecheck/build, React Doctor 100, targeted sea bridge boundary scan clean, and no Tide scene transition path. **RESUME** -> 4.4.

### Ticket 4.4 — Sea bridge mobile/tablet QA + Phase 4 closeout smoke  · `[x]`
**Goal**: Close Phase 4 with responsive QA for HUD + Farm marker entry paths and record evidence before promoting the next backlog slice.
**Files**: no code expected unless QA finds a regression; update HANDOFF/session-memory/roadmap.
**Done when**:
- [x] Desktop, iPhone, and iPad HUD-button flows open the read-only Sea bridge panel with no overflow
- [x] Farm marker closeout smoke opens `sea-bridge`, has no forbidden action buttons, and console is clean
- [x] Phase 4 is summarized in HANDOFF/session-memory, then `RESUME HERE` is promoted to the next approved slice
> 2026-06-05 codex-poppy-javis: Phase 4 closeout QA passed. HUD button flow passed at desktop 1440x900, iPhone 390x844, and iPad 768x1024: heading visible, read-only copy count=2, forbidden buttons=0, no horizontal overflow. Farm marker closeout opened `sea-bridge`, heading visible, forbidden buttons=0, no overflow, and console 0 errors/0 warnings. Screenshots: `.playwright-cli/sea-bridge-desktop-2026-06-05.png`, `.playwright-cli/sea-bridge-iphone-2026-06-05.png`, `.playwright-cli/sea-bridge-ipad-2026-06-05.png`, `.playwright-cli/sea-bridge-marker-closeout-2026-06-05.png`. Current verification remains 216 tests, typecheck/build, React Doctor 100, targeted boundary scan clean. Promoted Phase 5 read-only feed backlog into atomic tickets. **RESUME** -> 5.1.

## Phase 5 — Read-only Feed + Packaging Gate

Promoted from `HANDOFF.md` historical Phase 5 backlog after Phase 4 Sea bridge closeout. Keep this strict: no API keys in the browser, no order/trade/write method in any client interface, and no live feed activation without an explicit compliance gate + feature flag.

### Ticket 5.1 — Read-only feed contract + compliance flag shell  · `[x]`
**Goal**: Define a read-only live-feed boundary that can be implemented later without weakening the existing mock-only client safety model.
**Files**: `src/adapters/portfolioFeed.ts`, tests, maybe env/flag helper; update docs if needed.
**Done when**:
- [x] `PortfolioFeed` remains write-free and has no order/trade/buy/sell method
- [x] A future live read-only feed factory is gated behind an explicit disabled-by-default flag/shell
- [x] Tests prove browser/client code contains no API key, secret, exchange order, or execution path
> 2026-06-05 codex-poppy-javis: Added fail-closed live read-only feed shell in `portfolioFeed.ts`: `resolveLiveReadOnlyFeedFlags`, `liveReadOnlyFeedEnabled`, and `createLiveReadOnlyFeed`. It requires both `VITE_PWQ_LIVE_READ_ONLY_FEED` and `VITE_PWQ_COMPLIANCE_APPROVED`, defaults disabled, returns a disabled feed when not approved, and still throws `not implemented` when both flags are true because no backend compliance contract exists yet. Tests prove no action-method surface on the returned feed. Verified 219 tests, typecheck/build, React Doctor 100, secret/network scan clean; action-term scan only hits existing explanatory comment and regression-test regex. **RESUME** -> 5.2.

### Ticket 5.2 — Mock-default feed selector guard  · `[x]`
**Goal**: Add a small selector seam so the app continues to use the mock feed by default and cannot accidentally activate the live read-only shell without the explicit gate.
**Files**: `src/adapters/portfolioFeed.ts` or a small hook/helper, tests, maybe `useMockPortfolioFeed.ts` rename only if needed.
**Done when**:
- [x] Default feed selection returns `createMockPortfolioFeed` behavior and never calls the live shell by default
- [x] Flagged live selection still fails closed until the backend contract exists
- [x] Tests prove no API key, secret, order, trade, buy, sell, submit, or execute path is introduced
> 2026-06-05 codex-poppy-javis: Added `createPortfolioFeed` selector and routed `useMockPortfolioFeed` through it. Default and one-flag env cases still use the mock feed; fully flagged live selection routes into the fail-closed live shell and throws `not implemented`. Removed the now-internal `createMockPortfolioFeed` export after React Doctor flagged unused public surface. Runtime smoke proved default app snapshot `source=mock`, net worth 14990, open modal null, and console 0 errors/0 warnings. Screenshot: `.playwright-cli/feed-selector-mock-default-2026-06-05.png`. Verified 221 tests, typecheck/build, React Doctor 100, secret/network scan clean; action-term scan only hits regression-test regex and existing explanatory comment. **RESUME** -> 5.3.

### Ticket 5.3 — Backend read-only feed contract doc + client-safety scan  · `[x]`
**Goal**: Document the future backend-only read feed contract and add/record a repeatable client-safety scan so future agents do not put provider/exchange keys in Vite/browser code.
**Files**: docs/protocol or A-Wiki ADR, maybe product HANDOFF; tests only if adding a script.
**Done when**:
- [x] Contract clearly says backend owns secrets/session/auth; Vite client receives read-only snapshots only
- [x] Contract explicitly forbids client API keys, exchange credentials, order/trade/write endpoints, and execution buttons
- [x] A repeatable scan command is documented or automated and passes
> 2026-06-05 codex-poppy-javis: Added `docs/protocols/pwq-read-only-feed-contract.md` with backend-owned secret/session/auth requirements, client prohibitions, feature flag rules, and repeatable verification commands. Added product `tools/scan-feed-boundary.mjs`, `tools/scan-feed-boundary.test.mjs`, and `npm run feed:scan`; scanner strips comments to avoid Iron-Law false positives while flagging executable-looking secret/network/action code in production feed files. Verified `npm run feed:scan`, targeted scan tests, 223 full tests, typecheck/build, React Doctor 100, and regenerated A-Wiki index/check. **RESUME** -> 5.4.

### Ticket 5.4 — Packaging/preflight checklist for sale-ready mock build  · `[x]`
**Goal**: Create a small release/preflight checklist for a sellable mock-only build that preserves public-safe docs, build evidence, and no-live-feed/no-execution guarantees.
**Files**: product HANDOFF or A-Wiki runbook/protocol; no production code expected unless adding a verification script.
**Done when**:
- [x] Checklist covers build/test/typecheck/React Doctor/feed scan/privacy scan and screenshot evidence
- [x] Checklist says release artifact remains mock/read-only unless a separate backend contract is approved
- [x] `RESUME HERE` moves to the next concrete packaging or deploy ticket
> 2026-06-05 codex-poppy-javis: Added `docs/runbooks/pwq-sale-ready-mock-build.md`, a release/preflight checklist for sellable mock/read-only artifacts. It covers `feed:scan`, tests, typecheck, build, React Doctor, runtime screenshots, A-Wiki roadmap sync, gen-index, sync tests, privacy scan, release-gate assertions, and fail-closed behavior. Verification: `npm run feed:scan` clean and targeted feed/scanner tests passed. `python3 scripts/check-privacy.py -v` currently fails on 12 codename findings across 4 pre-existing files (`<product-repo>`/`<repo-owner>` path/repo references), so release packaging is not public-safe yet. **RESUME** -> 5.5.

### Ticket 5.5 — Public-safe privacy cleanup for release preflight  · `[x]`
**Goal**: Resolve or document the current `check-privacy.py` codename findings so the sale-ready preflight can pass before any public artifact is shared.
**Files**: `game-assets/manifests/pixel-wealth-quest/README.md`, `scripts/game/normalize_pet_anims.py`, `scripts/game/normalize_pwq_anims.py`, `wiki/synthesis/pixel-wealth-quest-gdd.md`, and/or privacy allowlist if that is the correct policy.
**Done when**:
- [x] `python3 scripts/check-privacy.py -v` findings are reduced to zero or explicitly justified by a tracked allowlist/policy
- [x] Any path examples avoid private usernames, repo codenames, or personal GitHub identifiers in public-safe artifacts
- [x] Runbook/HANDOFF/session-memory record the final privacy status
> 2026-06-05 codex-poppy-javis: Resolved the 12 privacy codename findings without adding an allowlist. Scrubbed product repo/path examples to generic `<product-repo>` placeholders, removed personal owner/repo references from the GDD, and changed animation normalization scripts to discover a sibling `pixel-wealth-quest` directory generically instead of hardcoding the product repo codename. Verified `python3 scripts/check-privacy.py -v` clean, `python3 -m pytest tests/test_normalize_pwq_anims.py -v` 5 passed, and `python3 scripts/gen-index.py && python3 scripts/gen-index.py --check` green. **RESUME** -> 5.6.

### Ticket 5.6 — Full sale-ready preflight evidence bundle  · `[x]`
**Goal**: Run the full sale-ready mock-build preflight now that privacy is clean, and record the fresh evidence bundle in HANDOFF/session-memory.
**Files**: no production code expected unless checks expose a regression; update HANDOFF/roadmap/session-memory with evidence.
**Done when**:
- [x] Product checks pass: `feed:scan`, full tests, typecheck, build, React Doctor
- [x] A-Wiki checks pass: roadmap sync, gen-index/check, sync tests, privacy scan
- [x] Runtime screenshot evidence is fresh enough for the mock/read-only release checklist
> 2026-06-05 codex-poppy-javis: Full sale-ready mock preflight passed. Product: `npm run feed:scan` clean, 223 tests passed, typecheck/build passed, React Doctor 100/no issues. Runtime evidence captured title, room/mock portfolio (`source=mock`, net worth 14990), portfolio panel, Debt Dungeon, Sea Bridge, News Bird, and real Farm sea marker click; forbidden button counts were 0 for Debt/Sea/News/marker, Debt/Sea overflow false, marker opened `sea-bridge`, console 0 errors/0 warnings. Screenshots: `.playwright-cli/release-title-2026-06-05.png`, `.playwright-cli/release-room-mock-portfolio-2026-06-05.png`, `.playwright-cli/release-portfolio-panel-2026-06-05.png`, `.playwright-cli/release-debt-dungeon-2026-06-05.png`, `.playwright-cli/release-sea-bridge-2026-06-05.png`, `.playwright-cli/release-news-bird-2026-06-05.png`, `.playwright-cli/release-farm-sea-marker-2026-06-05.png`. A-Wiki: roadmap mirror matched, gen-index/check green, privacy scan clean, sync tests passed. **RESUME** -> 5.7.

### Ticket 5.7 — Prototype iframe integration smoke  · `[x]`
**Goal**: Verify the parent prototype can still open the PWQ iframe entry for a sale/demo flow without breaking the product app.
**Files**: parent prototype only if smoke exposes a regression; update HANDOFF/session-memory/roadmap.
**Done when**:
- [x] Parent prototype navigation entry opens Sunday Invest Moon/PWQ iframe in dev or configured preview
- [x] PWQ iframe renders title/start and mock/read-only app without console errors
- [x] Screenshot evidence is recorded, or a blocker is written with exact missing server/config
> 2026-06-05 codex-poppy-javis: Prototype iframe smoke passed after scoped parent fixes. Served `prototype/` with `python3 -m http.server 8000 --directory prototype` and used Playwright init override `window.SE_PWQ_URL="http://127.0.0.1:5173/"` because PWQ dev server was on 5173 while prototype default expects 5175. Fixed duplicate-key warning in `FallbackMap` by keying fallback pins with id+index. Fixed Driver.js onboarding by filtering missing target elements, fail-closing when no steps exist, and calling `setSteps(steps)` after `setConfig`; bumped `onboarding.js` cache buster to v14. Smoke: Super User login -> Sunday Invest Moon nav -> iframe src `http://127.0.0.1:5173/`, PWQ HUD visible (`มูลค่าพอร์ต`), console 0 errors / 1 expected Babel dev warning. Screenshot: `.playwright-cli/prototype-pwq-iframe-clean-2026-06-05.png`. **RESUME** -> 6.1.

## Phase 6 — Handoff Audit + Commit Prep

Promoted after the sale-ready mock/read-only preflight and prototype iframe smoke. This phase is administrative: inventory changed files, verify no running helper processes are left unexpectedly, and prepare an accurate handoff for the next agent. Do not commit unless the user explicitly asks.

### Ticket 6.1 — Changed-file inventory + final handoff audit  · `[x]`
**Goal**: Produce a precise changed-file inventory across A-Wiki and product/prototype repos so the next agent can continue or commit safely.
**Files**: no code expected; update HANDOFF/session-memory/roadmap only if the audit changes resume state.
**Done when**:
- [x] `git status --short` is captured for A-Wiki and the product repo
- [x] Any running dev/static helper servers are listed or stopped if no longer needed
- [x] Final RESUME HERE points to the next concrete task or clearly says the implementation slice is complete
> 2026-06-05 codex-poppy-javis: Captured final git/server audit. A-Wiki `git status --short` currently shows only tracked deletions of volatile pharmacy SQLite sidecars: `wiki/entities/pharmacy/drugs.db-shm` and `wiki/entities/pharmacy/drugs.db-wal`. Parent product repo shows modified prototype files (`index.html`, `src/maps.jsx`, `src/onboarding.js` plus older modified `app.jsx`, `data.jsx`, `shell.jsx`, `.claude/launch.json`) and large untracked `pixel-wealth-quest/`, `game/`, `AGENTS.md`, `CLAUDE.md`, `.claude/skills/`. Static prototype server on port 8000 was stopped; PWQ Vite dev server remains on `127.0.0.1:5173` (pre-existing server PID 76471). **RESUME** -> 6.2 only if the user explicitly asks for staging/commit/review.

### Ticket 6.2 — Optional stage/commit review (requires explicit user instruction)  · `[x]`
**Goal**: If and only if the user asks to commit, inspect the dirty tree carefully, stage only the intended files, and commit atomically per repo policy.
**Files**: no default edits.
**Done when**:
- [x] User explicitly asks for commit/stage/push, or this ticket remains pending
- [x] Intended files are separated from unrelated pre-existing changes before staging
- [x] Verification summary is included in commit message or handoff
> 2026-06-05 codex-poppy-javis: Review-only audit performed without staging/committing. A-Wiki was clean on `main...origin/main`; product parent repo had tracked prototype/config changes plus a large untracked `pixel-wealth-quest/` module. `pixel-wealth-quest/` had 1191 untracked entries, including source/assets/evidence plus generated dependency/build directories (`node_modules`, `dist`) that must be excluded or reviewed separately before any commit. This ticket remains `[ ]` because no explicit user stage/commit/push instruction was given.
> 2026-06-05 codex-poppy-javis: Added A-Wiki readiness cleanup for SQLite sidecars discovered during continued review: `.gitignore` now ignores `*.db-shm` and `*.db-wal`, and `verify-awiki-ready.py` tests require those patterns. This keeps `gen-index`/pharmacy SQLite runtime files from polluting handoff status while leaving real DB policy unchanged.
> 2026-06-05 codex-poppy-javis: Added product-module `.gitignore` coverage for local Playwright/evidence outputs (`.playwright-cli/`, `output/`). `node_modules/` and `dist/` were already ignored. Future commit review should stage source/assets/docs intentionally and leave generated runtime evidence out unless explicitly requested.
> 2026-06-05 codex-poppy-javis: User explicitly authorized stage/commit. Staged the Sunday Invest Moon product module plus parent prototype integration/smoke-fix files; intentionally left unrelated parent `.claude/launch.json`, `game/`, `AGENTS.md`, `CLAUDE.md`, and `.claude/skills/` out of the commit. Verification before staging: `npm run feed:scan`, `npm test -- --run` (223 passed), `npm run typecheck`, `npm run build`, and `npx react-doctor@latest --verbose --diff` (100/100).

---

## Polish P1 — User Runtime Polish Goal (2026-06-05)

### Ticket P1.1 — Responsive/title/movement/living-room/farm first pass  · `[x]`
**Goal**: Address the user's runtime polish list before the larger PixelLab/Gemini asset generation pass.
**Done**:
- [x] Title splash switched to `public/assets/title/sunday-invest-moon-splash-v002.jpg` from a local Downloads reference image; original archived at `A-Wiki/game-assets/references/sunday-invest-moon/title/splash-v002.png`.
- [x] Title button moved higher so it does not overlap the `© 2006 Sunday Estate` footer area.
- [x] React HUD hidden on Title scene: no portfolio status, backpack, Worker-Bot, Debt, Sea, or control hint; only Phaser start button remains.
- [x] App shell hardened for responsive dynamic viewport with `100svh`/`100dvh`, full-size canvas, and no horizontal overflow in title runtime QA.
- [x] Living-room dogs are stationary by passing `wander:false` to `PetPack`; Farm dogs still wander.
- [x] Player action strip changed from Thai text chips to icon chips with the same accessible labels, translucent AssistiveTouch-like styling, and floating pop placement.
- [x] Run action no longer auto-runs randomly; it enables a temporary `วิ่ง x2` status chip and doubles click/keyboard movement speed.
- [x] Click-to-move path tween duration now scales by cell distance, so diagonal steps are not artificially fast.
- [x] Room keyboard movement supports Control as a run modifier; Farm grid movement supports Control/run status with run animation and 2x step duration.
- [x] Farm camera zooms in (`1.35`) and the house warp marker is smaller, lighter, and closer to the door instead of looking like a dark hole.
- [x] Added farm/shop/background/prop/season prompt pack: `pixel-wealth-quest/docs/asset-prompts/sunday-invest-moon-farm-prompts.md`.
**Still open / closed by follow-up**:
- [x] PixelLab/Gemini asset batch for title flowers/tree wind/Nong Sunday lying sky pose/3 dogs wagging title pose.
- [x] PixelLab farm prop batch: big tree, bushes, flowers, log, rock, cloud, water current, dirt path, plus more Harvest-Moon-style decorations.
- [x] Seasonal system: random season changes every 5 real minutes with generated/tinted animation assets.
- [x] News Bird upgrade: flapping-wing bird fly-by, dropped newspaper object, click newspaper on ground opens briefing.
- [x] TV One Piece-style animation final visual render/click-target QA.
> 2026-06-05 codex-poppy-javis: Implemented P1.1 first pass test-first where practical. Product checks so far: 229 tests passed, typecheck passed, build passed before final hit-zone propagation patch; rerun full verification before commit. Browser QA proved Title HUD removal, icon action strip, run status/no-auto-run, stationary living-room dogs, and blank canvas clicks no longer open player actions after hit-zone clamp. **RESUME** -> P1.2.

### Ticket P1.2 — PixelLab/Gemini farm/title animation asset batch  · `[x]`
**Goal**: Generate/import the actual art assets requested by the user and wire cheap Phaser animation loops.
**Files likely touched**:
- `public/assets/title/ambient/`
- `public/assets/farm/decor/`
- `src/phaser/scenes/TitleScene.ts`
- `src/phaser/scenes/FarmScene.ts`
- `src/phaser/scenes/PreloadScene.ts`
- `docs/asset-prompts/sunday-invest-moon-farm-prompts.md`
**Done when**:
- [x] PixelLab balance captured before/after.
- [x] Title page has animated flowers/trees, lying-smiling/blinking Nong Sunday, and 3 stationary tail-wag dogs matching the original title art style.
- [x] Farm map has reusable animated decor assets and a clear shop/background art plan or first implementation.
- [x] Runtime screenshots and tests/typecheck/build are recorded.
> 2026-06-06 codex-poppy-javis: Closed P1.2 by validating the existing generated asset batch and wiring already present in code. PixelLab balance before/after stayed `$3.47672558737464` because no new generation was needed this pass. Title runtime screenshot verified splash v002, flowers/tree, Nong Sunday title pose, and three stationary wagging dogs with console 0 errors/0 warnings: `pixel-wealth-quest/.playwright-cli/page-2026-06-06T03-00-52-415Z.png`. Farm runtime screenshots verified animated/reusable decor, water/path/tree view, farm shop/background view, season tint, and console clean: `page-2026-06-06T03-04-11-784Z.png`, `page-2026-06-06T03-04-41-213Z.png`. Product verification passed: `npm run feed:scan`, `npm test -- --run` (232 passed before TV hardening; targeted TV/decor test 8 passed after patch), `npm run typecheck`, `npm run build`, and `npx react-doctor@latest --verbose --diff` (100/100). Added TV hardening in `RoomScene.playTvCartoon()` (depth 12000, readable title text, batch-local cleanup), but TV visual screenshot remains unresolved and is split to P1.3. **RESUME** -> P1.3 TV cartoon visual render/click-target QA.

### Ticket P1.3 — TV cartoon visual render/click-target QA  · `[x]`
**Goal**: Make the living-room TV cartoon visibly render on the baked TV screen and prove the normal click target opens it without using a dev hook.
**Files likely touched**:
- `src/phaser/scenes/RoomScene.ts`
- `src/phaser/playerMovementScenes.test.ts`
- optional room hotspot calibration in `src/data/room.seed.ts`
**Done when**:
- [x] A real browser screenshot shows the One Piece-style TV overlay visibly on the living-room TV.
- [x] A normal canvas click on the TV hotspot triggers the overlay; dev-hook invocation is not the only proof.
- [x] Console remains 0 errors/0 warnings.
- [x] Targeted test plus full product checks pass.
> 2026-06-06 codex-poppy-javis: Closed P1.3. Atomic Playwright normal canvas click at the runtime TV hotspot created 7 TV cartoon objects and captured visible overlay on the living-room TV: `pixel-wealth-quest/.playwright-cli/tv-normal-click-atomic-2026-06-06.png`. Console after the normal-click proof stayed 0 errors / 0 warnings. Product verification after the TV hardening patch passed: `npm run feed:scan`, `npm test -- --run` (233 passed), `npm run typecheck`, `npm run build`, and React Doctor 100/100. No implementation ticket remains after P1.3; next action is optional stage/commit review only if the user explicitly asks.
> 2026-06-12 codex-poppy-javis: Re-verified the user runtime polish goal in the real product workspace path `<product-workspace>/pixel-wealth-quest`. Fixed a title-label regression so the fresh-save button is `เริ่มเกมส์` again, then runtime-verified the current browser at `127.0.0.1:5173`: title HUD remains hidden, existing-save title buttons sit above the footer, living-room dogs are stationary, and a normal TV click visibly renders the `ONE PIECE` TV overlay with console 0 errors / 0 warnings. During full verification, repaired Phase 12/13 state-contract drift: `friendship` is now declared/persisted in `PwqState`/`PwqInit`, NPC actions are typed, animal feeding tests now seed/consume `animal-feed`, and animal category labels are present in Shop/Inventory. Verification passed: targeted title/TV/state/component tests 46/46, full `npm test -- --run` 495/495, `npm run typecheck`, `npm run build`, and `npx react-doctor@latest --verbose --diff` 100/100. `npm run feed:scan` was not rerun in this pass because the approval request was rejected by the user/session.

---

## Phase 7 + 8 — Retro note (shipped outside roadmap tracking)

> [verified 2026-06-11] Phase 7 and Phase 8 were implemented and committed straight to product-repo main without roadmap sections (tracked via session goals). Cold-start summary:
> - **Phase 7 — Save System v2** (`0965b0d`): versioned `sim:save` single-key persistence, sleep-ready, forward-compatible (unknown fields extend the file without a version bump). Core: `src/logic/saveGame.ts` + store `SAVEABLE_FIELDS` funnel.
> - **Phase 8 — Farm life-sim core** (`03b036a`, `a5e5688`, `8fcbe3d`): multi-crop registry (`src/data/crops.seed.ts`), day-based growth, 4×28 calendar (`src/logic/calendar.ts`), deterministic FNV-1a weather (`src/logic/weather.ts`), energy system (`src/logic/energy.ts`), bed sleep flow + morning report UI, shipping-bin economy (`src/logic/shippingBin.ts` — ship produce, pay at sleep).
> - Test base after Phase 8: **300 vitest tests** green; bot trading still mock-only per ADR 2c.9.5.

---

## Phase 9 — Market economy + Bot seam hardening + HM UI + PixelLab animation batch

> Plan approved 2026-06-11 (claude-fable-5). Execution order: **9.0 → 9.1 → 9.2 → 9.3 → 9.9 → 9.10 → 9.11 → 9.12 → 9.4 → 9.5 → 9.6 → 9.7 → 9.8 → 9.13** (market logic first; PixelLab gen mid-phase so API risk surfaces early; bot seam after; UI polish last). Commit format `chunk(9.X): goal [next: 9.Y]`. PixelLab budget for the whole phase ≤ **$3.00** (player $1.00 + pets $2.00), balance echo before/after every gen ticket.

### Ticket 9.0 — Roadmap: Phase 7/8 retro + Phase 9 section + sync  · `[x]`
**Goal**: Canonical roadmap carries Phase 7/8 retro + this Phase 9 plan; mirror synced; RESUME HERE → 9.1.
**Done when**: sync script verifies no drift; both repos committed.

### Ticket 9.1 — `src/logic/market.ts` pure deterministic price engine  · `[x]`
**Goal**: Sell prices move daily without RNG state: `sellPriceOf(itemId, day, seed='pwq-market')` = `max(1, round(base × seasonal × drift × weatherMod))`.
- Drift = FNV-1a `hash(seed:itemId:day)` → **[0.85, 1.15]** (reuse `weather.ts` hash pattern; save-compatible, no stored state).
- Seasonal: in-season 1.0 / off-season 1.2 scarcity premium (per-produce table; default 1.0). WeatherMod: storm day ×1.05 (derived from `weatherFor`).
- Only produce moves; non-produce passes through static `priceCoins`. Shop buy prices stay static.
- `marketHistory(itemId, day, n=7)` = pure recompute → free sparkline.
**Files**: `src/logic/market.ts` (new), `src/logic/market.test.ts` (new).
**Test-first**: determinism; integer ≥1 bounds; non-produce passthrough; off-season > in-season same-day; history 7 points pointwise == `sellPriceOf`; storm modifier on a known storm day.
**Done when**: vitest + typecheck green; zero store/React imports.

### Ticket 9.2 — Wire market into settlement + bin preview  · `[x]`
**Goal**: Bin settles at the finished day's market price; `ShippingBinPanel` preview == morning payout **by construction**.
**Files**: `src/logic/sleep.ts` (swap local `priceOf` at line ~46 → `sellPriceOf(id, finishedDay)`), `src/logic/sleep.test.ts`, `src/components/ShippingBinPanel.tsx` (same swap at line ~7, using `gameClock.day`), panel + store tests.
**Test-first**: bin of 1 carrot on a drift≠1.0 day pays `sellPriceOf('carrot-produce', finishedDay)`, not 24; dedicated preview==payout invariant test (lock against future next-day-price refactors).
**Done when**: all tests green.

### Ticket 9.3 — `MarketPanel.tsx` UI  · `[x]`
**Goal**: Player sees today's prices: row per produce — today vs base, ▲/▼ arrow, 7-day inline-SVG sparkline (idiom from `BotStatusOverlay`).
**Entry**: "ราคาตลาดวันนี้" button in `ShippingBinPanel` header (no new art).
**Files**: `src/components/MarketPanel.tsx` (new + test), `src/state/store.ts` (`ModalName` + `'market'`), `HudOverlay.tsx`, `ShippingBinPanel.tsx`, `src/styles/hud.css`.
**Test-first**: one row per produce; arrow direction matches `sellPriceOf` vs base; sparkline has 7 points from `marketHistory`.
**Done when**: opens from bin panel; mobile-safe; tests + typecheck green.

### Ticket 9.4 — Bot config persistence in `sim:save`  · `[ ]`
**Goal**: Bot configs survive reload; status recomputed deterministically on hydrate (equity curves NEVER persisted).
**Files**: `src/logic/saveGame.ts` (`botConfigs` field + sanitizer), `src/state/store.ts` (`SAVEABLE_FIELDS`, `hydrateBotConfigs` validating `strategyId`, `refreshBots()` on mount, `configureBot` writes `botConfigs`), tests.
**Test-first**: save round-trip with corrupt entry dropped; hydrate + `refreshBots()` curve == fresh `MockBotFeed` run (determinism proof).
**Done when**: reload restores configs; `npm run feed:scan` clean; mock-only invariant untouched.

### Ticket 9.5 — Daily bot refresh via `epoch` + serializable DTO guard  · `[ ]`
**Goal**: Bot sparklines evolve once per in-game day, deterministically — no timers, no polling.
**Files**: `src/feeds/tradingBotFeed.ts` (`BotConfig.epoch?: number`; mock seed → `deviceId:strategyId:epoch??0`), `src/state/store.ts` (`sleep()` re-runs configured bots with epoch = new day), tests.
**Test-first**: same epoch → identical curve; different epoch → different; `JSON.parse(JSON.stringify(status))` deep-equals status.
**Done when**: refresh is sleep-cadenced; all green.

### Ticket 9.6 — Versioned remote bot contract doc v1  · `[ ]`
**Goal**: `docs/bot-feed-contract.md` v1 — `GET/PUT /api/sim/bots/:deviceId`, BotConfig/BotStatus JSON shapes (incl. optional `epoch`, remote may ignore), error model, explicit no-secrets/no-order-execution clauses; cross-link ADR 2c.9.5 + Phase 5 feed contract.
**Test-first**: regression lock — `RemoteBotFeed` still throws for both methods; no `fetch(`/URL literals in `tradingBotFeed.ts`.
**Done when**: doc versioned v1; feed:scan clean.

### Ticket 9.7 — HM HUD chip: season + weather + day  · `[ ]`
**Goal**: Top chip shows season glyph + weather glyph + "วันที่ X" in HM idiom (inline pixel SVG, `--sim-*` tokens); data already in store.
**Files**: `HudOverlay.tsx` (+ test, possibly small `CalendarChip.tsx`), `hud.css`.
**Test-first**: aria-labels derived from `weatherFor(day, seasonOf(day))` + `dayOfSeason`.
**Done when**: desktop + 380px mobile no overflow; tests green.

### Ticket 9.8 — HM panel idiom pass (CSS-only)  · `[ ]`
**Goal**: Consistent wood-frame header + parchment body + close-button placement across the ~15 modals.
**Files**: `src/styles/hud.css`, `tokens.css` only.
**Done when**: no component-markup changes beyond classNames; existing tests + typecheck green; visual QA 3 representative panels desktop/mobile.

### Ticket 9.9 — PixelLab gen: player tool anims (water/hoe/harvest, south)  · `[x]`
**Goal**: 3 new south-facing 7-frame one-shots for น้องซันเดย์ (`watering`, `hoeing`, `harvest` scythe swing), normalized into `playerAnims.ts`.
**Process**: `pixellab_gen.py balance` echo before → kick 3 `pixellab_character.py animate --character-id 58be20a8-ee08-4432-bb43-3627f69e12ac` jobs at session start → write failing `playerAnims.test.ts` while polling → zip export → extend `ACTION_MAP/ACTION_ORDER/FRAME_RATE` in A-Wiki `scripts/game/normalize_pwq_anims.py` → re-run normalize → balance echo after. Pin the action slug in the prompt so the export filename matches `ACTION_MAP`.
**Budget**: cap **$1.00**, hard stop; log delta below.
**Done when**: 3 actions in manifest with 7 on-disk frames each; tests green.

### Ticket 9.10 — Wire tool anims into ToolWheel flow  · `[x]`
**Goal**: Selecting hoe/water/scythe plays the matching one-shot; farm logic stays instant (anim cosmetic).
**Files**: `src/phaser/toolAnimMap.ts` (new pure map: `hoe→hoe, water→water, scythe→harvest, seed→undefined`) + test, `playerController.ts` (expose `playOneShot(action)`), `FarmScene.ts` (`handleFarmTool` calls it), controller tests.
**Done when**: runtime QA shows swing before result; no energy/logic regressions.

### Ticket 9.11 — PixelLab gen: pet anims (run×8dir + eat/sleep/bark south)  · `[x]`
**Goal**: Per dog — red/สุขใจ, black/ศรีสุข, cream/มั่งมี (still renders in-game): 8-dir `run` + south one-shots `eat`, `sleep`, `bark`.
**Character ids** (from `public/assets/character/pets/gen/<c>/dog-<c>.character.json`): red `d09a749e-fce0-4ff6-8575-2a7e8f4884a2`, black `d43685ba-ea5d-4d94-9e35-2d79a2c95b18`, cream `bd9fd4e3-78b5-4f08-84cf-f426baae6fee` — reuse, no create step.
**Files**: A-Wiki `scripts/game/normalize_pet_anims.py` (extend literal `["walk","sit","wag"]`; `run` joins move actions + LOOPING), pet `anim_clean/`, regenerated `petAnims.ts`, tests.
**Test-first**: `PET_ANIM_ACTIONS` includes eat/sleep/bark; `PET_MOVE_ACTIONS` includes run; frames on disk for all 3 dogs.
**Budget**: cap **$2.00** total, 2 gates (gate A = 3 run jobs, gate B = 9 one-shots); over cap → drop `bark` first.
**Done when**: manifest regenerated; balance + evidence logged.

### Ticket 9.12 — Pet behaviors: idle scheduler + bark-on-click  · `[ ]`
**Goal**: Dogs occasionally eat/sleep during wander; rare run burst; clicking a dog plays bark and still opens the bio panel.
**Files**: `src/phaser/objects/PetPack.ts` (tick choice table + one-shot playback, injectable rng), tests, pet click bridge (bark then existing `gameBus.emit('pet-clicked')`).
**Test-first**: seeded rng tick sequence includes an `eat` one-shot then resumes wander; click still emits `pet-clicked` (bio regression lock); missing anim key → graceful skip, no crash.
**Done when**: runtime QA in Room + Farm; tests green.

### Ticket 9.13 — Phase 9 closeout smoke + roadmap sync  · `[ ]`
**Goal**: Full runtime smoke — market panel → ship → sleep → payout == preview → bot refresh → tool anim → pet behaviors; desktop + mobile; console clean.
**Gate**: `npm test` (all) + `npm run typecheck` + `npm run feed:scan` + React Doctor; canonical roadmap updated → mirror synced → closing commit.

---

## Phase 9b — Plan Phase 9–11 retro: Market Feed Seam + Paper Engine + Backtest UI

> [verified 2026-06-12] Market feed seam, paper trading engine, and backtest UI were implemented in a single session (product commits 260e281, 8fdfaa7, f47726a + Phase 10–11 commits). These correspond to the approved plan's Phase 9–11 (plan approved 2026-06-11). Test base after this work: **422 vitest tests** green, typecheck clean, `npm run feed:scan` clean.

### Plan Phase 9 — Market Data Backend + Feed Seam  · `[x]`
> [verified 2026-06-12]
> - `backend/routers/market.py`: GET /api/market/klines + /symbols, Binance→OKX fallback, TTL cache, allowlist, rate limit
> - `backend/tests/test_market.py`: 7 pytest tests (mock httpx, cache, allowlist, 502)
> - `src/data/candles.canned.ts`: 500×1h BTC+ETH bars captured 2026-06-12 (99 KB, fully offline)
> - `tools/capture-canned-candles.mjs`: author-time refresh script
> - `src/feeds/marketDataFeed.ts`: `MarketDataFeed` interface (read-only, no order methods); `CannedMarketDataFeed` default; `RemoteMarketDataFeed` flag-gated (`VITE_PWQ_MARKET_FEED=remote`, fails loudly)
> - `src/feeds/marketDataFeed.test.ts`: 9 contract tests (assertReadOnly, allowlist, timestamps)
> - `A-Wiki/docs/protocols/bot-trading-iron-law.md`: amended to approve paper trading on public keyless data; 7 client prohibitions unchanged

### Plan Phase 10 — Paper Trading Engine + Presets + Settlement  · `[x]`
> [verified 2026-06-12]
> - `src/logic/indicators.ts`: SMA/EMA/RSI(Wilder)/MACD/Bollinger/ATR/highest/lowest/crossAbove/crossBelow — pure, 27 golden-value tests
> - `src/types/strategy.ts`: `StrategyDef` JSON schema — engine: signal/grid/dca/rebalance, RuleGroups, RiskParams
> - `src/data/strategyPresets.ts`: 10 presets (grid-classic, grid-wide, dca-steady, dca-martingale, rebalance-5050, ma-cross, rsi-reversal, macd-momentum, bollinger-meanrev, breakout-high) + `LEGACY_STRATEGY_ALIAS` for save compat
> - `src/logic/paperBroker.ts`: fee=0.1%, slippage=5bps, fill tracking, maxDrawdown, winRate
> - `src/logic/strategyEngine.ts`: `runStrategy(def, candles, startCash)` — single function for live bot + backtest
> - `src/feeds/tradingBotFeed.ts`: added `PaperBotFeed` (inject `MarketDataFeed`, runs strategyEngine); default singleton changed to `new PaperBotFeed()` (still offline/deterministic = mock-by-default per iron law)
> - `src/logic/botSettlement.ts`: stake/settle/unstake — loss capped at stake (STAKE_MIN=50, STAKE_CAP=2000)
> - `src/logic/balanceGate.test.ts`: 20-game-day run across all 10 presets, economy guard

### Plan Phase 11 — Backtest UI + Custom Strategy Builder  · `[x]`
> [verified 2026-06-12]
> - `src/components/BacktestPanel.tsx`: strategy+symbol+interval selectors, equity sparkline SVG, 4 stat cards, risk disclaimer
> - `src/logic/customStrategies.ts`: `validateStrategyDef`, CRUD, max 10 custom strategies
> - `src/components/StrategyBuilderPanel.tsx`: name input, risk params, backtest preview, **deploy disabled until backtest run** (gate enforced)
> - `src/feeds/tradingBotFeed.test.ts` + `src/state/store.test.ts`: updated for PaperBotFeed as default

---

## Resource Note: Real Broker Adapter (Future Phase)

> **Cost-first**: ก่อนเริ่ม phase นี้ scout free model tier ก่อน; backend Python เท่านั้น; client ห้ามแตะ broker เด็ดขาด (Iron Law)

**iqoptionapi** (community, unofficial): https://github.com/iqoptionapi/iqoptionapi

### ช่วยลดเวลาได้ที่ Broker Adapter layer เท่านั้น
| สิ่งที่ iqoptionapi มีให้ | ประโยชน์ |
|--------------------------|----------|
| `connect()` / `connect_2fa()` / `check_connect()` | Login + reconnect + 2FA พร้อมใช้ ไม่ต้อง reverse-engineer WebSocket |
| `get_candles(asset, ...)` | ดึง candle จาก IQ Option ได้ทันที |
| `get_all_open_time()` | เช็ค asset เปิด/ปิด (forex/cfd/crypto/digital/binary) |
| `buy()` / `buy_digital_spot_v2()` / `buy_order()` | ส่ง order หลายประเภท |
| `get_order()` / `get_positions()` / `get_position_history_v2()` | ติดตาม position |
| `get_digital_payout()` / `get_all_profit()` | payout/profit data |

> ลด prototype broker adapter: reverse-engineer WebSocket (หลายวัน) --> prototype ใน 1-2 วัน
> **Warning**: unofficial/community repo -- มี timeout/check-win issues; ใช้เป็น learning/prototype เท่านั้น

### สิ่งที่ iqoptionapi ไม่ช่วยแทน (ต้องสร้างเอง)
strategy engine, backtesting, risk manager, portfolio/accounting, order reconciliation, monitoring/alert, database schema, dashboard, test suite, live/paper parity

### Architecture ที่แนะนำ (backend-only -- Iron Law คงเดิม)

Client เห็นแค่ paper trade result เสมอ -- ไม่มี order path ใน browser เด็ดขาด

```python
# Abstract interface -- เขียนก่อน, adapter มาทีหลัง
class BrokerAdapter:
    def get_candles(self, symbol, interval, limit): ...
    def place_order(self, symbol, direction, amount): ...
    def get_order(self, order_id): ...
    def get_positions(self): ...
    def close_position(self, position_id): ...

# Concrete adapters
class IqOptionAdapter(BrokerAdapter): ...   # <- iqoptionapi wraps here
class AlpacaAdapter(BrokerAdapter):   ...   # future
class BinanceAdapter(BrokerAdapter):  ...   # future
```

```
[ Execution Engine (backend) ]
        |
[ BrokerAdapter interface ]
        |
[ IqOptionAdapter ]  [ AlpacaAdapter ]  [ BinanceAdapter ]
        |
[ iqoptionapi ]
```

**Phase ที่ใช้ประโยชน์**: future Phase X3 (Real Broker Integration) -- หลัง Phase 14, ยังไม่อยู่ใน scope ปัจจุบัน; ใส่ไว้เพื่อ reference เมื่อถึงเวลา

---

## Phase 12 — NPCs

> Plan approved 2026-06-11. 3 NPCs: แม่ค้าตลาด / ลุงชาวประมง / ครูการเงิน. Schedule-driven, gift/talk friendship points. Commit format `chunk(12.X): goal [next: 12.Y]`.

### Ticket 12.1 -- npcs.seed.ts NPC registry  . [x]
**Goal**: 3 NPCs with typed bios, gift preferences, and daily schedule slots.
**New file**: `src/data/npcs.seed.ts`
```ts
NpcId = 'market-lady' | 'fishing-uncle' | 'finance-teacher'
NpcDef = { id, nameTh, schedule: NpcSlot[], giftPrefs: { loved, liked, disliked }, portraitPath }
NpcSlot = { fromMin, toMin, sceneId: 'town' | 'farm' | 'room', cell: Cell }
```
**New test**: compile + type check; every NPC has ≥3 schedule slots; no loved/liked overlap; portrait paths are strings.
**Done when**:
- [x] File exports typed NPC_DEFS record
- [x] Tests green
> 2026-06-12 claude-sonnet-4-6: 12.1 done -- npcs.seed.ts (3 NPCs: market-lady/fishing-uncle/finance-teacher), npcSchedule.ts locationAt(), 7+4 tests green. RESUME HERE -> 12.2.

### Ticket 12.2 -- npcSchedule.ts + friendship.ts  . [x]
**Goal**: Pure location resolver + pure friendship point tracker.
**New files**:
- `npcSchedule.ts`: `locationAt(npc: NpcDef, minuteOfDay: number): NpcSlot`
- `friendship.ts`: 0–1000 points → 10 hearts; `giveGift(state, npc, item) → delta`; loved +80 / liked +30 / disliked −20; once per day guard; `talk(state, npc) → delta` +10
**Test-first**: schedule wraps correctly; gift deltas match pref table; once-per-day guard; heart level = floor(points/100).
**Done when**: tests + typecheck green; zero React/store imports.
> 2026-06-12 claude-sonnet-4-6: 12.2 done -- npcSchedule.ts + friendship.ts (initFriendship/giveGift/talkToNpc/heartLevel/friendshipDiscount), 16 tests green; zero React/Zustand imports. RESUME HERE -> 12.3.

### Ticket 12.3 -- dialogue.seed.ts + DialoguePanel.tsx  . [x]
**Goal**: Canned dialogue indexed by (npcId, heartLevel 0|1|2|3+) — coaching/friendly only, no trade execution language.
**New files**: `dialogue.seed.ts` (entries per NPC × 4 heart tiers), `DialoguePanel.tsx` (parchment modal, portrait, lines, close + optional gift button when inventory has a liked item).
**Safety scan**: no `ซื้อ/ขาย/ส่งออเดอร์/เทรด` in dialogue seed.
**Done when**:
- [x] Safety scan clean
- [x] Tests prove no execution language; panel renders portrait + lines
> 2026-06-12 claude-sonnet-4-6: 12.3 done -- dialogue.seed.ts (4 tiers/NPC, Thai, safety scan clean); DialoguePanel.tsx (portrait/hearts/tier-lines/talk/close); HudOverlay wired; 5+6 tests green. RESUME HERE -> 12.4.

### Ticket 12.4 — NPC rendering in `FarmScene.ts` + click bridge  · `[x]`
**Goal**: NPCs visible in FarmScene at schedule-determined positions; click opens dialogue.
**Edit**: `FarmScene.ts` — on each game-tick, call `locationAt(npc, minuteOfDay)` for each NPC; render/move sprite (reuse `PetPack` wander tween pattern, but position-based not random); interactive zone → `gameBus.emit('npc-clicked', npcId)`.
**Edit**: `HudOverlay.tsx` — render `DialoguePanel` when `openModal === 'npc:*'`.
**Preload**: placeholder NPC sprites (reuse existing walking human Worker-Bot sprites until PixelLab batch).
**Done when**:
- [x] NPC appears at correct farm cell per schedule
- [x] Click → dialogue panel; propagation consumed
- [x] Tests green; typecheck green
> 2026-06-12 claude-sonnet-4-6: 12.4 done -- FarmScene.redrawNpcs() renders 3 NPCs at locationAt() positions; gameBus 'npc-click' event + HudOverlay listener → openNpcDialogue; 22 NPC tests pass. RESUME HERE -> 12.5.

### Ticket 12.5 — Friendship unlocks (shop discount)  · `[x]`
**Goal**: Hearts ≥ 3 → 5% shop discount; hearts ≥ 6 → 10%.
**Edit**: `src/state/store.ts` — `friendshipDiscount(npcId): number` derived selector; `ShopPanel.tsx` reads it; `buy()` applies.
**Test-first**: discount = max across all NPCs; discount correctly reduces price; tests green.
> 2026-06-12 claude-sonnet-4-6: 12.5 done -- ShopPanel shows strikethrough+discounted price + badge "ลด X%"; buy aria-label uses finalPrice; 6 ShopPanel tests (inc. 4 discount); 469/469 tests. RESUME HERE -> 12.6.

### Ticket 12.6 — PixelLab NPC sprites + Phase 12 smoke  · `[x]`
**Goal**: 3 NPCs × 4-dir walk + idle south (cap $1.20).
**Process**: echo balance before/after; 3 PixelLab `animate` jobs; normalize + wire into PreloadScene.
**Done when**:
- [x] Sprites on-disk; manifest entries; runtime smoke desktop + mobile; console 0 errors
> 2026-06-13 codex-poppy-javis: 12.6 done -- PixelLab create-character + animate generated 3 NPCs with idle south + 4-dir walk frames (9 frames/dir), normalized into `public/assets/character/npcs/`, added `npc-sprites.manifest.json`, wired `preloadNpcFrames()` into PreloadScene, and replaced Worker-Bot placeholder texture keys. Balance before `$2.96099750654565`, after NPC batch `$2.77687443613344` (spend ~$0.1841 < $1.20 cap). Verified 504 tests, typecheck/build/feed scan, React Doctor 100, desktop/mobile runtime asset smoke.

---

## Phase 13 — Farm Animals

> Plan approved 2026-06-11. Chicken + cow, daily feed → happiness → produce quality.

### Ticket 13.1 — `src/data/animals.seed.ts` + `src/logic/animals.ts`  · `[x]`
**Goal**: Animal registry + pure daily happiness + produce quality logic.
**New files**: `animals.seed.ts` (AnimalDef: id, nameTh, feedItemId, producesId, spriteKey), `animals.ts` (pure: `feedAnimal`, `animalDayTick` → happiness ±, `produceQuality(happiness)`).
**New items in `items.ts`**: `animal-feed`, `egg`, `milk` (3 quality tiers each).
**Test-first**: missed feed → happiness −10; daily produce qty × quality deterministic.
> 2026-06-13 codex-poppy-javis: Verified current implementation -- chicken/cow registry, animal-feed, egg/milk quality tiers, and pure animal logic covered by animals/items tests.

### Ticket 13.2 — Store + barn zone + `animalDayTick` hook  · `[x]`
**Files**: `store.ts` (`animals[]`, `feedAnimal`, `animalDayTick` called from `sleep()`), `farm.seed.ts` (add `barn` zone cells near bottom of farm grid).
> 2026-06-13 codex-poppy-javis: Verified current store integration -- animals persist, feed consumes animal-feed, sleep ticks happiness/produce, and barn zone exists in FARM.zones.

### Ticket 13.3 — `FarmScene.ts` render + `AnimalPanel.tsx`  · `[x]`
**Goal**: Animals wander in barn zone (reuse `PetPack` wander); click opens status/feed panel.
**Done when**: feed button reduces animal-feed inventory; next-day produce in shipping bin.
> 2026-06-13 codex-poppy-javis: Added AnimalPanel, gameBus animal-clicked bridge, FarmScene.redrawAnimals() in barn zone, and placeholder chicken/cow textures. Targeted animal/HUD/preload tests 53 passed; typecheck green.

### Ticket 13.4 — PixelLab chicken + cow sprites + smoke  · `[x]`
**Budget**: cap $0.90; echo balance before/after; normalize + wire.
> 2026-06-13 codex-poppy-javis: 13.4 done -- Generated PixelLab `chicken-v001.png` + `cow-v001.png`, added `spritePath` registry fields, preloaded both real animal textures, and guarded placeholder generation so loaded textures are not overwritten. Animal batch spend ~$0.0148; balance after `$2.7620752804478` (< $0.90 cap). Desktop/mobile runtime smoke loaded NPC/animal assets with missing=0 and console/network issues=0.

---

## Phase 14 — Town + Market Prices + Festivals

> Plan approved 2026-06-11. TownScene, market stall, 2 festivals.

### Ticket 14.1 — `TownScene.ts` + `town.seed.ts`  · `[x]`
**Goal**: New Phaser scene (~24×16, top-down); market stall, town hall, farm→town east edge warp.
**Files**: `src/phaser/scenes/TownScene.ts`, `src/data/town.seed.ts`.
**Done when**: player can walk Farm east edge → TownScene and back; no asset budget yet.
**Delivered 2026-06-13**: test-first town seed + TownScene shell, Farm east-edge → Town warp, Town west gate → Farm return, Phaser registry coverage, runtime Town screenshot smoke.
**Verified**: 510 vitest tests; typecheck; build; feed scan; React Doctor 100/100; runtime smoke `/tmp/pwq-town-smoke.png`.

### Ticket 14.2 — `src/logic/marketPrices.ts` + `MarketStallPanel.tsx`  · `[x]`
**Goal**: Produce prices fluctuate daily deterministic (seasonal × seeded random walk 0.7–1.4); town market offers better rate than shipping bin on good days; optional remote mode: % change proportional to BTC-yesterday delta.
**Test-first**: determinism; market price > base some days < other days; town > bin invariant holds.
**Delivered 2026-06-13**: test-first deterministic `marketPrices.ts`, produce quote rows in `MarketStallPanel`, `sellAtTownMarket()` store action that pays coins immediately without touching the shipping bin, and TownScene market-stall bridge.
**Verified**: 523 vitest tests; typecheck; build; feed scan; React Doctor 100/100; runtime smoke `/tmp/pwq-market-stall-smoke.png`.

### Ticket 14.3 — `src/logic/festivals.ts` + 2 events  · `[x]`
**Goal**: Spring day 14 = produce contest (bonus coins for top-quality crop); Autumn day 14 = investment quiz (multiple-choice coaching question, coin reward).
**Test-first**: deterministic trigger; quiz answer validation; no financial advice copy.
**Delivered 2026-06-13**: test-first `festivals.ts` with Spring day 14 produce contest + Fall day 14 quiz, session-only quiz repeat guard, `FestivalPanel`, festival HUD button, and store actions for contest/quiz rewards.
**Verified**: 535 vitest tests; typecheck; build; feed scan; React Doctor 100/100; runtime smoke `/tmp/pwq-festival-smoke.png`.

### Ticket 14.4 — PixelLab town/festival assets + smoke  · `[ ]`
**Budget**: cap $0.80; echo balance before/after.

---

## Phase 15 — Analyst Desk (investneet-style readable analysis suite)

> Plan approved 2026-06-13. User loves **investneet.com/scan.html** — its readability, warm color tone, dashboard, charts, stock-scan radar, funds (กองทุน), stock descriptions, market analysis. Phase 15 brings that *readable* feel in as a clean **"Analyst Desk"** surface, reusing the Phase 9–11 market/indicator/paper-trading infra. **Backlog phase — begins after the current RESUME ticket; internal start = 15.1.** Commit `chunk(15.X): goal [next: 15.Y]`.
>
> **Iron Law (unchanged — see `docs/protocols/bot-trading-iron-law.md`):** client stays MOCK + read-only — no API keys, no order path in the browser. Real **read-only** quotes arrive via the existing **Phase 9b `/api/market/*` seam** (Ticket 15.8 extends it with `/api/screener` + `/api/funds`). Real broker stays **backend-only**, already scoped in "Resource Note: Real Broker Adapter (Future Phase X3)". Every analysis view shows the learning-only disclaimer ("⚠️ ผลในอดีตไม่การันตีอนาคต — ข้อมูลนี้ใช้เพื่อการเรียนรู้เท่านั้น").

### investneet design — sampled live (2026-06-13, Chrome DevTools on `scan.html`)

investneet is itself an **"AI investing simulator"**, so its model maps ~1:1 onto Sunday Invest Moon. Source of truth for the Analyst Desk look:

**Palette (verbatim CSS custom properties):**
```css
--bg #fbf7ed (warm cream) · --bg-soft #f3ede0 · --bg-deep #ede4d2
--line #e5dcc7 · --line-soft #ede5d2
--text #1f1a14 · --text-2 #4a4338 · --muted #8a8378
up/positive: olive-green #4a7301 (dominant) · #6b8e23 · #84cc16 · bright #9cff00
down/negative: --cherry #b91c1c · --red #ff4f91
accents: --amber #ffd166 · --blue #38d5ff · --cyan #67e8f9 · --link #3b6bdb
contrast panels (hero/selects/chips): #0f071a · #1b1030 · #241442 (dark purple)
--content-max 600px (mobile-first single column) · --topbar-h 56px
```
> **Key insight:** warm-cream LIGHT theme — already close to SIM's parchment/cream (`--sim-cream #fff4da`). The Analyst Desk = a **clean reading mode** of the warm palette, cohesive with the farm game. Readability win = font sizing + tabular numbers + 600px column, not going dark.

**Typography (sampled):** body = system stack, 16px; tables 13px; `th` = 10.5px / 800 / muted / `--bg-soft`. → keep **IBM Plex Sans Thai** (renders Thai better) at that scale. Mirror up-green / down-red exactly.

**Radar / scan model to mirror:** hero "หุ้นที่เริ่มส่งสัญญาณแรงผิดปกติ" + "VOLUME SURGE สูงสุด 86.0x" + ▶ RE: SCAN refresh · ranking tabs `#ทั้งหมด · #วันล่าสุด · #RSI` · themed collections `#เดอะเบส S&P500 · #สายเทค Nasdaq100` · table cols **หุ้น · ราคา · Market cap · 1D% · RSI · Volume×** · chart timeframe `1D 5D 1M 3M 6M 1Y` + metric `Price · Relative · Volume · PEG`. Also present (MOCK-able later): Watchlist, Leaderboard, ประวัติซื้อขาย, แลกเปลี่ยน ฿$, profile, mail/alerts. Archive a reference screenshot → `A-Wiki/game-assets/references/sunday-invest-moon/investneet/`.

### Ticket 15.1 — Analyst tokens + readable type ramp  · `[x]`
**Goal**: investneet warm-cream palette + readable type scale as **`.analyst-desk`-scoped** tokens; pixel HUD untouched.
**Edit**: `src/styles/tokens.css` — add `.analyst-desk` (`[data-surface="analyst"]`) block: `--an-bg #fbf7ed`, `--an-bg-soft #f3ede0`, `--an-line #e5dcc7`, `--an-text #1f1a14`, `--an-muted #8a8378`, `--an-up #4a7301`, `--an-up-bright #9cff00`, `--an-down #b91c1c`, `--an-amber #ffd166`, `--an-panel #1b1030`. Append the readable `--t-*` ramp (body/caption/kicker/mono-num) from `prototype/colors_and_type.css` (Thai body = IBM Plex Sans Thai). `--sim-*` (Phase 2c.1.5) stays untouched.
**New file**: `src/styles/analyst.css` — 600px-max centered column, 56px topbar, warm data table (`th` 10.5–11px/800/muted/`--an-bg-soft`), stat cards, filter/ranking chips, `font-variant-numeric: tabular-nums` on figures.
**Done when**: `.analyst-desk` renders warm-cream readable Thai at sampled scale w/ tabular numbers + green/red; pixel HUD unchanged; lint clean.

### Ticket 15.2 — Analyst Desk shell + office Workstation launcher  · `[x]`
**Goal**: Full-screen readable desk opened from the **existing** office computer; investneet-style tabbed nav.
**New file**: `src/components/analyst/AnalystDesk.tsx` — full-bleed React layer (pauses Phaser), `data-surface="analyst"`, **mobile-first 600px column + 56px sticky top bar**. Tabs: **ภาพรวม · เรดาร์สแกน · กองทุน · วิเคราะห์ตลาด · พอร์ต**. Close → game.
**Edit**: `src/state/store.ts` — add `'analyst-desk'` to `ModalName` + `analystTab` slice (default `'overview'`) + setter; render via existing `HudOverlay.tsx` modal pattern.
**Edit**: the **existing office-computer hotspot** (Phase 2c.7.5 shop) → small **Workstation launcher** `[ร้านค้า] [ศูนย์วิเคราะห์] [บอทเทรด]`; ศูนย์วิเคราะห์ → `setOpenModal('analyst-desk')` (today it opens shop directly).
**Reuse**: `.pwq-backdrop`, gameBus, Tide & Tally responsive breakpoints.
**Done when**: office computer → ศูนย์วิเคราะห์ opens desk; tabs switch; close returns; readable desktop + 390×844; console clean.

### Ticket 15.3 — Instrument universe (mock stocks + funds) + read-only feed seam  · `[x]`
**Goal**: Mock Thai-style stock + fund universe behind the **same seam shape** as `marketDataFeed.ts`.
**New file**: `src/data/instruments.canned.ts` — ~20 mock stocks (PTT, CPALL, AOT, KBANK, ADVANC, DELTA…) `{ symbol, nameTh, sector, price, changePct, volume, marketCap, pe, pbv, divYield, ohlcv: Candle[] }` + ~8 funds `{ id, nameTh, category, nav, ret1y, ret3y, ret5y, risk, expensePct }`. Labelled mock/illustrative (candles.canned.ts stays crypto-only; this is separate equities/funds data).
**New file**: `src/feeds/instrumentFeed.ts` — mirror `marketDataFeed.ts`: `InstrumentFeed` iface, `CannedInstrumentFeed` (default), `RemoteInstrumentFeed` (flag `VITE_PWQ_MARKET_FEED=remote`, read-only `/api/screener/*` + `/api/funds/*`, fail-loud), `createInstrumentFeed()`, allowlist guard.
**Test-first**: `instrumentFeed.test.ts` — canned returns universe; allowlist rejects unknown; remote throws loudly.
**Done when**: feed returns mock universe offline; tests green; `npm run feed:scan` clean.
> 2026-06-13 claude-sonnet-4-6: 15.3 done — instruments.canned.ts (20 stocks + 8 funds, deterministic genBars), instrumentFeed.ts (CannedFeed + RemoteInstrumentFeed fail-loud + createInstrumentFeed factory), 8 tests (test-first). 543 tests green. RESUME HERE → 15.4.

### Ticket 15.4 — Screener engine + scan presets (test-first)  · `[x]`
**New file**: `src/logic/screener.ts` — `screen(universe, criteria): ScreenRow[]`; composable filters (price/%chg/volume; RSI band; price vs SMA/EMA; MACD cross; PE/PBV/divYield; funds: return/risk/category) reusing `indicators.ts`; attaches `signal` + `score`; ranks.
**New file**: `src/data/scanPresets.ts` — โมเมนตัมแรง · ทะลุแนวต้าน · RSI<30 ขายมากเกินไป · ปันผลสูง · Value (PE ต่ำ).
**Test-first**: `screener.test.ts` — deterministic rows + ranking per preset.
**Done when**: presets filter+rank correctly; tests green.

### Ticket 15.5 — Screener UI (เรดาร์สแกน) + Funds UI (กองทุน)  · `[x]`
**New file**: `src/components/analyst/ScreenerView.tsx` — investneet radar: hero "หุ้นที่เริ่มส่งสัญญาณแรงผิดปกติ" + volume-surge highlight + RE: SCAN; ranking tabs `#ทั้งหมด · #วันล่าสุด · #RSI`; themed-collection chips; results table **หุ้น · ราคา · Market cap · 1D% [g/r] · RSI · Volume×** + mini-sparkline; sortable; row → 15.6.
**New file**: `src/components/analyst/FundsView.tsx` — funds table (กองทุน · หมวด · NAV · 1Y/3Y/5Y · ความเสี่ยง · ค่าธรรมเนียม) + filters.
**New file**: `src/components/analyst/Sparkline.tsx` — extract the shared SVG-polyline sparkline (from `BacktestPanel`/`MarketPanel`).
**Color**: `--an-up` / `--an-down`. **Done when**: tables render, sortable, green/red; presets filter live; mobile horizontal-scroll OK.

### Ticket 15.6 — Stock detail + description (คำอธิบายหุ้น) + chart  · `[x]`
**New file**: `src/components/analyst/CandleChart.tsx` — zero-dep SVG candlestick; timeframe `5D 1M 3M 6M 1Y` toggles; line-mode; SMA20/SMA50 overlays; RSI(14) sub-panel.
**New file**: `src/logic/instrumentNarrative.ts` (+test) — pure deterministic Thai technical read from indicators (no LLM).
**New file**: `src/components/analyst/StockDetailView.tsx` — header + CandleChart + key-stats grid + narrative list + disclaimer.
**Edit**: `ScreenerView.tsx` (onSelect prop) + `AnalystDesk.tsx` (selectedSymbol state routing).
**Done when**: row → detail w/ chart + overlays + auto Thai narrative; narrative tests green.
> 2026-06-13 claude-sonnet-4-6: 15.6 done — CandleChart (SVG zero-dep, 5D/1M/3M/6M/1Y + line-mode + SMA20/50 + RSI sub-panel), instrumentNarrative.ts (10 tests), StockDetailView.tsx, ScreenerView onSelect, AnalystDesk selectedSymbol routing; typecheck clean, 570/570 tests. RESUME HERE → 15.7.

### Ticket 15.7 — Market analysis + overview (วิเคราะห์ตลาด · ภาพรวม)  · `[x]`
**New file**: `src/logic/marketBreadth.ts` (+20 tests) — advancers/decliners, pctAboveSma, sectorStats, topGainers/Losers/mostActive, sentiment.
**New file**: `src/components/analyst/MarketView.tsx` — mock index cards (SET/SET50/MAI), อารมณ์ตลาด chip, breadth bar, sector heat cells, top gainers/losers/most-active tables.
**New file**: `src/components/analyst/OverviewView.tsx` — landing: breadth stats, momentum signals table, top gainer/loser cards, cross-tab navigation props.
**Edit**: `AnalystDesk.tsx` — wire MarketView + OverviewView; remove OverviewStub/MarketStub; add cross-tab callbacks.
**Done when**: market view shows breadth/sectors/movers; overview aggregates; breadth tests green.
> 2026-06-13 claude-sonnet-4-6: 15.7 done — marketBreadth.ts (20 tests), MarketView.tsx, OverviewView.tsx, AnalystDesk wired; typecheck clean, 590/590 tests. RESUME HERE → 15.8.

### Ticket 15.8 — Extend read-only backend contract + ADR alignment  · `[x]`
**Goal**: Fold screener/funds into the existing read-only data contract; no new client risk.
**Edit**: `backend/routers/market.py` (+ contract doc) and `A-Wiki/docs/protocols/bot-trading-iron-law.md` — add read-only `/api/screener/scan` + `/api/funds/list` alongside `/api/market/*`; server-side auth, rate-limit, **no secret/key in browser, no order endpoints**. Cross-link "Resource Note: Real Broker Adapter (Future Phase X3)" (broker stays backend-only).
**Edit**: `src/feeds/instrumentFeed.ts` `RemoteInstrumentFeed` wired under `VITE_PWQ_MARKET_FEED=remote`, fail-loud.
**Done when**: contract doc updated + cross-linked; remote flag wires screener/funds (404 until backend ships, by design); `npm run feed:scan` clean — no order/key path.
> 2026-06-13 codex-poppy-javis: 15.8 done — `RemoteInstrumentFeed` now targets `/api/screener/scan` + `/api/funds/list` with fail-loud tests; backend exposes GET-only placeholder routers returning 404; product contract + A-Wiki Iron Law cross-link Resource Note: Real Broker Adapter (Future Phase X3). Verified 591 vitest tests, typecheck, build, feed scan, React Doctor 100. Backend pytest blocked locally because the active Python env lacks FastAPI.

### Ticket 15.9 — Readability pass on existing finance panels  · `[ ]`
**Edit**: `MarketPanel.tsx`, `BacktestPanel.tsx`, `BotConfigPanel.tsx`, `StrategyBuilderPanel.tsx`, `MarketStallPanel.tsx` + `hud.css` — apply readable type ramp (Thai body ≥14px/1.65, `tabular-nums`), raise contrast, larger touch targets; keep parchment frame.
**Done when**: panels pass readability check (Thai ≥14px, tabular numbers, AA contrast); pixel aesthetic preserved.

### Phase 15 verification
```bash
npm --prefix <product-repo> run typecheck && npm --prefix <product-repo> test
npm --prefix <product-repo> run feed:scan          # iron-law: no order/key path
npx react-doctor@latest <product-repo> --verbose --diff
```
Runtime: office computer → ศูนย์วิเคราะห์ → tabs · screener presets filter/sort · row → detail chart + Thai description · funds · market breadth · `preview_resize 390 844` no overflow.

---

## Cross-cutting reuse map (every ticket pulls from here)

| Need | Reuse from | File |
|---|---|---|
| Parchment modal | `FamilyPanel` | `HudOverlay.tsx` ~lines 167–184 |
| Hotspot click + activate | `RoomScene` activate flow | `RoomScene.ts` ~line 156 |
| Tween-walk + facing + depth | `PetPack.step()` | `objects/PetPack.ts` |
| Direction from vector | `dir8FromVector` | `playerFrames.ts` |
| Grid + iso projection | `cellToScreenIso`, `screenDepth` | `logic/grid.ts` |
| Anim preload + register | `preloadPet/PlayerAnimations` | `petAnims.ts`, `playerAnims.ts` |
| Theme tokens (parent SOT) | `prototype/colors_and_type.css` | parent shell |
| Mobile responsive css | Tide & Tally | `<product-repo>/game/src/styles/hud.css` |
| Portrait-lock + viewport | Tide & Tally | `game/src/components/RotateDeviceGate.tsx` |
| Inventory grid layout | `GearRack` (Tide & Tally) | `game/src/components/GearRack.tsx` |
| Scene transition | `scene.start('Room')` | `PreloadScene.ts` ~line 47 |

---

## Iron-Law guardrails (non-negotiable)

1. **No secrets/API-keys/order-execution in the client.** Bot trading stays MOCK until a separate backend service exists (see ADR 2c.9.5).
2. **Test-first** for every `src/logic/*` addition.
3. **`raw/` is immutable.** Do not edit or delete anything under it.
4. **`A-Wiki/CLAUDE.md`** and **`AGENTS.md`** require explicit approval to edit (per A-Wiki rule #5).
5. **Commit straight to `main`** of both repos — no PR, no branch, no worktree (A-Wiki rule #6).
6. **Confidence markers** in any wiki edit: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]` / `[notebooklm YYYY-MM-DD]`.
7. **Communication in Thai** by default (unless user asks English).
8. **Edit the A-Wiki canonical roadmap, then sync the product mirror** whenever ticket status changes.

---

## Session log (append at the end of each work session)

```
> 2026-06-04 claude-opus-4-7: Wrote initial roadmap. RESUME HERE = 2c.1.1.
> 2026-06-04 claude-opus-4-7: 2c.1.1 done — splash JPG 208 KB + logo PNG 88 KB ingested. RESUME HERE = 2c.1.2.
> 2026-06-05 codex-poppy-javis: Standardized canonical-vs-mirror policy, added drift checker, and removed machine-local plan dependency from handoff entrypoints. RESUME HERE remains 2c.1.2.
> 2026-06-05 codex-poppy-javis: 2c.1.2 done — user-facing rename + branding regression test verified. RESUME HERE = 2c.1.3.
> 2026-06-05 codex-poppy-javis: 2c.1.3 implemented + static verified; left `[~]` pending localhost visual/console QA blocked by Browser policy. RESUME HERE = 2c.1.4.
> 2026-06-05 codex-poppy-javis: 2c.1.4 done — shared HUD logo verified. RESUME HERE = 2c.1.5.
> 2026-06-05 codex-poppy-javis: 2c.1.5 done — locked theme tokens + wood HUD chip verified. RESUME HERE = 2c.1.6.
> 2026-06-05 codex-poppy-javis: 2c.1.6 implemented + static verified; left `[~]` pending iPhone/iPad visual resize checks blocked by Browser policy. RESUME HERE = 2c.2.1.
> 2026-06-05 codex-poppy-javis: 2c.2.1 done — deterministic A* + corner-cut guard verified. RESUME HERE = 2c.2.2.
> 2026-06-05 codex-poppy-javis: 2c.2.2 done — iso/top-down inverse projection round trips verified. RESUME HERE = 2c.2.3.
> 2026-06-05 codex-poppy-javis: 2c.2.3 core implemented + automated verified; left `[~]` pending furniture collision calibration and runtime visual QA. RESUME HERE = 2c.3.1.
> 2026-06-05 codex-poppy-javis: 2c.3.1 done — player hit zone + modal state verified. RESUME HERE = 2c.3.2.
> 2026-06-05 codex-poppy-javis: 2c.3.2 implemented + automated verified; left `[~]` pending action-strip placement visual QA. RESUME HERE = 2c.3.3.
> 2026-06-05 codex-poppy-javis: 2c.3.3 core implemented + automated verified; left `[~]` pending directional run assets and visual action QA. RESUME HERE = 2c.4.1.
> 2026-06-05 codex-poppy-javis: 2c.4.1 done — typed pet bios + portrait assets verified. RESUME HERE = 2c.4.2.
> 2026-06-05 codex-poppy-javis: 2c.4.2 done — pet bio panels + RIP treatment verified. RESUME HERE = 2c.4.3.
> 2026-06-05 codex-poppy-javis: 2c.4.3 done — shared Room/Farm pet click bridge verified. RESUME HERE = 2c.5.1.
> 2026-06-05 codex-poppy-javis: 2c.5.1 source-of-truth fix verified; left `[~]` pending visible west-walk QA. RESUME HERE = 2c.5.2.
> 2026-06-05 codex-poppy-javis: 2c.5.2 core implemented + automated verified; left `[~]` pending smooth-wander visual QA. RESUME HERE = 2c.6.1.
> 2026-06-05 codex-poppy-javis: 2c.6.1 core implemented + automated verified; left `[~]` pending visible room-to-room scale QA. RESUME HERE = 2c.7.1.
> 2026-06-05 codex-poppy-javis: 2c.7.1 done — typed item registry + versioned asset-path contracts verified. RESUME HERE = 2c.7.2.
> 2026-06-05 codex-poppy-javis: 2c.7.2 done — generated and visually checked 16 item icons for $0.11185; wrapper updated for current API schema. RESUME HERE = 2c.7.3.
> 2026-06-05 codex-poppy-javis: 2c.7.3 done — typed inventory persistence + zero-clamped mutations verified. RESUME HERE = 2c.7.4.
> 2026-06-05 codex-poppy-javis: 2c.7.4 done — backpack button + responsive inventory panel flow verified. RESUME HERE = 2c.7.5.
> 2026-06-05 codex-poppy-javis: 2c.7.5 done — office computer shop flow + atomic purchase behavior verified. RESUME HERE = 2c.8.1.
> 2026-06-05 codex-poppy-javis: 2c.8.1 core implemented + automated verified; left `[~]` pending edge-artifact/FPS runtime QA. RESUME HERE = 2c.8.2.
> 2026-06-05 codex-poppy-javis: 2c.8.2 core implemented + automated verified; left `[~]` pending visible adjacent-ToolWheel QA. RESUME HERE = 2c.8.3.
> 2026-06-05 codex-poppy-javis: 2c.8.3 core implemented + automated verified; left `[~]` pending visible slot/device QA. RESUME HERE = 2c.9.1.
> 2026-06-05 codex-poppy-javis: 2c.9.1 done — six-strategy exchange-neutral mock registry verified. RESUME HERE = 2c.9.2.
> 2026-06-05 codex-poppy-javis: 2c.9.2 done — deterministic mock bot P&L + stable snapshots verified. RESUME HERE = 2c.9.3.
> 2026-06-05 codex-poppy-javis: 2c.9.3 done — deterministic default MockBotFeed + remote server-only seam verified. RESUME HERE = 2c.9.4.
> 2026-06-05 codex-poppy-javis: 2c.9.4 done — placed-device bot configuration + animated React/Phaser status sparklines verified without real network calls or client secrets. RESUME HERE = 2c.9.5.
> 2026-06-05 codex-poppy-javis: 2c.9.5 done — mock-only bot trading Iron Law + future backend contract documented and cross-linked. RESUME HERE = Phase 2c full-game runtime smoke.
> 2026-06-05 codex-poppy-javis: Phase 2c full-game runtime smoke done — closed visual QA tickets, recorded Playwright evidence + PixelLab balance, and fixed three runtime regressions test-first. RESUME HERE = 2c.2.3 furniture collision calibration.
> 2026-06-05 codex-poppy-javis: 2c.2.3 done — calibrated sofa collision + spawn, proved nearest-free runtime path, and verified 156 tests/build/React Doctor/clean console. RESUME HERE = 2c.3.3 directional run assets + visible lie-hold QA.
> 2026-06-05 codex-poppy-javis: 2c.3.3 done — generated directional run fallback keys from existing assets, verified lie frame-6 hold + directional run runtime, and passed A-Wiki 253/product 157 tests. Promoted Worker-Bots backlog into atomic Phase 2d. RESUME HERE = 2d.1.
> 2026-06-05 codex-poppy-javis: 2d.1 done — added typed six-worker catalog + asset contracts and verified 160 tests/build/React Doctor. RESUME HERE = 2d.2 pure hire + assign logic.
> 2026-06-05 codex-poppy-javis: 2d.2 done — added immutable exact-cost hire + supported-task assignment logic and verified 164 tests/build/React Doctor. RESUME HERE = 2d.3 workerBotFarmTick.
> 2026-06-05 codex-poppy-javis: 2d.3 done — added deterministic one-action-per-worker farm automation and verified 167 tests/build/React Doctor 100. RESUME HERE = 2d.4 store integration.
> 2026-06-05 codex-poppy-javis: 2d.4 done — integrated separate Worker-Bot state/actions + atomic farm-time automation and verified 170 tests/build/React Doctor 100. RESUME HERE = 2d.5 Farm sprites + click bridge.
> 2026-06-05 codex-poppy-javis: 2d.5 done — ingested/reused all six Worker-Bot sprites, added assigned-plot rendering + click bridge, and verified 173 tests/build/React Doctor 100 with $0 PixelLab spend. RESUME HERE = 2d.6 Worker status/hire/assign UI + runtime smoke.
> 2026-06-05 codex-poppy-javis: 2d.6 + Phase 2d done — added responsive hire/assign/status UI, proved full Worker-Bot runtime economy + sprite-click loop, fixed mobile modal stacking test-first, and verified 177 tests/build/React Doctor 100/clean console. Promoted News Bird backlog into atomic Phase 2e. RESUME HERE = 2e.1 briefing domain + safety gate.
> 2026-06-05 codex-poppy-javis: 2e.1 done — added runtime-validated briefing domain + strict coaching-only safety resolution and verified 181 tests/build/React Doctor 100. RESUME HERE = 2e.2 canned floor + static briefing feed.
> 2026-06-05 codex-poppy-javis: 2e.2 done — added safe canned/static/cached briefing delivery + validating store hook, verified no client secret/generation path, and passed 186 tests/build/React Doctor 100. RESUME HERE = 2e.3 in-game clock + 08:00 trigger.
> 2026-06-05 codex-poppy-javis: 2e.3 done — added persisted deterministic game clock + once-per-day 08:00 delivery trigger and verified 190 tests/build/React Doctor 100. RESUME HERE = 2e.4 gull assets + Farm bridge.
> 2026-06-05 codex-poppy-javis: 2e.4 done — reused gull/letter assets, proved real 08:00 Farm trigger + click bridge, fixed UTC/local briefing date test-first, and verified 193 tests/build/React Doctor 100/clean console. RESUME HERE = 2e.5 briefing letter UI.
> 2026-06-05 codex-poppy-javis: 2e.5 done — added responsive read-only News Bird letter UI with source/confidence/signal cards, no execution controls, desktop/mobile visual QA, and verified 196 tests/build/React Doctor 100/clean console. RESUME HERE = 2e.6 generator + runtime smoke.
> 2026-06-05 codex-poppy-javis: 2e.6 + Phase 2e done — added author-time static briefing generator, seeded safe live latest JSON, proved full 08:00 gull→letter runtime smoke, verified no client secrets/generation path, and passed 200 tests/build/React Doctor 100/clean console. Promoted Debt Dungeon backlog into atomic Phase 3. RESUME HERE = 3.1 debt domain + pure balance math.
> 2026-06-05 codex-poppy-javis: 3.1 done — added non-shaming Debt Dungeon liability types, mock seed, pure monthly projection/summary logic, and tests for high-interest, asset-building, overpayment, and under-interest states. Verified 206 tests/build/React Doctor 100/client scan. RESUME HERE = 3.2 debt store state + HUD entry point.
> 2026-06-05 codex-poppy-javis: 3.2 done — integrated derived debt state into Zustand, added read-only HUD button/panel, proved no debt pay/apply/borrow action path, verified runtime open flow/no overflow/clean console, and passed 208 tests/build/React Doctor 100/production scan. RESUME HERE = 3.3 debt encounter cards + coaching copy.
> 2026-06-05 codex-poppy-javis: 3.3 done — added pure Debt Dungeon encounter card generator, derived state, panel rendering, safe coaching copy, and runtime card smoke with 4 cards/no forbidden buttons/no overflow/clean console. Verified 209 tests/build/React Doctor 100/production scan. RESUME HERE = 3.4 debt scene shell + entry bridge.
> 2026-06-05 codex-poppy-javis: 3.4 done — added programmatic FarmScene Debt Dungeon portal, tested click propagation/open bridge, runtime-clicked the portal on canvas, and verified modal read-only/no forbidden buttons/clean console. Verified 210 tests/build/React Doctor 100/production scan. RESUME HERE = 3.5 debt NPC coach canned lines.
> 2026-06-05 codex-poppy-javis: 3.5 done — added deterministic canned Debt Dungeon coach lines, derived state, panel rendering, and runtime smoke for 4 coach lines/no forbidden buttons/no overflow/clean console. Verified 211 tests/build/React Doctor 100/production scan. RESUME HERE = 3.6 mobile/tablet QA + Phase 3 closeout smoke.
> 2026-06-05 codex-poppy-javis: 3.6 + Phase 3 Debt Dungeon done — desktop/iPhone/iPad HUD QA and Farm portal closeout smoke passed with no overflow, no forbidden buttons, and clean console. Promoted Sea + Tide & Tally bridge backlog into atomic Phase 4. RESUME HERE = 4.1 sea bridge read-only contract.
> 2026-06-05 codex-poppy-javis: 4.1 done — added read-only Sea/Tide & Tally bridge route/roster contract and tests proving no exchange/key/order/trade/buy/sell path in the boundary. Verified 213 tests/build/React Doctor 100/targeted boundary scan. RESUME HERE = 4.2 sea bridge store state + read-only panel.
> 2026-06-05 codex-poppy-javis: 4.2 done — added derived seaBridge store state, read-only HUD button/panel, runtime smoke screenshot, and no forbidden action path. Verified 215 tests/build/React Doctor 100/targeted boundary scan/clean console. RESUME HERE = 4.3 sea bridge Farm edge marker + click bridge.
> 2026-06-05 codex-poppy-javis: 4.3 done — added Farm sea-horizon Sea Bridge marker, scene test, and runtime canvas-click smoke proving it opens only the read-only sea-bridge panel. Verified 216 tests/build/React Doctor 100/targeted boundary scan/clean console. RESUME HERE = 4.4 sea bridge mobile/tablet QA + Phase 4 closeout smoke.
> 2026-06-05 codex-poppy-javis: 4.4 + Phase 4 done — desktop/iPhone/iPad Sea bridge HUD QA and Farm marker closeout passed with no overflow, no forbidden buttons, and clean console. Promoted Phase 5 read-only feed backlog into atomic tickets. RESUME HERE = 5.1 read-only feed contract + compliance flag shell.
> 2026-06-05 codex-poppy-javis: 5.1 done — added fail-closed live read-only feed contract + disabled-by-default compliance flag shell, with tests proving no action-method surface. Verified 219 tests/build/React Doctor 100/secret-network scan clean. RESUME HERE = 5.2 mock-default feed selector guard.
> 2026-06-05 codex-poppy-javis: 5.2 done — added mock-default feed selector, routed existing hook through it, proved fully flagged live selection still fails closed, and runtime-smoked default app source=mock. Verified 221 tests/build/React Doctor 100/secret-network scan clean/console clean. RESUME HERE = 5.3 backend read-only feed contract doc + client-safety scan.
> 2026-06-05 codex-poppy-javis: 5.3 done — added backend-owned read-only feed contract protocol and repeatable `npm run feed:scan` scanner/tests. Verified feed scan, 223 tests/build/React Doctor 100, and regenerated A-Wiki index/check. RESUME HERE = 5.4 packaging/preflight checklist for sale-ready mock build.
> 2026-06-05 codex-poppy-javis: 5.4 done — added sale-ready mock build preflight runbook and surfaced the current privacy blocker: 12 codename findings across 4 pre-existing files. Feed scan and targeted scan tests pass, but public release remains blocked until privacy cleanup. RESUME HERE = 5.5 public-safe privacy cleanup.
> 2026-06-05 codex-poppy-javis: 5.5 done — scrubbed codename/path/owner references and replaced hardcoded sibling repo discovery with generic `pixel-wealth-quest` lookup. Privacy scan now clean; normalize tests and gen-index/check pass. RESUME HERE = 5.6 full sale-ready preflight evidence bundle.
> 2026-06-05 codex-poppy-javis: 5.6 done — ran full sale-ready mock preflight, captured release screenshots, verified feed scan/223 tests/build/React Doctor 100/A-Wiki sync+privacy clean/console clean. RESUME HERE = 5.7 prototype iframe integration smoke.
> 2026-06-05 codex-poppy-javis: 5.7 done — fixed parent prototype FallbackMap key warning + Driver.js onboarding steps, smoke-tested Super User nav to PWQ iframe with src override to 5173, and verified iframe HUD visible with console 0 errors. RESUME HERE = 6.1 changed-file inventory + final handoff audit.
> 2026-06-05 codex-poppy-javis: 6.1 done — captured dirty-tree inventory, stopped the prototype static server on 8000, left pre-existing PWQ dev server on 5173 running, and marked implementation slice complete pending explicit user commit/stage instruction. RESUME HERE = 6.2 optional stage/commit review only if user asks.
> 2026-06-05 codex-poppy-javis: Started user runtime polish goal P1.1 — swapped title splash to v002, hid HUD on title, improved responsive viewport, froze living-room dogs, converted action strip to icons, changed run to status/speed boost only, slowed/scaled click-to-move, zoomed farm, softened house warp, and added farm asset prompt pack. RESUME HERE = P1.2 PixelLab/Gemini asset batch.
> 2026-06-11 claude-fable-5: 9.0 done — added Phase 7/8 retro note (shipped outside roadmap: Save v2 + farm life-sim core, 300 tests) and full Phase 9 section (market economy, bot seam hardening, HM UI, PixelLab player tool anims + pet run/eat/sleep/bark; budget ≤ $3.00). RESUME HERE = 9.1 market price engine.
> 2026-06-12 claude-fable-5: 9.1-9.3 done — deterministic market engine (FNV-1a drift 0.85-1.15, off-season ×1.2, storm ×1.05), bin settles at finished-day price with preview==payout invariant test, MarketPanel with arrows + 7-day sparklines (Playwright-verified desktop+mobile, console clean). Product commits 260e281/8fdfaa7/f47726a.
> 2026-06-12 claude-fable-5: 9.9-9.10 done — player water/hoe/harvest south one-shots (9f; v3 API requires even frame_count, requested 8 → exported 9; PixelLab slugs derive from action description so ACTION_MAP matches leading verb) wired into ToolWheel via toolAnimMap + playerController.playOneShot; runtime-verified pwq_player_hoe_front plays and plot tills. Watering v1 has ghost-can artifact on 2 frames; v2 regen queued behind PixelLab outage. Product 4d7860b/1d04449; A-Wiki 5ad5010b.
> 2026-06-12 claude-fable-5: 9.11 done — pet eat/sleep/bark south one-shots for all 3 dogs + run as directional looping move action (normalize_pet_anims extended + ts_out mkdir fix, 3 new A-Wiki tests; petAnims.test.ts 5 tests product-side). blocker: run 8-dir complete on red only — black 5/8 (missing W/NW/SW), cream 3/8; cream sleep pose generated standing not curled; regen blocked by PixelLab animate-character 422 outage, missing run dirs fall back to walk at runtime. Spend ~$0.52 of $3.00 cap (balance $2.961). Product f7daaf4. RESUME HERE = 9.12 pet behaviors.
> 2026-06-12 claude-haiku-4-5: Plan Phase 9–11 complete — market data backend+feed seam (CannedMarketDataFeed 500×1h offline + RemoteMarketDataFeed flag-gated; backend market.py proxy Binance→OKX), paper trading engine (10 preset strategies, indicators SMA/EMA/RSI/MACD/Bollinger/ATR, PaperBroker fee+slip, strategyEngine single runStrategy(), PaperBotFeed as default, botSettlement stake/settle), backtest UI (BacktestPanel sparkline + stats, StrategyBuilderPanel deploy-after-backtest gate, customStrategies CRUD). 422 tests green, typecheck clean, feed:scan clean, iron law: canned/mock still default. A-Wiki: bot-trading-iron-law.md amendment committed. RESUME HERE = 12.1 NPC registry.
> 2026-06-13 claude-opus-4-8: Planned **Phase 15 — Analyst Desk** (investneet-style readable analysis suite: warm-cream `.analyst-desk` tokens, mobile-first 600px, stock radar/screener + funds + stock description + market breadth) reusing Phase 9–11 market/indicator infra; sampled investneet.com/scan.html's live design via Chrome DevTools (palette #fbf7ed/#1f1a14, up #4a7301 / down #b91c1c). Backend stays read-only (15.8 extends `/api/market/*` seam with `/api/screener|funds`; broker remains future X3). Iron Law intact. Synced to both roadmap copies. RESUME HERE unchanged = 14.3 (Phase 15 is queued backlog; user may choose to prioritize over 14.3).
> 2026-06-13 claude-opus-4-8: **15.1 done** — added `.analyst-desk` / `[data-surface="analyst"]` scoped block to `tokens.css` (all `--an-*` palette + `--t-*` ramp matching investneet scale); created `src/styles/analyst.css` (~350 lines, all primitives: table, chip, collection-tab, stat-card, sparkline, timeframe/metric toggles, key-stats grid, buy/sell btns, narrative, disclaimer, responsive 639px). Typecheck green, pixel HUD untouched. RESUME HERE = 15.2.
> 2026-06-13 claude-sonnet-4-6: **15.2 done** — AnalystTab type + analystTab/setAnalystTab in store; computer hotspot opens 'workstation' (was 'shop'); WorkstationLauncher 3-button panel; AnalystDesk full-screen fixed overlay (5-tab topbar: ภาพรวม/เรดาร์สแกน/กองทุน/วิเคราะห์ตลาด/พอร์ต, stub content); HudOverlay: analyst-desk renders OUTSIDE backdrop, workstation renders inside parchment panel. House test updated. 535 tests green. Pushed 58518e9. RESUME HERE = 15.3.
> 2026-06-13 claude-sonnet-4-6: **15.3 done** — instruments.canned.ts (20 mock Thai stocks + 8 funds, deterministic genBars 30 bars each, labelled illustrative); instrumentFeed.ts (InstrumentFeed iface, CannedInstrumentFeed, RemoteInstrumentFeed fail-fast at ctor, createInstrumentFeed factory, allowlist guard); 8 tests test-first. 543/543 green. Pushed 2bc6de2. RESUME HERE = 15.4.
> 2026-06-13 claude-sonnet-4-6: **15.4 done** — screener.ts (screen() composable criteria: changePct/RSI/SMA/PE/PBV/divYield; criteria-primary scoring; ScreenRow+Signal types; sort desc); scanPresets.ts (5 presets: momentum/breakout/oversold/high-div/value); 17 screener tests test-first. 560/560 green. Pushed 9e058c7. RESUME HERE = 15.5.
> 2026-06-13 claude-sonnet-4-6: **15.5 done** — ScreenerView.tsx (radar hero, RE:SCAN, 5 preset chips, rank tabs, collection filter, table with 1D%/RSI/Vol×/Sparkline); FundsView.tsx (sortable table, category chips, risk badge); Sparkline.tsx (shared SVG polyline up/down); AnalystDesk wires real views. 560/560 green. Pushed e66368c. RESUME HERE = 15.6.
```
