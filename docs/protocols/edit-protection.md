# Edit Protection — CLAUDE.md ห้ามแก้โดยไม่ได้รับอนุญาต

> อ่านไฟล์นี้เมื่อต้อง setup lock, unlock, หรือ debug การ block edit
> Summary ใน CLAUDE.md (root) — รายละเอียดเต็มอยู่ที่นี่

---

## หลักการ

**กฎเหล็ก**: CLAUDE.md เป็น schema หลัก — Claude **ห้ามแก้ไขเอง** ทุกกรณี
ถ้าจะแก้ ต้อง user อนุญาต + unlock hook ให้ผ่าน

## กลไก 2 ชั้น (defense in depth)

### 1. Soft lock (Claude มีจิตสำนึก)

- เมื่อ user สั่งให้แก้ CLAUDE.md → Claude **หยุดทันที** + ตอบกลับ:
  > "CLAUDE.md ถูก protect ไว้ — กรุณาบอก password ก่อนแก้"
- รอ user พิมพ์ password → ตรวจกับเนื้อใน `.claude/lock.txt` (อ่านเงียบๆ **ห้าม echo password ใน chat**)
- ถ้าตรง → ดำเนินการแก้ + แจ้งสรุปสิ่งที่แก้
- ถ้าไม่ตรง → ปฏิเสธ + แจ้ง user ว่าผิด ลองใหม่ได้

### 2. Hard lock (PreToolUse hook)

- Hook script `.claude/hooks/check-claudemd-lock.sh` block tool `Edit/Write/MultiEdit` บน `CLAUDE.md`
- Hook ตรวจ `WIKI_UNLOCK` env var ว่าตรงกับ `.claude/lock.txt` ไหม
- ทำงานบน Claude Code CLI / VS Code / Mac/Win desktop — bypass ไม่ได้ผ่าน Claude (Edit tool)
- ⚠️ บน mobile / web Claude Code (cloud) — hook **อาจไม่รัน** → fallback เป็น soft lock เท่านั้น
- 📌 **Bash ไม่ block** — เพราะ matcher คือ `Edit|Write|MultiEdit` เท่านั้น. ใช้ Bash sed/python3 เลี่ยงได้ — โดยเจตนา (เจ้าของแก้ตรงได้เสมอ)

## Setup ครั้งแรก (ต่อเครื่อง)

```bash
cp .claude/lock.example .claude/lock.txt
# แก้ .claude/lock.txt → ลบ comment ออก เหลือ password บรรทัดเดียว
chmod 600 .claude/lock.txt
```

## Unlock (ทุก terminal session ที่อยากแก้ CLAUDE.md)

```bash
cd /Users/aase7en/Desktop/InW-Wiki
export WIKI_UNLOCK="$(cat .claude/lock.txt)"
claude    # launch Claude Code in this terminal → env var inherited
```

> ปิด terminal → env หาย → lock อัตโนมัติ
> ⚠️ **ต้อง launch claude ใน terminal ที่ export แล้ว** — Claude session ที่เปิดอยู่แล้วใน VS Code GUI **ไม่ได้** WIKI_UNLOCK เพราะ env var ไม่ propagate ข้าม process

## ขอบเขต

- ✅ Protect: `CLAUDE.md` (root) จาก Claude tool calls (`Edit` / `Write` / `MultiEdit`)
- ❌ ไม่ protect: external editor (Obsidian / vim / GitHub web UI) — ตามเจตนา (เจ้าของแก้ตรงได้เสมอ)
- ❌ ไม่ protect: ไฟล์อื่น (`Home.md`, `README.md`, `index*.md`, `wiki/**`)
- ❌ ไม่ protect: Bash commands (sed, python3 -c, mv) — ตามเจตนา

## ข้อจำกัดต้องรู้

- เป็น **deterrent** ไม่ใช่ encryption — `.claude/lock.txt` เก็บ plaintext (gitignored)
- กันแค่ Claude เผลอแก้ — ไม่กัน attacker ที่ access เครื่องได้แล้ว
- บน mobile/cloud env hard lock อาจไม่ทำงาน — ถ้าจำเป็นแก้ CLAUDE.md ให้ทำบน desktop

## Hook implementation note

- Hook ใช้ Python3 parse JSON (ไม่ต้องพึ่ง jq) — fallback เป็น sed ถ้า python3 ก็ไม่มี
- ถ้าทั้งคู่ไม่มี → fail-open (อนุญาต) เพราะการ block แบบไม่บอกอะไรเลยจะ debug ยาก
- บนระบบ production จริง: ติดตั้ง python3 (มีบน macOS/Linux เป็น default แล้ว)

## Security Rules (broader — applies to all wiki ops, not just CLAUDE.md)

1. **ห้าม commit credentials** — ถ้า source มี API key, password, token → อย่า copy ลง wiki
2. **ห้าม hardcode IP/MAC ส่วนตัว** ใน wiki pages (ให้ใช้ `<raspberry-pi-ip>` แทน)
3. **ห้ามแก้ raw/** — ถ้าต้องการ sanitize ให้ copy ไฟล์ออกมาก่อน (enforced by `check-raw-immutable.sh`)
4. **ตรวจ source ก่อน ingest** — ถ้า source มีข้อมูลส่วนตัวให้แจ้งผู้ใช้ก่อน
5. **ตรวจ exports/ ก่อน push** — script export-to-notebooklm ต้องไม่ leak secret/IP/MAC ออกไป NotebookLM
6. **CLAUDE.md ห้ามแก้เอง** — ต้อง user อนุญาต + WIKI_UNLOCK env (ดูส่วนบน)
7. **Destructive git ops** — `check-bash-destructive-git.sh` block reset --hard / clean -f / checkout -- เมื่อ WT dirty. Workaround: stash หรือ commit ก่อน
8. **Secret-leak scan ก่อน commit** — `check-secret-leak.sh` block `git commit` ถ้าเจอ sk-/ghp_/AKIA/AIza/JWT ใน staged diff

## Related

- `.claude/hooks/check-claudemd-lock.sh` — hook implementation
- `.claude/hooks/check-secret-leak.sh` — secret-leak scanner
- `.claude/hooks/check-raw-immutable.sh` — raw/ protection
- `.claude/hooks/check-bash-destructive-git.sh` — git ops guard
- `.claude/lock.example` → `.claude/lock.txt` — password template
- `.claude/settings.json` — PreToolUse matcher wiring
- `.gitignore` — `.claude/lock.txt` excluded (ห้าม commit password)
