# Hermes Multi-Device Ecosystem — Secure Sync Guide

**วันที่**: 2026-06-21 | **Profile**: `tech_and_ai_architect`

## Architecture (SECURE — No HTTP Exposure)

```
┌──────────────────────────────────────────────────────────┐
│                    TWO-LAYER SYNC                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  PUBLIC (GitHub)              PRIVATE (Google Drive)      │
│  ─────────────                ─────────────────────      │
│  • config.yaml                • .env (API keys)          │
│  • skills/                    • auth.json (OAuth)        │
│  • cron/ definitions          • SOUL.md (persona)        │
│  • scripts/                   • MEMORY.md (agent memory) │
│  • hooks/                     • USER.md (user profile)   │
│                               • global.env (A-Wiki .env) │
│                                                          │
│  Flow:                                                   │
│  Mac ──git push──→ GitHub ←──git pull── Pi5/Windows      │
│  Mac ──cp──→ Google Drive ←──pull── Pi5/Windows          │
│                                                          │
│  ⚠️  NO HTTP server. NO port exposure. NO plain-text LAN. │
│     Secrets ONLY move via Google Drive (encrypted).       │
└──────────────────────────────────────────────────────────┘
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

### 3. Import Profile (public layer)
```bash
# MacBook/Linux
hermes profile import ~/A-Wiki/scripts/hermes/hermes-export-*.tar.gz

# Windows
hermes profile import %USERPROFILE%\A-Wiki\scripts\hermes\hermes-export-*.tar.gz

# Pi5 (Docker)
sudo docker cp ~/A-Wiki/scripts/hermes/hermes-export-*.tar.gz hermes-agent_web_1:/tmp/
sudo docker exec hermes-agent_web_1 /opt/hermes/bin/hermes profile import /tmp/hermes-export-*.tar.gz
```

### 4. Pull Secrets from Google Drive (private layer)
```bash
# One command — pulls .env, auth.json, SOUL.md, MEMORY.md, USER.md
bash scripts/hermes/sync-secrets-from-drive.sh
```

### 5. Full Sync (one command)
```bash
bash scripts/hermes/sync-all.sh              # pull mode: GitHub + Drive → local
bash scripts/hermes/sync-all.sh --push       # push mode: Mac → Drive + GitHub
```

## Secure Sync Commands

| Command | Direction | What it syncs |
|---------|-----------|---------------|
| `sync-secrets-to-drive.sh` | Mac → Drive | .env, auth.json, SOUL.md, MEMORY.md, USER.md |
| `sync-secrets-from-drive.sh` | Drive → Device | Same as above |
| `sync-all.sh` | Both layers | Git pull/push + Drive pull/push + profile import |
| `export-macbook-config.sh` | Mac → GitHub | Profile package (public files only) |
| `auto-sync-from-git.sh` | GitHub → Pi5 | Public layer + auto-import |

## Drive/ Directory Structure

```
Google Drive / A-Wiki-Data /
└── hermes-sync/
    ├── config/
    │   ├── .env           ← API keys (NEVER in git)
    │   ├── auth.json      ← OAuth tokens
    │   └── SOUL.md        ← Agent persona
    ├── memories/
    │   ├── MEMORY.md      ← Cross-session agent memory
    │   └── USER.md        ← User profile
    └── global.env         ← A-Wiki root .env
```

## Auto-Sync Schedule

| When | Device | Command |
|------|--------|---------|
| Every 6h | Pi5 | `bash scripts/hermes/sync-all.sh` |
| Every 6h | Windows | `powershell -File scripts/hermes/auto-sync.ps1` |
| On config change | MacBook | `bash scripts/hermes/sync-all.sh --push` |
| Daily 3AM | MacBook | `bash scripts/hermes/backup-to-drive.sh` |
| Hourly | Pi5 | `python3 scripts/hermes/subagent-alert-poller.py --once` (critical Observatory alert → Telegram) |

### Subagent Alert Poller (Pi5 systemd timer)

Sends a Telegram banner when the Observatory detects a critical subagent
alert (pass_rate < 0.70 with ≥5 samples). Idempotent: each subagent alerted
at most once per 4h cooldown.

Install on Pi5:
```bash
sudo cp scripts/hermes/systemd/awiki-alert-poller.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now awiki-alert-poller.timer
# Verify: systemctl list-timers | grep alert-poller
```

State file: `.tmp/subagent-alert-poller-state.json` (last-alerted ts per subagent).

## Telegram Setup (Pi5)

1. Create bot with @BotFather → `TELEGRAM_BOT_TOKEN`
2. Add to Pi5 container `.env`
3. `hermes gateway setup` → enable Telegram
4. Verify: `hermes gateway status`

## Security Principles

| Rule | Reason |
|------|--------|
| `.env` NEVER in git | Contains API keys |
| `.env` ONLY via Google Drive | Encrypted at rest, private |
| NO HTTP server for config | Prevents LAN exposure |
| NO hardcoded paths | Cross-device compatible |
| `chmod 600` on all secret files | Owner-only access |
| Backup before overwrite | Recovery from sync conflicts |

## Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|--------|
| Config diverged | `bash scripts/hermes/sync-all.sh` |
| Secrets outdated | `bash scripts/hermes/sync-secrets-from-drive.sh` |
| Gateway down | `hermes gateway restart` |
| Skills missing | `hermes skills check` |
| Cron not running | Check `crontab -l`, check logs |
| Docker permission | Use `sudo docker` on Umbrel |
| Drive not mounted | Run `bash scripts/setup-drive-link.sh` |

## References

- `scripts/hermes/sync-all.sh` — **One-command full sync** (use this most)
- `scripts/hermes/sync-secrets-to-drive.sh` — Push secrets → Drive
- `scripts/hermes/sync-secrets-from-drive.sh` — Pull secrets ← Drive
- `scripts/hermes/export-macbook-config.sh` — Export profile package
- `scripts/hermes/auto-sync-from-git.sh` — Pi5 auto-sync (cron)
- `scripts/hermes/auto-sync.ps1` — Windows auto-sync
- `scripts/hermes/backup-to-drive.sh` — Full Drive backup
- `scripts/hermes/compact-memories.py` — Memory dedup
