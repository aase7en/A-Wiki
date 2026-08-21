# A-Wiki vNext — Phase 7 Model Control Plane Work Order

**Status:** EXECUTION AUTHORIZED — Phase 7 only (user-directed 2026-08-21)
**Executor:** GLM / ZCode · **Base main:** `75443259`
**Branch:** `refactor/awiki-model-control`

## Division of labor (binding, อ้าง brain-vs-conductor-division.md)

- **A-Wiki (brain) = POLICY authority**: tier classes, งบ/กติกาการใช้,
  vendor-neutral capability vocabulary, ต้นทุน policy — สาธารณะ ตรวจได้
- **A-Conductor (control plane) = EXECUTION routing/dispatch**: เลือก
  model/provider จริงตอนรันงาน โดย**อ่าน policy จากสมอง** ผ่าน bridge
- ห้าม: สมอง bind ชื่อโมเดลจริงในไฟล์สาธารณะ · ห้าม conductor มี policy
  สำเนาของตัวเองที่ไม่ได้อ่านจากสมอง

## Scope

1. `config/models/policy.yaml` (schema `awiki-model-policy/v1`) —
   tier classes (free/cheap/capable/primary) เป็น **capability class**
   ไม่ใช่ชื่อโมเดล, budget rules ต่อ task-type, ข้อห้าม (เช่น
   hardcode vendor), fail-closed validation
2. `scripts/lib/model_policy.py` — loader + validator (fail-closed,
   unknown schema/field = error) + tier resolution helpers
3. `config/models/runtime.local.yaml.example` — template เครื่อง local
   (slot→ชื่อจริง) **ตัวจริง gitignored** (Iron Law #6)
4. `conductor` bridge command `models` — read-only: แสดง policy +
   slot resolution สำหรับ A-Conductor
5. Tests TDD ครบ: schema validation, fail-closed paths, budget rules,
   no-vendor-names in public files, bridge output

## Out of scope
- routing/dispatch engine, fallback chains, quota tracking runtime,
  benchmark/health scoring, daemon ใดๆ (ของ A-Conductor/เฟสถัดไป)
