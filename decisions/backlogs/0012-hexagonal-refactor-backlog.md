---
type: backlog
adr: 0012
title: Hexagonal Architecture Refactor Backlog
created: 2026-07-29
updated: 2026-07-29
last_verified: 2026-07-29
source_inventory: 2026-07-29 explore-agent inventory
status: active
---

# Backlog — Hexagonal Architecture Refactor (ADR-0012)

รายการ code ทั้งหมดที่กระทบ ADR-0012. แต่ละรายการคือ slice หนึ่งของ strangler migration — ทำทีละ slice พร้อม **characterization test ก่อน extract** (ตาม `/hexagonal-architecture` Migration Playbook).

> **วิธีใช้**: เริ่มจาก Tier A → Tier B → Tier C (minimal). แต่ละ slice = 1 commit chunk ในรูป `chunk(0012-<tier><n>): <file>: <use-case> [next: ...]`

---

## Tier A — MUST refactor (binding runtime, monolithic-mixed)

**7 slices / 10 files / ~5,895 LOC** (ปรับปรุง 2026-08-01 — review พบว่า Hermes มี 6 ไฟล์ ไม่ใช่ 5). binding ตามตัวบทของ ADR.

> ⚠️ **Slice เริ่มต้นต้องเป็นไฟล์ที่มี test อยู่แล้ว** (ADR-0012 prerequisite G4) → **A4 ก่อน A1**. `mcp-wiki-server.py` (A1) ติด Iron-Law-protected Layer 3 slower track — ต้องผ่าน G1-G3 ก่อน.
>
> ✅ **2026-08-01: A4 DONE, G1 DONE, C6 DONE**. ✅ **2026-08-02: a-council UNBLOCK SHIP** (3 critical + 5 important resolved, 89 tests pass) — see Completed section below.

| ID | File | LOC | ทำอะไร | Ports ที่จะ extract (proposed) |
|---|---|---|---|---|
| **A1** ✅ **gates ผ่านหมด — พร้อมเริ่ม** | `scripts/mcp-wiki-server.py` | 736 | MCP server หลัก (7 tools + 3 resources), `sqlite3` FTS5 + subprocess + `raw/` I/O inline. **Iron-Law-protected Layer 3**. G1+G2+G3+G4 ผ่านหมด (2026-08-02) | `WikiSearchPort`, `RawStorePort`, `VectorIndexPort`, `RagQueryPort`, `SourceReadPort` |
| **A2** | `scripts/live-dashboard/server.py` | 1757 | HTTP daemon + 1100 LOC handler, capability mapping + model recommendation + file/SQLite state | `ModelPoolPort`, `CapabilityMapPort`, `DashboardStatePort`, `KeyStorePort` |
| **A3** | `scripts/live-dashboard/skills_service.py` | 1262 | skill registry serving + filesystem I/O | `SkillRegistryPort`, `FileSystemPort` |
| **A4** ✅ **DONE 2026-08-01** | `scripts/lib/neural_spine_mcp.py` | 625 | 18+ tool_* (memory/blackboard/task/focus/claims) + SQLite/JSON inline. **มี `test_neural_spine_mcp.py`** | `MemoryPort`, `TaskBoardPort` extracted (Blackboard/Claims/Focus/Routing pending sub-slice) |
| **A5** | `scripts/hermes/dual-mode-router.py` | 438 | mode-decision + provider JSON + subprocess | `ModeStatePort`, `ModelScoutPort` |
| **A6** | `scripts/hermes/persona-orchestrator.py` | 304 | orchestration + config I/O | `PersonaConfigPort` |
| **A7** | `scripts/hermes/{cost_budget_poller,subagent_alert_poller,pi5-brain-sync,provider-balance-check}.py` | ~773 (4 files) | poller loops + provider API + file state | `ProviderApiPort`, `CostBudgetStatePort`, `SyncPort` |

**ลำดับแนะนำ (หลัง review)**: ~~A4~~ ✅ → **A2/A3 → A5 → A6 → A7 → A1** (สุดท้าย). A4 done แล้ว; A1 ยัง slower track แต่ G1 (char-test prerequisite) ผ่านแล้ว เหลือ G2 (sqlite-vec install) + G3 (compat port spec) ก่อนเริ่ม

