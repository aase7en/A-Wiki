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
GLM-5.1 (live flagship) / GLM-4.7 / GLM-4.6 เป็น model เด่นด้าน **coding + reasoning + agentic**
ที่เข้าระบบ swarm ของ A-Wiki เป็น **direct route** (`try_zhipu_direct` ใน `scripts/swarm/delegate.sh`
+ generic `zai` entry ใน `providers.json`).
API เป็น **OpenAI-compatible** (`/chat/completions`, Bearer auth) จึง reuse parser `_extract_smart openai` ได้. [verified 2026-06-16]

## Endpoint (binding)

| Brand | Endpoint | ใช้กับ |
|-------|----------|--------|
| **Z.ai สากล** (default) | `https://api.z.ai/api/paas/v4/chat/completions` | ผู้ใช้นอกจีน (ไทย) — key จาก z.ai |
| Zhipu mainland | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | key ที่สมัครผ่าน Zhipu จีน |
| OpenRouter | `z-ai/glm-4.5-air:free` | ผ่าน `OPENROUTER_API_KEY` (free quota) |

A-Wiki default = **Z.ai สากล** + model `glm-5.1` (live flagship). [verified 2026-06-16 via GET /models]

### ความพร้อมใช้งานจริง (verified 2026-06-16)

GET `https://api.z.ai/api/paas/v4/models` คืน: `glm-5.1`, `glm-5`, `glm-4.7`, `glm-5-turbo`, `glm-4.6`, `glm-4.5`, `glm-4.5-air`.
**`glm-5.2` ไม่มีบน direct API** — เป็น alias เฉพาะแพ็กเกจ Codeplan (Kilo Code) เท่านั้น. สำหรับ direct harness ให้ใช้ `glm-5.1`.
delegate.sh seed = `glm-4.6` (คงไว้เพื่อ test-compat) — ปักจริงด้วย `ZHIPU_DIRECT_MODEL=glm-5.1` หรือ dashboard ⚙️.

## การใช้ใน A-Wiki

- **Key**: `ZHIPU_API_KEY` — มีอยู่แล้วใน `drive/.secrets` (verified 2026-06-16); env name ตรงกับ `delegate.sh` + `providers.json` zai.auth_env (reconciled — เดิม doc บางที่เขียน `ZAI_API_KEY` ผิด แก้หมดแล้ว). ดู [[secrets-policy]].
- **เปิดใช้**: `providers.json` zai = `enabled:true`, `auth_env:ZHIPU_API_KEY`, `default_model:glm-5.1`, ไม่มี `via:openrouter` → direct (no markup). disable ได้ด้วย `AWIKI_DISABLE_ZHIPU=1`.
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
