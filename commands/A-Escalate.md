# /A-Escalate — แพ็คปัญหาที่ติดเป็น prompt พร้อมบริบทครบ…

Maps to: `skills/awiki/a-escalate/SKILL.md`

## When to use
- ติดวนเกิน 3 รอบ
- อยาก second opinion จากโมเดลใหญ่กว่า

Auto-picks on: `ส่งให้โมเดลอื่น`, `escalate`, `ถามโมเดลที่เก่งกว่า`, `second opinion`

## Flow
1. รวบรวม goal + constraints
2. ดึงสิ่งที่ลองแล้วจาก memory-ledger
3. แนบ excerpt ไฟล์
4. render เป็น exports/escalate/<slug>.md
5. user ก๊อปไปวาง

เต็ม ๆ: `skills/awiki/a-escalate/SKILL.md` · ตาราง routing: `wiki/A-ROUTER.md`
