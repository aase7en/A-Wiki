# /A-Claim — ระบบจองงานข้าม agent — ประกาศ scope+goal+phase ก่อนเริ่ม, เห็น

Maps to: `skills/awiki/a-claim/SKILL.md`

## When to use
- ก่อนแก้ shared surface (skills/, scripts/, commands/, registry, AGENTS.md) — **บังคับ**
- ก่อนเริ่มงานไม่ trivial → `claim_list` ดูว่ามี agent อื่นทำอยู่ไหม

Auto-picks on: `claim`, `จอง`, `agent อื่น`, `ชนกัน`, `coordination`

## Flow
1. claim_list ดูก่อน
2. claim_acquire ประกาศ scope+goal
3. ทำงาน
4. claim_advance ตาม phase
5. claim_release

เต็ม ๆ: `skills/awiki/a-claim/SKILL.md` · ตาราง routing: `wiki/A-ROUTER.md`
