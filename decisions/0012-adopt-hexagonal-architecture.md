---
adr: 0012
title: Adopt Hexagonal Architecture (Ports & Adapters) as binding pattern for A-Wiki services
status: Proposed
date: 2026-07-29
updated: 2026-08-01
tags: [architecture, hexagonal, ports-and-adapters, refactor, binding-policy, adr]
related_journal: []
supersedes: []
superseded_by: []
---

# ADR-0012: Adopt Hexagonal Architecture (Ports & Adapters) as binding pattern for A-Wiki services

## Status

**Proposed 2026-07-29 → พร้อม promote Accepted 2026-08-02** — ทุก prerequisite gate ผ่าน (G1+G2+G3+G4), C6 ผ่าน, a-council UNBLOCK SHIP

**ความคืบหน้า**:
- 2026-08-01 review: เพิ่ม risks R6-R14, Validation section, caller-contract freeze, measurable revisit conditions
- 2026-08-02 a-council: ⛔ → ✅ UNBLOCK SHIP (3 critical + 5 important resolved, 89 tests)
- 2026-08-02 G2+G3: sqlite-vec+fastembed installed (540 embeddings built), MCP compat port spec frozen
- **พร้อม promote** — รอ user decision

## Context

### ที่มา
- วันที่ 2026-07-29 มีการสังเคราะห์ความรู้จาก [Cockburn — Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture) เป็น `wiki/concepts/ai-tools/hexagonal-architecture.md` และพบว่า A-Wiki เองมี skill `/hexagonal-architecture` (comprehensive, multi-language) อยู่แล้ว แต่ **ไม่เคย binding** เป็น policy
- Inventory พบว่า code การผลิตหลักของ A-Wiki มีลักษณะ **monolithic-mixed**: domain logic ปนกับ I/O (SQLite, subprocess, file, HTTP) โดย **ไม่มี abstraction ของ domain I/O ports** (สำหรับ FTS5, sqlite-vec, raw/, drive/, external API) — *มีเฉพาะ `scripts/batch/adapters/Adapter` ABC สำหรับ LLM providers เท่านั้น* (verified `scripts/batch/adapters/__init__.py:47`)

### ปัญหาที่ต้องแก้
1. **Testability ต่ำ** — ไม่สามารถ run MCP server / dashboard แบบ headless ได้; ทดสอบต้องเชื่อม I/O จริงเสมอ
2. **Replaceability ต่ำ** — สลับ backend (เช่น sqlite-vec → turbovec, FTS5 → external search) ต้องแก้หลายไฟล์
3. **Parallel development ติดขัด** — เปลี่ยน transport (HTTP, stdio, Telegram) กระทบ core logic
4. **A-Wiki's own Iron Laws ละเมิดโดยนัย** — Iron Law #1 "no production code without a failing test first" ทำได้ยาก เพราะ code ผูก I/O; Iron Law #5 "core (AGENTS.md, registry) ต้องไม่รั่วเข้า outside" แต่ enforcement ไม่ได้กินลึกถึงตัว code

### ข้อจำกัด (จาก grill)
- **ขอบเขต binding**: A-Wiki repo ทั้งหมด
- **ข้อยกเว้น**: script, hook, fixture, SKILL.md, eval harness (ไม่บังคับ — จะ over-engineer)
- **Migration strategy**: ใช้ทันทีสำหรับ code ใหม่ + วางแผน refactor ทั้งหมดใน backlog

### Inventory ของ code ที่กระทบ (วัดจาก LOC + I/O + domain logic)

| Tier | รายละเอียด | ขนาด |
|---|---|---|
| **A — ต้อง refactor (binding services/servers)** | `mcp-wiki-server.py` (736), `live-dashboard/server.py` (1757) + `skills_service.py` (1262), `lib/neural_spine_mcp.py` (625), Hermes daemons 6 ไฟล์ (dual-mode-router 438 + persona-orchestrator 304 + 4 pollers ~773 = ~1,515 LOC) | **7 slices / 10 files / ~5,895 LOC** |
| **B — ควร refactor (large scripts ที่มี domain+I/O จริง)** | wiki index/search stack (`gen-index.py`, `build-wiki-graph.py`, `build-vec-index.py`, `wiki/query-rag.py`, `wiki/ingest-source.py`), `pharmacy_lookup.py` (831), ฯลฯ | **~30 ไฟล์ / ~10,500 LOC** |
| **C — สอดคล้องแล้ว / reference model** | `scripts/batch/` package (มี `Adapter` ABC จริงที่ `adapters/__init__.py:47`), `scripts/hermes/model-pool/`, `live-dashboard/` leaf modules | minimal work |

