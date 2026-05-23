> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — Environmental Health Concepts

> **โดเมน**: Environmental Health (อนามัยสิ่งแวดล้อม) — Concepts  
> **Last updated**: 2026-05-09  
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน concepts/env/ เท่านั้น**

---

## Concepts ที่มีอยู่ (4)

| Slug | Abstract |
|------|----------|
| `hospital-wastewater-treatment` | น้ำเสียโรงพยาบาล — SBR, Activated Sludge, มาตรฐาน BOD ≤ 20 mg/L |
| `infectious-waste-management` | ขยะติดเชื้อ — คัดแยก → เก็บ ≤48 ชม. → บันทึกปริมาณ |
| `water-quality-parameters` | ค่าทางกายภาพ เคมี ชีวภาพ — วัดคุณภาพน้ำเสีย |
| `rabies-pep-protocol` | PEP — wound care 15 min, IM 5 เข็ม vs TRC-ID 2-2-2-0-2 vs 1-week ID |

---

## Rules

1. **frontmatter บังคับ**: `type`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **ทุก concept ต้องมี**: นิยาม, ความสำคัญ, วิธีการ, ตัวอย่าง, ข้อดี/ข้อเสีย
3. **อ้างอิงกฎหมาย**: ระบุ พ.ศ. / เลขที่ประกาศ
4. **Cross-reference**: เชื่อมโยง entities และ synthesis ที่เกี่ยวข้อง

---

## ความสัมพันธ์กับ entities

| Concept | Entity ที่เกี่ยวข้อง |
|---------|---------------------|
| hospital-wastewater-treatment | activated-sludge-system |
| infectious-waste-management | — |
| water-quality-parameters | activated-sludge-system |
| rabies-pep-protocol | rabies-pep-surveillance |

---

## Workflow

1. ตรวจสอบ concept ซ้ำ
2. ใช้ template จาก CLAUDE.md หลัก
3. เชื่อมโยง entities + synthesis
4. อัปเดต `index-env.md` + รัน `python3 scripts/gen-index.py`
5. บันทึก `log.md`