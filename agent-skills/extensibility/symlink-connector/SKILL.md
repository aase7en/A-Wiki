---
name: symlink-connector
description: Universal agent-config linker — symlinks every harness's skills to the A-Wiki repo and .env to Google Drive so a new machine needs one bootstrap command, not per-agent setup.
domain: engineering
lifecycle_phase: ship
---

# Symlink Connector — Universal Agent-Config Linker

> **Purpose:** Bridge `agent-skills/` (and the ecosystem skill dirs) into every
> AI agent harness on this machine, and point each harness's `.env` at Google
> Drive, so switching machines never means reinstalling skills or re-typing
> secrets.

## Two sources of truth

| What | Source of truth | Why |
|---|---|---|
| Skills, `SKILL.md`, shareable config | **This git repo** (already synced across machines) | Edit once, `git pull` everywhere |
| Secrets, `.env`, per-agent private state | **Google Drive `A-Wiki-Data`** via `drive/` (see `docs/protocols/...` cloud link) | Never committed; cloud-synced |

**Never** put the git repo itself inside Google Drive, and never expect a
symlink placed *inside* the Drive folder to sync — Google Drive for Desktop
does not reliably follow or sync symlinks. Links must point **into** the
Drive mount; only real files live on Drive.

## The linker: `scripts/link-agent-configs.sh`

```bash
bash scripts/link-agent-configs.sh              # link every detected agent
bash scripts/link-agent-configs.sh --status     # health check (exit 1 on broken links)
bash scripts/link-agent-configs.sh --agent zcode  # force one agent (creates its dir)
bash scripts/link-agent-configs.sh --unlink     # remove managed links only
bash scripts/link-agent-configs.sh --list       # preview agents + linkable skills
```

Runs automatically as part of `bash scripts/setup-local.sh` (one command per
new machine) and is checked by `scripts/verify-next-machine.py`.

### Target environments

| Agent | Skills dir | `.env` linked to Drive? |
|---|---|---|
| Claude Code | `~/.claude/skills/` | no (uses `drive/.secrets` via `import-keys.py`) |
| Codex | `~/.codex/skills/` | no (`load-drive-keys.sh` hook) |
| Cline | `~/.cline/skills/` | no |
| Hermes | `~/.hermes/skills/` (or `$HERMES_HOME`) | **yes** → `drive/.agents/hermes/.env` |
| Gemini CLI | `~/.gemini/skills/` | no |
| ZCode | `~/.zcode/skills/` | **yes** → `drive/.agents/zcode/.env` |
| Antigravity | `~/.antigravity/skills/` | no |
| Windsurf | `~/.windsurf/skills/` | no |
| OpenClaw | `~/.openclaw/skills/` | no |
| Kilo | `~/.config/kilo/` | rendered separately by `scripts/setup-kilo-config.sh` (not duplicated here) |
| *(repo root)* | – | `.env` → `drive/.env` (seeded from `.env.example`) |

Auto-detection links only agents whose home dir already exists on this
machine; `--agent <name>` forces one into existence. Override any harness's
home dir without editing the script: `AWIKI_AGENT_DIR_<AGENT>=/custom/path`
(e.g. `AWIKI_AGENT_DIR_ZCODE`). Hermes also respects `$HERMES_HOME`.

## Symlink strategy

```
~/.claude/skills/debug-mantra/ → A-Wiki/agent-skills/engineering/debug-mantra/
~/.hermes/.env                 → drive/.agents/hermes/.env
A-Wiki/.env                    → drive/.env
```

Skills come from `agent-skills/*/*/`, `skills/anthropic-skills/*/`, and
`skills/mattpocock/*/` — the same source set the legacy
`scripts/link-my-skills.sh` used (now a deprecated shim that forwards here).

Rules that keep re-runs safe:
- A **real directory** already at a skill target is never deleted — only
  stale symlinks/files are replaced. Locally installed skills A-Wiki doesn't
  manage survive untouched.
- If a machine already has **static copies** of A-Wiki skills (e.g. from
  before this linker existed), pass `--force-skills` to convert them into
  live symlinks: any real directory whose name matches a known A-Wiki skill
  is renamed to `<name>.pre-link-backup-<timestamp>` (never deleted) before
  the symlink is created. Directories whose name does **not** match any
  A-Wiki skill are left alone even with `--force-skills` — only matching
  names are ever touched.
- A **real `.env` file** is left alone unless `--force` is passed, in which
  case its content is migrated to Drive (with a timestamped backup if a Drive
  copy already exists) before the local path becomes a symlink.
- On Windows without Developer Mode, directory links fall back to a
  PowerShell junction, then `mklink /J` (same chain as
  `scripts/setup-cloud-link.sh`). Junctions can't target a single file, so a
  `.env` link that can't be a symlink falls back to a plain copy — re-run
  after editing the Drive copy.
- **Windows junctions vs `ls -la`/`Get-Item`**: a junction is a real, working
  reparse point, but Git Bash's `ls -la` shows it as a plain directory (`d`,
  not `l`) and Windows PowerShell 5.1's `Get-Item ... | Select LinkType`
  sometimes reports it as blank too — neither recognizes a junction the way
  they recognize a true symlink. `--status` accounts for this (it resolves
  through `realpath`, which does follow junctions, instead of relying on the
  symlink bit) so its skill counts are accurate on Windows. If you want to
  double check by hand, read a file through the link instead of `ls`-ing it:
  `cat <agent_dir>/skills/<skill>/SKILL.md` — if the content matches the repo,
  the link works, regardless of what `ls`/`Get-Item` display.
- `--unlink` only removes true symlinks it detects via the symlink bit, so it
  currently leaves Windows junctions in place rather than risk `rm` behaving
  unexpectedly on a reparse point it can't fully identify — a known, safe
  (non-destructive) limitation, not planned to change without real Windows
  testing.

## Verifying

```bash
bash scripts/link-agent-configs.sh --status
python3 scripts/verify-next-machine.py
pytest tests/test_link_agent_configs.py -v
```
