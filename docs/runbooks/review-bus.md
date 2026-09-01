# Review Bus — Operator Runbook (Phases 8–9)

> ระบบ review อัตโนมัติของ A-Wiki: executor เผยแพร่ review request → reviewer ให้ findings → executor แก้ → retest ที่ head ปัจจุบัน → CI เขียว → READY
> Engine: `scripts/lib/review_bus.py` (state ล้วน — **ไม่มี** merge/push) · Loop gate: `scripts/lib/a_loop_review.py` · Contract: `schemas/awiki-review/v1.schema.json`

## State หนึ่งรอบ (cycle)

```
REVIEW_REQUESTED → REVIEWING → CHANGES_REQUIRED ⇄ (fix → resolve → verify → re-review)
                            ↘ APPROVED → (retest@head + ci เขียว) → READY
                            任何 new SHA หลัง approval → กลับ REVIEW_REQUESTED (approval เก่าเพิกถอน)
```

- หนึ่ง cycle ผูกกับ **หนึ่ง HEAD SHA** — fix commit = SHA ใหม่ = ต้อง review ใหม่ (โดยดีไซน์)
- findings มี id คงที่ `R-<phase>-<NNN>` · blocker ที่ยัง open ขวาง READY เสมอ
- state เก็บที่ `.tmp/review-bus/<phase>-c<cycle>.json` (atomic, อยู่รอด restart)

## คำสั่งที่ใช้จริง (python)

```python
import sys; sys.path.insert(0, "scripts/lib")
from review_bus import ReviewBus

bus = ReviewBus(".tmp/review-bus", phase="P8")
bus.publish(head_sha="<git rev-parse HEAD>", executor="glm-executor",
            required_tests=["python -m pytest tests/ -q"])          # เปิดรอบ
bus.add_finding(severity="blocker", area="engine", summary="...")    # R-P8-001
bus.resolve_finding("R-P8-001", fix_sha="<sha ของ fix>")             # open→addressed
bus.verify_finding("R-P8-001")                                       # addressed→verified
bus.set_verdict(reviewer="reviewer-adapter", verdict="PASS_WITH_NOTES")
bus.record_retest(sha="<head ปัจจุบัน>", ok=True)                      # sha ต่าง head = invalidate
bus.record_ci(ok=True)
bus.readiness()   # {"ready": bool, "reasons": [...]} — ครบทุกเงื่อนไข才 READY
```

## A-Loop v2 completion gate

```python
from a_loop_review import ALoopReview
gate = ALoopReview(bus)  # head ผ่าน git plumbing (rev-parse) — worktree/detached-safe (RB-1)
gate.open_review_for_task("T-101", ["pytest..."])
gate.task_gate("T-101")
# {"allow_complete": True เฉพาะ READY, "status", "blockers", "reasons"}
```

task เสร็จจริง = `allow_complete: True` เท่านั้น — งานที่ fix ใหม่ (head ใหม่) วนกลับไป review อัตโนมัติ

## Policies

- **Race telemetry (N-P1-001, เฟส 8)**: `races-history` = artifact/runtime เท่านั้น — promotion job ห้าม stage เข้า tracked tree (บังคับโดย `tests/test_race_history_policy.py`)
- **Reviewer สลับได้**: reviewer เป็นข้อมูล (name+transport) ไม่ใช่ dependency — เปลี่ยน implementation ไม่กระทบ protocol
- **ห้าม auto-merge**: engine ไม่มีคำสั่ง git ใดๆ — merge เป็นการตัดสินใจของ human/CI เสมอ

## world-intel (เฟส 10 — module ภายนอก optional)

`scripts/lib/world_intel.py` — lazy bridge ผ่าน env `WORLD_INTEL_MCP_CMD` (machine-local): ไม่ผูก = ตอบ `enabled:false` พร้อมเหตุผล, ผูกแล้ว = stdio JSON-RPC + local cache (TTL 6 ชม. ไม่ commit) — รายละเอียด registry: `config/integrations.yaml` (`world-intel: status: optional`)
