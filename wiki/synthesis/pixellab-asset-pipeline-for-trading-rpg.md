---
type: synthesis
title: "PixelLab Asset Pipeline for Trading RPG"
tags: [pixellab, mcp, pixel-art, spritesheet, phaser, game-assets, trading-rpg]
sources: [pixellab-api-v2-openapi-2026-06-01, trading-rpg-project-brief-2026-05-30]
created: 2026-06-01
updated: 2026-06-01
---

# PixelLab Asset Pipeline for Trading RPG

## คำถามที่ตอบ

"จะใช้ PixelLab API/MCP สร้างตัวละคร เรือ ฉาก และ animation สำหรับ Anime Pirate Trading RPG + Bot Management Tycoon อย่างไร โดยเก็บ secret ให้ปลอดภัย?"

## สรุป

[verified 2026-06-01] PixelLab เหมาะเป็น **AI art generation layer** ของโปรเจกต์นี้ ส่วน Pixelorama/Aseprite เหมาะเป็น **cleanup layer** และ Phaser เป็น **runtime layer**. วิธีเร็วสุดคือใช้ PixelLab MCP ให้ agent สร้าง asset ขณะ coding แล้วใช้ Pixelorama เก็บขอบ/แก้เฟรมเสียก่อนนำเข้าเกม.

## Architecture

```text
Prompt / reference image
        |
        v
PixelLab MCP or API v2
        |
        v
Generated assets: character rotations, animations, objects, tiles
        |
        v
Pixelorama / Aseprite cleanup
        |
        v
repo assets/ or external asset folder
        |
        v
Phaser game scene + React HUD
```

## Asset workflow สำหรับ MVP

| Step | PixelLab tool/API | Output |
|---|---|---|
| Captain base | `create_character` / `/create-character-v3` | 8-direction captain sprite |
| Captain movement | `animate_character` / `/animate-character` | idle + walking spritesheets |
| Emotional states | `create_character_state` | profit, worried, tired, resting variants |
| NPC bot crew | `create_character` with different roles | Grid/DCA/MACD crew sprites |
| Ship props | `create_map_object` / `/map-objects` | cannon, barrel, mast, treasure chest |
| Deck tiles | `create_isometric_tile` / `/create-isometric-tile` | wood deck, rail, stairs, cabin tiles |
| Ocean/islands | `create_topdown_tileset` or image generation | ocean, beach, island pieces |
| HUD pieces | `/generate-ui-v2` | pixel buttons, status panels, icons |

## Prompt baseline

```text
Original anime pirate trading captain, retro 16-bit pixel art game sprite, strong readable silhouette, straw adventure hat, red captain shirt, blue shorts, yellow waist sash, sandals, confident expression, no copyrighted character, no logo, no text, transparent background, low top-down RPG view.
```

Negative prompt:

```text
One Piece, Luffy, existing anime character, copyrighted logo, watermark, realistic, 3D, blurry, painterly, cropped body, background scene, extra fingers
```

## Codex/agent workflow

1. Create character first and keep the returned `character_id`.
2. Queue only `idle` and `walking` animations first; do not spend credits on every emotion before scale and view are verified.
3. Download and inspect the sprite in Phaser at target size.
4. If readable, create state variants and NPC crew.
5. Use Pixelorama cleanup for edge noise, palette drift, and broken frames.
6. Store generated asset metadata in a local manifest, not inside prompt history.

## Secret handling

- Store `PIXELLAB_API_TOKEN` only in external `drive/.secrets`, local shell env, macOS Keychain, or the MCP client secret store.
- Do not put token in `.mcp.json`, repo files, wiki pages, screenshots, or chat.
- Codex should reference the token by env var:
  ```bash
  codex mcp add pixellab --url https://api.pixellab.ai/mcp --bearer-token-env-var PIXELLAB_API_TOKEN
  ```

## Decision

For the first playable prototype, use PixelLab MCP rather than raw REST API. Keep REST API v2 knowledge for later automation such as batch-generating 10 NPCs, polling jobs, downloading ZIPs, and organizing files into a Phaser asset folder.

## แหล่งข้อมูล

- [[sources/pixellab-api-v2-openapi-2026-06-01]]
- [[sources/trading-rpg-project-brief-2026-05-30]]
- PixelLab MCP docs: https://api.pixellab.ai/mcp/docs
- PixelLab API v2 LLM docs: https://api.pixellab.ai/v2/llms.txt