**รวม**: ~40 production files / ~16,500 LOC ต้อง extract port — โดย ~5,895 LOC (10 files) เป็น binding ตามตัวบท

> ℹ️ ตัวเลขปรับปรุง 2026-08-01 หลัง review (ก่อนหน้านี้อ้าง "~8 ไฟล์ ~6,000 LOC" ซึ่ง undercount Hermes daemons จาก 6 → 5)

> ดู backlog เต็มที่ `decisions/backlogs/0012-hexagonal-refactor-backlog.md`

## Decision

**เราจะ adopt Hexagonal Architecture (Ports & Adapters) เป็น binding architectural pattern สำหรับทุก service/app/MCP-server/daemon ใน A-Wiki repo ที่มี I/O ผสมกับ domain logic** เพราะเป็นทางออกที่ตรงกับจุดประสงค์ของ Cockburn (testability + replaceability) และเสริมกับ Iron Laws ที่มีอยู่

### บทบัญญัติ (binding ทันทีที่ ADR เป็น Accepted)

1. **Code ใหม่/ที่แก้** ที่เข้าเกณฑ์ (service/app/MCP-server/daemon + I/O + domain logic) **ต้อง** แยก port (interface) ออกจาก adapter (implementation) ตาม skill `/hexagonal-architecture`
2. **ทิศทาง dependency**: adapter → application/domain เท่านั้น; domain ไม่ import adapter/external
3. **Port ตั้งชื่อตามจุดประสงค์** (`WikiSearchPort`, `ModelPoolPort`) ไม่ใช่เทคโนโลยี (`SqliteVecPort`)
4. **Composition root รวมที่เดียว** — wiring ของ adapter ต้องอยู่ใน entry point เดียว (`main()`, container)
5. **Test adapter + mock adapter** ต้องมีสำหรับทุก port ที่ binding — ไม่งั้น Iron Law #1 ไม่ผ่าน

### ข้อยกเว้น (ไม่บังคับ)

| ประเภท | เหตุผล |
|---|---|
| `scripts/hooks/*` | hook = adapter อยู่แล้ว และเป็น cross-cutting enforcement ไม่ใช่ domain |
| `scripts/eval/*` | test/eval harness ไม่ใช่ production runtime |
| `scripts/*.sh`, `*.ps1`, `*.cmd` | shell glue |
| ไฟล์ < 50 บรรทัดที่เป็น one-off | overhead มากกว่าคุณค่า |
| `SKILL.md`, `*.md` docs | declarative knowledge ไม่ใช่ code |
| `tests/fixtures/*` | test data |
| `apps/personnel-checkin-grouping/` | Google Apps Script — runtime ต่างคนละ platform |

### Migration strategy

- **Code ใหม่**: บังคับใช้ทันทีเมื่อ ADR Accepted
- **Code เก่า**: วางแผน refactor ทั้งหมดใน backlog — เริ่มจาก **Tier A → Tier B** ตามลำดับ (ทำ Tier A ก่อนเพราะเป็น binding runtime จริง)
- **Pattern**: strangler + slice-by-slice + characterization test ก่อน extract (ตาม skill `/hexagonal-architecture` Migration Playbook)
- **No big-bang rewrite** — ห้าม rewrite ทั้งไฟล์; ทำทีละ use case พร้อม behavior-preserving test
- **Caller-contract freeze** (บังคับก่อน refactor ทุก slice): freeze public surface (CLI exit codes / stdout JSON shape / MCP stdio JSON-RPC method names + schemas) เป็น **compatibility port** ก่อนแตะ internals — เพื่อไม่ให้ caller (agent, hook, skill ที่ subprocess/shell เข้ามา) พัง. Compat port = adapter ชั้นนอกที่หุ้ม use case เดิมไว้
- **Track 2 ความเร็ว**: `mcp-wiki-server.py` (Iron-Law-protected Layer 3) วิ่งใน track ช้ากว่า (slower cadence, stricter gates) เพราะกระทบทุก agent

