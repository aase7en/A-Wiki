# Agent Visual Event Protocol

> Purpose: แปลงงานของ AI agents, free/cheap delegates, และ trading-RPG bot crew ให้เป็น event เล็ก ๆ ที่ UI มองเห็นได้ โดยไม่ยก server/extension หนัก ๆ เข้ามาใน A-Wiki

## Decision

[verified 2026-06-01] A-Wiki จะรับ pattern จาก `pixel-agents-hq/pixel-agents` เฉพาะส่วนที่คุ้ม: **agent as character, normalized event stream, state machine, token/risk indicators, and external asset manifest discipline**. ไม่ copy VS Code extension, Claude-specific parser, หรือ Fastify runtime เข้ามาเป็น always-on layer.

## Why This Fits A-Wiki

| Gate | Answer |
|---|---|
| Capability gain | ทำให้ agent/trading bot/swarms ถูก inspect ได้เป็นภาพ ไม่ใช่ log ยาว ๆ |
| Lightweight | protocol + render-html surface เท่านั้น; no daemon, no DB, no always-loaded context |
| Cost-first | event มาจาก local hooks/scripts ก่อน; LLM ใช้เฉพาะสรุปข่าวหรือ critique |
| Cross-device | JSON ธรรมดา ใช้ path relative หรือ `drive/` สำหรับ asset หนัก |
| Public-safe | ห้ามส่ง secret, broker key, full private transcript, หรือ raw trade ledger เข้า artifact |

## Event Envelope

```json
{
  "event_id": "evt_20260601_001",
  "at": "2026-06-01T12:30:00+07:00",
  "source": "a-wiki",
  "lane_id": "risk-guard",
  "kind": "riskChanged",
  "label": "Breakout Gunner drawdown crossed watch threshold",
  "state": "waiting",
  "risk": "watch",
  "payload": {
    "bot_id": "breakout",
    "drawdown_pct": -1.4
  }
}
```

Required fields: `at`, `lane_id`, `kind`, `label`.

Allowed `kind` values for the first version:

| kind | Meaning | UI mapping |
|---|---|---|
| `sessionStart` | agent/bot lane became visible | spawn/appear |
| `toolStart` | tool/task began | active/typing/reading |
| `toolEnd` | tool/task finished | done tick |
| `turnEnd` | agent returned control | waiting/idle |
| `permissionRequest` | human approval needed | warning bubble |
| `riskChanged` | trading or process risk changed | lane color |
| `subagentStart` | delegate/subagent spawned | child crew |
| `subagentEnd` | delegate/subagent completed | despawn/merge |
| `tokenUsage` | context/cost changed | fuel bar |
| `error` | lane failed | danger state |

## Lane Schema

The render-html `agents` surface consumes a compact snapshot:

```json
{
  "mode": "trading-rpg-ops",
  "summary": {"active_agents": 4, "attention": 2, "blocked": 1, "risk": "watch"},
  "lanes": [
    {
      "id": "risk-guard",
      "title": "Risk Guard",
      "role": "drawdown and exposure gate",
      "state": "waiting",
      "risk": "watch",
      "token_ratio": 0.09,
      "events": [
        {"type": "riskChanged", "label": "Drawdown crossed watch threshold", "at": "12:28"}
      ]
    }
  ],
  "decisions": [
    {"id": "keep-paper-only", "label": "Keep paper-only mode", "default": true}
  ]
}
```

## State Mapping

| State | Meaning | Trading RPG interpretation |
|---|---|---|
| `idle` | nothing active | crew resting |
| `reading` | lookup/search/news digest | scout reading map |
| `typing` | writing/editing/building | crew working station |
| `reviewing` | critic/check phase | captain inspecting log |
| `waiting` | needs user or next event | speech bubble |
| `blocked` | cannot proceed safely | danger marker |

Risk values are `normal`, `watch`, `danger`. Rewards must never come from trade frequency alone; rewards should come from low drawdown, rule adherence, verified completion, or safe refusal.

## Do Not Send

- API keys, broker keys, withdrawal permissions, `.secrets`, cookies, auth headers
- full private Claude/Codex transcripts
- raw customer data or pharmacy data
- live order instructions from an LLM
- any event that allows the game client to execute a trade

## First Integration Target

Use the `agents` render surface:

```bash
python3 skills/render-html/scripts/render.py agents --in skills/render-html/fixtures/agents.json
```

For the trading RPG prototype, the next backend adapter should emit only these small events:

```json
{
  "bot_id": "grid",
  "status": "sailing",
  "pnl_pct": 1.25,
  "drawdown_pct": -0.6,
  "risk_state": "normal",
  "animation_hint": "idle",
  "timestamp": "2026-06-01T12:30:00+07:00"
}
```

The game client remains visualization-only. Trading execution, risk guard, and audit log stay outside the game UI.
