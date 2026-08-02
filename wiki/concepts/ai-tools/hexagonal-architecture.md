---
type: concept
tags: [architecture, hexagonal, ports-and-adapters, clean-architecture, dependency-inversion, testability, domain-driven-design]
sources: [cockburn-hexagonal-architecture]
domain: ai-tools
related_skills: [hexagonal-architecture, android-clean-architecture, codebase-design, domain-modeling, api-design]
related_adrs: [0012]
created: 2026-07-29
updated: 2026-08-01
last_verified: 2026-08-01
verify_tool: WebFetch
---

# Hexagonal Architecture (Ports & Adapters)

รูปแบบการออกแบบระบบที่แยก **business logic** ออกจาก **เทคโนโลยีภายนอก** (UI, database, queue, external API) ผ่าน "พอร์ต" และ "อะแดปเตอร์" — เพื่อให้แอปทำงานได้เท่ากันไม่ว่าจะถูกขับเคลื่อนโดยคน, สคริปต์ทดสอบ, batch job หรือเซิร์ฟเวอร์อื่น

[verified 2026-07-29] จาก [Alistair Cockburn — Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture) + skill `.zcode/skills/hexagonal-architecture/SKILL.md`

> 💡 **หน้านี้ = "ทำไม + เมื่อไหร่ + map กับ A-Wiki"** — ส่วน "วิธี implement" (folder layout, code ตัวอย่าง TS/Java/Kotlin/Go, migration playbook, testing matrix) อยู่ใน skill `/hexagonal-architecture` ไม่ duplicate ที่นี่

---

## 1. ปัญหาที่รูปแบบนี้แก้

Cockburn เริ่มจากปัญหาคลาสสิก 2 อย่างที่ทำให้ระบบ "เป็นพิษ" ต่อการพัฒนา:

| ปัญหา | อาการ | ผลกระทบ |
|---|---|---|
| **Business logic รั่วเข้า UI** | เช่น logic คำนวณส่วนลดอยู่ใน event handler ของปุ่ม | ทดสอบอัตโนมัติไม่ได้ — เพราะต้องคลิกผ่าน GUI ที่เปลี่ยนบ่อย |
| **Business logic ผูกติด database** | เช่น use case เรียก SQL ตรงๆ | dev ต้องรอ DB ออนไลน์, ทดสอบช้า, เปลี่ยน DB ไม่ได้โดยไม่เขียนใหม่ |

**รากของปัญหาเดียวกัน**: การกองปนกัน (entanglement) ระหว่าง *กฎธุรกิจ* กับ *การโต้ตอบกับภายนอก*

> "code pertaining to the inside part should not leak into the outside part" — Cockburn

---

## 2. Intent (เจตนา)

> **"Allow an application to equally be driven by users, programs, automated test or batch scripts, and to be developed and tested in isolation."**

กล่าวคือ — แอปเดียวกัน ทำงานเหมือนกันทุกประการ ไม่ว่าใครจะเป็นคน "ขับ" มัน: มนุษย์ผ่าน GUI, สคริปต์ทดสอบอัตโนมัติ, batch ที่รันตอนค่ำ, หรือเซิร์ฟเวอร์อื่นผ่าน HTTP. **แอปนั้น "ไม่รู้และไม่สนใจ"** ว่ากำลังคุยกับอะไรอยู่ฝั่งตรงข้าม

---

## 3. แนวคิดหลัก