## Validation / Prerequisites (ต้องทำก่อน promote เป็น Accepted)

> เรียนรู้จาก ADR-0006 (RAG) ที่มี Validation section พิสูจน์ test-backed — ADR นี้ต้องระบุ baseline ปัจจุบันก่อนอ้างว่า migration "safe"

### Baseline การทดสอบปัจจุบัน (audit 2026-08-01) `[verified]`

| Tier A file | LOC | มี test ไหม | สถานะ |
|---|---|---|---|
| `scripts/mcp-wiki-server.py` | 736 | ❌ **ไม่มี `test_mcp_wiki_server.py`** | characterization test เขียนไม่ได้ในสภาพนี้ |
| `scripts/live-dashboard/server.py` | 1757 | ⚠️ มี dashboard tests แต่ test HTML/events ไม่ใช่ domain logic | partial |
| `scripts/live-dashboard/skills_service.py` | 1262 | ❌ **ไม่มี dedicated test** | characterization test เขียนไม่ได้ |
| `scripts/lib/neural_spine_mcp.py` | 625 | ✅ `test_neural_spine_mcp.py` มี | เริ่ม slice นี้ก่อนได้ |
| `scripts/hermes/dual-mode-router.py` | 438 | ❌ ไม่มี dedicated | characterization ต้องเขียนใหม่ |
| `scripts/pharmacy_lookup.py` (Tier B) | 831 | ❌ **ไม่มี** | characterization เขียนไม่ได้ |

### Prerequisite gates (BLOCKING — ทำก่อน promote เป็น Accepted)

- [x] **G1 ✅ DONE 2026-08-01**: เขียน characterization test สำหรับ `mcp-wiki-server.py` — 21 tests ใน `tests/test_mcp_wiki_server.py`, ครอบ 9 tools + 3 resources + JSON-RPC dispatch, mutation-verified (พบ 4 char-test gaps จริง)
- [x] **G2 ✅ DONE 2026-08-02**: `sqlite-vec` 0.1.9 + `fastembed` installed, vec index built (**540 embeddings** from 540 files) — vector path ทดสอบได้แล้ว
- [x] **G3 ✅ DONE 2026-08-02**: compat port spec frozen ที่ `docs/protocols/adr-0012-g3-mcp-compat-port-spec.md` — MCP stdio surface (JSON-RPC methods, 9 tool names + schemas, 3 resource URIs, serverInfo, capabilities, error codes). G1 char-test ทำหน้าที่ enforce เป็น regression floor
- [x] **G4 ✅ DONE 2026-08-01**: slice เริ่มต้น = `neural_spine_mcp.py` (มี test) → **A4 DONE** (26 tests green, ports + 2 adapters + contract suite, caller contract frozen)

> ✅ **ทุก prerequisite gate ผ่านแล้ว (G1+G2+G3+G4)** + **C6 (hook feasibility) ผ่านแล้ว** (FP rate 0%) + **a-council UNBLOCK SHIP** (3 critical + 5 important resolved). ADR-0012 พร้อม promote เป็น **Accepted**.

## Alternatives Considered

> ℹ️ ใช้ 4 options (A/B/C/D) ต่างจาก convention ADRs เดิม (A/B/C) — เพราะมี pattern ใกล้เคียงที่ต้อืองคำนึง (Clean Architecture) ที่สมควรแยกออก. Chosen = Option D

### Option A: บังคับเฉพาะ code ใหม่ (ส่วนเก่า grandfathered)
- **Pros**: เร็ว, ความเสี่ยงต่ำ, ไม่กระทบ production
- **Cons**: code เก่า (~15.5k LOC) ยัง testability ต่ำ, ADR ไม่ได้แก้ปัญหาเดิมจริง
- **ทำไมไม่เลือก**: user ระบุชัด "วางแผน refactor ทั้งหมด" — Option A ไม่ตอบโจทย์

