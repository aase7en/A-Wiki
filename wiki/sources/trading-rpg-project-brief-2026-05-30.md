---
type: source
title: "8-Bit Trading RPG Project Brief"
slug: trading-rpg-project-brief-2026-05-30
date_ingested: 2026-05-30
original_file: raw/trading-rpg-project-brief-2026-05-30.md
tags: [trading-bot, gamification, rpg, phaser, pixijs, websocket, llm-npc, reinforcement-learning]
quality: "[verified 2026-05-30]"
---

# 8-Bit Trading RPG Project Brief

**ประเภท**: conversation-derived project brief + verified repo shortlist  
**วันที่**: 2026-05-30  
**เกี่ยวข้องกับ**: [[synthesis/dream-projects]], [[sources/freqtrade-pi5]], [[entities/iot/raspberry-pi]], [[concepts/iot/dashboard-design]]

## ประเด็นหลัก

1. เป้าหมายคือเปลี่ยน trading dashboard ให้เป็น **8-bit investment RPG** ที่แสดงสถานะ portfolio, bot, และ strategy เป็น world/game state
2. ต้องแยก **Trading Engine** ออกจาก **Game State Server** อย่างเด็ดขาด เพื่อไม่ให้ animation, badge, หรือ dopamine loop ไปกระทบเงินจริง
3. MVP ควรเริ่มที่ paper trading/read-only portfolio ก่อน: data feed → PnL event → NPC state → character customization
4. LLM NPC ใช้สำหรับ dialogue/behavior เท่านั้น ไม่ควรให้ LLM ส่ง order ตรง
5. Reinforcement Learning ควรอยู่ใน lab/backtest เท่านั้นจนกว่าจะผ่าน reproducible backtest, slippage model, risk limits, และ human approval

## Repo / library shortlist ที่ verify แล้ว

| Area | Candidate | Verified signal | Use in project |
|---|---|---|---|
| Game framework | [Phaser](https://github.com/phaserjs/phaser) | HTML5 game framework, WebGL/Canvas, JS/TS, active ecosystem | ดีสุดสำหรับ MVP RPG scene, sprite, animation, input |
| Renderer | [PixiJS](https://github.com/pixijs/pixijs) | Lightweight 2D WebGL/WebGPU renderer | ใช้ถ้าต้องการ renderer เบากว่า game framework เต็ม |
| Multiplayer | [Colyseus](https://github.com/colyseus/colyseus) | Authoritative multiplayer framework for Node.js | Phase 3 community town / shared lobby |
| Crypto exchange API | [CCXT](https://github.com/ccxt/ccxt) | Unified crypto exchange API across many exchanges | Crypto connector; ไม่ครอบคลุม stock/forex broker ทั้งหมด |
| Financial chart | [Lightweight Charts](https://github.com/tradingview/lightweight-charts) | HTML5 Canvas financial charting library | Embed chart inside in-game trading terminal |
| LLM NPC example | [RezixDev/llm-game](https://github.com/RezixDev/llm-game) | Local LLM RPG example using LM Studio | Pattern for local dialogue loop; repo is small, treat as reference only |
| Local NPC example | [local-llm-npc](https://github.com/code-forge-temple/local-llm-npc) | Ollama/Gemma NPC, local/offline-ready pattern | Reference for endpoint-configurable NPC host |
| Trading RL env | [TradingGym](https://github.com/Yvictor/TradingGym) | RL/backtesting environment; no published releases found | Research reference only, not production trading engine |
| Game RL toolkit | [Unity ML-Agents](https://github.com/Unity-Technologies/ml-agents) | Mature Unity training toolkit for RL/imitation learning | Good for simulation research; too heavy for web MVP |

## Financial risk sources

- [CFTC forex advisory](https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/CustomerAdvisory_MustKnowForex.html) — retail forex involves dealer/counterparty, margin, and fraud risks
- [FINRA day trading](https://www.finra.org/investors/investing/investment-products/stocks/day-trading) — pattern day trading and margin requirements matter for stocks/options
- [FINRA auto-trading services](https://www.finra.org/investors/insights/auto-trading-unregistered-entities) — data/credential sharing and unregistered auto-trading risks
- [SEC crypto scam alert](https://www.sec.gov/oiea/investor-alert-5-ways-fraudsters-may-lure-victims-scams-involving-crypto-asset) — crypto popularity is used in investment scams

## ข้อโต้แย้ง / ข้อควรระวัง

- Gamification can improve engagement, but in trading it can also encourage overtrading. The product must reward discipline, risk control, and drawdown reduction more than raw trade frequency.
- "Profit unlocks cosmetics" is motivating but can create bad incentives. Safer unlock metrics: risk-adjusted return, max drawdown, paper-trading consistency, and rule compliance.
- CCXT is excellent for crypto, but forex/stocks need broker-specific compliance, market data licensing, and order-routing rules.
- Do not store broker/exchange secrets in git. Use local secret vault or deployment secrets only.

## หน้า Wiki ที่ได้รับการอัปเดต

- [[synthesis/8-bit-trading-rpg-blueprint]]
- [[synthesis/dream-projects]]
