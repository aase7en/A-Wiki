---
type: source
title: "แผน Vibe Coding: Pocketbase + Frontend — คำแนะนำจาก Gemini Pro"
slug: vibe-pocketbase-gemini-plan
date_ingested: 2026-05-11
original_file: (paste จาก chat)
tags: [vibe-coding, pocketbase, react, vite, tailwind, infra, nginx, cloudflare-r2]
---

# แผน Vibe Coding: Pocketbase + Frontend — คำแนะนำจาก Gemini Pro

**ประเภท**: คำแนะนำจาก AI (Gemini Pro) — วิธีตั้ง project structure สำหรับ vibe coding  
**วันที่**: 2026-05-11  
**ผู้เขียน**: Gemini Pro (paste โดยผู้ใช้)

## ประเด็นหลัก

1. **โครงสร้างโฟลเดอร์ที่แนะนำ** — แบ่ง 4 ส่วนชัดเจน: `.ai/`, `frontend/`, `backend/`, `infra/`
2. **Tech stack**: React + Vite + TailwindCSS (frontend) + PocketBase self-hosted (backend)
3. **ปรัชญา Vibe Code**: Keep it simple — ไม่ใช้ state management ซับซ้อน (ไม่ต้องมี Redux) — เน้นสร้างเร็ว
4. **PocketBase ฉลาดในตัวเอง** — Admin UI สร้าง table ได้เหมือน Excel และงอก REST API ให้อัตโนมัติ
5. **MCP optional**: SQLite MCP (query DB ตรง) + Brave Search MCP (ดึง Docs ล่าสุด) — ไม่บังคับ
6. **Roadmap 4 ขั้น**: Setup → OTP Login → CRUD แทน Excel → Deploy + Backup

## โครงสร้าง Project ที่แนะนำ

```
vibe_pocketbase_project/
├── .ai/                       # rules.md + skills/
│   └── skills/
│       ├── pocketbase-crud.md
│       └── otp-login.md
├── frontend/                  # React + Vite + Tailwind
│   ├── src/
│   ├── package.json
│   └── .env                   # VITE_PB_URL=http://127.0.0.1:8090
├── backend/                   # PocketBase
│   ├── pocketbase             # binary
│   ├── pb_data/               # SQLite (ห้าม AI ยุ่ง)
│   └── pb_migrations/         # schema migrations
└── infra/
    ├── nginx.conf             # reverse proxy port 80/443 → 8090
    └── backup_to_r2.sh        # auto backup pb_data → Cloudflare R2
```

## Skill.md Template (`.ai/rules.md` หรือ `CLAUDE.md`)

```markdown
# Vibe Coding: Pocketbase + Frontend
## Tech Stack
- Frontend: React (Vite) + TailwindCSS
- Backend: Pocketbase (http://127.0.0.1:8090)
## Core Philosophy
- Keep it simple — ไม่ต้องใช้ Redux
- ใช้ Pocketbase SDK (`pocketbase` npm package) เสมอ
## Pocketbase Rules
- OTP Login: สร้างฟังก์ชันส่ง OTP → บันทึกใน PB → verify → authWithPassword()
## Infrastructure
- Nginx: reverse proxy port 80/443 → 127.0.0.1:8090
- Backup: zip pb_data/data.db → push Cloudflare R2 ทุกเที่ยงคืน
```

## Self-Study Roadmap (4 Steps)

| Step | Prompt ที่ใช้สั่ง AI |
|------|---------------------|
| 1 Setup | "ช่วยสร้างโครง React ด้วย Vite และสอนรัน PocketBase ไฟล์เดียว" |
| 2 OTP Login | "เขียนหน้า Login OTP เชื่อม PocketBase SDK — UI Tailwind Minimal" |
| 3 CRUD | "ออกแบบ DB Schema + หน้าเว็บ CRUD แทน Excel column ที่ให้" |
| 4 Deploy | "เขียน nginx.conf reverse proxy + script Backup pb_data → R2" |

## ข้อมูลที่น่าสนใจ

- PocketBase เป็น single binary — download แล้วรันได้เลย ไม่ต้อง install อะไร
- `pb_data/data.db` คือไฟล์ SQLite ที่เก็บข้อมูลทั้งหมด — backup แค่ไฟล์นี้พอ
- Gemini ย้ำว่า "ไม่จำเป็นต้องมี MCP" — PocketBase มี Admin UI + REST API ครบในตัว
- MCP ที่แนะนำ (optional): SQLite MCP (ให้ AI query DB ตรง), Brave Search MCP (ค้น Docs ล่าสุด)

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/ai-tools/pocketbase]]
- [[concepts/ai-tools/vibe-coding]]
- [[synthesis/vibe-pocketbase-project]]
