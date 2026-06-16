---
type: entity
category: [company, model]
tags: [llm, provider, glm, zai, openrouter, cost-first]
sources: []
created: 2026-06-15
updated: 2026-06-15
last_verified: 2026-06-15
verify_tool: training
---

# Z.ai — GLM Series

**ประเภท**: LLM provider / model family
**สถานะ**: ใช้งานใน A-Wiki ผ่าน provider registry (`wiki/context/providers.json` → `zai`)

## ภาพรวม
Z.ai (เดิม Zhipu AI) ผู้พัฒนาโมเดลตระกูล **GLM**. ใน A-Wiki ใช้เป็นทางเลือก cost-first ที่ "ถูกและเก่ง" สำหรับ reasoning/coding. API เป็น **OpenAI-compatible** จึงเสียบเข้า generic adapter ได้ทันที [training]

## รุ่นปัจจุบัน (ใช้เป็นตัวอย่าง — ราคา volatile, ยืนยันด้วย scout ก่อนเลือก)
- **GLM-4.6** — flagship (จัดเป็น *primary* ใน catalog); reasoning/coding แข็ง context ยาว [training]
- **GLM-4.5-Air** — รุ่นถูก/เร็ว (จัดเป็น *secondary*); งานเบา latency-sensitive [training]

> หมายเหตุ: ไม่มีรุ่น "GLM-3.5" เป็น coding model ปัจจุบันของ Z.ai — ไลน์อัปคือ GLM-4.5 / GLM-4.6

## การเข้าถึงใน A-Wiki
- **ค่าเริ่มต้น (แนะนำ): ผ่าน OpenRouter** — model id `z-ai/glm-4.6` ใช้ `OPENROUTER_API_KEY` เดิม ไม่ต้องเพิ่ม key. registry entry `zai` มี `via: openrouter` + `enabled:false` → `resolve_transport()` route ผ่าน OpenRouter อัตโนมัติ
- **Direct (เมื่อต้องการ Coding Plan ถูกกว่า)**: ตั้ง `ZAI_API_KEY` (โหลดผ่าน `load-drive-keys.sh`) แล้ว `enabled:true` → `provider_registry.py` ยิงตรง `api.z.ai` (OpenAI-compatible). ตั้งได้ด้วย `scripts/add-provider.py --provider zai --env-name ZAI_API_KEY --key-stdin --enable`

## การใช้งานใน Swarm / Cost-First
- อยู่ใน 6 providers ของ registry; `delegate.sh` เรียกผ่าน `try_registry_model zai z-ai/glm-4.6` ใน tier 2 (reason/compare)
- `model_match.py` จัด GLM-4.6 เป็น primary (L4), GLM-4.5-Air เป็น secondary (L2) — เลือกตาม task→tier→price

## ความสัมพันธ์
- เข้าถึงผ่าน: [[openrouter]] (aggregator)
- แข่งขันกับ: DeepSeek, Qwen, Gemini Flash (cost-first reasoning tier)
- ใช้ร่วมกับ: provider registry, [[model-cost-switching]]

## แหล่งข้อมูล
- `wiki/context/providers.json` — registry entry `zai`
- `docs/protocols/model-switching.md` — Provider Registry section