```
                          ┌─────────────────────────────────┐
        Driving side       │      APPLICATION CORE          │     Driven side
   (primary / left)        │  (Inside — business logic)     │   (secondary / right)
                          │                                 │
  ┌──────────┐   adapter  │   ┌─────────────────────────┐   │   adapter   ┌──────────┐
  │  Human   │──────────▶│   │   Use Case              │   │───────────▶│ Postgres │
  │   GUI    │           │   │   (application logic)   │   │             │   DB     │
  └──────────┘           │   │                         │   │             └──────────┘
                          │   │   Domain Model          │   │
  ┌──────────┐   adapter  │   │   (pure business rules) │   │   adapter   ┌──────────┐
  │   HTTP   │──────────▶│   │                         │   │───────────▶│  Stripe  │
  │   API    │           │   │         ▲               │   │             │  Payment │
  └──────────┘           │   │         │               │   │             └──────────┘
                          │   │    PORT (interface)     │   │
  ┌──────────┐   adapter  │   │                         │   │   adapter   ┌──────────┐
  │   Test   │──────────▶│   │   ─ port = บทสนทนา      │   │───────────▶│   Mock   │
  │  suite   │           │   │     ที่จงใจกำหนดขึ้น     │   │             │    DB    │
  └──────────┘           │   │     ตามวัตถุประสงค์     │   │             └──────────┘
                          │   └─────────────────────────┘   │
                          │                                 │
                          └─────────────────────────────────┘
```

### 3.1 Port (พอร์ต)
- = **บทสนทนา/สัญญา** ระหว่างแอปกับโลกภายนอก ที่กำหนดขึ้น *ตามจุดประสงค์* (purpose) **ไม่ใช่ตามเทคโนโลยี**
- ตั้งชื่อตาม *ความสามารถ* (`OrderRepositoryPort`, `PaymentGatewayPort`) ไม่ใช่ตามเทคโนโลยี (`PostgresPort`, `StripePort`)
- พอร์ตเดียวอาจมีหลายอะแดปเตอร์

### 3.2 Adapter (อะแดปเตอร์)
- = ส่วนที่ *จำเพาะต่อเทคโนโลยี* — แปลงสัญญาณจากโลกภายนอก (HTTP request, SQL row, queue message) เป็น procedure call ที่แอปเข้าใจ และในทางกลับกัน
- ตัวอย่าง: REST controller, SQL repository, Stripe SDK wrapper, FIT test harness

### 3.3 Application Core (Inside)
- = **functional specification** ของระบบ — กฎธุรกิจและกระบวนการทำงาน
- ประกอบด้วย: **domain model** (entities, value objects, pure rules) + **use cases** (orchestration)
- ไม่ import framework, ORM, web server, SDK ใดๆ

---

## 4. กฎเหล็ก (กฎการพึ่งพิง — Dependency Rule)

```
   adapter ──────▶ application ──────▶ domain ──────▶ (nothing external)
     ▲                                            ▲
     │ ชี้เข้าเสมอ                                  │ ไม่พึ่งพาอะไรภายนอกเลย
     └── เป็นสิ่งที่ "รู้จัก" เทคโนโลยี
```

**ทิศทางการพึ่งพาชี้เข้าหาศูนย์กลางเสมอ** (inward):
- adapter → application/domain
- application → port interface
- domain → *ไม่มีอะไรภายนอก*

ความสำคัญ: **โค้ดฝั่ง inside ต้องไม่รั่วออกสู่ outside.** ฝืนกฎนี้ = hexagonal พังทลายทันที

---

## 5. ความไม่สมมาตรของพอร์ต: Driving vs Driven

แม้หลักการวางพอร์ตแบบสมมาตรทุกด้าน แต่ในการ implement พอร์ตจะมี 2 รสชาติ:

| | Primary (Driving) | Secondary (Driven) |
|---|---|---|
| **ตำแหน่ง** | ซ้าย/บน | ขวา/ล่าง |
| **ใครเริ่ม** | actor ภายนอก trigger แอป | แอปเรียกใช้ dependency ภายนอก |
| **ตัวอย่าง** | GUI, REST endpoint, test script | database, payment API, message bus |
| **พอร์ตเป็น** | use-case interface (แอปกำหนด API ของตัวเอง) | dependency interface (แอปกำหนดสัญญาที่ต้องการจากภายนอก) |
| **อะแดปเตอร์** | เรียก use case | ถูก use case เรียก (implements port) |

> "The distinction between primary and secondary lies in who triggers or is in charge of the conversation." — Cockburn

---

