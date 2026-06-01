---
type: synthesis
title: "8-Bit Trading RPG Blueprint"
tags: [trading-bot, game-design, gamification, webapp, ai-npc, reinforcement-learning, finance-safety]
sources: [trading-rpg-project-brief-2026-05-30, freqtrade-pi5]
created: 2026-05-30
updated: 2026-05-30
---

# 8-Bit Trading RPG Blueprint

## คำถามที่ตอบ

"จะออกแบบเว็บบอทเทรด Forex/Crypto/หุ้น ให้เป็น 8-Bit Investment RPG ได้อย่างไร โดยยังเบา เร็ว ปลอดภัย และใช้ต่อยอด A-Wiki ได้?"

## สรุป

[verified 2026-05-30] แนวคิดนี้มี potential สูง แต่ต้องจัด priority ใหม่: **เกมเป็น visualization/reward layer เท่านั้น ส่วนการส่ง order ต้องอยู่ใน trading engine ที่มี risk guard แยกต่างหาก**. MVP ที่ถูกต้องคือ paper trading + read-only portfolio + NPC state ก่อน ไม่ใช่ live bot ที่ใช้เงินจริง.

หลักชนะของโปรเจกต์นี้คือเอาความน่าเบื่อของ dashboard มาแปลงเป็น **behavioral feedback**: bot ที่กำไรไม่ได้แค่โชว์ตัวเลข แต่เปลี่ยนท่าทาง/ชุด/บทสนทนา; bot ที่ drawdown ไม่ใช่ตัวเลขแดงเฉยๆ แต่เป็น NPC ที่เหนื่อยและบังคับให้ผู้ใช้กลับไปดู risk.

## คำศัพท์สำคัญ

| คำ | แปลไทย | ความหมาย | รากศัพท์ |
|---|---|---|---|
| Gamification | การทำให้เหมือนเกม | เอากลไกเกม เช่น level, reward, progress, quest มาใช้กับงานจริง | game + -ification หมายถึง "ทำให้กลายเป็น" |
| Dopamine Loop | วงจรกระตุ้นโดพามีน | loop ของ cue → action → reward ที่ทำให้คนอยากกลับมาใช้งาน | dopamine เป็นสารสื่อประสาท; loop คือวงรอบ |
| PnL | กำไรขาดทุน (Profit and Loss) | ผลรวมกำไร/ขาดทุนของ bot, strategy, หรือ portfolio | accounting/finance term |
| Drawdown | เงินทุนลดลงจากจุดสูงสุด | วัดความเสียหายระหว่างทาง แม้สุดท้ายอาจยังมีกำไร | draw + down = ถูกดึงลง |
| AUM | สินทรัพย์ภายใต้การจัดการ | มูลค่ารวมของเงิน/สินทรัพย์ที่ระบบหรือผู้ใช้ดูแล | Assets Under Management |

## Architecture ที่ควรล็อกตั้งแต่วันแรก

```
[Market/Broker APIs]
        |
        v
[Data Ingest + Normalizer] ----> [Market Data Store]
        |
        v
[Trading Engine] ---- order ----> [Broker/Exchange]
        |
        +----> [Risk Guard / Kill Switch]
        |
        v
[Portfolio + Trade Ledger]
        |
        v
[Game Event Adapter] -- small events --> [Game State Server / WebSocket]
        |
        v
[8-Bit Client: Phaser or PixiJS Canvas]
```

**กฎเหล็กของ architecture**:

- Game client ห้ามมี broker key, exchange key, หรือ permission ส่ง order
- LLM NPC ห้ามเรียก trading API ตรง ให้ส่งได้แค่ `dialogue_intent` หรือ `coach_suggestion`
- Trading engine ต้องมี kill switch, max position, max daily loss, max order count, and no-withdrawal API key policy
- Game event ต้องเป็นข้อมูลเบา เช่น `bot_id`, `status`, `pnl_pct`, `risk_state`, `animation_hint`
- Reward ต้องผูกกับ risk-adjusted behavior ไม่ใช่แค่ "เทรดบ่อย" หรือ "กำไรวันเดียว"

## Stack decision

| Layer | Recommended MVP | Later | เหตุผล |
|---|---|---|---|
| Game client | Phaser | PixiJS if custom renderer needed | Phaser ให้ scene/sprite/input ครบกว่า เหมาะ MVP |
| Chart | Lightweight Charts | TradingView paid/embedded options | เบาและเป็น Canvas เหมาะกับ in-game terminal |
| Crypto connector | Freqtrade or CCXT | Hummingbot for market making | ใช้ paper/dry-run ก่อน; CCXT ยืดหยุ่นแต่ต้องเขียน risk เอง |
| Forex/stocks connector | Read-only first, broker-specific later | Alpaca/IBKR/etc. after legal review | stock/forex มี compliance และ market-data licensing มากกว่า crypto |
| Realtime | WebSocket | Colyseus when multiplayer exists | MVP ยังไม่ต้องใช้ multiplayer server |
| LLM NPC | Local/Ollama or hosted LLM via adapter | personality memory per bot | ใช้สร้างบทพูด ไม่ใช้ตัดสินใจส่ง order |
| RL | Offline backtest notebook | isolated research service | ห้ามปนกับ live order path ในช่วงแรก |

## Gameplay loop ที่ปลอดภัยกว่า

