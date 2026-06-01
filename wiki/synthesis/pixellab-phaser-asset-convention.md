---
type: synthesis
title: "PixelLab to Phaser Asset Convention"
slug: pixellab-phaser-asset-convention
tags: [pixellab, phaser, asset-pipeline, spritesheet, manifest, naming-convention, trading-rpg]
sources: [pixellab-api-v2-openapi-2026-06-01, trading-rpg-project-brief-2026-05-30]
created: 2026-06-01
updated: 2026-06-01
quality_score: 9/10
domain: ai-tools
---

# PixelLab to Phaser Asset Convention

## คำถามที่ตอบ

"ถ้า PixelLab สร้าง asset ได้แล้ว จะตั้งชื่อไฟล์ จัดโฟลเดอร์ เก็บ metadata และ import เข้า Phaser อย่างไรให้ scale ได้โดยไม่มั่ว?"

## สรุป

[verified 2026-06-01] วิธีที่คุ้มสุดคือแยก **binary asset** ออกจาก **asset manifest** อย่างชัดเจน: ไฟล์ PNG/ZIP/spritesheet อยู่ใน asset folder หรือ external storage ส่วน repo tracked knowledge เก็บเฉพาะ manifest, naming rules, tags, source ids, และ import contract สำหรับ Phaser. แนวนี้สอดคล้องกับ A-Wiki ที่เน้น lightweight repo + reusable metadata.

## Folder convention

ใช้โครงนี้เป็น default:

```text
game-assets/
  characters/
    captain/
      captain-trader-01/
        base/
        idle/
        walk/
        states/
        export/
  crew/
    grid-bot-01/
    dca-bot-01/
  objects/
    ship/
    props/
    ui/
  tiles/
    topdown/
    isometric/
    sidescroller/
  manifests/
    characters/
    objects/
    tiles/
```

### กฎแยกชั้น

- `game-assets/` อาจอยู่ใน repo ถ้าเบาพอ หรืออยู่ external storage ถ้าไฟล์เริ่มหนัก
- `manifests/` ควรเป็นไฟล์ tracked เพื่อให้ agent อ่าน, diff, และอ้างอิงได้
- binary exports จาก PixelLab เช่น ZIP, raw spritesheet, reference PNG ควรเก็บแยกจาก markdown knowledge pages

## Naming convention

### Asset key format

ใช้รูปแบบ:

```text
<domain>.<family>.<name>.<variant>.<action?>.<direction?>.<size?>
```

ตัวอย่าง:

```text
character.captain.captain-trader-01.base.8dir.64
character.captain.captain-trader-01.walk.south.64
character.captain.captain-trader-01.state.profit.64
crew.grid-bot.grid-bot-01.idle.east.64
object.ship.sloop-01.base.8dir.96
object.prop.cannon-01.state.damaged.64
tile.topdown.deck-oak-01.base.32
ui.panel.pnl-status-01.base.256x128
```

### Filename format

ใช้ kebab-case + stable suffix:

```text
captain-trader-01--base--8dir--64.png
captain-trader-01--walk--south--64.png
captain-trader-01--state-profit--64.png
sloop-01--anim-sail-idle--8dir--96.png
deck-oak-01--tileset-topdown--32.png
pnl-status-01--ui-panel--256x128.png
```

### กฎสำคัญ

- ชื่อ `name` เป็น stable identity; อย่า encode prompt ทั้งประโยคลง filename
- `variant` ใช้กับ branch สำคัญ เช่น `base`, `state-profit`, `state-worried`, `damaged`, `winter`
- `action` ใช้เฉพาะ asset ที่ animate จริง เช่น `idle`, `walk`, `fire`, `sail-idle`
- `direction` ใช้เมื่อ asset แยกเป็นไฟล์ต่อทิศ; ถ้าเป็น packed sheet ให้ระบุ `8dir` หรือ `4dir`

## Manifest contract

ใช้ JSON หรือ YAML ก็ได้ แต่ default แนะนำ JSON เพื่อให้ script/agent parse ง่าย

ตัวอย่าง character manifest:

