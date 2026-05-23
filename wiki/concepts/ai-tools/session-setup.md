---
type: concept
tags: [workflow, claude-code, github, local-backup, setup]
sources: []
created: 2026-04-22
updated: 2026-05-17
---

# Session Setup — ขั้นตอนก่อนเริ่ม Wiki Session

## ทำไมถึงต้องมี checklist นี้

Wiki นี้ใช้ **folder `/Users/aase7en/Desktop/InW-Wiki` เป็น working copy หลัก**, ใช้ **GitHub เป็น sync หลัก**, และเก็บไฟล์ใหญ่แบบ **local-only/manual backup**:
- **GitHub** — เก็บ wiki, index, config, และ `raw/*.md` ที่เป็น text source
- **Local-only/manual backup** — เก็บไฟล์ใหญ่ใต้ `raw/` เช่น PDF, รูปภาพ, CSV, JSON ที่ gitignore ไว้

Google Drive ไม่ใช่ dependency ของ Wiki นี้แล้ว และไม่ควรใช้ sync โฟลเดอร์ Wiki หลัก

---

## Checklist ก่อนเริ่ม Session

### ขั้นตอนที่ 1 — Git Pull

**ทาง Terminal:**
```bash
cd '/Users/aase7en/Desktop/InW-Wiki'
git pull
```

**ทาง VS Code (ง่ายกว่า):**
- เปิด folder wiki ใน VS Code
- กด Source Control (Ctrl+Shift+G)
- กด "Sync Changes" หรือ pull icon

### ขั้นตอนที่ 2 — ตรวจ Git metadata ปกติ

บนเครื่องนี้ย้าย Git metadata กลับเข้า repo ปกติแล้วเมื่อ 2026-05-17:

```bash
test -d .git && git status --short --branch
# ควรได้: ## main...origin/main
```

สถานะที่ถูกต้องตอนนี้คือ `.git/` เป็น **directory** อยู่ใน `/Users/aase7en/Desktop/InW-Wiki`

ถ้า `.git` เป็น pointer ไป `/Users/aase7en/git-data/Aase7en-InW-Wiki.git` แปลว่าเจอ legacy setup จากยุค Google Drive redirect; ยังใช้ได้ แต่ไม่ใช่ preferred setup ของ Wiki นี้แล้ว

### ขั้นตอนที่ 3 — ตรวจ local-only raw files เมื่อจำเป็น

ตรวจเฉพาะเมื่อจะอ่านหรือ ingest ไฟล์ใหญ่:
- ตรวจ path ที่ระบุใน `wiki/context/local-sources.md` ว่ายังมีอยู่ใต้ `raw/`
- ถ้าไฟล์หาย ให้ copy/restore จากเครื่องหลักหรือ local backup ก่อน
- ห้ามย้าย `raw/` ทั้งก้อนออกจาก vault โดยไม่มี symlink/mount ที่ทำให้ path `raw/...` ยังอยู่

---

## โครงสร้างการเก็บไฟล์

```text
GitHub (git pull/push)                 Local-only/manual backup
├── CLAUDE.md                          └── raw/ large ignored files
├── wiki/                                  ├── assets/
│   ├── context/                           ├── pharmacy/*.json
│   ├── entities/                          ├── UthaiHospital/*.pdf
│   ├── concepts/                          └── ...
│   ├── sources/
│   └── synthesis/
├── raw/          ← logical source path ต้องคงไว้
│   ├── *.md      ← tracked text sources
│   └── ...       ← ignored large files on machines that need them
├── index*.md
└── log.md
```

---

## ทำไมไฟล์ใหญ่ใต้ raw/ ไม่อยู่ใน GitHub?

GitHub มี hard limit 100MB ต่อไฟล์ และไฟล์ binary/data ใหญ่ไม่คุ้มกับ git version control
ไฟล์ binary (PDF, รูปภาพ) ไม่ได้รับประโยชน์จาก git version control
จึงเก็บเป็น local-only/manual backup และใส่ `raw/assets/`, `raw/**/*.pdf`, `raw/**/*.json`, ฯลฯ ใน `.gitignore`

> Decision 2026-05-17: ไม่ย้าย `raw/` ทั้งก้อนออกจาก vault เพราะ Obsidian links, `/ingest`, hooks, และ source metadata อ้าง path `raw/...` อยู่จำนวนมาก

---

## VS Code vs Terminal — อันไหนดีกว่า?

| | VS Code + Claude Code Extension | Terminal Claude Code |
|--|--------------------------------|---------------------|
| Token ที่ใช้ | **เท่ากันทุกประการ** | **เท่ากันทุกประการ** |
| Git pull | ✅ ทำผ่าน UI ได้เลย | ต้อง run terminal |
| ดูไฟล์ diff | ✅ Built-in | ต้องใช้ git diff |
| Convenience | ✅ สูงกว่า | ปานกลาง |

**สรุป**: VS Code สะดวกกว่า token เท่ากัน — แนะนำใช้ VS Code

---

## ความสัมพันธ์
- [[wiki/synthesis/dual-ai-workflow]] — workflow Gemini + Claude
- [[wiki/entities/ai-tools/hermes-agent]] — alternative CLI agent
