---
type: synthesis
title: "8-Bit Trading RPG Project Brief — Synthesis"
slug: synth-trading-rpg-project-brief-2026-05-30
tags: [trading-bot, gamification, rpg, ai-npc, reinforcement-learning]
sources: [trading-rpg-project-brief-2026-05-30]
created: 2026-05-30
updated: 2026-05-30
quality_score: 9/10
domain: ai-tools
---

# 8-Bit Trading RPG Project Brief — Synthesis

## Summary

[verified 2026-05-30] User brief proposes an 8-bit RPG layer for trading bots across crypto, forex, and stocks. The core idea is sound as a visualization and motivation system, but the safe architecture must separate trading execution from game state and AI NPC behavior.

## Key Points

- Use Phaser or PixiJS for lightweight canvas/WebGL pixel-art UI.
- Convert PnL, drawdown, and risk state into small WebSocket game events.
- Use LLM NPCs for dialogue/coaching only, not order execution.
- Keep reinforcement learning in offline sandbox/backtest until risk controls are proven.
- Reward disciplined trading behavior, not trade frequency.

## Relevance

Canonical project plan: [[synthesis/8-bit-trading-rpg-blueprint]]

Related runtime note: [[sources/freqtrade-pi5]]