---

## Completed slices

### ✅ A4 — `scripts/lib/neural_spine_mcp.py` (2026-08-01)

- **Char-test gap closed**: 8 → 17 tests (found 2 bugs: `release_session` คืน int ไม่ใช่ bool; `AWIKI_CLAIMS_PATH` env ignored)
- **Ports extracted**: `MemoryPort`, `TaskBoardPort` (in `scripts/lib/ports/__init__.py`)
- **Adapters**: `JsonlMemoryAdapter` + `InMemoryMemoryAdapter` (memory), `JsonlTaskBoardAdapter` + `InMemoryTaskBoardAdapter` (taskboard) — 2 adapters per port = real seam (Cockburn)
- **Contract suite**: `tests/test_ports_contract.py` (9 tests, runs same assertions against every adapter — R10 mitigation)
- **Composition seam**: `_wire(memory=..., taskboard=...)` centralised in `neural_spine_mcp.py`
- **Caller contract frozen (R8)**: `TOOLS` dict + `set_paths()` signature unchanged → MCP server + every agent/hook keeps working, 0 regressions
- **Test result**: 26 tests green post-refactor (17 char + 9 contract)
- **Remaining for A4**: extract Blackboard/Claims/Focus/Routing ports (sub-slice A4b) — not blocking; current slice proved the pattern
- **Lesson recorded**: memory-ledger `outcome` tag `adr-0012,slice-a4`

### ✅ G1 — Characterization tests for `mcp-wiki-server.py` (2026-08-01)

- **Was**: 0 dedicated tests. **Now**: 21 char-tests in `tests/test_mcp_wiki_server.py`
- **Coverage**: 9 tools (registry shape + schema) + 3 resources + JSON-RPC dispatch (initialize/list_tools/call_tool/list_resources)
- **Char-test findings** (4): no `name` key in tool spec (dict key IS name); `RESOURCES` is dict not list; `handle_*` return result not envelope (envelope wrapped in `main()`); unknown tool raises MCPError not returns error dict
- **Mutation-verified**: dropping a tool from registry → test fails loud
- **Lesson recorded**: memory-ledger tag `g1,char-test,mcp-server`

### ✅ C6 — Hook enforce feasibility (2026-08-01)

- **Prototype**: `scripts/hooks/check_hexagonal_boundary.py` — narrow convention-based design (only checks `ports/` files for forbidden imports: `sqlite3`, `adapters`, `subprocess`, web frameworks)
- **Deliberately NOT attempted**: whole-codebase "does this mix domain+I/O?" static check — would over-fire on legacy Tier B
- **False-positive rate**: **0%** on real `ports/` files (well under C6 threshold of <20%)
- **Test suite**: `tests/test_check_hexagonal_boundary.py` (16 tests: scope filtering, true +/- , fail-open, FP measurement, subprocess invocation)
- **Verdict**: **C6 RESOLVED** — hook feasible, can promote from prototype to live once ADR Accepted
- **Lesson recorded**: memory-ledger tag `c6,hook,feasibility`

## Tier B — SHOULD refactor (large scripts with real domain + I/O)

~25 ไฟล์ / ~9,500 LOC. ไม่ binding ตามตัวบท แต่ควรทำตาม pattern.

### B.1 — Wiki index/search stack (highest leverage — refactor กลุ่มนี้ shrinks Tier A1)

| ID | File | LOC | Ports |
|---|---|---|---|
| **B1** | `scripts/gen-index.py` | 712 | `WikiOverviewPort`, `FtsIndexPort`, `GraphBuildPort` |
| **B2** | `scripts/build-wiki-graph.py` | 406 | `GraphBuildPort` |
| **B3** | `scripts/build-vec-index.py` | 273 | `VectorIndexPort` (multi-backend: sqlite-vec / turbovec) |
| **B4** | `scripts/wiki/query-rag.py` | 327 | `RagQueryPort` |
| **B5** | `scripts/wiki/ingest-source.py` | 493 | `IngestPipelinePort` (เรียก `batch/` — ใกล้เป็น hexagonal แล้ว) |

### B.2 — Wiki content pipeline

