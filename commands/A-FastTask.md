Maps to: `skills/awiki/a-fasttask/SKILL.md`

## When to use
- งาน repository ที่ไม่ trivial และต้องเลือก workflow / executor / lane
- ต้องเร่งงานด้วย parallel lanes ที่ไม่ overlap
- resume / takeover หลัง agent หยุด, rate-limit หรือ transport failure
- closeout temporary worktree/lane โดยต้องมี evidence ก่อน cleanup

## Routing
1. อ่าน `skills/awiki/a-fasttask/SKILL.md`
2. bind authority ของ repository ปัจจุบันก่อน mutation
3. ถ้ามี repo-local A-FastTask ให้ defer ไป binding นั้น
4. ถ้า authority/ownership ขัดแย้งหรือไม่ชัด ให้ fail closed — ห้ามสร้าง claim/review/completion system ซ้ำ

Bypass งาน Q&A, edit เล็กที่ชัดเจน หรือ mid-lane ที่ workflow/claim ถูก bind อยู่แล้ว.

เต็ม ๆ: `skills/awiki/a-fasttask/SKILL.md`
