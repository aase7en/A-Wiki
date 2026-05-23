> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — Pharmacy Concepts

> **โดเมน**: Pharmacy (ร้านขายยา — ภูฟาร์มาซี) — Concepts  
> **Last updated**: 2026-05-09  
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน concepts/pharmacy/ เท่านั้น**

---

## Concepts ที่มีอยู่ (8)

| Slug | Abstract |
|------|----------|
| `drug-aliases` | ชื่อเล่นยา / ตัวย่อ — "อม็อก"=Amoxicillin, "พารา"=Paracetamol |
| `drug-classification` | ATC code — มาตรฐาน WHO จำแนกยาตามระบบอวัยวะ |
| `drug-validation` | ตรวสอบรายการยาก่อนสั่ง — ถูกต้อง / ต้องถามกลับ |
| `fuzzy-match` | เทคนิค match ชื่อยาสะกดผิด → ชื่อมาตรฐาน |
| `order-workflow` | ขั้นตอนรับออเดอร์ → ตรวจสอบ → export |
| `ordering-workflow` | (alias ของ order-workflow) |
| `pharmacy-context` | ภาพรวมธุรกิจร้าน — workflow, หน่วยสั่งซื้อ |
| `ui-design-pharmacy` | UI/UX design สำหรับ pharmacy web app |

---

## Rules

1. **frontmatter บังคับ**: `type`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **ภาษาไทย-อังกฤษผสมได้**
3. **อ้างอิง raw data**: `sp_drugs_full_3760.json` สำหรับราคา/SKU
4. **Cross-reference**: เชื่อมโยง synthesis (pharmacy-order-checker, pharmacy-web-app-roadmap)

---

## ความสัมพันธ์

| Concept | Entity ที่เกี่ยวข้อง |
|---------|---------------------|
| drug-aliases, fuzzy-match | drug-matching-system, drug-database |
| drug-classification, drug-validation | drug-database, sp-drugstore-2020 |
| order-workflow, pharmacy-context | pharmacy-business |
| ui-design-pharmacy | — |

---

## Workflow

1. ตรวจสอบ concept ซ้ำ
2. สร้าง/แก้ไข → เชื่อมโยง entities + synthesis
3. อัปเดต `index-pharmacy.md` + รัน `python3 scripts/gen-index.py`
4. บันทึก `log.md`