| ID | File | LOC | Ports |
|---|---|---|---|
| **B6** | `scripts/wiki/build-capability-map.py` | 610 | `CapabilityMapPort` |
| **B7** | `scripts/wiki/synthesize.py` | 473 | `SynthesisPort` |
| **B8** | `scripts/wiki/auto-synthesize.py` | 397 | `SynthesisPort` |
| **B9** | `scripts/wiki/scrape-advanced.py` | 418 | `ScraperPort` (multi-tier) |
| **B10** | `scripts/raw-to-synth.py` | 352 | `RawPipelinePort` |
| **B11** | `scripts/raw-to-source.py` | 304 | `RawPipelinePort` |

### B.3 — Pharmacy domain (standalone vertical)

| ID | File | LOC | Ports |
|---|---|---|---|
| **B12** | `scripts/pharmacy_lookup.py` | 831 | `PharmacySearchPort`, `ThaiNormalizePort`, `PharmacyDbPort` |
| **B13** | `scripts/build_pharmacy_db.py` | 148 | `PharmacyDbBuildPort` |
| **B14** | `scripts/compare_delivery.py` | 551 | `DeliveryComparePort` |
| **B15** | `scripts/build_order_sheet.py` | 380 | `OrderSheetPort` |

### B.4 — Skills registry / wiki operations

| ID | File | LOC | Ports |
|---|---|---|---|
| **B16** | `scripts/skills_registry/thai_guide.py` | 803 | `SkillGuidePort` |
| **B17** | `scripts/skills_registry/batch_thai.py` | 475 | `SkillGuidePort` |
| **B18** | `scripts/skills_registry/scan.py` | 311 | `SkillScanPort` |
| **B19** | `scripts/skills_registry/routing.py` | 273 | `RoutingPort` |
| **B20** | `scripts/skills_registry/quality_gate_thai.py` | 266 | `QualityGatePort` |
| **B21** | `scripts/regen-skill-surfaces.py` | 270 | `SurfaceGenPort` |
| **B22** | `scripts/new-skill.py` | 413 | `SkillScaffoldPort` |

### B.5 — Operations / utilities

| ID | File | LOC | Ports |
|---|---|---|---|
| **B23** | `scripts/check-privacy.py` | 483 | `PrivacyScanPort` |
| **B24** | `scripts/review-check.py` | 526 | `ReviewCheckPort` |
| **B25** | `scripts/agent-preflight.py` | 346 | `PreflightPort` |
| **B26** | `scripts/agents/agent_model_scan.py` | 360 | `ModelScanPort` |
| **B27** | `scripts/swarm/multiagent-proof.py` | 482 | `SwarmProofPort` |
| **B28** | `scripts/gen-domain-indexes.py` | 350 | `DomainIndexPort` |
| **B29** | `scripts/query-graph.py` | 277 | `GraphQueryPort` |
| **B30** | `scripts/model-scout-current.py` | 386 | `ModelScoutPort` (เรียกจาก A5) |

### B.6 — `scripts/lib/` leaf modules (partially separated — interface extraction only)

| ID | File | LOC | Ports |
|---|---|---|---|
| **B31** | `scripts/lib/agent_claims.py` | 270 | `ClaimStorePort` (ใช้ซ้ำกับ A4) |
| **B32** | `scripts/lib/a_flow_state.py` | 332 | `FlowStatePort` |
| **B33** | `scripts/lib/council_room.py` | 503 | `CouncilPort` |
| **B34** | `scripts/lib/skill_learning.py` | 524 | `SkillLearningPort` |
| **B35** | `scripts/lib/render_kilo_config.py` | 452 | `SurfaceGenPort` (ใช้ซ้ำกับ B21) |

**ลำดับแนะนำ**: B.1 ก่อน (leverage สูงสุด, shrink Tier A1) → B.2 → B.3 → B.4 → B.5 → B.6

---

## Tier C — ALREADY aligned / reference model (minimal work)

ไม่ต้อง refactor — ยกเป็น reference มาตรฐานของ ADR

