# /A — ทางเข้าเดียวของ A-Suite (one-entry)

Maps to: `skills/awiki/a-router/SKILL.md` (alias ทางการ: `/A-Router`)

## When to use
- มี objective แต่ไม่อยากจำชื่อคำสั่งอื่นเลย — พิมพ์ `/A <objective>` จบ
- อยากให้สมองเดิน spine ครบ 7 phase ให้เอง (think → grill ถามกลับ → council → implement → debug loop → verify)

## Flow
1. routing 3-tier: trigger ตรง → skill นั้น / description match → skill นั้น / **ไม่ match → default spine `a-flow`** (เดินกระบวนการเต็ม ไม่ตอบ "ไม่รู้")
2. คำถาม/คำทักทาย → เงียบ (ไม่ใช่ objective)

## Examples
- `/A ทำเว็บขายของ` → a-web (IMPLEMENT phase)
- `/A ออกแบบ dashboard พลังงาน` → a-plan (DESIGN + grill ≥3 คำถาม)
- `/A จัดระเบียบคลังภาพทั้งบริษัท` → a-flow default spine (ไม่มี skill เฉพาะ — เดินครบ think→grill→council→implement→debug→verify)
