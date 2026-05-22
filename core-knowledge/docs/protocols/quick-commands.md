# Quick Commands — คำสั่งลัดทุก session

> อ่านไฟล์นี้เมื่อ user พิมพ์ `/` หรือถามว่ามีคำสั่งอะไรบ้าง
> Reference ใน CLAUDE.md (root) — รายการเต็มอยู่ที่นี่

---

## คำสั่งหลัก (mobile + desktop)

| คำสั่ง | Claude ทำอะไร |
|--------|--------------|
| `/verify <ข้อความ>` | delegate ไปยัง engine ที่มี (WebSearch built-in → Web Research Layer) → ตรวจสอบข้อมูลพร้อม source URL |
| `/search <หัวข้อ>` | ค้นหาข้อมูลใหม่ → สรุป → ถามว่าจะ ingest ลง wiki ไหม |
| `/status` | สรุปสถานะ wiki: จำนวนหน้า, หน้าที่ค้างอัปเดต, stale pages |
| `/lint` | ตรวจสุขภาพ wiki ทั้งหมด — **delegate `general-purpose` subagent** |
| `/today` | สรุปสิ่งที่ทำใน session นี้ พร้อม commit message แนะนำ |
| `/ingest <URL หรือ text>` | เริ่ม ingest workflow ทันที ข้ามขั้นตอน confirmation |
| `/snapshot-nb [domain]` | export wiki → `exports/notebooklm/` (desktop only) |
| `/ask-nb <คำถาม>` | แนะนำ user ถาม NotebookLM ก่อน → รอ paste คำตอบ → Claude action ต่อ |
| `/compact [focus]` | บีบอัด context กลาง session (ประหยัด 40-60%) — ใช้หลังจบ subtask เช่น `/compact focus on wiki edits` |
| `/clear` | เคลียร์ context ทั้งหมด — ใช้เมื่อเปลี่ยน task ใหม่ที่ไม่เกี่ยวกัน (ทำ `/rename <task>` ก่อนเสมอ) |

## คำสั่งจาก Superpowers-adapted skills (auto-invoke)

ไม่ต้องพิมพ์ `/` — Claude trigger จาก keyword ใน user message:

| Skill | Trigger keywords | สิ่งที่บังคับ |
|---|---|---|
| `brainstorm-before-build` | "ออกแบบ", "วางระบบ", "สร้างฟีเจอร์", "/brainstorm" | clarify 3 ข้อ → เสนอ 2-3 approach → user เลือกก่อนเริ่ม |
| `verify-before-done` | "เสร็จแล้ว", "done", "/today", "commit" | 4-point self-check ก่อนบอกเสร็จ |
| `root-cause-first` | "แก้บั๊ก", "ทำไมพัง", "error", "ไม่ทำงาน" | reproduce → root cause 1 ประโยค → fix |

## คำสั่ง git workflow

| คำสั่ง | ผลลัพธ์ |
|---|---|
| `git push origin <branch>` | OK ถ้า `<branch>` ไม่ใช่ main/master |
| `git push origin main` | ❌ **BLOCK** โดย `.claude/hooks/check-bash-push-main.sh` — ใช้ PR แทน |
| `git pull origin main` | OK (SessionStart hook ทำให้อัตโนมัติทุก session แล้ว) |

## Related

- `.claude/skills/*/SKILL.md` — skill definitions + workflows
- `docs/protocols/delegation.md` — engine fallback ของ /search, /verify
- `docs/protocols/notebooklm.md` — workflow ของ /snapshot-nb, /ask-nb
- `wiki/concepts/ai-tools/context-management.md` — `/compact`, `/clear` deep dive
