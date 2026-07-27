# A-Flow Stage: DESIGN

> โหลดเมื่อ: `state.stage == "DESIGN"` (อย่า auto-load)
>
> Goal: shape the solution — ≥2 approaches + trade-off + อนุมัติ

## 1. ≥2 Approaches (a-think step 4)

Generate อย่างน้อย 2 — ห้าม single-hypothesis:

| Approach | Complexity | Cost | Failure mode | Reversible? |
|---|---|---|---|---|
| A | ... | ... | ... | two-way |
| B | ... | ... | ... | one-way ⚠️ |

Flag one-way doors ชัดๆ (architecture, schema, deploy-strategy)

## 2. Design tool ตาม domain

| Domain | Skill | Output |
|---|---|---|
| UX/UI | `frontend-design` + `taste-skill` + `design-first-ui-prompting` | wireframe HTML + design-direction |
| Database | `domain-modeling` | ER diagram + entity list |
| API | `api-design` | OpenAPI contract + endpoint list |
| Architecture | `codebase-design` | component diagram + ADR |
| Web (3D/motion) | `gsap` + `webgl-3d-object` + `threejs` | prototype HTML |
| Game | `game-phaser-pipeline` + `threejs` | prototype |

**UI/design task**: ใช้ design-first prompting template (MengTo):
```
goal → format → layout → type → color → constraints
```
Generate **variants ≥ 2** (เปลี่ยน ≥2 dimensions เพื่อเปรียบเทียบจริง)

## 3. Pre-mortem (a-think step 5)

"ถ้า approach นี้ผิด เพราะอะไร?"
- Edge cases
- Strongest counter-argument
- Disproof attempt ก่อนยืนยัน

## 4. User approve

เสนอ:
- 2+ approaches + recommendation + why + what would change recommendation
- User confirm ทางเลือก → record เป็น ADR entry ใน `state.notes[]`

## Outputs

- Design artifact (diagram / mockup / contract)
- ADR-XXX entry in `state.notes[]`
- Advance: `a_flow_state.advance("PLAN")`

## ห้าม

- ❌ ลงมือ implement โดย user ยังไม่อนุมัติ (hook บล็อก)
- ❌ Single approach (a-think step 4 Iron Law)