### Option B: Recommended default ไม่ enforce ผ่าน hook
- **Pros**: ความยืดหยุ่นสูง, ไม่ block work
- **Cons**: ADR ไม่มี teeth — กลับสู่สภาพเดิมใน 6 เดือน
- **ทำไมไม่เลือก**: A-Wiki มีวัฒนธรรม enforcement (Iron Laws + hooks) — pattern ที่ไม่ enforce ขัดกับรากฐาน

### Option C: Clean Architecture ของ Uncle Bob แทน hexagonal
- **Pros**: เหมือนกันแทบทุกประการ เป็น generalization ที่คุ้นชื่อกว่าในบางวงการ
- **Cons**: ความหมายกว้างกว่า ตีความได้หลายแบบ; hexagonal ของ Cockburn เป็นต้นตำรับและกระชับกว่า
- **ทำไมไม่เลือก**: A-Wiki มี skill `/hexagonal-architecture` อยู่แล้ว; ใช้ชื่อเดียวกันกับ skill ลดความสับสน

### Option D (chosen): Hexagonal binding + วางแผน refactor ทั้งหมด + hook enforce แบบค่อยเป็นค่อยไป
- **Pros**: ตอบโจทย์ grill ครบ, มี teeth ผ่าน hook, ใช้ skill ที่มีอยู่, ขนาดงานชัดเจน
- **Cons**: scope ใหญ่ (~15.5k LOC) ต้องการระยะเวลานาน, ต้องการ hook ใหม่ 1-2 ตัว, ความเสี่ยง refactor regression
- **ทำไมเลือก**: สมดุลที่สุด — binding จริง + migration ทีละ slice + ใช้ pattern ที่ A-Wiki มี reference model (`scripts/batch/`) อยู่แล้ว

## Consequences

### Positive
- **Testability สูงขึ้นมาก** — MCP server, dashboard, Hermes daemons สามารถ run headless ได้; Iron Law #1 ทำได้จริง
- **Replaceability** — สลับ FTS5 → external, sqlite-vec → turbovec, OpenRouter → provider ใหม่ โดยแตะเฉพาะ adapter
- **Parallel development** — ทีม/agent ทำ adapter คนละตัวได้พร้อมกันหลังตกลง port
- **Late decisions** — เลื่อนเลือกเทคโนโลยีได้; core ออกแบบก่อน
- **A-Wiki กลายเป็น reference ของตัวเอง** — `scripts/batch/` ที่เป็น adapter pattern อยู่แล้วจะถูกยกเป็นมาตรฐาน
- **เสริม Iron Laws** — #1 (test-first) ทำได้จริง, #5/#10 (core ไม่รั่ว) บังคับใน code level ไม่ใช่แค่ doc

### Negative / Trade-offs
- **ภาระงานใหญ่** — ~33 files / ~15.5k LOC ต้อง refactor; Tier A (~6k LOC) เป็น binding ตามตัวบท
- **ความเสี่ยง refactor regression** — แก้ด้วย characterization test ก่อน extract (ตาม skill Migration Playbook)
- **การเรียนรู้** — ทีม/agent ที่เขียน code ใหม่ต้องเข้าใจ port/adapter; แก้ด้วยการอ้าง skill `/hexagonal-architecture` + reference `scripts/batch/`
- **Overhead เล็กน้อยสำหรับ code เล็ก** — แม้จะยกเว้น < 50 บรรทัด แต่บางไฟล์ borderline อาจรู้สึกว่า "มากเกินไป"
- **ต้องการ hook ใหม่** — เพื่อ enforce ต้องมี `scripts/hooks/check_hexagonal_boundary.py` (สามารถข้ามได้ด้วย `HOOK_SKIP=check_hexagonal_boundary`)
- **Composition root ใหม่** — หลาย entry point ต้องเขียนใหม่

### Risks

**ลำดับความรุนแรง (R6-R14 เพิ่มจาก review 2026-08-01):**

#### 🔴 Critical

