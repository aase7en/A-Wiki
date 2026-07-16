---
name: symlink-connector
version: 2.1.0
description: Universal agent-config linker — symlinks every harness's skills to the A-Wiki repo, links every agent's .env to a universal secrets/global.env on Google Drive, and injects an IDE terminal hook so a new machine needs one bootstrap command, not per-agent setup.
domain: engineering
lifecycle_phase: ship
---

# Symlink Connector — Universal Agent-Config Linker

> **Purpose:** Bridge `agent-skills/` (and the ecosystem skill dirs) into every
> AI agent harness on this machine, point each harness's `.env` at the
> universal `secrets/global.env` on Google Drive, and inject a shell hook so
> every terminal (including IDE-embedded) auto-loads the global secrets.
> Switching machines never means reinstalling skills or re-typing secrets.

## Two sources of truth

| What | Source of truth | Why |
|---|---|---|
| Skills, `SKILL.md`, shareable config | **This git repo** (already synced across machines) | Edit once, `git pull` everywhere |
| Secrets, `.env`, per-agent private state | **Google Drive `A-Wiki-Data/secrets/`** via `drive/` (see `docs/protocols/secrets-global-env.md`) | Never committed; cloud-synced |

**Never** put the git repo itself inside Google Drive, and never expect a
symlink placed *inside* the Drive folder to sync — Google Drive for Desktop
does not reliably follow or sync symlinks. Links must point **into** the
Drive mount; only real files live on Drive.

## Universal .env — hybrid global + per-repo (v2.1.0)

Every agent now links its `~/.<agent>/.env` to **one** universal file on
Drive: `secrets/global.env`. This holds AI keys + shared tokens that apply
across all agents and repos. Repo-specific secrets (DB URLs, project PATs)
live beside it as `secrets/<repo>.env` and are loaded on top by the loader
when working in that repo.

```
<Drive>/A-Wiki-Data/secrets/
  global.env                      # AI keys — every agent reads this
  env-wastewater-webapp.env       # repo-specific (Supabase URL, PAT)
  <other-repo>.env                # add per-repo as needed
  README.md                       # convention doc
```

Three surfaces read these secrets:

| Surface | Mechanism | Script |
|---|---|---|
| Shell scripts / repos with config loaders | `source scripts/load-global-env.sh [--repo NAME]` | `load-global-env.sh` |
| Agent harnesses (.zcode, .claude, ...) | `~/.<agent>/.env` → Drive `secrets/global.env` | `link-agent-configs.sh` |
| IDE terminals (VSCode, Windsurf, Devin) | shell rc hook auto-sources the loader | `setup-ide-env.sh` |

## The linker: `scripts/link-agent-configs.sh`

```bash
bash scripts/link-agent-configs.sh              # link every detected agent
bash scripts/link-agent-configs.sh --status     # health check (exit 1 on broken links)
bash scripts/link-agent-configs.sh --agent zcode  # force one agent (creates its dir)
bash scripts/link-agent-configs.sh --force-skills # convert static copies → live links (backs up first)
bash scripts/link-agent-configs.sh --clean-backups  # delete *.pre-link-backup-* dirs, verified-safe
bash scripts/link-agent-configs.sh --unlink     # remove managed links only
bash scripts/link-agent-configs.sh --list       # preview agents + linkable skills
```

`--force-skills` leaves a `<skill>.pre-link-backup-<timestamp>` directory next
to each converted skill. Once you've confirmed the live links work
(`--status` shows the skills linked), `--clean-backups` removes those backup
directories — but **only** where the live `<skill>` is a verified working
managed link into the repo. If any skill's link is missing or broken, its
backup is kept (never deletes the only surviving copy). Add `--dry-run` to
preview what it would remove without touching anything.

Runs automatically as part of `bash scripts/setup-local.sh` (one command per
new machine) and is checked by `scripts/verify-next-machine.py`.

### Target environments