## 6. ทำไมต้องใช้ — คุณค่าหลัก

### 6.1 Testability (เป้าหมายแรกของ Cockburn)
- แทนที่จะต้องรอ DB/UI จริง ก็ **run แอปทั้งหมดแบบ "headless"** ด้วย mock adapter ฝั่ง driven + test adapter ฝั่ง driving
- QA วิ่ง regression test ก่อน GUI/DB เสร็จ — เพราะ core เป็นอิสระจากสิ่งเหล่านั้น

### 6.2 Replaceability
- สลับ adapter ได้โดยไม่แตะ core: SQL → in-memory, REST → gRPC, human GUI → batch script
- Cockburn's weather example: เปลี่ยน wire feed → HTTP feed, เพิ่ม email โดย core ไม่เปลี่ยนบรรทัดเดียว

### 6.3 Parallel development
- ทีมทำ adapter คนละตัวได้พร้อมกัน (front-end, DB, integration) เพราะตกลงสัญญาพอร์ตไว้ก่อน

### 6.4 Late decisions
- เลื่อนการเลือกเทคโนโลยีออกได้ — ออกแบบ core ก่อน เลือก DB/framework ทีหลัง

---

## 7. เมื่อไหร่ใช้ / เมื่อไหร่อย่าใช้

✅ **ใช้เมื่อ**
- ระบบมีกฎธุรกิจที่ซับซ้อนและจะอยู่นาน (long-lived)
- ต้องการทดสอบอัตโนมัติอย่างจริงจัง
- มีหลาย interface เข้ามาแตะ use case เดียวกัน (HTTP + CLI + cron + queue)
- ต้องการสลับ infrastructure (DB, external API) โดยไม่เขียน core ใหม่
- refactor โค้ด legacy ที่ logic ปนกับ I/O

❌ **อย่าใช้เมื่อ**
- CRUD ล้วน (logic น้อยมาก) — overhead มากกว่าคุณค่า
- prototype/POC ที่จะทิ้ง — เร็วกว่าถ้าเขียนตรง
- ทีมยังไม่เคย และ timeline แน่นมาก — เส้นโค้งเรียนรู้ต้นทุนสูง
- script/automation ที่เป็น single-purpose ไม่มี domain

---

## 8. ตัวอย่างคลาสสิกจาก Cockburn

### 8.1 Discounter (ทุ่นแรงคำนวณส่วนลด)
1. เริ่มจาก isolate core + test script + constant mock
2. ใส่ UI adapter
3. แยก `RateRepository` เป็น port → สลับ `MockRateRepository` ↔ database adapter จริงได้ไม่ต้องแตะ use case

### 8.2 Weather System (ระบบพยากรณ์อากาศ)
- 4 พอร์ตตามจุดประสงค์: weather feed, admin interface, notified subscribers, subscriber DB
- สลับ wire feed → HTTP feed, เพิ่ม email ได้โดย core เดิม

> 💡 บทเรียน: **ชื่อพอร์ตอิงจุดประสงค์** ไม่ใช่เทคโนโลยี — นี่คือหัวใจที่ทำให้ replaceability เป็นไปได้

---

## 9. Map → A-Wiki (เชื่อมกับสถาปัตยกรรม A-Wiki ที่มีอยู่)

[assumed 2026-07-29] A-Wiki เองก็เป็นระบบที่มีลักษณะ hexagonal โดยนัย — map ได้ดังนี้ (ดู `AGENTS.md` §Agent Foundation Architecture):

