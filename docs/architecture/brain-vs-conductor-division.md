# Division of Labor — A-Wiki (Brain) vs A-Wiki-Conductor (Control Plane)

> Binding 2026-08-21 · แก้ปัญหา duplication ที่เกิดเมื่อสอง track สร้าง "Conductor" พร้อมกัน

| | **A-Wiki** (repo นี้) | **A-Wiki-Conductor** (repo แยก) |
|---|---|---|
| บทบาท | 🧠 สมอง: knowledge, policies, gates, memory (L0–L5), protocols | 🎛️ Control plane: workers, processes, Serena instances, UI, dispatch |
| เจ้าของงาน | agents ดูแลสมอง (ตาม AGENTS.md ของ repo นี้) | ตาม PROJECT-PLAN.md/COLLAB.md ของ repo นั้น |
| ห้ามทำ | ไม่ทำ orchestration/dispatch/process management | ไม่ duplicate brain logic — เรียกผ่าน bridge |

## Brain Bridge (`conductor/` ใน A-Wiki)

`conductor/` ของ repo นี้ **ไม่ใช่ orchestrator คู่แข่ง** — เป็น **thin brain-side API**
ที่ A-Conductor (หรือ agent ใดๆ) เรียกใช้สมองแบบ read-mostly:

| command | หน้าที่ | สถานะ |
|---|---|---|
| `status` | claims + branches + hard-gate count (read-only) | ✅ v0.1 |
| `gate` | GO/NO-GO + claim row แนะแนว | ✅ v0.1 |
| `plan` | objective → work orders (deterministic) | ✅ v0.1 |
| `verify` | รัน repo gates (scan/health/tests) แบบ bounded → JSON | 🔜 v0.2 |
| `recall` | ค้น L1 memory ledger (read-only, redacted) | 🔜 v0.2 |
| `claim` | จอง claim row ใน COLLAB (ผ่าน gate GO เท่านั้น, idempotent) | 🔜 v0.2 |

Dispatch/process/UI = อยู่ที่ A-Conductor เท่านั้น ถ้า bridge ต้องการ capability ใหม่
ให้เป็น brain capability ที่ thin (อ่าน/ตรวจ/จด) ไม่ใช่การควบคุม execution