```json
{
  "asset_key": "character.captain.captain-trader-01.base.8dir.64",
  "asset_type": "character",
  "name": "captain-trader-01",
  "variant": "base",
  "actions": ["idle", "walk"],
  "directions": 8,
  "frame_size": {"w": 64, "h": 64},
  "source": {
    "provider": "pixellab",
    "endpoint": "/create-character-v3",
    "resource_id": "character_id_here",
    "job_id": "background_job_id_here"
  },
  "files": {
    "zip": "characters/captain/captain-trader-01/export/captain-trader-01.zip",
    "spritesheets": {
      "idle": "characters/captain/captain-trader-01/idle/captain-trader-01--idle--8dir--64.png",
      "walk": "characters/captain/captain-trader-01/walk/captain-trader-01--walk--8dir--64.png"
    }
  },
  "phaser": {
    "texture_key": "character.captain.captain-trader-01",
    "atlas": false,
    "frame_config": {"frameWidth": 64, "frameHeight": 64},
    "animations": [
      {"key": "captain-trader-01:idle:south", "sheet": "idle"},
      {"key": "captain-trader-01:walk:south", "sheet": "walk"}
    ]
  },
  "tags": ["captain", "hero", "pirate", "trading-rpg"]
}
```

ตัวอย่าง object manifest:

```json
{
  "asset_key": "object.ship.sloop-01.base.8dir.96",
  "asset_type": "object",
  "name": "sloop-01",
  "variant": "base",
  "directions": 8,
  "frame_size": {"w": 96, "h": 96},
  "source": {
    "provider": "pixellab",
    "endpoint": "/create-8-direction-object",
    "resource_id": "object_id_here",
    "job_id": "background_job_id_here"
  },
  "review_flow": {
    "review_object": true,
    "promoted_from_select_frames": true
  },
  "tags": ["ship", "sea", "vehicle", "pirate"]
}
```

## Phaser import convention

### Loader rule

- ใช้ `texture_key` ที่ stable และไม่โยงกับ prompt text
- ชื่อ animation key ใช้ pattern:

```text
<name>:<action>:<direction>
```

ตัวอย่าง:

```text
captain-trader-01:idle:south
captain-trader-01:walk:east
sloop-01:sail-idle:northwest
```

### Example preload

```ts
this.load.spritesheet(
  "character.captain.captain-trader-01.idle",
  "game-assets/characters/captain/captain-trader-01/idle/captain-trader-01--idle--8dir--64.png",
  { frameWidth: 64, frameHeight: 64 }
);
```

### Example animation registration

```ts
this.anims.create({
  key: "captain-trader-01:walk:south",
  frames: this.anims.generateFrameNumbers("character.captain.captain-trader-01.walk", {
    start: 0,
    end: 5
  }),
  frameRate: 8,
  repeat: -1
});
```

## Mapping from PixelLab resource to local asset

| PixelLab output | Local action |
|---|---|
| `background_job_id` | เก็บใน manifest เพื่อ poll/retrace งานย้อนหลัง |
| `character_id` / `object_id` / `tile_id` | เก็บเป็น `resource_id` เพื่อ refresh, tag, export, or inspect |
| ZIP export | เก็บใน `export/` แล้วแตกไฟล์ที่ผ่านการคัดเลือกไปยัง folder ใช้งานจริง |
| review object | อย่า import เข้าเกมทันที; ต้องผ่าน `select-frames` หรือ `dismiss-review` ก่อน |
| prompt enhancement output | เก็บเฉพาะ final approved prompt ใน manifest หรือ companion note; ไม่ต้องเก็บ prompt history ทั้งหมด |

## Recommended workflow

### Character asset

1. Generate with `/create-character-v3`
2. Animate with `/animate-character`
3. Inspect `/characters/{character_id}`
4. Export `/characters/{character_id}/zip`
5. Put binary files under `game-assets/characters/...`
6. Write/update manifest in `game-assets/manifests/characters/...json`
7. Load through stable Phaser `texture_key` and animation keys

### Object asset

1. Generate with `/create-1-direction-object` or `/create-8-direction-object`
2. Poll `/objects/{object_id}`
3. If review object, curate via `/objects/{object_id}/select-frames`
4. Save accepted frames under `game-assets/objects/...`
5. Write manifest with `review_flow` and `tags`

### Tiles and UI

1. Generate tiles/UI using `/create-tileset`, `/create-isometric-tile`, `/create-tiles-pro`, or `/generate-ui-v2`
2. Normalize sizes and naming immediately after export
3. Keep tile manifest separate from character/object manifests because import rules differ

## Helper script

เริ่ม asset ใหม่เร็วสุด:

```bash
python3 scripts/game/write_phaser_manifest_template.py \
  game-assets/manifests/characters/captain-trader-01.json \
  --asset-key character.captain.captain-trader-01.base.8dir.64 \
  --action idle \
  --action walk \
  --tag captain \
  --tag hero
```

คำสั่งนี้จะสร้าง starter manifest ที่ infer `texture_key`, `frame_size`, sprite-sheet paths, และ animation keys ให้ก่อน แล้วค่อยเติม `source.endpoint`, `resource_id`, `job_id`, และ path จริงหลัง export จาก PixelLab

