# Hermes Config Migration — MacBook → Raspberry Pi 5

**Date**: 2026-06-20 | **Profile**: `tech_and_ai_architect`

## ภาพรวม (Overview)

การย้าย configuration ทั้งหมดของ Hermes จาก MacBook ไปยัง Raspberry Pi 5
ประกอบด้วย: config.yaml, SOUL.md, skills (77), memories, cron jobs, toolsets, provider settings

## สิ่งที่อยู่ใน Package (What's Included)

| ไฟล์/โฟลเดอร์ | รายละเอียด |
|---------------|-----------|
| `config.yaml` | ตั้งค่าทั้งหมด — model, provider, toolsets, terminal, display, memory, delegation |
| `SOUL.md` | Agent persona ภาษาไทย |
| `skills/` | 77 skills — A-Wiki, creative, github, mlops, media, research, productivity |
| `memories/MEMORY.md` | ความจำ跨 session — A-Wiki path, cron jobs, project status |
| `memories/USER.md` | ข้อมูลผู้ใช้ — Thai language, dashboard preferences |
| `cron/` | Cron job definitions |

## สิ่งที่ต้องทำ Manual (ต้องจัดการเอง)

ไฟล์เหล่านี้ **ไม่อยู่ใน package** เพราะเป็น secrets — ต้อง copy เอง:

### 1. API Keys (.env)

```bash
# บน MacBook — copy .env ไป Pi5
scp ~/.hermes/profiles/tech_and_ai_architect/.env pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/
scp ~/.hermes/.env pi@umbrel.local:~/.hermes/
```

### 2. OAuth Tokens (auth.json)

```bash
# บน MacBook — copy auth.json ไป Pi5
scp ~/.hermes/profiles/tech_and_ai_architect/auth.json pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/
scp ~/.hermes/auth.json pi@umbrel.local:~/.hermes/
scp ~/.hermes/shared/nous_auth.json pi@umbrel.local:~/.hermes/shared/
```

## วิธีการ Import บน Pi5

### วิธีที่ 1: Import โดยตรง (แนะนำ)

```bash
# 1. Copy package ไป Pi5
scp scripts/hermes/hermes-export-*.tar.gz pi@umbrel.local:~/

# 2. SSH เข้า Pi5
ssh pi@umbrel.local

# 3. Import profile
hermes profile import ~/hermes-export-*.tar.gz

# 4. Copy secrets (ทำจาก MacBook)
#    (ดูคำสั่ง scp ด้านบน)

# 5. ปรับ path สำหรับ Pi5
hermes -p tech_and_ai_architect config set terminal.cwd /home/pi/A-Wiki

# 6. ตรวจสอบ
hermes -p tech_and_ai_architect doctor
hermes -p tech_and_ai_architect skills list
```

### วิธีที่ 2: Git Pull + Script

```bash
# บน Pi5 — pull A-Wiki repo แล้วรัน import script
cd ~/A-Wiki
git pull
bash scripts/hermes/import-on-pi5.sh scripts/hermes/hermes-export-*.tar.gz
```

### วิธีที่ 3: ใช้ Script เต็มรูปแบบ

```bash
# บน Pi5
bash scripts/hermes/import-on-pi5.sh ~/hermes-export-20260620.tar.gz
```

Script จะ:
1. Backup profile เดิม (ถ้ามี)
2. Import profile ใหม่
3. แจ้งเตือน path ที่ต้องปรับ
4. ตรวจสอบจำนวน skills

## หลัง Import — ปรับแต่งสำหรับ Pi5

```bash
# 1. ตั้งค่า working directory (ตามที่ A-Wiki อยู่บน Pi5)
hermes -p tech_and_ai_architect config set terminal.cwd /home/pi/A-Wiki

# 2. ตรวจสอบ model/provider (ถ้าต้องการใช้คนละตัวกับ MacBook)
hermes -p tech_and_ai_architect model

# 3. ตรวจสอบ tools
hermes -p tech_and_ai_architect tools

# 4. เปิด gateway (ถ้าต้องการ Telegram/Discord)
hermes -p tech_and_ai_architect gateway setup

# 5. ตรวจสุขภาพระบบ
hermes -p tech_and_ai_architect doctor --fix
```

## Path Differences — Mac vs Pi5

| Setting | MacBook | Pi5 |
|---------|---------|-----|
| `terminal.cwd` | `/Users/aase7en/Desktop/A-Wiki` | `/home/pi/A-Wiki` |
| `HOME` | `/Users/aase7en` | `/home/pi` |
| Shell | zsh | bash |
| Python | python3 (macOS) | python3 (Linux ARM64) |

## โครงสร้างไฟล์ใน Package

```
tech_and_ai_architect/
├── config.yaml          # ตั้งค่าหลัก
├── SOUL.md              # Persona ภาษาไทย
├── skills/              # 77 skills
│   ├── awiki/           # A-Wiki core skills
│   ├── creative/        # Design, art, music
│   ├── github/          # GitHub workflows
│   ├── mlops/           # ML/AI tools
│   └── ...
├── memories/
│   ├── MEMORY.md        # Agent memory
│   └── USER.md          # User profile
├── cron/                # Cron job definitions
└── hooks/               # Session hooks
```

## Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|--------|
| Skills ไม่โหลด | `hermes -p tech_and_ai_architect skills check` |
| Model ไม่ทำงาน | ตรวจสอบ API key ใน `.env` → `hermes -p tech_and_ai_architect auth list` |
| Config ไม่ตรง | `hermes -p tech_and_ai_architect config check` |
| Path ไม่ถูก | `hermes -p tech_and_ai_architect config set terminal.cwd /path/to/A-Wiki` |
| Secrets หาย | Copy `.env` และ `auth.json` manual (ดูด้านบน) |
