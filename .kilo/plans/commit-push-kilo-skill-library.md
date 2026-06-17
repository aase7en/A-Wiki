# Plan: Commit & Push Kilo skill library (verified)

## Goal
ตรวจสอบ staged changes ในรูป Source Control แล้ว commit & push ไป `main` (ตามคำขอผู้ใช้ + Iron Law #6: commit ตรง main, ไม่มี branch/PR/worktree)

## Verified current state (read-only)
- สาขาปัจจุบัน: **`main`** ✓ (ถูกต้องตามกฎ)
- Staged: **217 files / +35,463 insertions** ทั้งหมดเป็นการเพิ่มใหม่ (`+++`)
  - `.kilo/agents/` → `code-simplifier.md`, `docs-specialist.md`
  - `.kilo/plans/fix-indexing-free-embed-orchestrator.md`
  - `.kilo/skills/**` → ชุด skills ใหญ่ (agent-md-refactor, angular-*, vercel-*, react rules, webapp-testing, youtube-downloader, ฯลฯ)
  - `tests/test_kilo_skill_discovery.py`
- Unstaged/Untracked: **ไม่มี** (ทุกอย่าง staged หมดแล้ว)
- Commit message ที่ staged ในรูป:
  `feat(kilo): add extensive skill library and indexing configuration` + body (Angular/Vercel/research skills + agent defs + indexing config + discovery tests) — ตรง format `type(scope): description` ของ repo ✓
- Remote: `origin/main` (upstream ผูกอยู่) ; commit ล่าสุด `37a839bc fix(kilo): switch indexing embed provider to Gemini free tier`

## Hooks / guards ที่เกี่ยวข้อง
- `.git/hooks/pre-commit` = react-doctor soft-scan: แม้จะเจอ warning ก็ **ไม่ block** (แค่พิมพ์ stderr) และไม่มีไฟล์ React/TSX ในชุด staged จึง N/A
- ก่อน push จะรัน `scripts/check-privacy.py` ป้องกัน personal path/codename/secret รั่ว

## Steps (execution phase)
1. **Final verify** (read-only)
   - `git status --porcelain` ยืนยันไม่มี unstaged เหลือ
   - `git diff --cached --stat` สรุปขอบเขตอีกครั้ง
2. **Privacy scan** (read-only safety)
   - `python3 scripts/check-privacy.py` (หรือกำหนด target ที่ staged) → หากเจอ personal path/secret หยุดแจ้งผู้ใช้ก่อน commit
3. **Commit** (บน `main`, ไม่สร้าง branch)
   - ใช้ message ที่ staged ในรูป: `feat(kilo): add extensive skill library and indexing configuration` + body
   - `git commit` (pre-commit hook ทำงานเอง, soft)
4. **Push**
   - `git push origin main` (no `--force`)
5. **Verify result**
   - `git log --oneline -1`, `git show --stat HEAD | tail`, `git status` (clean)
   - ยืนยัน `origin/main` เดินเท่ากับ HEAD (`git rev-parse HEAD origin/main`)

## Notes / risks
- ชุดเป็น docs + skills (markdown/python) ไม่ใช่ production code → ไม่ต้องเขียน failing test ก่อน (Iron Law #1 ไม่ผูกกับการ commit docs/skills)
- diff ใหญ่ (~35k บรรทัด) push อาจใช้เวลาเล็กน้อย
- หาก pre-commit hook พยายาม `npx react-doctor@latest` (ดาวน์โหลด) อาจช้าแต่ไม่ block — ถ้าช้ามากอาจ `--no-verify` **ไม่ได้** เพราะต้องเคารพ hook; แต่ hook soft อยู่แล้ว
- ผู้ใช้อนุญาต commit & push แล้วอย่างชัดเจน ✓
