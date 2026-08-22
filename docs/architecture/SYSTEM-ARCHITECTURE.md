# A-Wiki System Architecture — สมอง + A-Conductor (ฉบับรวมระบบ)

> อัปเดต 2026-08-21 · โดย GLM/ZCode · ประกอบจากสถานะจริงของทั้งสอง repo
> สมอง: repo `A-Wiki` (main `9fe5aaf2`) · Control plane: repo `A-Wiki-Conductor` (main `5a34c3b`) — สอง repo พี่น้องในโฟลเดอร์ GitHub ของเครื่อง

## 1. ภาพใหญ่ — สองระบบหนึ่งเป้าหมาย

```
┌─────────────────────────────────────────────────────────────────┐
│                    คุณ (Human = เจ้าของเป้าหมาย + merge gate)      │
└──────────────┬──────────────────────────────────┬───────────────┘
               ▼                                  ▼
┌─────────────────────────┐        ┌──────────────────────────────┐
│   A-WIKI  🧠 (สมอง)      │◀──────▶│  A-CONDUCTOR 🎛️ (Control Plane)│
│  knowledge + policy +    │ bridge │  dispatch + process + UI      │
│  memory + gates          │ (CLI)  │  + Serena workers            │
└─────────────────────────┘        └──────────────────────────────┘
        ▲          ▲                          │ spawns & wakes
        │ read     │ enforce hooks             ▼
   ┌────┴───┐ ┌────┴────────┐     ┌────────────────────────┐
   │  wiki/  │ │ hooks (17   │     │ Serena worker instance │
   │ 544 หน้า│ │ hard gates) │     │ + system_prompt ที่ชี้   │
   │ + graph │ │ registry 29 │     │ → BRAIN-ENTRY.md       │
   │ 553n/   │ │ hooks       │     │   (Index+Pull model)   │
   │ 1839e   │ └─────────────┘     └────────────────────────┘
   └────────┘
```

**หลักการแบ่ง (binding — `brain-vs-conductor-division.md`):**
| | สมอง (A-Wiki) | A-Conductor |
|---|---|---|
| เป็นเจ้าของ | ความรู้ · กฎ/Iron Laws · ความจำ L0–L5 · gates/hooks · model **policy** | การกระจายงาน · process lifecycle · UI/desktop · worker pool · model **dispatch** |
| ห้ามทำ | orchestration/dispatch/process mgmt | สร้าง policy/memory/gate ซ้ำ — ต้อง reuse ผ่าน bridge |

## 2. สมอง (A-Wiki) — 7 ชั้น

| ชั้น | องค์ประกอบ | สถานะ |
|---|---|---|
| **1. Knowledge** | `wiki/` 544 หน้า · `.wiki-graph.json` (553 nodes/1,839 edges) · FTS5 + vec 384-dim hybrid · `brain-map.canvas` | ✅ ใช้งานจริง |
| **2. Enforcement** | hook registry 29 ตัว (17 hard) · `hooks_runner.py` (fail-closed ทุกทาง) · provider adapters Claude/Codex/Gemini/Cline · stop-auto-commit 2 ชั้น | ✅ เฟส 6 |
| **3. Memory** | L0 .tmp → L1 ledger (BM25) → L2 project (isolated) → L3 wiki (5-gate promotion) → L4 raw (immutable) → L5 experiments | ✅ เฟส 5 |
| **4. Project Adapter** | `.awiki/project.yaml` + validate/attach/status (fail-closed) | ✅ เฟส 4 |
| **5. Skill Plane** | registry 243 skills · tier-2 description fallback (ทุกตัวหาได้แบบ lazy) · `skill_route` MCP · A-ROUTER triggers | ✅ ปรับปรุงล่าสุด |
| **6. Model Policy** | `config/models/policy.yaml` (tiers free/cheap/capable/primary + budgets) · runtime จริง gitignored เครื่อง local | ✅ เฟส 7 |
| **7. Brain Bridge** | `python -m conductor status/gate/plan/verify/recall/claim/models` **+ search/related/hubs** (กราฟ!) | ✅ v0.3 |

**จุดเข้า:** ภายนอก → `BRAIN-ENTRY.md` (ไฟล์เดียวจบ: 3 กฎ + SSoT map + คำสั่งกราฟ) · ภายใน repo → `AGENTS.md` First Action → continuity gate (COLLAB claims)

## 3. A-Conductor — สถานะและบทบาท