| Agent | Skills dir | `.env` linked to Drive? |
|---|---|---|
| Claude Code | `~/.claude/skills/` | **yes** → `secrets/global.env` (v2.1.0) |
| Codex | `~/.codex/skills/` | **yes** → `secrets/global.env` (v2.1.0) |
| Cline | `~/.cline/skills/` | **yes** → `secrets/global.env` (v2.1.0) |
| Hermes | `~/.hermes/skills/` (or `$HERMES_HOME`) | **yes** → `secrets/global.env` |
| Gemini CLI | `~/.gemini/skills/` | **yes** → `secrets/global.env` (v2.1.0) |
| ZCode | `~/.zcode/skills/` | **yes** → `secrets/global.env` |
| Antigravity | `~/.gemini/config/skills/` (IDE+CLI read global skills only from here, not `~/.antigravity` — verified 2026-07-10) | **yes** → `secrets/global.env` (v2.1.0) |
| Windsurf | `~/.windsurf/skills/` | **yes** → `secrets/global.env` (v2.1.0) |
| OpenClaw | `~/.openclaw/skills/` | **yes** → `secrets/global.env` (v2.1.0) |
| Kilo | `~/.config/kilo/` | rendered separately by `scripts/setup-kilo-config.sh` (not duplicated here) |
| *(repo root)* | – | `.env` → `drive/.env` (legacy stub; secrets/global.env is the SSOT now) |
| *(IDE terminals)* | – | shell rc hook via `setup-ide-env.sh` (auto-sources `load-global-env.sh`) |

**v2.1.0 change**: `ENV_AGENTS` was expanded from `hermes zcode` to **every**
supported agent. The legacy per-agent `drive/.agents/<a>/.env` files are kept
untouched for back-compat but no longer the link target — everything points
at the universal `secrets/global.env`.

Auto-detection links only agents whose home dir already exists on this
machine; `--agent <name>` forces one into existence. Override any harness's
home dir without editing the script: `AWIKI_AGENT_DIR_<AGENT>=/custom/path`
(e.g. `AWIKI_AGENT_DIR_ZCODE`). Hermes also respects `$HERMES_HOME`.

## Symlink strategy

```
~/.claude/skills/debug-mantra/ → A-Wiki/agent-skills/engineering/debug-mantra/
~/.<agent>/.env                → drive/secrets/global.env        (v2.1.0 universal)
~/.bashrc                      → sources drive/secrets/global.env via load-global-env.sh
A-Wiki/.env                    → drive/.env (legacy stub)
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
- **Git Bash `ln -s` silently falls back** (the nastiest Windows quirk): on
  MSYS builds without symlink support, `ln -s` exits 0 but creates a fake
  plain directory or deep copy instead of a link — the result *looks* fine
  (`cat` shows correct content) but is a static snapshot. `create_link()`
  defends against this: it forces `MSYS=winsymlinks:nativestrict` (real
  symlink or fail immediately, no wasted copy), verifies the result with
  `[ -L ]`, deletes any fake entry that got created anyway, and only then
  falls back to an NTFS junction for directories. So on Windows you get:
  true symlink (if Developer Mode/admin) → junction (no privileges needed) →
  honest failure message — never a silent fake.
- **Verifying a link on Windows**: `--status` resolves through `realpath`
  (follows junctions too) so its counts are trustworthy. To check one by
  hand: `realpath <agent_dir>/skills/<skill>` must print the **repo** path —
  if it prints the agent path back, it's a copy/fake, not a link. (Don't
  trust `cat` alone: a fresh copy also shows correct content, and don't
  trust `ls -la`/PowerShell 5.1 `Get-Item` alone either: neither reliably
  identifies junctions.)
- `--unlink` only removes true symlinks it detects via the symlink bit, so it
  currently leaves Windows junctions in place rather than risk `rm` behaving
  unexpectedly on a reparse point it can't fully identify — a known, safe
  (non-destructive) limitation, not planned to change without real Windows
  testing.

## Verifying

```bash
bash scripts/link-agent-configs.sh --status      # every agent linked?
bash scripts/setup-ide-env.sh --status            # IDE hook injected?
python3 scripts/verify-next-machine.py            # full machine check (includes
                                                  # global.env + IDE hook + loader)
pytest tests/test_global_env_system.py -v          # loader + IDE hook + linker tests
```
