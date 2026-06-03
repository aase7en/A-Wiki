# Pixel Wealth Quest — asset manifests

Tracked recipes for PWQ assets. Binary PNGs live in the product
(`sunday-estate-webapp/pixel-wealth-quest/public/assets/`); pristine source
references live in `A-Wiki/game-assets/references/pixel-wealth-quest/`.

## Status (2026-06-03)

- **น้องซันเดย์ (player)** uses **direct directional frame paths** (crew-style, like
  Tide & Tally's `frames_256/`) via `src/phaser/playerFrames.ts` — NOT the
  manifest→bootstrap pipeline yet. 8 frames sliced from the rotation sheet; index
  at `public/assets/character/nong-sunday/nong-sunday.frames.json`.
- **Room furniture/floor** are programmatic placeholders (`src/phaser/textures.ts`)
  with stable keys — swap in PixelLab PNGs later with no code change.

## Phase 3 (animated character) — when to use the manifest pipeline

When น้องซันเดย์ gets animated actions (walk/run/sit/lie/eat/cry) via the PixelLab
`/create-character-v3` + `/animate-character` endpoints, author manifests here and
run the pipeline (see `skills/claude-code/pixellab-asset-ingest/SKILL.md`):

```bash
python3 scripts/game/write_phaser_manifest_template.py \
  game-assets/manifests/pixel-wealth-quest/nong-sunday.json \
  --asset-key character.player.nong-sunday.base.8dir.192x256 --action idle --action walk --tag player
# …fill provenance, then:
python3 scripts/game/report_phaser_asset_pack.py game-assets/manifests/pixel-wealth-quest \
  --root /Users/aase7en/Desktop/sunday-estate-webapp/pixel-wealth-quest/public --check-files
python3 scripts/game/bootstrap_phaser_asset_pack.py game-assets/manifests/pixel-wealth-quest \
  --out-dir game-assets/generated/pixel-wealth-quest --root . \
  --module-name pwq_assets --scene-name PwqAssetScene --scene-key pwq-assets --module-import ./pwq_assets \
  --copy-to-project /Users/aase7en/Desktop/sunday-estate-webapp/pixel-wealth-quest/src/generated
```