| Path | หมายเหตุ |
|---|---|
| `scripts/batch/` (router.py, route.py, scout.py, state.py + `adapters/{anthropic,deepseek,gemini,openai,openrouter}_*.py`) | **canonical reference** — adapter pattern จริง. ทุก ADR-0012 refactor ควรเทียบกับสิ่งนี้ |
| `scripts/hermes/model-pool/` (4 files, ~893 LOC) | แยกเป็น pool package ที่ single-responsibility ชัด |
| `scripts/live-dashboard/{alerts,cost_history,eval_history,event_logger,subagent_stats,suite_editor,pipeline_graph}.py` (~1010 LOC) | แยก module ชัด; แค่ interface boundary lift เล็กน้อย |

---

## ข้อยกเว้น (exempt — ไม่เข้า backlog)

| Path | เหตุผล |
|---|---|
| `scripts/hooks/*` | hook = adapter อยู่แล้ว; cross-cutting enforcement ไม่ใช่ domain |
| `scripts/eval/*` (race, pipeline, ab_routing, dag, adaptive, run_subagent_eval) | test/eval harness ไม่ใช่ production runtime |
| `apps/personnel-checkin-grouping/` | Google Apps Script — runtime ต่าง platform |
| `*.sh`, `*.ps1`, `*.cmd` | shell glue |
| `< 50 LOC` one-offs | overhead มากกว่าคุณค่า |
| `SKILL.md`, `*.md` docs | declarative knowledge |
| `tests/fixtures/*` | test data |

---

## Estimasi (rough)

| Tier | Files | LOC | Effort estimate | ระยะเวลา (1 agent) |
|---|---|---|---|---|
| A | 10 | ~5,895 | สูง | 4-8 สัปดาห์ (slice ละ 1-3 วัน + characterization test + G1-G4 prerequisites ก่อนเริ่ม) |
| B | 30 | ~10,500 | กลาง | 8-16 สัปดาห์ |
| **รวม** | **40** | **~16,395** | — | **3-6 เดือน** |

> ⚠️ Estimasiนี้ **ไม่รวม** characterization test ที่ต้องเขียนก่อน extract (เพิ่ม ~30% เวลา และเพิ่มเวลามากขึ้นสำหรับ Tier A ไฟล์ที่ยังไม่มี test), **ไม่รวม** hook enforce prototype (`scripts/hooks/check_hexagonal_boundary.py`), และ **ไม่รวม** G1-G4 prerequisite gates (ซึ่ง ADR-0012 บังคับก่อน promote เป็น Accepted)

---

## Acceptance ของแต่ละ slice

Slice หนึ่งถือว่าเสร็จเมื่อ:
1. ✅ **Caller-contract frozen** (ADR-0012 R8 mitigation) — public CLI/stdio/JSON-RPC surface ถูกหุ้มเป็น compat port ก่อนแตะ internals
2. ✅ **Characterization test เขียนก่อน extract** — พิสูจน์ behavior เดิม (G4 บังคับ — slice ต้องเริ่มจากไฟล์ที่มี test อยู่แล้วก่อน; ถ้าไม่มี = เขียนก่อน)
3. ✅ Port interface ถูก extract ออกเป็นไฟล์/module แยก (ไม่ import external)
4. ✅ อย่างน้อย 2 adapter (prod + mock/test) สำหรับ port นั้น — **ผ่าน contract test suite เดียวกัน** (R10 mitigation)
5. ✅ Composition root รวม wiring ไว้ที่ entry point
6. ✅ Test ผ่านทั้ง prod adapter + mock adapter
7. ✅ **Iron Law #11 claim released** (R9 mitigation) — ปล่อย claim ทันทีที่ slice เสร็จ ไม่ lock ข้ามวัน
8. ✅ Commit chunk: `chunk(0012-<id>): <file>: <use-case> [next: <id>]`

> Slice ที่เป็น **A1 (mcp-wiki-server.py)** ต้องผ่าน gate เพิ่ม: G1 characterization test, G2 sqlite-vec install, G3 compat port spec — ก่อนเริ่ม`

---

## Handoff

- Backlog นี้คือ living document — อัปเดตเมื่อสถานะ slice เปลี่ยน
- เมื่อ slice เสร็จ → ย้ายบรรทัดนั้นไปด้านล่าง "Completed" section พร้อม commit hash
- Hook enforce (เมื่อสร้างแล้ว) จะ block Write/Edit ของ code ใหม่ที่ไม่มี port — ดู ADR-0012 §Decision
