> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — Pharmacy Entities

> **โดเมน**: Pharmacy (ร้านขายยา — ภูฟาร์มาซี)
> **Last updated**: 2026-07-21
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน entities/pharmacy/ เท่านั้น**

---

## Entities ที่มีอยู่ (4)

| Slug | Abstract |
|------|----------|
| `drug-database` | ฐานข้อมูลยาจาก SP Drugstore 2020 — 3,760 SKU (ยา + เครื่องสำอาง + อาหารเสริม) |
| `drug-matching-system` | ระบบ fuzzy match ชื่อยาสะกดผิด → ชื่อมาตรฐาน |
| `pharmacy-business` | ข้อมูลธุรกิจร้านภูฟาร์มาซี — workflow, suppliers |
| `sp-drugstore-2020` | บริษัทขายส่งยา — supplier หลัก |

---

## Raw data ที่สำคัญ

```yaml
raw/pharmacy/sp_drugs_full_3760.json:    3,760 รายการ (primary — ยา + อื่นๆ)
raw/pharmacy/sp_drugs_medications_2895.json:  2,895 รายการ (เฉพาะยา — reference)
```

## Business context

- **เจ้าของร้าน**: คุณ Aase7en
- **Supplier หลัก**: เอสพีดรักสโตร์ (SP Drugstore 2020)
- **ช่องทางรับออเดอร์**: LINE (ข้อความ / รูปภาพ)
- **การสะกด**: ลูกน้องมักสะกดชื่อยาผิด — ต้องใช้ fuzzy match
- **หน่วยสั่งซื้อ**: กล่อง / แผง / ขวด / กระปุก

---

## Rules

1. **frontmatter บังคับ**: `type`, `category`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **confidence markers** ทุกครั้ง
3. **ภาษาไทย-อังกฤษผสมได้** — ชื่อยามีทั้งสองภาษา
4. **อ้างอิง raw data**: เมื่อพูดถึงราคาหรือ SKU ต้องระบุ source file

---

## ความสัมพันธ์กับ domains อื่น

| Domain | ความเกี่ยวข้อง |
|--------|---------------|
| AI Tools | Claude API สำหรับ OCR + drug validation |
| IoT | Cold-chain monitoring สำหรับวัคซีน |