1. **R1 — Refactor fatigue**: scope ใหญ่อาจทำให้ท้อ → แก้ด้วยการทำ Tier A ทีละ slice + commit chunk ย่อย (`chunk(0012-A1):`)
2. **R6 — `awiki` MCP server เป็น Iron-Law-protected Layer 3 foundation** (`AGENTS.md:181` — "the only wiki/memory MCP with `disabled: false` + auto-approved"): ทุก agent ใน swarm พึ่ง runtime. R4 เดิมปฏิบัติต่อมันเหมือน "regression ทั่วไป" — ไม่พอ. **ไม่มี `test_mcp_wiki_server.py`** → snapshot test ที่อ้าง เขียนไม่ได้ในสภาพปัจจุบัน. Mitigation: carve `mcp-wiki-server.py` เป็น slower track + บังคับ G1 characterization test เป็น prerequisite gate + compat port (G3) ก่อนแตะ internals
3. **R7 — Characterization-test prerequisite อาจ execute ไม่ได้**: audit `tests/` พบว่าไฟล์ Tier A ส่วนใหญ่ **ไม่มีเทสเลย** (mcp-wiki-server, skills_service, pharmacy_lookup, dual-mode-router). Migration safety mechanism หลัก = กลไกที่ปัจจุบัน execute ไม่ได้. Mitigation: G1+G4 prerequisite gates; เริ่ม slice ที่ `neural_spine_mcp.py` (มี test) ก่อน ไม่ใช่ MCP server
4. **R13 — Hook enforce ที่ทั้ง decision ยึด ~~อาจสร้างไม่ได้~~ ✅ FEASIBLE 2026-08-01**: ~~static-detect "domain import adapter" ใน Python dynamic codebase มี false-positive สูง~~ → prototype `scripts/hooks/check_hexagonal_boundary.py` พิสูจน์แล้ว: narrow convention-based design (เช็คเฉพาะ `ports/` files) ให้ **FP rate 0%** บน codebase จริง (well under C6 threshold <20%). Hard whole-codebase check ไม่ทำโดยเจตนา (จะ over-fire บน legacy Tier B). **C6 resolved** — hook promote-able เมื่อ ADR Accepted. Mitigation: คงไว้เป็น prototype จนกว่า ADR Accepted, แล้วเสียบเข้า `hooks_runner.py`

#### 🟠 High

