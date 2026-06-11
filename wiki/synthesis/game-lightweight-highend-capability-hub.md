---
type: synthesis
title: "Game Lightweight High-end Capability Hub"
slug: game-lightweight-highend-capability-hub
tags: [capability-lane, game-design, phaser, pixellab, performance, sunday-invest-moon]
sources: [trading-rpg-project-brief-2026-05-30, pixellab-api-v2-openapi-2026-06-01]
created: 2026-06-12
updated: 2026-06-12
---

# Game Lightweight High-end Capability Hub

> [verified 2026-06-12] A-Wiki game lane targets high-end feeling with lightweight runtime: small web builds, curated pixel assets, deterministic logic tests, and no financial execution in the client.

## Route

| Step | Tooling | Done when |
|---|---|---|
| Concept | GDD/roadmap in A-Wiki | Core loop, constraints, and safety rules are explicit |
| Engine | Phaser + Vite + TypeScript | Logic is testable outside Phaser scenes |
| Assets | PixelLab manifest pipeline | Asset pack report is READY or warnings are documented |
| Verify | Unit tests, typecheck/build, browser/Playwright smoke | No blank canvas, no asset miss, no mobile overflow |

## Safety Gate

- Game client remains visualization/reward layer unless a separate backend contract is reviewed.
- PixelLab tokens and generated binary dumps stay out of tracked wiki files.
- Performance budget is part of scope: prefer sprite atlases/manifests and avoid heavy always-loaded assets.

## Related

- [[synthesis/8-bit-trading-rpg-blueprint]]
- [[synthesis/pixel-wealth-quest-gdd]]
- [[synthesis/sunday-invest-moon-roadmap]]
- [[synthesis/pixellab-asset-pipeline-for-trading-rpg]]
- [[synthesis/pixellab-phaser-asset-convention]]
- `docs/protocols/pwq-read-only-feed-contract.md`
