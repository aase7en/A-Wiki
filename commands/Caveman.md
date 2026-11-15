# /Caveman — ตอบกระชับ ตัด filler (เฉพาะ output ความเสี่ยงต่ำ)

Maps to: `skills/awiki/caveman/SKILL.md`

## When to use
- คำตอบ/สรุป/status ทั่วไปที่ไม่ใช่ของสูญหายไม่ได้
- ผู้ใช้เห็น tool calls แล้ว อยากได้แค่ข้อสรุป
- แนะนำทางเลือก A/B พร้อมเหตุผลบรรทัดเดียว

Auto-picks on: `caveman`, `be brief`, `less tokens`, `สั้นๆ`, `ตอบกระชับ`

## Flow
1. คำตอบนำหนึ่งประโยค → เหตุผลตาม (ถ้าจำเป็น)
2. ไม่มี preamble/recap; bullets ≤3/section; ตาราง >5 แถว → artifact + path
3. คำถามใช่/ไม่ → ตอบใช่/ไม่ + เหตุผลหนึ่งบรรทัด

## ห้ามใช้กับ (hard exclusions)
โค้ด · security evidence · test/CI output · diff · ตัวเลข billing — อ้างอิงด้วย path/URL แทนการบีบอัด
