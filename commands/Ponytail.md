# /Ponytail — ทางออกที่ง่ายที่สุดที่ใช้งานได้จริง

Maps to: `skills/awiki/ponytail/SKILL.md`

## When to use
- งานมีแนวโน้ม over-engineer / speculative generality
- เลือกไม่ถูกว่าจะ dependency เองหรือใช้ของที่มี
- ต้อง checkpoint context ข้าม session โดยไม่ลากทุกอย่างตาม

Auto-picks on: `ponytail`, `lazy mode`, `simplest solution`, `yagni`, `ง่ายที่สุด`

## Flow (ladder — ใช้ขั้นล่างสุดที่ทำงานได้)
1. งานนี้ต้องมีอยู่ไหม (YAGNI)
2. stdlib/platform ก่อน dependency
3. ของมีอยู่ใน project ก่อน abstraction ใหม่
4. หนึ่งบรรทัดก่อนห้าสิบ; extract เมื่อเกิดซ้ำจริงเป็นครั้งที่สอง

## Checkpoint (เก็บเฉพาะ 4 อย่าง)
objective หนึ่งประโยค · การตัดสินใจ + why บรรทัดเดียว · จุด resume (file:line/cmd) · blocker เปิด

## Hard rules
ไม่และความง่ายลงบน safety/correctness/review gate — ceremony ลดได้ ความปลอดภัยลดไม่ได้
