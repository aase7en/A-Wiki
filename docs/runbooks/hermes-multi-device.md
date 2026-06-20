# Hermes Multi-Device Ecosystem — Setup Guide

**วันที่**: 2026-06-20 | **Profile**: `tech_and_ai_architect`

## Architecture

```
┌─────────────┐     git push/pull      ┌──────────────┐
│  MacBook    │ ←──────────────────→ │  Raspberry Pi5│
│  (dev)      │    config + skills    │  (24/7 server)│
└─────────────┘                       └──────┬───────┘
       │                                     │
       │  backup sessions                    │  Telegram gateway
       ▼                                     ▼
┌─────────────┐                       ┌──────────────┐
│ Google Drive│                       │  Telegram    │
│ A-Wiki-Data │                       │  @BotFather  │
└─────────────┘                       └──────────────┘
```

## Quick Setup — Any Device

### 1. Install Hermes
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### 2. Clone A-Wiki
```bash
git clone https://github.com/aase7en/A-Wiki.git ~/A-Wiki
```

### 3. Import Profile
```bash
# MacBook/Linux
hermes profile import ~/A-Wiki/scripts/hermes/hermes-export-*.tar.gz

# Windows
hermes profile import %USERPROFILE%\A-Wiki\scripts\hermes\hermes-export-*.tar.gz

# Pi5 (Docker)
sudo -S -p '' docker cp ~/A-Wiki/scripts/hermes/hermes-export-*.tar.gz hermes-agent_web_1:/tmp/
sudo -S -p '' docker exec hermes-agent_web_1 /opt/hermes/bin/hermes profile import /tmp/hermes-export-*.tar.gz
```

### 4. Copy Secrets (.env + auth.json)
Transfer via scp, USB, or HTTP — NEVER commit to git.

### 5. Enable Auto-Sync
```bash
# Pi5 — cron every 6 hours
(crontab -l 2>/dev/null; echo "0 */6 * * * cd $HOME/A-Wiki && bash scripts/hermes/auto-sync-from-git.sh") | crontab -

# Windows — Task Scheduler
# Create task: Trigger=every 6 hours, Action=powershell -File auto-sync.ps1

# MacBook — Hermes cron job
# Created automatically via scripts/hermes/backup-to-drive.sh
```

## Telegram Setup (Pi5)

1. Create bot with @BotFather → `TELEGRAM_BOT_TOKEN`
2. Add to Pi5 container `.env`
3. `hermes gateway setup` → enable Telegram
4. Verify: `hermes gateway status`

## Auto-Sync Flow

```
MacBook:  manual export + git push
Pi5:      cron auto-pull every 6h → docker cp → hermes import
Windows:  Task Scheduler every 6h → git pull → hermes import
```

## Backup Schedule

| When | What | Where |
|------|------|-------|
| Daily 2AM | Sessions (JSONL.gz) | `drive/backups/hermes/sessions/` |
| Daily 3AM | Config + Memories | `drive/backups/hermes/` |
| Weekly | Memory compaction | `scripts/hermes/compact-memories.py` |

## Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|--------|
| Config diverged | `hermes profile import` from latest export |
| Gateway down | `hermes gateway restart` |
| Skills missing | `hermes skills check` |
| Cron not running | Check `crontab -l`, check logs |
| Docker permission | Use `sudo docker` on Umbrel |

## References

- `scripts/hermes/export-macbook-config.sh` — Re-export config package
- `scripts/hermes/import-on-pi5.sh` — One-command Pi5 import
- `scripts/hermes/auto-sync-from-git.sh` — Pi5 auto-sync
- `scripts/hermes/auto-sync.ps1` — Windows auto-sync
- `scripts/hermes/backup-sessions.sh` — Session backup
- `scripts/hermes/backup-to-drive.sh` — Full Drive backup
- `scripts/hermes/compact-memories.py` — Memory dedup
