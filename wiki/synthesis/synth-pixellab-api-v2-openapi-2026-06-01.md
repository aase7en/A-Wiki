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

[verified 2026-06-01] PixelLab API v2 exposes REST endpoints for pixel-art image generation, character rotations, animation, editing, tilesets, map objects, and prompt enhancement. For agent-driven workflow, PixelLab MCP is the preferred interface; API v2 is better for custom batch scripts.

## Key Points

- API auth uses Bearer token; token must stay in `drive/.secrets` or local env, never tracked wiki files.
- Character endpoints support 4/8 directions, persistent character records, details, ZIP export, tags, and animation jobs.
- Animation endpoints include text animation, skeleton animation, interpolation, animation edit, and outfit transfer.
- Game environment endpoints cover top-down tilesets, sidescroller tilesets, isometric tiles, and map objects.
- Long-running operations use background job polling via `/background-jobs/{job_id}`.

## Relevance

Canonical local workflow: [[synthesis/pixellab-asset-pipeline-for-trading-rpg]]

Setup runbook: `docs/runbooks/pixellab-mcp-codex-setup.md`
