# Cross-Device A-Wiki Skill Sync — Runbook

> **One-line summary:** Skills live in the repo (GitHub = single source of truth). Each device clones the repo and links skills back to it. Windows/Mac use native symlinks; Pi5 uses Docker container sync.
>
> **Daily sync:** just `git pull` — the post-merge hook re-links automatically (Windows/Mac). Pi5 has a 6h cron. Or run `git awiki-sync` for explicit full sync.

---

## Architecture

```
GitHub (origin/main)          ← SINGLE SOURCE OF TRUTH
    ↓ git clone / pull
    ├── Windows  (A:\GitHub\A-Wiki)   ← native symlinks → repo
    ├── MacBook  (~/A-Wiki)           ← native symlinks → repo
    └── Pi5      (Docker container)   ← docker cp + profile import
                /opt/data/A-Wiki      ← in-container clone
                /opt/data/skills/     ← in-container symlinks → /opt/data/A-Wiki
```

**Key principle:** Editing a skill in the repo updates it for all agents on that device instantly (via symlink). Pushing to GitHub + pulling on another device propagates it everywhere.

---

## Mechanism per device

| Device | Agents | Mechanism | Skill count |
|---|---|---|---|
| **Windows** | claude, zcode, codex, cline, gemini, hermes | Native symlinks (`~/.<agent>/skills/<skill>` → repo) | 49 per agent |
| **MacBook** | Same 6 (native home dirs) | Native symlinks (macOS native `ln -s`) | 49 per agent |
| **Pi5** | Hermes only (in Docker) | `docker cp` + `hermes profile import` + gateway rescan | 37+ in `/opt/data/skills/` |

### ⚠️ Do NOT do on Pi5
- **Never run `link-agent-configs.sh` on Pi5.** It creates host-side symlinks that the Hermes Docker container cannot see. Pi5 uses a completely different mechanism (Docker container sync).
- The host `~/.hermes` directory on Pi5 is irrelevant to Hermes — it lives in `/opt/data` inside the container.

---

## First-time setup (per device)

Run **once** after cloning A-Wiki on a new machine:

```bash
cd ~/A-Wiki   # or A:\GitHub\A-Wiki on Windows
bash scripts/setup-local.sh         # full setup: drive links, .mcp.json, keys, skill links (step 8b)
bash scripts/install-git-hooks.sh   # install post-merge hook + git awiki-sync alias
```

`setup-local.sh` step 8b already calls `link-agent-configs.sh` automatically. `install-git-hooks.sh` adds the post-merge hook and the `git awiki-sync` alias.

**Pi5 exception:** On Pi5, skip `setup-local.sh` (it's for native agents). The Hermes container has its own setup — see `docs/runbooks/hermes-raspberry-pi5.md`.

---

## Daily sync (per device)

### Windows / Mac

**Automatic (recommended):** Just pull normally.
```bash
git pull
# post-merge hook runs link-agent-configs.sh --skills-only automatically
# (quiet unless something changes or fails)
```

**Manual (when you want to force re-link or see status):**
```bash
git awiki-sync
# = git pull + link-agent-configs --force-skills + --status
```

### Pi5

**Automatic:** Cron job runs every 6 hours — no action needed.
```bash
# Verify cron is active:
crontab -l | grep auto-sync
# Expected: 0 */6 * * * cd ~/A-Wiki && bash scripts/hermes/auto-sync-from-git.sh
```

**Manual (when you don't want to wait for cron):**
```bash
bash scripts/hermes/awiki-pi5-sync.sh
# = git pull + docker cp + profile import + gateway rescan + verify
```

---

## Troubleshooting

### "Skills missing on Windows/Mac after pull"
```bash
git awiki-sync                    # force re-link
bash scripts/link-agent-configs.sh --status   # check link health
```

### "Skills missing on Pi5"
```bash
# 1. Check container is running
sudo docker ps | grep hermes

# 2. Run manual sync
bash scripts/hermes/awiki-pi5-sync.sh

# 3. If still missing, restart container (forces full rescan)
sudo docker restart hermes-agent_web_1

# 4. Check cron is active
crontab -l | grep auto-sync
```

### "post-merge hook didn't run"
```bash
# Hooks are not git-tracked — reinstall on new machines:
bash scripts/install-git-hooks.sh

# Verify:
ls -la .git/hooks/post-merge   # should exist and be executable
```

### "git awiki-sync: command not found"
The alias isn't installed. Run:
```bash
bash scripts/install-git-hooks.sh
git config alias.awiki-sync    # should show: !bash ".../scripts/awiki-sync.sh"
```

---

## What each script does

| Script | Purpose | Runs on |
|---|---|---|
| `scripts/link-agent-configs.sh` | Create/maintain symlinks from agent homes → repo | Windows, Mac |
| `scripts/awiki-sync.sh` | Platform-aware router: pull + link (Win/Mac) or pull + Pi5-sync | All |
| `scripts/hermes/awiki-pi5-sync.sh` | Pi5 Docker sync: wraps auto-sync + adds gateway rescan + verify | Pi5 only |
| `scripts/hermes/auto-sync-from-git.sh` | Pi5 cron logic: host git pull + container brain FF + gateway rescan (via `pi5-brain-sync.py`) | Pi5 (cron) |
| `scripts/hermes/pi5-brain-sync.py` | FF `/opt/data/A-Wiki` inside the container (stash/pop, auto-gen conflict handling) + SIGHUP rescan; dry-run default | Pi5 |
| `scripts/hooks/post_merge_relink.sh` | Auto re-link after `git pull` (skips Pi5) | Windows, Mac |
| `scripts/install-git-hooks.sh` | Install hooks + register `git awiki-sync` alias | All (once per clone) |

---

## Related docs
- `docs/runbooks/hermes-raspberry-pi5.md` — Pi5 Hermes container details
- `docs/runbooks/hermes-multi-device.md` — Multi-device sync architecture (public + private layers)
- `docs/architecture/hermes-cross-agent-handoff.md` — LIVE Pi5 container facts (`/opt/data` layout)
- `docs/protocols/cross-agent-plan-handoff.md` — Cross-agent session handoff protocol