| Hexagonal | A-Wiki equivalent | หมายเหตุ |
|---|---|---|
| **Application core (inside)** | **4 foundation layers** (Enforcement / Orchestration / Memory & Knowledge / Skill Catalog) | สมองจริง ลบออกแล้วระบบพัง — เป็น "inside" |
| **Domain rules** | Iron Laws + Cost Pyramid + Swarm protocol | กฎธุรกิจที่ไม่พึ่งพา agent/harness |
| **Use cases** | `a-plan`, `a-debug`, `a-loop`, lifecycle skills | orchestration ของกฎธุรกิจ |
| **Inbound port** | `agents: [all]` field + slash-command grammar (`/A-Plan`) | สัญญา: "อะไรที่ agent เรียกได้" |
| **Inbound adapters (driving)** | Claude Code, Codex, Gemini, ZCode, Cline, Hermes, ... | แต่ละ agent = adapter หนึ่งตัวที่ขับ use case เดียวกัน |
| **Outbound port** | `awiki` MCP tools (`wiki_ingest_route`, `skill_route`), `wiki_ingest_route` contract | สัญญา: "อะไรที่ core ต้องการจากโลกภายนอก" |
| **Outbound adapters (driven)** | FTS5/sqlite-vec index, raw/ symlink, Google Drive, OpenRouter free tier, batch API | เทคโนโลยีที่ implement port |
| **Composition root** | `scripts/setup-local.sh`, `.mcp.json`, `skills-registry.json` | wiring — ที่ผูก adapter เข้ากับ core |
| **Test adapter (driving)** | `tests/`, `scripts/agent-preflight.py`, `scripts/audit_a_suite.py` | ทดสอบ core โดยไม่ต้องผ่าน agent จริง |
| **Mock adapter (driven)** | `scripts/sync-smoke.py` (temp repos), Tier 0 free backend, MOCK bot trading | ทดสอบ core โดยไม่ต้อง DB/secret จริง |

**ผลของการ map**: A-Wiki ทำตามกฎเหล็กของ hexagonal อยู่แล้ว — เช่น
- **Iron Law #5/#10**: core (AGENTS.md, skills-registry) ต้องไม่รั่วเข้า outside (machine path, secret) = inside-outside rule
- **`agents: [all]` + symlink farm**: 1 use case (`a-plan`) ขับได้จากหลาย adapter (Claude/Codex/Gemini/...) = พอร์ตเดียวหลายอะแดปเตอร์
- **Universal Cost-First Routing Tier 0-3**: mock adapter ฝั่ง driven (free/mock backend) ที่สลับกับ prod adapter = replaceability
- **brain-improvement-gate**: = "ก่อนแตะ core ต้องผ่าน gate" — กลไกป้องกันการรั่ว

---

## 10. เครื่องมือ/ทักษะที่เกี่ยวข้องใน A-Wiki

| เครื่องมือ | หน้าที่ | ที่อยู่ |
|---|---|---|
| **`/hexagonal-architecture`** skill | คู่มือ implement เต็มรูปแบบ (folder layout, TS/Java/Kotlin/Go, migration playbook, testing matrix, anti-patterns) | `.zcode/skills/hexagonal-architecture/SKILL.md` |
| `/android-clean-architecture` skill | สำหรับ Android/KMP (Room, SQLDelight, Ktor, Koin/Hilt, Gradle convention plugins) | `.zcode/skills/android-clean-architecture/SKILL.md` |
| `codebase-design` skill | "deep module" vocabulary — **DEEPENING.md dependency category 3 = Ports & Adapters โดยตรง** ("one adapter = hypothetical seam; two adapters = real seam") | `skills/mattpocock/codebase-design/` |
| `api-design` skill | REST contract สำหรับ driving adapter ฝั่ง HTTP | `skills/ecosystem/api-design/` |
| `domain-modeling` skill | entity/ER modeling + สร้าง `CONTEXT.md` glossary + ADR | `skills/mattpocock/domain-modeling/` |
| **`/A-Plan`** aggregator | chain ที่วิ่งผ่าน a-think → grill → spec → codebase-design+api-design+domain-modeling → plan-orchestrate เพื่อออกแบบระบบ | `skills/awiki/a-plan/SKILL.md` |

> 💡 **Workflow แนะนำ** เมื่อจะออกแบบระบบใหม่ด้วย hexagonal: `/A-Plan` → เลือก design tool = `codebase-design` + `api-design` + `domain-modeling` → เมื่อถึงขั้น implement เรียก `/hexagonal-architecture` เพื่อดู folder layout + multi-language mapping + migration playbook

