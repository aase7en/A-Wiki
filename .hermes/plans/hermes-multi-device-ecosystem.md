# Hermes Multi-Device Ecosystem — Implementation Plan

> **Goal**: Hermes ทุกเครื่อง (MacBook, Windows, Pi5) 24/7 — config เดียวกัน, สำรองบทสนทนา, เพิ่มความฉลาด, Telegram, slash commands ครบ

**Architecture**: Git = config sync hub, Google Drive = backup, Pi5 = Telegram 24/7

**วันที่**: 2026-06-20 | **Profile**: `tech_and_ai_architect`

---

## Phase 1: Cross-Device Auto-Sync (Config Unification)

### Task 1.1: Auto-Sync Scripts — All Platforms
- `scripts/hermes/auto-sync-from-git.sh` ✅ (Linux/Pi5 — created)
- `scripts/hermes/auto-sync.ps1` 🆕 (Windows PowerShell)
- MacBook: manual export + push (user-initiated)

### Task 1.2: Pi5 Cron — ทุก 6 ชม.
```bash
# บน Umbrel Terminal
(crontab -l 2>/dev/null; echo "0 */6 * * * cd $HOME/A-Wiki && bash scripts/hermes/auto-sync-from-git.sh") | crontab -
```

### Task 1.3: Windows Auto-Sync (PowerShell)
- Clone A-Wiki → Task Scheduler ทุก 6 ชม.
- `hermes profile import` (native install, not Docker)

### Task 1.4: Unified Memory Sync
- SOUL.md + MEMORY.md + USER.md รวมใน export package แล้ว ✅
- Cron job weekly: compact + deduplicate memories

---

## Phase 2: Conversation Backup + Intelligence

### Task 2.1: Session Backup Script
- **File**: `scripts/hermes/backup-sessions.sh`
- Export: `hermes sessions export → JSONL.gz → drive/backups/hermes/`

### Task 2.2: Pi5 Auto-Backup (Docker)
```bash
# บน Pi5 host — daily 2AM
sudo -S -p '' docker exec hermes-agent_web_1 /opt/hermes/bin/hermes -p tech_and_ai_architect sessions export /tmp/sessions.jsonl
gzip /tmp/sessions.jsonl
mv /tmp/sessions.jsonl.gz ~/A-Wiki/drive/backups/hermes/sessions-$(date +%Y%m%d).jsonl.gz
```

### Task 2.3: Memory Compaction Script
- **File**: `scripts/hermes/compact-memories.py`
- อ่าน MEMORY.md + USER.md → deduplicate → summarize → write back
- Run: weekly cron

---

## Phase 3: Google Drive Backup (A-Wiki-Data)

### Task 3.1: Backup Structure
```
drive/backups/hermes/
├── sessions/       # JSONL.gz — daily
├── config/         # config.yaml snapshots
├── memories/       # MEMORY.md + USER.md
└── skills/         # skills backup
```

### Task 3.2: MacBook → Drive Script
- **File**: `scripts/hermes/backup-to-drive.sh`
- Hermes cron job: daily 3AM → export sessions → copy to drive

### Task 3.3: Pi5 → MacBook Relay → Drive
- Pi5 backup → git push to A-Wiki repo
- MacBook cron → git pull → copy to drive

---

## Phase 4: Telegram on Raspberry Pi 5

### Task 4.1: Create Telegram Bot
1. คุย @BotFather → `/newbot` → ชื่อ `A-Wiki-Hermes`
2. ได้ `TELEGRAM_BOT_TOKEN`

### Task 4.2: Add Token to Pi5 Container
```bash
# เพิ่มใน .env ของ container
echo "TELEGRAM_BOT_TOKEN=YOUR_TOKEN" | sudo -S -p '' docker exec -i hermes-agent_web_1 tee -a /opt/data/profiles/tech_and_ai_architect/.env
```

### Task 4.3: Enable Telegram Gateway
```bash
sudo -S -p '' docker exec hermes-agent_web_1 /opt/hermes/bin/hermes -p tech_and_ai_architect gateway setup
```

### Task 4.4: Verify Gateway Running
```bash
sudo -S -p '' docker exec hermes-agent_web_1 /opt/hermes/bin/hermes gateway status
# Expected: Telegram: ✅ connected
```

---

## Phase 5: Slash Commands — All Working

### Task 5.1: Current Commands
| Command | Status | File |
|---------|--------|------|
| `/spec` | ❓ Untested | `commands/spec.md` |
| `/plan` | ❓ Untested | `commands/plan.md` |
| `/build` | ❓ Untested | `commands/build.md` |
| `/test` | ❓ Untested | `commands/test.md` |
| `/review` | ❓ Untested | `commands/review.md` |
| `/code-simplify` | ❓ Untested | `commands/code-simplify.md` |
| `/ship` | ❓ Untested | `commands/ship.md` |

### Task 5.2: New Commands
| Command | Purpose |
|---------|---------|
| `/wiki <query>` | ค้น A-Wiki FTS5 |
| `/search <query>` | Web + wiki search |
| `/backup` | Manual backup trigger |
| `/status` | System status |

### Task 5.3: Register via A-Wiki Skill
- **File**: `skills/awiki/a-wiki-commands/SKILL.md`
- สร้าง Hermes skill → register เป็น slash commands
- หรือใช้ `hermes_cli/commands.py` CommandDef pattern

---

## Phase 6: Documentation

### Task 6.1: Multi-Device Guide
- **File**: `docs/runbooks/hermes-multi-device.md`

### Task 6.2: Update AGENTS.md
- Add: Hermes multi-device sync protocol
- Add: Telegram gateway reference

---

## Execution Order (ตามความสำคัญ)

| Priority | Phase | Why |
|----------|-------|-----|
| 🔴 P0 | Phase 4 — Telegram | Quick win, user visible, Pi5 24/7 |
| 🔴 P0 | Phase 1 — Auto-Sync | Foundation for everything |
| 🟡 P1 | Phase 5 — Commands | User productivity |
| 🟡 P1 | Phase 2 — Backup | Data safety |
| 🟢 P2 | Phase 3 — Drive | Storage optimization |
| 🟢 P2 | Phase 6 — Docs | Wrap up |