5. **R8 — Caller compatibility**: MCP server + scripts ถูกเรียกผ่าน subprocess/stdio โดยทุก agent + hooks + skills; เปลี่ยน interface = ทุก caller พัง. Mitigation: caller-contract freeze (G3) ก่อน refactor internals; compat port = adapter ชั้นนอก
6. **R9 — Cross-agent concurrent edits**: 9 agents + worktrees (`.claude/worktrees/`, `.kilo/worktrees/`) แก้ไฟล์เดียวกันระหว่าง refactor หลายเดือน → merge storm, partial-port state. R1 (fatigue) ไม่ใช่ concurrency. Mitigation: ใช้ `task_lease_reaper.py` + claim gate (Iron Law #11) ประกอบ; หนึ่ง slice = one claim; commit chunk ทันทีที่เสร็จ
7. **R10 — DI/composition-root เป็น pattern ใหม่ของ codebase นี้**: ไม่เคยมี Protocol/ABC port (มีเฉพาะ `batch/adapters/Adapter` สำหรับ LLM providers — scope เฉพาะ). Wire ผิด = runtime failure ที่ mock อาจจับไม่ได้ถ้า mock หละหลวม. Mitigation: contract test สำหรับทุก port (prod + mock adapter ต้องผ่าน suite เดียวกัน); reference implementation = `scripts/batch/`

#### 🟡 Medium

8. **R2 — Hook false-positive**: hook อาจ block script ที่ไม่เข้าเกณฑ์ → แก้ด้วย allowlist + ข้อยกเว้นชัดใน hook
9. **R3 — Drift หลัง refactor**: ทีมอาจกลับไปเขียนแบบเดิม → แก้ด้วย hook enforce + audit ใน `/A-Council`
10. **R4 — MCP server regression** (โดยทั่วไป): use case ทำทีละตัว + snapshot test. ซ้ำซ้อนกับ R6 แต่ R6 กิน architecture level; R4 กิน slice level
11. **R5 — sqlite-vec dependency** ยังไม่ติดตั้ง (`build-vec-index.py:50` `sys.exit("missing dependency...")`, chained โดย `gen-index.py` ที่ print generic warn) → vector path ทดสอบไม่ได้จนกว่าจะ install. Mitigation: G2 prerequisite; port extraction ต้องเป็นกลางต่อ backend (sqlite-vec / turbovec)
12. **R11 — Performance overhead ใน hot paths**: MCP `query`, RAG search ที่ทุก agent เรียก → adding port indirection + adapter + DI resolution per call ไม่ฟรีใน Python. Mitigation: benchmark hot paths before/after; regression budget p99 +5%
13. **R12 — Documentation drift ระหว่าง migration**: ADR + wiki concept + backlog พูด target state ขณะที่ code mid-migration เป็นเดือน → agent อ่าน doc แล้ว assume port มีอยู่. Mitigation: backlog ต้อง mark DONE/IN-PROGRESS/TODO ต่อ slice; wiki concept ต้องมี banner "binding since ADR-0012, migration in progress" จนกว่า Tier A จบ
14. **R14 — sqlite-vec missing = characterization test เขียนไม่ได้สำหรับ vector path**: R5 เลื่อนจาก footnote เป็น prerequisite (G2) — ไม่ใช่แค่ port design note

## Revisit Conditions

ย้อนกลับพิจารณา ADR นี้ใหม่ถ้า:
- **C1 (timebox)**: Tier A ใช้เวลาเกิน **3 เดือน** นับจาก Accepted → ลดขอบเขต (เช่น ผูกเฉพาะ MCP server + dashboard, ปล่อย Hermes daemons เป็น recommended)
- **C2 (hook quality)**: `check_hexagonal_boundary.py` มี false-positive rate เกิน **20%** ในการวัด 30 วันแรก → ปรับ allowlist หรือลดเป็น advisory
- **C3 (coverage, pinned scope)**: test coverage **แบบ per-file** ของ Tier A ไฟล์ใดไฟล์หนึ่งไม่ถึง **60%** ภายใน **6 เดือน** นับจากเริ่ม slice นั้น → ถือว่า pattern ไม่คุ้มสำหรับไฟล์นั้น ให้ carve out
- **C4 (alternative, measurable)**: มี benchmark ที่พิสูจน์ pattern อื่น (เช่น DDD bounded context + modular monolith) ให้ testability/replaceability ดีกว่า **≥20%** บน slice เดียวกัน → evaluate replacement
- **C5 (incident-triggered, NEW)**: refactor ของ `mcp-wiki-server.py` ก่อให้เกิด **agent outage ≥1 ครั้ง** (memory retrieval พังทุก agent) → rollback slice ทันที + revisit scope (อาจ carve MCP server ออกจาก ADR)
- **C6 (hook infeasibility, NEW, tied to R13)**: ถ้า prototype `check_hexagonal_boundary.py` ในช่วง Proposed พบว่า static-detect ไม่ได้ภายใน **4 สัปดาห์** → ADR fallback เป็น Option B (advisory, no hook); ย้อนกลับพิจารณาว่า "binding" ยังมีความหมายไหม
- **C7 (prerequisite gate fail, ~~NEW~~ ✅ PASSED 2026-08-02)**: ~~ถ้า G1-G4 ไม่ผ่านภายใน 8 สัปดาห์ → ADR ยังอยู่ Proposed~~ → **ผ่านครบทั้ง 4 gates** (G1+G2+G3+G4) ภายใน 4 วัน

## References

- **ต้นฉบับ**: [Cockburn — Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture) `[verified 2026-07-29]`
- **Skill**: `.zcode/skills/hexagonal-architecture/SKILL.md` (`/hexagonal-architecture`)
- **Wiki concept**: `wiki/concepts/ai-tools/hexagonal-architecture.md`
- **Reference implementation**: `scripts/batch/adapters/` (มี adapter pattern จริง)
- **Backlog**: `decisions/backlogs/0012-hexagonal-refactor-backlog.md`
- **เกี่ยวข้อง**: ADR-0008 (Universal Skill Architecture) — skill registry ทำตัวเป็น "port catalogue"; ADR-0012 ขยายแนวคิดไปยัง code การผลิต
- **Iron Laws**: #1 (test-first), #5/#10 (core ไม่รั่วเข้า outside) — ADR นี้คือการยก enforcement ขึ้นไปในระดับ code
