---
name: game-phaser-pipeline
description: "Phaser + Vite + TypeScript + PixelLab game pipeline for A-Wiki game projects (PWQ): route, asset naming/manifest convention, verify steps, and the visualization-only client safety gate."
version: 1.0.0
domain: [code, media]
lifecycle_phase: build
category: game
agents: [all]
status: canonical
---

# Game Phaser Pipeline

Operational route for building 2D pixel games in the A-Wiki ecosystem (Pixel Wealth Quest lineage: Phaser + Vite + TypeScript + PixelLab assets). This skill is the checklist; deep knowledge stays in the wiki pages linked at the bottom — read those only when a step needs detail.

## Triggers

- Building or extending a Phaser game (PWQ / Tide & Tally lineage, or a new A-Wiki game project).
- Generating or importing pixel art via PixelLab (characters, crew, objects, tiles, UI panels, scene backgrounds).
- Wiring spritesheets/animations into Phaser scenes; any asset naming, folder, or manifest question.
- Verifying a game build or debugging blank canvas / missing texture / mobile overflow.
- User says "phaser", "pixellab", "sprite", "spritesheet", "ทำเกม", "asset เกม", "ตัวละครเกม".

## Non-Triggers

- General web/dashboard UI work → design-web lane (`wiki/synthesis/design-web-capability-hub.md`).
- Trading engine, order execution, broker/exchange connectivity → **not game work**; stop and follow `docs/protocols/bot-trading-iron-law.md` (Iron Law #7) before writing anything.
- 3D previews/prototypes → Three.js MCP (`show_threejs_scene`) where available; this skill is the 2D pixel pipeline.

## Route

| Step | Do | Done when |
|---|---|---|
| Concept | GDD/roadmap entry first — core loop, constraints, safety rules on paper | loop + constraints + safety rules are explicit |
| Engine | Phaser + Vite + TypeScript; game logic lives in **pure TS modules outside Phaser scenes**; failing test first (Iron Law #1) | logic is unit-testable without a browser |
| Assets | PixelLab → manifest pipeline (convention below) | asset pack report is READY, or warnings documented |
| Verify | unit tests + `tsc -b` + `vite build` + browser/Playwright smoke | no blank canvas, no missing texture, no mobile overflow |

## Asset convention (binding)

- **Asset key**: `<domain>.<family>.<name>.<variant>.<action?>.<direction?>.<size?>` — e.g. `character.captain.captain-trader-01.walk.south.64`
- **Filename**: kebab-case with double-dash segments — `captain-trader-01--walk--south--64.png`
- **Animation key**: `<name>:<action>:<direction>` — e.g. `captain-trader-01:walk:south`
- **Folders**: `game-assets/{characters,crew,objects,tiles,manifests}` — manifest JSON is tracked; binary exports stay out of markdown/wiki pages
- **`texture_key` is stable forever**: regenerating art replaces the PNG only — game code and manifests never rename keys
- **PixelLab review objects**: curate via `select-frames` (or dismiss) before import — never load a raw review object into the game
- Frame sizes follow the existing pack (64 characters / 96 large objects / 32 tiles) unless the GDD says otherwise

**Anti-patterns (reject on sight)**: prompt text as filename · `job_id` as texture key · importing uncurated review objects · asset metadata kept in chat instead of a manifest · ad-hoc naming per generation round.

## Toolchain — lives in the product repo (run from `pixel-wealth-quest`, not A-Wiki)

Game helper code moved to the product repo on 2026-07-12; A-Wiki keeps the knowledge, the product repo keeps the scripts.

| Tool (product repo path) | Purpose |
|---|---|
| `.claude/skills/pixellab-asset-ingest/` | guided asset-ingest workflow — start here for repeat runs |
| `scripts/game/write_phaser_manifest_template.py` | starter manifest (infers texture_key, sheet paths, anim keys) |
| `scripts/game/build_phaser_asset_manifest.py` | validate manifests + emit Phaser preload/animation payload (fail-fast) |
| `scripts/game/report_phaser_asset_pack.py --check-files` | READY/BLOCKED readiness report; `--fail-on-issues` for CI |
| `scripts/game/bootstrap_phaser_asset_pack.py` | one command: payload → loader TS → scene stub (`--copy-to-project`) |
| `scripts/game/pixellab_generate_image.py` | pixflux scene/background — transparency reliable only ≤200px, then `--upscale` (NEAREST) |

## Safety gate (Iron Law #7 — non-negotiable)

Game client = **visualization/reward layer only**. Full protocol with the 7 client prohibitions and approved read-only amendments: `docs/protocols/bot-trading-iron-law.md`.

- No exchange/broker keys, secrets, request signing, or order execution anywhere in the client; no direct browser→exchange calls.
- `MockBotFeed` / `CannedMarketDataFeed` stay the defaults; remote feeds are read-only, backend-proxied, flag-gated (`VITE_PWQ_MARKET_FEED=remote`), and must fail loudly — never silent fallback to or from live data.
- LLM/NPC output can never become an executable order.
- Rewards bind to discipline (low drawdown + rule-following), never raw profit or trade frequency.
- `PIXELLAB_API_TOKEN` fetched on demand from `drive/.secrets` via `scripts/lib/drive_secrets.py` — never in manifests, TS, logs, or chat.
- Performance budget is scope: sprite atlases/manifests, no heavy always-loaded assets.

## Deep knowledge (read only when a step needs it)

| Page | When |
|---|---|
| `wiki/synthesis/game-lightweight-highend-capability-hub.md` | lane overview / route rationale |
| `wiki/synthesis/pixellab-phaser-asset-convention.md` | full naming/manifest/loader contract + JSON and Phaser examples |
| `wiki/synthesis/pixellab-asset-pipeline-for-trading-rpg.md` | PixelLab endpoint per asset type, prompt baseline, credit-saving order |
| `wiki/synthesis/8-bit-trading-rpg-blueprint.md` | architecture, stack decisions, safe gameplay loop, MVP sequencing |
| `docs/protocols/bot-trading-iron-law.md` | client prohibitions + approved read-only data amendments |
| Product repo `pixel-wealth-quest`: `docs/pixel-wealth-quest-gdd.md`, `ROADMAP.md`, `docs/pwq-read-only-feed-contract.md` | product-specific decisions |
