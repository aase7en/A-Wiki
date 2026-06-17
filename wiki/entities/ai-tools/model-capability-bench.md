---
type: entity
category: concept
tags: [benchmark, leaderboard, swe-bench, terminal-bench, nl2repobench, model-routing, capability, cost-first]
sources: []
created: 2026-06-15
updated: 2026-06-15
---

# Model Capability Benchmarks (Routing)

## ภาพรวม

ระบบจัดลำดับ model ตาม **ความสามารถ (capability)** ก่อนแจกจ่ายงานใน swarm — อ้างอิง
leaderboard สาธารณะ 3 แหล่ง แล้วเลือก model ที่เหมาะกับชนิดงาน **ภายใต้ cost-first**
(ไม่ escalate ไป paid). เพิ่มเข้า A-Wiki 2026-06-15. [verified 2026-06-15]

## แหล่ง leaderboard

| Benchmark | URL | วัดอะไร | map → task |
|-----------|-----|---------|-----------|
| **SWE-bench** | https://www.swebench.com/ | resolve GitHub issue (coding) | (เก็บ badge; รอ task `code`) |
| **Terminal-Bench 2.0** | https://www.tbench.ai/leaderboard/terminal-bench/2.0 | agentic / terminal task | `scan` |
| **NL2RepoBench** | https://github.com/multimodal-art-projection/NL2RepoBench | NL → repo-scale code | (เก็บ badge; รอ task `repo`) |
| **Aider Polyglot** | https://aider.chat/docs/leaderboards/ | edit/refactor หลายภาษา | (เพิ่ม 2026-06-16; เสริม `code`) |
| **LiveCodeBench** | https://livecodebench.github.io/ | competitive programming + contamination control | (เพิ่ม 2026-06-16; reasoning + code) |
| reasoning | (สังเคราะห์) | เหตุผลทั่วไป | `reason`/`compare` |
| speed | (สังเคราะห์) | latency/throughput | `search`/`lookup`/`summarize` |

> **ความซื่อสัตย์เรื่อง live fetch** (verified 2026-06-16): leaderboard coding ไม่มี JSON feed แบบ GET ตรง (`aider.chat/assets/leaderboard.json` = 404; swebench.com / tbench.ai เป็น JS page). `model-capability-scout.py` ลงทะเบียน source ไว้ทั้ง 5 และลอง parse markdown-table (`_parse_markdown_scores`); หน้าที่ไม่ machine-readable กลายเป็น `unparseable` → ใช้ค่า committed `[training]` (offline-first). ตัวเลข `[verified]` ต้องรอ dedicated parser หรือ curated manual update.

## สถาปัตยกรรม (offline-first)

1. **Scorecard committed** — `wiki/context/model-capability-scores.json`: durable floor,
   keyed by **family** + `match` substrings (กัน volatile model ids), คะแนน 0-100 ต่อ
   dimension + `source_urls` + `as_of` + `confidence`. ค่าเริ่มต้น `[training]` รอ refresh.
2. **Scout best-effort** — `scripts/model-capability-scout.py` (`--offline-ok`): โหลด
   committed เป็น base → fetch 3 source (GitHub raw ที่ parse ได้) → overlay เฉพาะ
   dimension ที่สำเร็จ → `.tmp/model-capability-cache.json`. **ห้าม raise** — network/parse
   fail → degrade เป็น committed, exit 0. ไม่ใช่ hard dependency.
3. **Ranking** — `delegate.sh::_rank_by_capability()`: sort key `(cost_rank ASC, score DESC)`.

## Cost-first guarantee

`cost_rank` เป็น **primary** sort key (0=free, 1=cheap paid direct, 2=premium) →
**paid ห้ามแซง free** ทางคณิตศาสตร์. capability (secondary key) สลับลำดับเฉพาะภายใน
cost class เดียวกัน. จัดลำดับเฉพาะ model ที่ **enabled + มี key** (ผู้ใช้คุมผ่าน dashboard).
ไม่เพิ่ม task_type ใหม่ (เลี่ยง blast radius) — infer dimension จาก task_type เดิม.

## Degradation (safe fallback)

cache หาย → ใช้ committed scorecard · ทั้งคู่หาย → คืนลำดับ cost-first เดิม · bad JSON → echo เดิม ·
empty enabled set → fallthrough ปกติ · ไม่มี key → engine return 1 ก่อน. ไม่มีกรณีไหน crash.

## เชื่อมโยง

- Routing engine: `scripts/swarm/delegate.sh` · Dashboard: [[live-dashboard]]
- Model ใหม่ที่ใช้ระบบนี้: [[zai-glm]]
- Protocol: `docs/protocols/model-switching.md` (capability-aware routing section)
- เกี่ยวข้อง: model-scout-current.py (volatile pricing scout — pattern เดียวกัน)
