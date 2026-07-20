# Secrets storage — global universal .env in Google Drive

> **Status**: implemented 2026-07-16 (chunks P6.1–P6.5 + P7 + P8).

## Why a universal .env

Personal Drive is private (single user) and synced across every machine.
One canonical secrets file there beats per-machine `.env` files that drift.

## Layout (Drive root, NOT git-tracked — Drive is SSOT)

```
<Drive>/A-Wiki-Data/
  secrets/
    global.env                      # AI keys + global tokens — every agent reads
    env-wastewater-webapp.env       # repo-specific (Supabase URL, PAT)
    <other-repo>.env                # add per-repo as needed
    README.md                       # convention doc
```

## Two-file pattern (hybrid)

- `global.env` — applies to every agent/repo. Loaded FIRST.
- `<repo>.env` — repo-specific secrets. Loaded SECOND, may override globals.

## Cross-platform Drive path resolution

Never hardcode. Resolution order (matches `scripts/drive_path.py`):

1. `$A_WIKI_DRIVE_PATH` env var
2. `A-Wiki/drive/` symlink/junction
3. `A-Wiki/.drive-path` file
4. `~/.a-wiki-data` fallback

## How each surface reads the secrets

| Surface | Mechanism | Script |
|---|---|---|
| Shell scripts / repos | `source scripts/load-global-env.sh [--repo NAME]` | `load-global-env.sh` |
| Repo Python config | `_resolve_env_file()` pattern | per-repo |
| Agent harnesses | `~/.<agent>/.env` → Drive `global.env` via linker | `link-agent-configs.sh` |
| IDE terminals (bash/zsh) | shell rc hook auto-sources loader | `setup-ide-env.sh` |
| Windows PowerShell terminals | `$PROFILE.CurrentUserAllHosts` hook auto-sources loader | `setup-ide-env.ps1` |

## Adding a new machine

1. Mount Google Drive so `A-Wiki-Data/secrets/` is reachable.
2. Set the Drive path via `A-Wiki/.drive-path` or the `drive/` link.
3. Run `bash A-Wiki/scripts/setup-local.sh` — links agents + injects IDE hook.

**Windows PowerShell users**: `setup-local.sh` injects the bash-family hook
(`.bashrc`/`.bash_profile`, for Git Bash/WSL terminals) but does not touch
PowerShell's own profile. Also run `powershell -File scripts/setup-ide-env.ps1`
once so `global.env` auto-loads into native `powershell.exe`/`pwsh.exe`
sessions too (console host, VS Code integrated terminal). Use
`-Status`/`-Remove` to check or undo, mirroring the bash version's flags.

## Editing secrets

Edit `secrets/global.env` (or `<repo>.env`) on Drive directly. Drive syncs
the change to every machine. No per-machine edits, no commit needed.
