---
type: entity
category: software
tags: [llm, glm, zhipu, z-ai, coding-model, openai-compatible, swarm, delegate]
sources: []
created: 2026-06-15
updated: 2026-06-15
---

# GLM / Z.ai (Zhipu)

## ภาพรวม

**GLM** (General Language Model) เป็นตระกูล LLM จาก **Zhipu AI** — แบรนด์สากลคือ **Z.ai**.
GLM-4.6 / GLM-5.2 เป็น model เด่นด้าน **coding + reasoning + agentic** เพิ่มเข้าระบบ swarm
ของ A-Wiki เป็น direct route ตัวใหม่ (`try_zhipu_direct` ใน `scripts/swarm/delegate.sh`).
API เป็น **OpenAI-compatible** (`/chat/completions`, Bearer auth) จึง reuse parser `_extract_smart openai` ได้. [verified 2026-06-15]

## Endpoint (binding)

| Brand | Endpoint | ใช้กับ |
|-------|----------|--------|
| **Z.ai สากล** (default) | `https://api.z.ai/api/paas/v4/chat/completions` | ผู้ใช้นอกจีน (ไทย) — key จาก z.ai |
| Zhipu mainland | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | key ที่สมัครผ่าน Zhipu จีน |
| OpenRouter | `z-ai/glm-4.5-air:free` | ผ่าน `OPENROUTER_API_KEY` (free quota) |

A-Wiki default = **Z.ai สากล** + model `glm-4.6` (แก้เป็น `glm-5.2` ได้ใน dashboard ⚙️).

## การใช้ใน A-Wiki

- **Key**: `ZHIPU_API_KEY` — ใส่ผ่าน Live Dashboard → ⚙️ Settings → API Keys (เก็บ `.tmp/` + `drive/.secrets`, ไม่ขึ้น git). ดู [[secrets-policy]].
- **เปิดใช้**: ship แบบ disabled by default → เปิด toggle GLM ใน dashboard + ใส่ key + Save.
- **Routing (cost-first)**: GLM เป็น paid direct → อยู่ใน TIER 2 (reason/compare) + TIER 3 (scan)
  **หลัง** free routes (Gemini direct, free OpenRouter) เสมอ. capability ranking ดัน GLM
  ขึ้นภายใน cost class เดียวกันเมื่อ reasoning score สูง (80) แต่ไม่แซง free.
- **env override**: `ZHIPU_DIRECT_MODEL`, `ZHIPU_API_URL`, `AWIKI_DISABLE_ZHIPU=1`.

## Capability (scorecard estimate)

`reasoning 80 · swe_bench 68 · terminal_bench 50 · nl2repobench 45 · speed 70` [training, pending live-leaderboard refresh] — ดู [[model-capability-bench]].

## เชื่อมโยง

- Engine + ranking: `scripts/swarm/delegate.sh` (`try_zhipu_direct`, `_rank_by_capability`)
- Dashboard config: `scripts/live-dashboard/` ([[live-dashboard]] README)
- Routing policy: [[model-capability-bench]] · `docs/protocols/model-switching.md`
