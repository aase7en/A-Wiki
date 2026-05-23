---
name: verify-before-done
description: Use BEFORE declaring task complete OR before any destructive git op (reset --hard, clean -f, checkout --, restore, branch -D). Triggers: "เสร็จแล้ว", "done", "/today", "git commit", "พร้อม push", "ทำเสร็จ", "git reset", "git clean", "git checkout --". Forces 4-point self-check + git-safety check. SKIP for read-only operations.
---

# verify-before-done

> Adapted from Superpowers `verification-before-completion` — wiki+coding hybrid

## เมื่อไหร่ใช้

✅ ก่อนตอบ user ว่า "เสร็จแล้ว / done / completed"
✅ ก่อน `git commit`
✅ ก่อน mark todo เป็น completed (สำหรับงานใหญ่)
✅ ก่อน session end protocol
✅ **ก่อน destructive git ops** (reset --hard, clean -f, checkout --, restore, branch -D) — ดู §5
❌ ข้าม: query ที่ไม่แก้ไฟล์, /status, /lint (read-only)

## Iron Law

> **NO "DONE" WITHOUT 4-POINT SELF-CHECK**

ตอบ "เสร็จแล้ว" → ห้าม! ตอบ "verify เสร็จแล้ว ตามนี้:" แทน

## 4-Point Self-Check (บังคับทุกข้อ)

### ✅ 1. ตอบโจทย์ user request?
- user ขออะไรตอนแรก? (ย้อนอ่าน user message แรก)
- สิ่งที่ทำ match ไหม? (ไม่ใช่แค่ "ทำอะไรซักอย่างที่เกี่ยวข้อง")
- ถ้า scope บาน → แจ้ง user ว่า "ทำเกินไปด้วย X — ต้องการไหม?"

### ✅ 2. Test / lint / build pass?
- ถ้าแก้ code → รัน test ที่เกี่ยวข้อง
- ถ้าแก้ wiki → ดูว่า cross-reference ยัง valid ไหม (broken link?)
- ถ้าแก้ hook → ทดสอบ hook execute ได้ไม่ error
- **ถ้าไม่ได้ test → บอก user ตรงๆ ว่า "ยังไม่ได้ verify ด้วย X"**

### ✅ 3. Side effects?
- ไฟล์อื่นที่อาจกระทบ — check
- skill/hook ที่อาจ overlap — check
- token footprint เพิ่มขึ้นไหม? ระบุตัวเลข
- มี broken backward compat ไหม?

### ✅ 4. Memory + log updated?
- `log.md` มี entry ใหม่ไหม? (สำหรับงานใหญ่)
- `wiki/context/wiki-overview.md` ต้อง regenerate ไหม? (ถ้าแก้ wiki หลายหน้า)
- `wiki/context/session-memory.md` มีประเด็นค้างจะบันทึกไหม?

### ✅ 5. Git-safety (เฉพาะก่อน destructive git ops)

> เพิ่มเข้ามาหลังเหตุการณ์ 2026-05-15: `git reset --hard` ทำลาย uncommitted edits ใน 5 ไฟล์
> Hook `check-bash-destructive-git.sh` ป้องกันชั้น hard อยู่แล้ว — skill นี้คือชั้น discipline

ถ้าจะรัน destructive git command (reset --hard, clean -f, checkout --, restore, branch -D):

1. **`git status` FIRST** — ดูทุกไฟล์ที่ modified/untracked แบบเต็ม:
   ```bash
   git status
   git status --porcelain  # short form
   ```
2. **สรุปให้ user ฟัง** — บอกชัดเจนว่าจะมีอะไรหายไป:
   ```
   จะรัน: git reset --hard origin/main
   จะหาย: 
     - M  log.md (2 lines append)
     - ?? new-script.sh (untracked, 50 lines)
   ```
3. **เสนอ stash ก่อน** — แทบทุกครั้งที่ destructive ทำตอน WT dirty ควรเริ่มด้วย stash:
   ```bash
   git stash push -u -m "before-<reason>"
   <destructive command>
   # ถ้าเปลี่ยนใจ: git stash pop
   ```
4. **รอ user confirm** — ห้ามรันเองถ้า user ไม่ได้ approve

**ข้อยกเว้น**: ถ้า `git status --porcelain` empty (WT clean) → ข้ามขั้นตอนนี้ได้ (hook ก็จะ allow)

## รูปแบบรายงาน

```
Verify: ✅ done | ❌ failed | ⚠️ partial

1. User request match: [✅/❌] [1 บรรทัด]
2. Test/lint: [✅/❌/skip] [reason]
3. Side effects: [none / list]
4. Memory: [updated / not needed]

[ถ้ามี ❌ → ห้ามบอก done — บอก blocker แทน]
```

## Red flags (STOP signals)

- "น่าจะใช้ได้แล้ว" → ไม่ verify → ไม่ใช่ done
- "เดี๋ยว user เทสเอง" → ผลักภาระ → ไม่ใช่ done
- "พรุ่งนี้ค่อยดู edge case" → partial → ระบุชัด ไม่ใช่ done

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "งานเล็ก ไม่ต้อง verify" | 30 วินาที self-check < แก้ bug 30 นาทีทีหลัง |
| "test ใช้ token เยอะ" | grep + ls + read 1 ไฟล์ = <100 token. ถูกกว่า rework รอบ 2 มาก |
| "user รีบ" | user รีบทำงาน**เสร็จ**ไม่ใช่รีบทำงาน**พัง** |

## ตัวอย่าง

**Bad**:
```
claude: เสร็จแล้วครับ สร้าง skill ทั้ง 3 อันให้แล้ว
```

**Good**:
```
claude: Verify ✅ partial:
1. User request match: ✅ cherry-pick 3 skills + ปรับ Thai
2. Test: ⚠️ ยังไม่ได้ทดสอบ trigger จริง (จะลอง /brainstorm หลังเสร็จ)
3. Side effects: เพิ่ม ~90 tokens (3 descriptions) — ต่ำกว่า budget
4. Memory: ❌ ยังไม่ได้ update log.md → จะทำหลัง Step 5 จบ

Blocker: เหลือ hook + memory file → ยังไม่ done เต็มที่
```