| ส่วน | สถานะ (จาก CURRENT-WORK ของมัน) |
|---|---|
| Desktop app + installer (A-Conductor-Setup.exe) | ✅ ship แล้ว (787 tests, install จริง) |
| Worker pool (multi-Serena, isolated SERENA_HOME) | ✅ Phase 1 เกือบจบ |
| **Second Brain Phase 1** (WO-052: system_prompt ปลุกสมองทุก worker) | 🔄 PR #18–21 ตามแผน — inject `system_prompt` ชี้ `BRAIN-ENTRY.md` (Index+Pull ห้ามฝังเนื้อหา) |
| Phase 2 Task Router | ⬜ ต้อง reuse `bridge plan/gate/verify` (ตาม Phase Mapping Contract) |
| Phase 3 Review/Repair | ⬜ reuse `recall + claim` |
| Phase 4 A-Wiki Integration | ⬜ = เรียก bridge 7+3 คำสั่ง — **API พร้อมแล้วฝั่งสมอง** |
| ห้ามของมัน | ไม่มี hook ของตัวเอง (enforcement = ของสมอง) · ไม่มี policy สำเนา |

## 4. จุดเชื่อม (Integration Contract)

```
A-Conductor ต้องการ X → เรียกผ่าน bridge CLI (--json ทุกตัว) → สมองตอบ
  จะเริ่มงานใหม่     → conductor gate --topic ...        → GO/NO-GO + conflicts
  จะกระจายงาน       → conductor plan "objective"        → work orders
  ตรวจก่อนเสร็จ      → conductor verify --gates ...      → pass/fail ต่อ gate
  หาความรู้/ประวัติ   → conductor search/recall/related   → ผล ranked
  จองงาน/ส่งมอบ      → conductor claim / COLLAB row      → idempotent
  เลือกโมเดล         → conductor models                  → policy tiers
```

**กฎเหล็กของการเชื่อม:** ถ้า conductor ต้องการความสามารถที่ bridge ยังไม่มี → เปิด work order **ฝั่งสมอง** เพิ่มที่ bridge (thin, read-mostly) — ห้าม implement เองฝั่ง conductor

## 5. Data Layer (Drive — private)

Drive data layer (`A-Wiki-Data` บน Google Drive ของเครื่อง — resolve ผ่าน junction `drive/` เท่านั้น) — จัดแล้ว 2026-08-21: `AGENTS.md`(กฎ 3 ข้อ) + `LAYOUT.md`(หนึ่ง role หนึ่ง path) + `inbox/`(ไม่รู้จะวางไหน) + `_archive/`(MANIFEST) — สมองเข้าถึงผ่าน junction `drive/` เท่านั้น ห้าม hardcode path

## 6. งานค้างทั้งระบบ (ตรวจแล้ว 2026-08-21)

### ฝั่งสมอง (HOLD ถูกปลดโดย user 2026-08-22 — เฟส 8–11 เสร็จครบ)
| # | งาน | เฟส | เหตุผลที่ค้าง |
|---|---|---|---|
| 1 | Eval vs routing promotion split + automated reviewer foundations | 8 | ✅ DONE `0db9cf0d` |
| 2 | A-Loop v2 (เชื่อม improvement-loop กับ review state machine) | 9 | ✅ DONE `55541e5b` |
| 3 | world-intel MCP (optional, lazy) | 10 | ✅ DONE `07d210a0` |
| 4 | Docs slimming + review-bus operator docs | 11 | ✅ DONE — runbook + status sync |
| 5 | follow-up เล็ก: ชื่อ identifier อื่นที่ยังมี "uthai" ใน function เก่า (alias คงไว้แล้ว) | — | เสริมได้เมื่อไหร่ |

### ฝั่ง A-Conductor (จากแผน/สถานะของมันเอง)
| # | งาน | สถานะ |
|---|---|---|
| 1 | Second Brain Phase 1 (PR #18–21) | 🔄 กำลังทำ |
| 2 | DECISION_REQUIRED 3 ข้อ: MCP gateway enforcement · code signing ลบ SmartScreen · DR-P1-003 transport | รอ user ตอบ |
| 3 | Phase 2 Task Router → 3 Review loop → 4 A-Wiki Integration | ⬜ หลัง Phase 1 |

### ร่วม
- **Test the seam:** เมื่อ A-Conductor จบ WO-052 → ทดสอบจริง end-to-end (worker ปลุก → อ่าน BRAIN-ENTRY → gate → claim → ทำงาน → verify) แล้วบันทึก evidence ที่นี่

## 7. วิธีดำเนินการต่อ (recommended order)

1. รอ A-Conductor ปิด WO-052 + user ตอบ DECISION_REQUIRED
2. E2E test จุดเชื่อม (ข้อร่วม) — ปรับ bridge ตามที่พบจริง
3. ยก HOLD เฟส 8 → 11 ตามลำดับ (8 ก่อน — reviewer อัตโนมัติช่วยทุกเฟสถัดไป)
