---
type: entity
category: [company, model]
tags: [llm, provider, glm, zai, zhipu, cost-first, direct-api, openai-compatible, swarm, delegate]
sources: []
created: 2026-06-15
updated: 2026-06-18
last_verified: 2026-06-16
verify_tool: training
---

# Z.ai — GLM Series

**ประเภท**: LLM provider / model family
**สถานะ**: ใช้งานใน A-Wiki แบบ **direct API** (`enabled:true`) ผ่าน provider registry (`wiki/context/providers.json` → `zai`)

## ภาพรวม
Z.ai (Zhipu AI) ผู้พัฒนาโมเดลตระกูล **GLM** (General Language Model). ใน A-Wiki ใช้เป็นทางเลือก cost-first ที่ "ถูกและเก่ง" สำหรับ reasoning/coding/agentic. API เป็น **OpenAI-compatible** (`/chat/completions`, Bearer auth) จึงเสียบเข้า generic adapter ได้ทันที (reuse parser `_extract_smart openai`). ใช้ **direct route** (`api.z.ai`) เพื่อเลี่ยง markup ของ OpenRouter [verified 2026-06-16]

## Endpoint (binding)

| Brand | Endpoint | ใช้กับ |
|-------|----------|--------|
| **Z.ai สากล** (default) | `https://api.z.ai/api/paas/v4/chat/completions` | ผู้ใช้นอกจีน (ไทย) — key จาก z.ai |
| Zhipu mainland | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | key ที่สมัครผ่าน Zhipu จีน |
| OpenRouter (fallback) | `z-ai/glm-4.5-air:free` | ผ่าน `OPENROUTER_API_KEY` (free quota) |

A-Wiki default = **Z.ai สากล** + model `glm-5.1` (live flagship). [verified 2026-06-16 via GET /models]

## รุ่นที่ direct API เปิดให้ (GET /models, ตรวจ 2026-06-16)
`glm-5.1` · `glm-5` · `glm-4.7` · `glm-5-turbo` · `glm-4.6` · `glm-4.5` · `glm-4.5-air`
- **GLM-5.1** — flagship (จัดเป็น *primary*); reasoning/coding แข็ง [verified 2026-06-16]
- **glm-4.5-air** — รุ่นถูก/เร็ว (จัดเป็น *secondary*); งานเบา latency-sensitive
- หมายเหตุ: `glm-5.2` **ไม่** เปิดบน direct API (เป็น Codeplan-only alias ของ Kilo Code) — ใช้ `glm-5.1` สำหรับ harness call

## การเข้าถึงใน A-Wiki
- **ค่าเริ่มต้น: Direct** — ตั้ง `ZHIPU_API_KEY` (โหลดผ่าน `load-drive-keys.sh` จาก `drive/.secrets`) → `provider_registry.py` / `delegate.sh::try_zhipu_direct` ยิงตรง `api.z.ai/api/paas/v4/chat/completions`. env name ตรงกับ `delegate.sh` + `providers.json` zai.auth_env (เดิม doc บางที่เขียน `ZAI_API_KEY` ผิด แก้หมดแล้ว)
- **เลือก/เปลี่ยนรุ่น**: ผ่าน Live Dashboard ⚙️ (`/api/models`) หรือ `ZHIPU_DIRECT_MODEL=glm-5.1`
- **เพิ่ม key**: `scripts/add-provider.py --provider zai --env-name ZHIPU_API_KEY --key-stdin --enable` (key ลง `drive/.secrets` เท่านั้น)
- **env override**: `ZHIPU_DIRECT_MODEL`, `ZHIPU_API_URL`, `AWIKI_DISABLE_ZHIPU=1`
- **Fallback ผ่าน OpenRouter**: roster ยังเก็บ `z-ai/glm-4.6` ไว้เป็น fallback + test-compat

## การใช้งานใน Swarm / Cost-First
- GLM เป็น paid direct → อยู่ใน TIER 2 (reason/compare) + TIER 3 (scan) **หลัง** free routes (Gemini direct, free OpenRouter) เสมอ
- `delegate.sh::try_zhipu_direct` (gated ด้วย `_provider_enabled ZHIPU`) เรียกใน tier 2; capability ranking ดัน GLM ขึ้นภายใน cost class เดียวกันเมื่อ reasoning score สูง (80) แต่ไม่แซง free
- `model_match.py` จัด GLM-5.1 เป็น primary, glm-4.5-air เป็น secondary — เลือกตาม task→tier→price

## Capability (scorecard estimate)
`reasoning 80 · swe_bench 68 · terminal_bench 50 · nl2repobench 45 · speed 70` [training, pending live-leaderboard refresh] — ดู [[model-capability-bench]]

## ความสัมพันธ์
- เข้าถึงผ่าน: direct `api.z.ai` (หลัก) · [[openrouter-api]] (fallback)
- แข่งขันกับ: DeepSeek, Qwen, Gemini Flash (cost-first reasoning tier)
- ใช้ร่วมกับ: provider registry, [[live-dashboard]] ⚙️, [[synth-claude-model-cost-switching-strategy-2026-06]]

## แหล่งข้อมูล
- `wiki/context/providers.json` — registry entry `zai`
- `docs/protocols/model-switching.md` — Provider Registry section
- Engine + ranking: `scripts/swarm/delegate.sh` (`try_zhipu_direct`, `_rank_by_capability`)
