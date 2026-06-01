---
name: pixellab-asset-ingest
description: Use when ingesting PixelLab-generated pixel art assets into A-Wiki, creating or updating Phaser asset manifests, validating PixelLab asset packs, generating Phaser loader/scene TypeScript, or copying generated asset registry files into a game project. Covers PixelLab REST/MCP outputs, character/object/tile/UI assets, spritesheets, review-object curation, and A-Wiki Trading RPG asset workflow.
---

# PixelLab Asset Ingest

Use this skill to turn PixelLab output into durable A-Wiki + Phaser project artifacts.

Core idea: binary images/ZIPs live in `game-assets/` or external storage; tracked repo files keep manifests, generated loader code, and wiki knowledge. Never store `PIXELLAB_API_TOKEN` or other secrets in manifests, wiki pages, generated TS, screenshots, or chat.

## Workflow

### 1. Establish the asset state

Identify which state the user is in:

| State | Action |
|---|---|
| No asset yet, just an idea | Create a manifest template first; use PixelLab MCP/API only if available and explicitly needed |
| PixelLab generated a character/object/tile/UI asset | Capture provider endpoint, `resource_id`, `job_id`, final file paths, frame size, actions, directions |
| Object is in review state | Curate via `select-frames`/`dismiss-review` before importing into Phaser |
| Manifest exists | Validate and bootstrap the Phaser asset pack |
| Game project path is known | Use `--copy-to-project` to mirror generated files into the project source tree |

Read detailed commands only when needed: `references/command-recipes.md`.

### 2. Create or update the manifest

For a new asset, prefer the starter template script:

```bash
python3 scripts/game/write_phaser_manifest_template.py \
  game-assets/manifests/characters/captain-trader-01.json \
  --asset-key character.captain.captain-trader-01.base.8dir.64 \
  --action idle \
  --action walk \
  --tag captain
```

Then fill the manifest with real PixelLab provenance:

- `source.endpoint`
- `source.resource_id`
- `source.job_id`
- actual spritesheet paths
- correct `frame_size` and `phaser.frame_config`
- tags useful for search and asset grouping

If the source asset is a review object, do not import it directly. Keep only promoted frames in the manifest.

### 3. Validate before generating code

Run the asset-pack reporter before writing project files:

```bash
python3 scripts/game/report_phaser_asset_pack.py game-assets/manifests --root . --check-files
```

Use the report to decide whether the pack is ready:

| Status | Meaning |
|---|---|
| `READY` | No blocking issues; safe to generate/bootstrap |
| `BLOCKED` | Fix issues before copying generated files into a game project |
| warnings only | Usually acceptable for drafts, but report them clearly |

Use `--format json` for automation and `--fail-on-issues` for CI/pre-handoff checks.

Then run the manifest builder when you need the Phaser payload:

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests --root .
```

Validation catches:

- missing `asset_key`
- missing `phaser.texture_key`
- invalid `frameWidth` / `frameHeight`
- animations pointing at missing sheets
- duplicate asset, preload, or animation keys

Use `--no-validate` only for debugging broken packs, not for final output.

### 4. Bootstrap Phaser files

For the normal path, use one command:

```bash
python3 scripts/game/bootstrap_phaser_asset_pack.py game-assets/manifests \
  --out-dir game-assets/generated \
  --root . \
  --module-name trading_rpg_assets \
  --scene-name TradingRpgAssetScene \
  --scene-key trading-rpg-assets \
  --module-import ./trading_rpg_assets
```

Output:

- `trading_rpg_assets.json`
- `trading_rpg_assets.ts`
- `TradingRpgAssetScene.ts`
- `README.md`

If the user gives a real game project path, add:

```bash
--copy-to-project path/to/your-game/src/generated
```

This also writes `index.ts` barrel exports in the target folder.

### 5. Update A-Wiki knowledge

For significant asset pipeline changes, update:

- `wiki/synthesis/pixellab-phaser-asset-convention.md`
- `wiki/synthesis/pixellab-asset-pipeline-for-trading-rpg.md` if workflow changed
- `log.md`
- `wiki/context/session-memory.md` only for durable decisions or next-session carryover

Then run:

```bash
python3 scripts/gen-index.py
python3 scripts/gen-index.py --check
```

## Guardrails

- Do not edit `raw/`.
- Do not commit large binary PixelLab exports unless the repo policy explicitly allows it.
- Do not put secret tokens in generated manifests or TS.
- Do not use job IDs as Phaser texture keys; use stable semantic keys.
- Do not import review objects into the game before curation.
- If the asset pack affects a real game project, use a temp output or `--copy-to-project` target and report exactly what files were written.

## Quick checks

Use these before reporting done:

```bash
python3 -m pytest tests/test_build_phaser_asset_manifest.py \
  tests/test_report_phaser_asset_pack.py \
  tests/test_build_phaser_loader_ts.py \
  tests/test_build_phaser_scene_stub_ts.py \
  tests/test_bootstrap_phaser_asset_pack.py \
  tests/test_write_phaser_manifest_template.py -q
```

For retrieval health:

```bash
python3 scripts/wiki/search-wiki.py "pixellab phaser manifest"
python3 scripts/wiki/search-wiki.py "manifest template bootstrap copy to project"
```
