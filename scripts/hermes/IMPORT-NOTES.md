# Hermes Config Import — MacBook → Pi5

## What's in the package
- `config.yaml` — All Hermes settings (model, toolsets, terminal, display, etc.)
- `SOUL.md` — Agent persona (Thai: คิดเชิงระบบ เน้นการทำงานอัตโนมัติ)
- `skills/` — 77 skills including A-Wiki skills
- `memories/` — MEMORY.md + USER.md
- `cron/` — Cron job definitions

## What's NOT in the package (needs manual handling)

| File | How to transfer |
|------|-----------------|
| `.env` (API keys) | `scp ~/.hermes/profiles/tech_and_ai_architect/.env pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/` |
| `.env` (global) | `scp ~/.hermes/.env pi@umbrel.local:~/.hermes/` |
| `auth.json` (OAuth) | `scp ~/.hermes/profiles/tech_and_ai_architect/auth.json pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/` |

## How to import on Pi5

```bash
# 1. Copy package to Pi5
scp scripts/hermes/hermes-export-*.tar.gz pi@umbrel.local:~/

# 2. SSH into Pi5 and import
ssh pi@umbrel.local
hermes profile import ~/hermes-export-*.tar.gz

# 3. Copy secrets
#    (do this on MacBook)
scp ~/.hermes/profiles/tech_and_ai_architect/.env pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/
scp ~/.hermes/profiles/tech_and_ai_architect/auth.json pi@umbrel.local:~/.hermes/profiles/tech_and_ai_architect/

# 4. Adjust paths for Pi5
hermes config set terminal.cwd /home/pi/A-Wiki

# 5. Verify
hermes doctor
hermes profile show tech_and_ai_architect
```

## Path differences to fix
- `terminal.cwd`: `$REPO_ROOT` → `/home/pi/A-Wiki` (or wherever A-Wiki lives on Pi5)
- Any other `/Users/aase7en` paths → adjust for Pi5

## Pi5-specific notes
- Terminal backend should be `local` (already set)
- Timezone GMT+7 (already set)
- Model will be auto-detected; run `hermes model` if needed