---

## 11. รูปแบบใกล้เคียง (เปรียบเทียบสั้น)

| รูปแบบ | ความสัมพันธ์กับ hexagonal |
|---|---|
| **Clean Architecture** (Uncle Bob) | เหมือนกันแทบทุกประการ — เป็น generalization ของ hexagonal + onion + entity-component. ดู `android-clean-architecture` skill |
| **Onion Architecture** (Palermo) | เน้นวงกลมซ้อน (domain ในสุด) — ทิศทาง dependency เหมือนกัน |
| **DDD bounded context** | เสริมกัน — bounded context = ขอบเขตของ hexagon หนึ่งตัว; ports = จุดสัมผัสระหว่าง context |
| **Layered (n-tier)** | บรรพบุรุษที่ hexagonal มาแก้ — logic มักรั่วข้ามเลเยอร์ |

---

## 12. อ้างอิง

- **ต้นฉบับ**: [Alistair Cockburn — Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture) `[verified 2026-07-29]`
- **Skill implement**: `.zcode/skills/hexagonal-architecture/SKILL.md` (origin: ECC)
- **เกี่ยวข้องใน A-Wiki**: `AGENTS.md` §Agent Foundation Architecture · `wiki/concepts/ai-tools/mcp-architecture.md` (MCP = port สำหรับ agent)
- **Glossary**: Ports = พอร์ต, Adapters = อะแดปเตอร์, Composition root = จุดต่อสาย, Driving/Driven = ขับ/ถูกขับ

---

## 13. สถานะและ next step

> 🚧 **Migration in progress** banner — ตาม ADR-0012 R12 mitigation. จะถูกถอดเมื่อ Tier A เสร็จ

- **[verified 2026-08-02]**: ADR-0012 (`decisions/0012-adopt-hexagonal-architecture.md`) — status: **Proposed** (ยังไม่ Accepted). ✅ **2026-08-02 a-council UNBLOCK SHIP** — 3 critical + 5 important findings บน slice A4/G1/C6 แก้ครบแล้ว ผ่าน independent re-review (89 tests pass)
- **ความคืบหน้า**:
  - ✅ **Slice A4 (`neural_spine_mcp.py`)** DONE — extracted `MemoryPort` + `TaskBoardPort`, 2 adapters each, contract suite, caller contract frozen. Council fix: `configure()` single entry + sandbox `_assert_within_sandbox`
  - ✅ **G1** DONE — 21 char-tests สำหรับ `mcp-wiki-server.py` (was 0), mutation-verified (dropped-tool → fail)
  - ✅ **C6** DONE — prototype `scripts/hooks/check_hexagonal_boundary.py` FEASIBLE, FP rate 0%, FORBIDDEN list expanded (os/pickle/ctypes/etc)
  - ✅ **A-Council** UNBLOCK SHIP — 89 tests pass, 0 claim leak, mutation-verified
- **ขอบเขต binding**: ทุก service/app/MCP-server/daemon ที่มี I/O + domain logic; **ยกเว้น** script/hook/fixture/SKILL.md/eval
- **Prerequisite gates ก่อน promote** (BLOCKING): G1 ✅, G4 ✅, **G2** ⬜ (sqlite-vec install), **G3** ⬜ (compat port spec — G1 ทำบางส่วนแล้ว)
- **Reference model**: `scripts/batch/adapters/__init__.py:47` มี `class Adapter(ABC)` จริง — ทุก slice เทียบกับสิ่งนี้. **Slice A4 เป็น reference ที่ 2 แล้ว** (`scripts/lib/ports/__init__.py`)
- **Hook enforce**: ✅ prototype feasible — promote สู่ `hooks_runner.py` เมื่อ ADR Accepted (revisit C6 resolved)
- **Next slice**: A2/A3 (dashboard) หรือ A1 (MCP server — เหลือ G2/G3)
