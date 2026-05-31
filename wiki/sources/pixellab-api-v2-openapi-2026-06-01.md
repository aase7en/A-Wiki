---
type: source
title: "PixelLab API v2 OpenAPI Spec"
slug: pixellab-api-v2-openapi-2026-06-01
date_ingested: 2026-06-01
original_file: raw/pixellab-api-v2-openapi-2026-06-01.json
tags: [pixellab, pixel-art, game-assets, mcp, api, spritesheet, animation, tileset]
quality: "[verified 2026-06-01]"
---

# PixelLab API v2 OpenAPI Spec

**ประเภท**: OpenAPI JSON specification  
**แหล่ง**: PixelLab API export from user download  
**เกี่ยวข้องกับ**: [[synthesis/pixellab-asset-pipeline-for-trading-rpg]], [[synthesis/8-bit-trading-rpg-blueprint]]

## ประเด็นหลัก

1. PixelLab API v2 เป็น REST API สำหรับสร้าง AI pixel art assets: images, UI, animations, tilesets, isometric tiles, map objects, persistent characters, and character animations.
2. Authentication ใช้ Bearer token: `Authorization: Bearer <token>`. ห้ามเก็บ token ใน git, wiki, prompt, หรือ chat.
3. API มี LLM-friendly docs ที่ `https://api.pixellab.ai/v2/llms.txt` สำหรับให้ AI assistant อ่าน endpoint summary.
4. มี Python client official-style workflow ผ่าน package `pixellab`:
   ```bash
   pip install pixellab
   ```
5. งานหนักหลาย endpoint เป็น background job: submit request -> ได้ `background_job_id` -> poll `GET /v2/background-jobs/{job_id}` -> download/use results.

## Endpoint groups ที่สำคัญ

| Group | Endpoint examples | ใช้กับ Trading RPG |
|---|---|---|
| Image generation | `/generate-image-v2`, `/create-image-pixen`, `/create-image-pixflux`, `/create-image-bitforge` | concept sprite, item icon, UI art |
| Image editing | `/remove-background`, `/resize`, `/edit-image`, `/inpaint` | clean sprite, scale pixel art, remove background |
| Animation | `/animate-with-text-v3`, `/animate-with-skeleton`, `/interpolation-v2`, `/edit-animation-v2` | idle/walk/celebrate/tired frames |
| Character | `/create-character-with-4-directions`, `/create-character-with-8-directions`, `/create-character-v3`, `/animate-character`, `/create-character-state` | captain, NPC bot crew, outfit/state variants |
| Tiles and objects | `/create-isometric-tile`, `/create-tileset`, `/create-tiles-pro`, `/map-objects` | ship deck, barrels, cannon, mast, ocean/island tiles |
| Management | `/characters`, `/objects`, `/background-jobs/{job_id}`, `/balance` | list/check assets, poll jobs, monitor credit |
| Prompt enhancement | `/enhance-pixen-prompt`, `/enhance-character-v3-prompt`, `/enhance-animation-v3-prompt` | turn short art direction into model-friendly prompts |

## Character system notes

- 4-direction characters: south, west, east, north.
- 8-direction characters: south, south-east, east, north-east, north, north-west, west, south-west.
- `create-character-v3` can rotate a south-facing reference image into 8 directions.
- Character assets are persistent and can be listed, exported as ZIP, animated, and tagged.
- Pro modes cost more generations but are better when style consistency matters.

## ข้อควรระวัง

- PixelLab API v2 and PixelLab MCP are different interfaces over related capabilities. MCP is easier for Codex/Claude/Cline; REST API is better for batch automation and custom scripts.
- Some URLs returned by the service are public asset URLs. Treat generated assets as project artifacts, but never expose account tokens.
- For commercially usable output, avoid prompts that copy One Piece/Luffy or other copyrighted characters directly. Use original anime pirate language instead.

## หน้า Wiki ที่ได้รับการอัปเดต

- [[synthesis/pixellab-asset-pipeline-for-trading-rpg]]
- [[synthesis/8-bit-trading-rpg-blueprint]]
