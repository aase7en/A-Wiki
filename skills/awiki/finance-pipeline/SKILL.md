---
name: finance-pipeline
description: "End-to-end investment analysis pipeline that chains three specialized subagents: finance-data-fetcher (raw market data) → finance-analyst (technical/fundamental/sentiment thesis) → finance-debater (bull/bear challenge). The primary agent orchestrates the handoff, passing each stage's output as the next stage's input. One command produces a complete, self-critiqued investment report. Pattern: FinRobot Lead + pipeline + debate."
version: 1.0.0
domain: [trader, data]
lifecycle_phase: meta
category: pipeline
agents: [all, zcode]
---

# finance-pipeline

ไปป์ไลน์วิเคราะห์การลงทุนแบบครบวงจร — โยนงานจาก subagent หนึ่งไปยังอีกตัวแบบเป็นขั้นตอน 3 stage ตามรูปแบบ FinRobot (Lead Agent + pipeline + debate)

## เมื่อไหร่ใช้

ใช้เมื่อ user ขอ **การวิเคราะห์การลงทุนที่สมบูรณ์** สำหรับหุ้น/crypto/market:

- "วิเคราะห์ AAPL ให้หน่อย"
- "I want a full investment thesis on NVDA"
- "เปรียบเทียบ bull vs bear case ของ MSFT"

**ไม่ใช้** เมื่อ user ขอแค่ราคาปัจจุบัน (ใช้ `finance-data-fetcher` ตรงๆ) หรือแค่มุมมองเดียว

## Pipeline flow (3 stages)

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ finance-data-fetcher│ ──▶ │   finance-analyst   │ ──▶ │   finance-debater   │ ──▶ REPORT
│  (raw market data)  │     │ (thesis: tech+fund+ │     │ (bull/bear challenge│
│                     │     │  sentiment)         │     │  + verdict)         │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
   Bash, WebFetch              Read, WebSearch              Read
   deepseek-v4-flash           deepseek-v4-pro              sonnet
```

## Handoff contract

แต่ละ stage รับ output จาก stage ก่อนหน้าผ่าน context ของ primary agent (ไม่ใช่ auto-pass):

### Stage 1: `finance-data-fetcher`
**Input**: ticker/crypto symbol (e.g. "AAPL", "BTC")
**Output schema** (must include all):
```json
{
  "symbol": "AAPL",
  "price": <current>,
  "pe_ratio": <number|null>,
  "market_cap": <number>,
  "revenue_ttm": <number>,
  "net_income_ttm": <number>,
  "key_metrics": {"<name>": <value>}
}
```
**Primary agent action**: ส่ง prompt "Retrieve current price, P/E, market cap, latest revenue and net income for <SYMBOL>" เข้า `finance-data-fetcher` subagent

### Stage 2: `finance-analyst`
**Input**: Stage 1 output (raw data) + โจทย์วิเคราะห์
**Output schema** (must include all):
```json
{
  "thesis": "<1-paragraph investment thesis>",
  "technical": "<RSI/MACD/MA read>",
  "fundamental": "<valuation/growth/profitability read>",
  "sentiment": "<market sentiment read>",
  "rating": "<buy|hold|sell>"
}
```
**Primary agent action**: รวม Stage 1 data + ส่ง prompt "Analyze this data: <stage1_json>. Build a thesis with technical, fundamental, sentiment read + rating" เข้า `finance-analyst`

### Stage 3: `finance-debater`
**Input**: Stage 2 thesis
**Output schema** (must include all):
```json
{
  "bull_case": "<strongest bull argument>",
  "bear_case": "<strongest bear argument>",
  "key_risks": ["<risk1>", "<risk2>"],
  "verdict": "<weighed conclusion>"
}
```
**Primary agent action**: ส่ง prompt "Challenge this thesis: <stage2_json>. Give the strongest bull case, bear case, key risks, and a weighed verdict" เข้า `finance-debater`

## Final report

Primary agent รวม output ทั้ง 3 stage เป็น markdown report:
```markdown
# Investment Analysis: <SYMBOL>

## Data (Stage 1)
<stage1_json>

## Thesis (Stage 2)
<stage2_thesis>

## Challenge (Stage 3)
<stage3_verdict>

**Final rating**: <rating> with <bull/bear> lean
```

## Cost

- Stage 1: deepseek-v4-flash (free) — data fetch
- Stage 2: deepseek-v4-pro (cheap) — analysis
- Stage 3: sonnet (primary tier) — debate
- รวม ~3 subagent calls, sequential (ไม่ parallel — แต่ละ stage ต้องรอก่อนหน้า)

## ข้อควรระวัง

- **Iron Law #8 (bot trading)**: pipeline นี้เป็น analysis เท่านั้น ห้ามใช้ผลลัพธ์ execute order จริง
- **Rate-limit diversity**: 3 stages ใช้ 3 buckets ต่างกัน (deepseek-flash, deepseek-pro, anthropic) — ไม่ชน bucket
- ถ้า stage ไหน fail ให้ primary agent ลอง fallback ผ่าน `subagent_fallback.sh` แล้ว resume จาก stage นั้น (ไม่ restart ทั้ง pipeline)