ใช้ `scripts/game/build_phaser_asset_manifest.py` เพื่อแปลง manifest JSON เป็น Phaser-friendly preload/animation payload:

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests --root .
```

ถ้าต้องการเจาะไฟล์เดียว:

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests/characters/captain-trader-01.json --root .
```

payload ที่ได้จะมี 3 ส่วน:

- `manifests`: สรุป manifest ที่อ่านเข้า
- `preload`: รายการ `spritesheet` พร้อม `key`, `path`, และ `frame_config`
- `animations`: รายการ animation config ที่ resolve `texture_key` แล้วจาก `phaser.texture_key` + `sheet`

**เจตนา:** ให้ฝั่งเกมหรือ generator script นำ JSON นี้ไปสร้าง `preload()` และ `anims.create()` ต่อได้ โดยไม่ต้อง parse manifest schema ซ้ำหลายรอบ

builder จะ validate ให้ก่อน generate:

- `asset_key` ต้องมี
- ถ้ามี spritesheet/animation ต้องมี `phaser.texture_key`
- spritesheet ต้องมี `frameWidth` และ `frameHeight` เป็น positive integer
- animation ที่ระบุ `sheet` ต้องชี้ sheet ที่มีจริงใน `files.spritesheets`
- ห้ามซ้ำ `asset_key`, preload key, หรือ animation key ใน pack เดียวกัน

ใช้ `scripts/game/build_phaser_loader_ts.py` เพื่อแปลง payload นี้ต่อเป็น TypeScript module:

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests --root . \
  | python3 scripts/game/build_phaser_loader_ts.py - --module-name trading_rpg_assets
```

output จะมี:

- `preloadPhaserAssets(scene)`
- `registerPhaserAnimations(scene)`
- `trading_rpg_assetsSummary`

แนวนี้เหมาะกับ v1 เพราะ deterministic, diff-able, และยังไม่บังคับโครงเกมเกินจำเป็น

ถ้าต้องการ one-command path ให้ใช้ `scripts/game/bootstrap_phaser_asset_pack.py`:

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

output จะได้ 3 ไฟล์พร้อมใช้:

- `game-assets/generated/trading_rpg_assets.json`
- `game-assets/generated/trading_rpg_assets.ts`
- `game-assets/generated/TradingRpgAssetScene.ts`
- `game-assets/generated/README.md`

ถ้าใส่ `--copy-to-project` เพิ่ม จะ copy generated files ไปยังโฟลเดอร์โปรเจกต์จริง และเขียน `index.ts` barrel ให้ด้วย

ถ้าต้องการแยกทีละขั้นเพื่อ debug หรือ customize ระหว่างทาง ค่อยใช้ manual chain ด้านล่าง:

```bash
python3 scripts/game/build_phaser_asset_manifest.py game-assets/manifests --root . > /tmp/trading_rpg_assets.json
python3 scripts/game/build_phaser_loader_ts.py /tmp/trading_rpg_assets.json --module-name trading_rpg_assets > trading_rpg_assets.ts
python3 scripts/game/build_phaser_scene_stub_ts.py /tmp/trading_rpg_assets.json \
  --scene-name TradingRpgAssetScene \
  --scene-key trading-rpg-assets \
  --module-import ./trading_rpg_assets > TradingRpgAssetScene.ts
```

scene stub ที่ได้จะ:

- `preload()` เรียก `preloadPhaserAssets(this)`
- `create()` เรียก `registerPhaserAnimations(this)`
- ถ้ามี asset/animation อย่างน้อย 1 ตัว จะวาง preview sprite กลางจอและเล่น animation แรกให้อัตโนมัติ

แนวนี้เหมาะกับการ bootstrap vertical slice ของเกมก่อน แล้วค่อย refactor scene structure ภายหลัง

## Anti-patterns

- เอา prompt text ยาวๆ ไปเป็น filename
- เอา `job_id` มาเป็น texture key หลัก
- import review objects เข้าเกมก่อนคัดเฟรม
- เก็บ binary asset metadata ไว้ใน chat history แทน manifest
- ปล่อยให้ artist/agent แต่ละรอบตั้งชื่อเองโดยไม่มี stable naming rule

## Decision

สำหรับ A-Wiki และ Trading RPG prototype ให้ใช้ **stable asset key + binary folder + tracked manifest** เป็นมาตรฐาน. เมื่อ asset เริ่มโต ให้ใช้ helper script generate preload/animation payload จาก manifest แทนการ hand-code ทุกไฟล์.

## Related pages

- [[synthesis/pixellab-asset-pipeline-for-trading-rpg]]
- [[synthesis/pixellab-api-endpoint-matrix]]
- [[synthesis/8-bit-trading-rpg-blueprint]]