| User desire | Unsafe version | Safer RPG mechanic |
|---|---|---|
| อยากเห็นพอร์ตโต | unlock จากกำไรดิบ | unlock จาก profit + drawdown ต่ำ + ทำตาม rule |
| อยากให้บอทฉลาด | RL ส่ง order จริง | RL เสนอ strategy candidate ใน sandbox |
| อยากมี dopamine | reward ทุกครั้งที่เปิด order | reward เมื่อปิดวันตาม risk plan |
| อยากอวด community | leaderboard กำไรสูงสุด | leaderboard Sharpe-like score, consistency, max drawdown |
| อยากให้ NPC มีชีวิต | LLM เชียร์ให้เทรด | LLM เป็น coach เตือน risk และอธิบายเหตุผล |

## MVP 30 วัน

### Week 1: Paper PnL Adapter

- เลือก crypto ก่อน เพราะ tooling พร้อมกว่า stock/forex
- ใช้ Freqtrade dry-run หรือ CCXT sandbox/read-only ถ้า exchange รองรับ
- สร้าง event schema:

```json
{
  "bot_id": "grid_btc_001",
  "asset_class": "crypto",
  "pnl_pct": 1.25,
  "drawdown_pct": -0.6,
  "risk_state": "normal",
  "timestamp": "2026-05-30T00:00:00Z"
}
```

### Week 2: Single Office Scene

- Phaser scene เดียว: office + player + one bot NPC
- Bot NPC state: `idle`, `winning`, `drawdown`, `paused`
- No marketplace, no multiplayer, no real-money unlock

### Week 3: Character + Cosmetics

- Sprite layer: hair, face, body, outfit, held item
- Unlock rules use simulated Wealth Points
- Add in-game terminal using Lightweight Charts with historical paper PnL

### Week 4: Risk Coach NPC

- LLM NPC generates short Thai dialogue from structured state only
- Prompt receives no API keys, no full trade ledger unless sanitized
- Add risk summary: daily max loss, exposure, bot pause reason

## Non-negotiable safety checklist

- [ ] Paper trading default
- [ ] Read-only portfolio mode before any order execution
- [ ] API keys: trade-only, no withdrawal
- [ ] Exchange/broker secrets outside git and outside game client
- [ ] Kill switch at engine layer, not UI layer
- [ ] Audit log for every proposed and executed order
- [ ] Backtest includes fee, slippage, spread, and failed order simulation
- [ ] Gamification rewards discipline, not trade frequency
- [ ] Legal/compliance review before public users or copy-trading features

## A-Wiki capability extension

This page adds a reusable "financial game product" pattern to A-Wiki:

- [[sources/trading-rpg-project-brief-2026-05-30]] keeps the original product idea and verified repo shortlist
- [[sources/freqtrade-pi5]] remains the practical crypto bot runtime reference
- [[synthesis/pixellab-asset-pipeline-for-trading-rpg]] defines the AI asset pipeline for characters, NPC bot crew, ship deck props, and animations
- [[synthesis/pixellab-phaser-asset-convention]] defines naming, folder, manifest, and Phaser import rules so generated assets stay manageable
- [[entities/iot/raspberry-pi]] keeps the hardware capacity warning for Pi 5
- [[concepts/iot/dashboard-design]] supplies dashboard UX principles that can be remapped into RPG feedback

## Decision

Start with **Crypto-only paper trading + Phaser office scene + one NPC bot**. Do not build Forex/stocks execution, multiplayer, marketplace, or live RL in Phase 1.

## Phase 1 realized — *Tide & Tally* (anime-pirate edition)

[verified 2026-05-31] Phase 1 prototype shipped as an isolated local game sub-project (React + Vite + TypeScript + Phaser + Zustand; separate from backend, nginx, and docker surfaces). It **honors and tightens** this blueprint:

- **Theme reframed** from "office/Wall-Street" → **original anime-pirate adventure** (ship deck = dashboard, crew NPC = bot, seas = markets). No existing anime IP — all names invented (working title *Tide & Tally — Corsairs of the Storm Sea*).
- **Even safer than the blueprint MVP**: Phase 1 is **mock-data only** — no Freqtrade/CCXT connector, no keys, no order path, no Buy/Sell. The only inbound shape is the blueprint's light `MarketEvent` (`botId, status, pnlPct, drawdownPct, riskState, animationHint, timestamp`).
- **Vertical slice**: 1 Phaser ship-deck scene + parallax ocean + **3 crew bots** (not 1) + click→status panel + mock WebSocket driving PnL/mood live + captain progression.
- **Discipline-based rewards** implemented as designed: EXP + Discipline Points accrue only from low-drawdown, non-danger ticks; **0 from raw profit or trade frequency**. Unlock conditions structurally cannot gate on profit.
- **NPC coaching** = canned Thai lines keyed to mood (no live LLM yet, cost-first); explains risk, never executes.
- **Deferred to Phase 2**: Three.js rotating globe (Phase 1 uses a 2D region map; 4 other seas locked), the four other markets' data, live LLM dialogue, any real connector/execution, multiplayer.
- **Verified**: 81 passing tests (test-first for all pure logic), `tsc -b` clean, `vite build` green, dev server renders the live slice (crew walk, mood/PnL update in real time, status panel, region map, upgrade tree).

## แหล่งข้อมูล

- [[sources/trading-rpg-project-brief-2026-05-30]]
- [[sources/freqtrade-pi5]]
- Phaser: https://github.com/phaserjs/phaser
- PixiJS: https://github.com/pixijs/pixijs
- Colyseus: https://github.com/colyseus/colyseus
- CCXT: https://github.com/ccxt/ccxt
- Lightweight Charts: https://github.com/tradingview/lightweight-charts
- TradingGym: https://github.com/Yvictor/TradingGym
- Unity ML-Agents: https://github.com/Unity-Technologies/ml-agents
- CFTC forex advisory: https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/CustomerAdvisory_MustKnowForex.html
- FINRA auto-trading warning: https://www.finra.org/investors/insights/auto-trading-unregistered-entities
