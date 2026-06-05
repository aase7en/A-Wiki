# Pixel Wealth Quest — asset manifests

Tracked recipes for PWQ assets. Binary PNGs live in the product
(`<product-repo>/pixel-wealth-quest/public/assets/`); pristine source
references live in `A-Wiki/game-assets/references/pixel-wealth-quest/`.

## Status (2026-06-03)

- **น้องซันเดย์ (player)** uses **direct directional frame paths** (crew-style, like
  Tide & Tally's `frames_256/`) via `src/phaser/playerFrames.ts` — NOT the
  manifest→bootstrap pipeline yet. Clean 8 rotations from PixelLab
  `create-character-v3` are indexed at
  `public/assets/character/nong-sunday/nong-sunday.frames.json`.
- **น้องซันเดย์ animations (Phase 1.5)** use direct normalized paths via
  `src/phaser/playerAnims.ts`: 51 south/front-facing frames in
  `public/assets/character/nong-sunday/anim_clean/` for idle, walk, run, sit,
  lie, eat, cry. Regenerate from raw PixelLab exports with:
  `python3 scripts/game/normalize_pwq_anims.py --pwq-root "$PWQ_ROOT"`.
- **House rooms (Phase 2a.1)** use baked room backdrops in
  `public/assets/room/`: `room-living-tv-iso-v001.png`,
  `room-office-iso-v001.png`, `room-bedroom-child-iso-v002.png` (bedroom), and
  `room-kitchen-iso-v001.png`. The bedroom is a child room with reading
  desk/lamp, toy shelf, teddy/soft doll, and no computer/TV. `RoomScene` uses
  invisible hotspot zones over these images plus translucent door markers from
  `src/data/room.seed.ts`.
- **Farm assets (Phase 2a)** live in
  `public/assets/farm/`: `farm-grass-tile-v001.png`,
  `farm-soil-plot-v001.png`, `crop-carrot-sprout-v001.png`,
  `crop-carrot-ready-v001.png`. Current `FarmScene` uses a green
  programmatic floor plus PixelLab plot/crop overlays. `farm-soil-plot-v001.png`
  is loaded as a candidate but not displayed because PixelLab returned a packed
  veggie sheet rather than a clean soil tile.

## Later — when to use the manifest pipeline

If PWQ outgrows direct frame paths (for example 8-dir walk/run sheets or multiple
characters), author manifests here and run the pipeline (see
`skills/claude-code/pixellab-asset-ingest/SKILL.md`). Use `PWQ_ROOT` instead of
hardcoded personal paths:

```bash
export PWQ_ROOT=/path/to/<product-repo>/pixel-wealth-quest
python3 scripts/game/write_phaser_manifest_template.py \
  game-assets/manifests/pixel-wealth-quest/nong-sunday.json \
  --asset-key character.player.nong-sunday.base.8dir.192x256 --action idle --action walk --tag player
# …fill provenance, then:
python3 scripts/game/report_phaser_asset_pack.py game-assets/manifests/pixel-wealth-quest \
  --root "$PWQ_ROOT/public" --check-files
python3 scripts/game/bootstrap_phaser_asset_pack.py game-assets/manifests/pixel-wealth-quest \
  --out-dir game-assets/generated/pixel-wealth-quest --root . \
  --module-name pwq_assets --scene-name PwqAssetScene --scene-key pwq-assets --module-import ./pwq_assets \
  --copy-to-project "$PWQ_ROOT/src/generated"
```
