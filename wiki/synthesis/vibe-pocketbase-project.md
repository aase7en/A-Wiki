---
type: synthesis
tags: [vibe-coding, pocketbase, react, vite, tailwind, self-hosted, otp-login, nginx, cloudflare-r2]
sources: [vibe-pocketbase-gemini-plan]
created: 2026-05-11
updated: 2026-05-11
---

# Vibe Coding: PocketBase + React Project Plan

## คำถามที่ตอบ

"จะสร้าง web application แทน Excel สำหรับจัดการข้อมูลโดยใช้ Vibe Coding methodology กับ PocketBase ได้อย่างไร?"

## สรุป

สร้าง full-stack web app ด้วย React + Vite (frontend) และ PocketBase (backend) ตาม Vibe Coding approach — ใช้ AI เป็น co-pilot เขียนโค้ด, ออกแบบ DB ผ่าน Admin UI, deploy บน VPS + Nginx + backup อัตโนมัติ

ประมาณการเวลา: **1-2 ชั่วโมง** ต่อ feature ถ้าใช้ AI ช่วย

## Tech Stack

```
[React + Vite + TailwindCSS]  ← frontend
         ↕  PocketBase SDK (npm)
[PocketBase :8090]            ← backend (single binary)
         ↕  pb_data/data.db
[SQLite]                      ← database
         ↕
[Nginx :80/443]               ← reverse proxy
[Cloudflare R2]               ← backup storage
```

## โครงสร้าง Project

```
vibe_pocketbase_project/
├── .ai/
│   ├── rules.md               ← กฎ + tech stack สำหรับ AI
│   └── skills/
│       ├── pocketbase-crud.md ← คู่มือ CRUD pattern
│       └── otp-login.md       ← คู่มือ OTP Login
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env                   ← VITE_PB_URL=http://127.0.0.1:8090
├── backend/
│   ├── pocketbase             ← binary file
│   ├── pb_data/               ← SQLite data (ห้าม AI แก้ตรง)
│   └── pb_migrations/         ← schema history (track ด้วย git)
└── infra/
    ├── nginx.conf             ← reverse proxy config
    └── backup_to_r2.sh        ← cron backup script
```

## Roadmap 4 ขั้น

### Step 1: Setup (ชั่วโมงที่ 1)

```bash
# 1. ดาวน์โหลด PocketBase
wget https://github.com/pocketbase/pocketbase/releases/latest/...
chmod +x pocketbase && ./pocketbase serve

# 2. สร้าง React app
npm create vite@latest frontend -- --template react
cd frontend && npm install pocketbase
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Prompt ให้ AI**:
> "ช่วยสร้างโครงโปรเจกต์ React ด้วย Vite ให้หน่อย และสอนวิธีรัน Pocketbase ไฟล์เดียวบนเครื่องของฉัน"

### Step 2: OTP Login

**Pattern OTP ที่ Gemini แนะนำ**:
1. สร้างฟังก์ชันส่ง OTP (จำลอง หรือต่อ SMS provider)
2. บันทึก OTP ชั่วคราวใน PocketBase collection `otp_tokens`
3. User กรอก OTP → verify → `pb.collection('users').authWithPassword()`

**Prompt ให้ AI**:
> "เขียนหน้าจอ Login ด้วย OTP โดยเชื่อมต่อกับ PocketBase SDK, UI แบบ Minimal ใช้ Tailwind, ห้ามใช้ Redux"

### Step 3: CRUD แทน Excel

1. ออกแบบ schema ผ่าน **PocketBase Admin UI** (คลิก ไม่ต้องเขียนโค้ด)
2. API งอกให้อัตโนมัติ
3. สั่ง AI เขียน frontend CRUD component

**Prompt ให้ AI**:
> "ฉันมีข้อมูลแบบ Excel [ส่ง column list ให้ AI] ช่วยออกแบบ DB Schema สำหรับ PocketBase และเขียนหน้าเว็บ CRUD พวกนี้ให้หน่อย"

### Step 4: Deploy + Backup

**nginx.conf** (reverse proxy):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**backup_to_r2.sh** (cron ทุกเที่ยงคืน):
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
zip /tmp/pb_backup_${DATE}.zip /path/to/pb_data/data.db
# aws s3 cp หรือ rclone ส่งขึ้น R2
rclone copy /tmp/pb_backup_${DATE}.zip r2:your-bucket/backups/
rm /tmp/pb_backup_${DATE}.zip
```

```bash
# crontab -e
0 0 * * * /path/to/backup_to_r2.sh >> /var/log/pb_backup.log 2>&1
```

## MCP ที่อาจเสริม (Optional)

| MCP | ประโยชน์ | ต้องการไหม |
|-----|---------|-----------|
| SQLite MCP | AI query `pb_data/data.db` ตรงได้ เมื่อ data พัง | Optional — ช่วยเมื่อต้อง debug DB |
| Brave Search / Web Search | AI ค้น PocketBase Docs เวอร์ชันล่าสุด | Optional — ใช้เมื่อ SDK เปลี่ยน |

> ตามคำแนะนำ Gemini: **ไม่จำเป็นต้องมี MCP** สำหรับ project เล็ก PocketBase Admin UI ครบพอ

## `.ai/rules.md` Template

```markdown
# Vibe Coding: Pocketbase + Frontend

## Tech Stack
- Frontend: React (Vite) + TailwindCSS
- Backend: Pocketbase (รันที่ http://127.0.0.1:8090)

## Core Philosophy (Vibe Code)
- Keep it simple — ไม่ต้องใช้ Redux หรือ state management ซับซ้อน
- เป้าหมายคือทำระบบจัดการข้อมูลแทน Excel ให้เร็วที่สุด
- ใช้ Pocketbase SDK (`pocketbase` npm package) เสมอ

## Pocketbase Rules
- Collection `users` ใช้ที่มากับ PocketBase
- OTP Login: ส่ง OTP → บันทึกใน PB → verify → authWithPassword()

## Infrastructure
- Nginx: reverse proxy port 80/443 → 127.0.0.1:8090
- Backup: zip pb_data/data.db → Cloudflare R2 ทุกเที่ยงคืน
```

## การวิเคราะห์

โปรเจ็คนี้เหมาะมากสำหรับ:
- **Internal tools**: แทน Google Sheets / Airtable สำหรับทีมเล็ก
- **Pharmacy order management**: ต่อยอดจาก [[synthesis/pharmacy-order-checker]]
- **Environmental health data**: แทน AppSheet (ดู [[synthesis/appsheet-to-webapp-pi5]])
- **Personal projects**: ที่ต้องการ backend แต่ไม่อยากเสียค่า SaaS

Stack นี้เหมาะมากกับ Pi 5 ที่มีอยู่แล้ว — PocketBase รันได้บน ARM64 สบาย

## แหล่งข้อมูลที่ใช้

- [[sources/vibe-pocketbase-gemini-plan]] — แผน project structure จาก Gemini Pro
- [[entities/ai-tools/pocketbase]]
- [[concepts/ai-tools/vibe-coding]]
