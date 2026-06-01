# PixelLab Asset Ingest Command Recipes

Use these commands from the A-Wiki repo root.

## Create a starter manifest

```bash
python3 scripts/game/write_phaser_manifest_template.py \
  game-assets/manifests/characters/captain-trader-01.json \
  --asset-key character.captain.captain-trader-01.base.8dir.64 \
  --action idle \
  --action walk \
  --tag captain \
  --tag hero
```

## Validate and inspect payload JSON

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests --root .
```

## Generate loader TS only

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests --root . \
  | python3 scripts/game/build_phaser_loader_ts.py - --module-name trading_rpg_assets
```

## Generate scene stub only

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests --root . > /tmp/trading_rpg_assets.json
python3 scripts/game/build_phaser_scene_stub_ts.py /tmp/trading_rpg_assets.json \
  --scene-name TradingRpgAssetScene \
  --scene-key trading-rpg-assets \
  --module-import ./trading_rpg_assets
```

## One-command bootstrap

```bash
python3 scripts/game/bootstrap_phaser_asset_pack.py game-assets/manifests \
  --out-dir game-assets/generated \
  --root . \
  --module-name trading_rpg_assets \
  --scene-name TradingRpgAssetScene \
  --scene-key trading-rpg-assets \
  --module-import ./trading_rpg_assets
```

## Copy generated files into a game project

```bash
python3 scripts/game/bootstrap_phaser_asset_pack.py game-assets/manifests \
  --out-dir game-assets/generated \
  --root . \
  --module-name trading_rpg_assets \
  --scene-name TradingRpgAssetScene \
  --scene-key trading-rpg-assets \
  --module-import ./trading_rpg_assets \
  --copy-to-project path/to/your-game/src/generated
```

Expected project files:

- `trading_rpg_assets.json`
- `trading_rpg_assets.ts`
- `TradingRpgAssetScene.ts`
- `README.md`
- `index.ts`
