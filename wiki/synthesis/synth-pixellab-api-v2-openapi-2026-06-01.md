---
type: synthesis
title: "PixelLab API v2 OpenAPI Spec — Synthesis"
slug: synth-pixellab-api-v2-openapi-2026-06-01
tags: [pixellab, api, mcp, pixel-art, game-assets, animation, spritesheet]
sources: [pixellab-api-v2-openapi-2026-06-01]
created: 2026-06-01
updated: 2026-06-01
quality_score: 9/10
domain: ai-tools
---

# PixelLab API v2 OpenAPI Spec — Synthesis

## Summary

[verified 2026-06-01] PixelLab API v2 exposes REST endpoints for pixel-art image generation, style transfer, rotation, animation, editing, tilesets, persistent characters, persistent objects, and prompt enhancement. For agent-driven workflow, PixelLab MCP is the preferred interface; API v2 is better for custom batch scripts, polling jobs, and asset lifecycle management.

## Key Points

- API auth uses Bearer token; token must stay in `drive/.secrets` or local env, never tracked wiki files.
- Character endpoints support 4/8 directions, persistent character records, details, ZIP export, tags, and animation jobs.
- Object endpoints form their own lifecycle: create -> inspect -> animate/state-edit -> review/promote -> tag/manage.
- Animation endpoints include text animation, skeleton animation, interpolation, animation edit, and outfit transfer.
- Game environment endpoints cover top-down tilesets, sidescroller tilesets, isometric tiles, and map objects.
- Long-running operations use background job polling via `/background-jobs/{job_id}`.

## Operational guidance

### Variant policy

- Use base/sync endpoints (`/create-image-pixflux`, `/create-image-pixen`, `/edit-image`, `/inpaint`) for rapid ideation, one-off repairs, and low-cost prompt iteration.
- Use `v2` or `v3` endpoints when you need higher consistency across multiple images or frames and can tolerate async polling.
- Prefer `v3` for character creation and text-driven animation when the workflow starts from one approved reference and must stay readable in all directions.
- Use `pro` when the style target is already clear and regenerate cost is more expensive than the extra credits. Typical examples: batch NPCs, UI sets, or outfit-consistent animation runs.

### Style and image conversion workflow

1. If the source is not yet pixel art, start with `/image-to-pixelart`.
2. If style consistency is the goal, use `/generate-with-style-v2`.
3. Normalize asset size with `/resize` and cut the background with `/remove-background`.
4. Fix local defects with `/edit-image`, `/edit-images-v2`, `/inpaint`, or `/inpaint-v3`.

**Practical rule:** use sync endpoints when you are still choosing the look, and switch to async `v2`/`v3`/`pro` once the art direction is locked.

### Object workflow

1. Create the prop via `/create-1-direction-object` or `/create-8-direction-object`.
2. Poll `/objects/{object_id}` until processing completes.
3. Add motion with `/objects/{object_id}/animations` or create alternate states via `/objects/{object_id}/states`.
4. If the result is a review object, keep selected frames with `/objects/{object_id}/select-frames` or discard the branch with `/objects/{object_id}/dismiss-review`.
5. Classify reusable outputs using `/objects/{object_id}/tags`, then monitor the library through `/objects`.

**Interpretation:** `/map-objects` is for transparent prop generation, while `/objects/*` is the persistent object-management layer after generation exists.

### Review/select frame flow

- A review object is a temporary staging result where PixelLab gives candidate frames that are not yet fully accepted into the persistent object library.
- Use `/objects/{object_id}/select-frames` when only some candidates are good and deserve promotion to completed objects.
- Use `/objects/{object_id}/dismiss-review` when the whole review branch is noise, off-style, or not worth keeping.
- After promotion, treat the saved outputs like normal managed objects: inspect, animate, state-edit, and tag them.

### Character creation and export flow

1. Expand a weak prompt with `/enhance-character-v3-prompt`.
2. Create the base using `/create-character-v3` or `/create-character-pro`.
3. Add action loops through `/animate-character` or `/characters/animations`.
4. Create emotion or outfit branches with `/create-character-state`.
5. Inspect `/characters/{character_id}`, tag `/characters/{character_id}/tags`, then export `/characters/{character_id}/zip`.

### Async map/tiles flow

1. Submit creation via `/tilesets`, `/create-tileset`, `/tilesets-sidescroller`, `/create-tileset-sidescroller`, `/create-isometric-tile`, or `/create-tiles-pro`.
2. Poll `/background-jobs/{job_id}` while the job is processing.
3. Fetch the resource payload from `/tilesets/{tileset_id}`, `/isometric-tiles/{tile_id}`, or `/tiles-pro/{tile_id}` when applicable.

## Decision shortcuts

- Want to turn a photo or painted concept into pixel art: `/image-to-pixelart`
- Want to keep the same approved style across new outputs: `/generate-with-style-v2`
- Want to inspect, export, or tag a persistent character: `/characters/{character_id}`, `/characters/{character_id}/zip`, `/characters/{character_id}/tags`
- Want to manage review outputs from object generation: `/objects/{object_id}`, `/objects/{object_id}/select-frames`, `/objects/{object_id}/dismiss-review`
- Want the complete endpoint inventory instead of the summary: [[synthesis/pixellab-api-endpoint-matrix]]

## Relevance

Canonical local workflow: [[synthesis/pixellab-asset-pipeline-for-trading-rpg]]

Setup runbook: `docs/runbooks/pixellab-mcp-codex-setup.md`

Full endpoint catalog: [[synthesis/pixellab-api-endpoint-matrix]]
