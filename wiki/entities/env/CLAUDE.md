> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — Environmental Health Entities

> **โดเมน**: Environmental Health (อนามัยสิ่งแวดล้อม)
> **Last updated**: 2026-07-10
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน entities/env/ เท่านั้น**

---

## Entities ที่มีอยู่ (2)

| Slug | Abstract |
|------|----------|
| `activated-sludge-system` | ระบบบำบัดน้ำเสียแบบ Activated Sludge — จุลินทรีย์ในบ่อเติมอากาศ |
| `rabies-pep-surveillance` | ระบบเฝ้าระวังโรคติดต่อ — จัดการผู้ถูกสัตว์กัด + PEP |

---

## กฎหมาย/มาตรฐานที่เกี่ยวข้อง

- **พรบ.ส่งเสริมและรักษาคุณภาพสิ่งแวดล้อม พ.ศ. 2535**
- **ประกาศกรมอนามัย** — มาตรฐานน้ำทิ้งโรงพยาบาล
- **กฎกระทรวงว่าด้วยการกำจัดมูลฝอยติดเชื้อ พ.ศ. 2545** (แก้ไขเพิ่มเติม 2564)
- **WHO guidelines** — rabies, water quality

---

## Rules

1. **frontmatter บังคับ**: `type`, `category`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **confidence markers** ทุกครั้ง
3. **อ้างอิงกฎหมาย**: ต้องระบุ พ.ศ. / เลขที่ประกาศให้ชัดเจน
4. **Cross-reference**: entity → concept → synthesis เสมอ

---

## ความสัมพันธ์กับ domains อื่น

| Domain | ความเกี่ยวข้อง |
|--------|---------------|
| IoT | IoT sensors สำหรับวัดคุณภาพน้ำ/อากาศในระบบบำบัด |
| AI Tools | AI วิเคราะห์ข้อมูลสิ่งแวดล้อม, แจ้งเตือนอัตโนมัติ |