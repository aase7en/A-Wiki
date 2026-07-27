# A-Flow Stage: ASK

> โหลดเมื่อ: `state.stage == "ASK"` (อย่า auto-load ถ้าไม่ได้อยู่ใน stage นี้)
>
> Goal: restate the real problem + ได้ done-criteria ที่ measure ได้ + grill user ≥3 Qs

## 1. Restate (a-think step 1)

- 1 ประโยค: "ปัญหาจริงๆ คือ..."
- Fix wrong question ก่อน answer (ถ้าคำถาม user ผิด)
- Premise check: สมมุติฐานของ user ถูกมั้ย?

## 2. Done-criteria (a-think step 2)

เขียน acceptance ที่ verify ได้ concrete:
- ✅ "Dashboard load <2s บน iPad" (ดี)
- ❌ "Dashboard เร็วขึ้น" (ไม่ดี — ไม่ measurable)

Constraints ต้องถาม:
- Budget (time / token / money)
- Environment (mobile? legacy compat? offline?)
- Skill level / agent capability

**Hospital-specific**:
- วันที่ = พ.ศ. (Buddhist Era = CE + 543)
- PHI ไม่ออกจากระบบ
- Z.ai/GLM cloud = กฎหมายจีน → ห้าม route PHI

## 3. Grill-with-docs (MANDATORY ≥3 Qs)

ถาม **ทีละข้อ** (ไม่พร้อมกัน):

| Q | สิ่งที่ถาม |
|---|---|
| 1 ขอบเขต | ครอบคลุมแค่ไหน? แค่ไหนที่ไม่ทำ? |
| 2 ข้อจำกัด | budget? environment? legacy compat? |
| 3 success | ทำเสร็จแล้วยืนยันยังไงว่าใช้ได้ |
| 4 (ถ้ามี) | architecture decision ที่ต้อง user ตัดสินใจ |

## Outputs

- `state.notes[]`: restate, done-criteria, Q&A, ADR stub
- Advance: `a_flow_state.advance("DESIGN")`

## ห้าม

- ❌ อ่าน code มากก่อนถาม (assume เอง)
- ❌ Implement ใดๆ (hook บล็อก)
- ❌ ข้ามไป DESIGN โดยไม่ได้ ≥3 answers
