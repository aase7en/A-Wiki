# Next Machine Verification

Use this after pulling A-Wiki on Work PC, WSL, Linux, or a fresh Mac.

```bash
git pull origin main
bash scripts/setup-local.sh
python3 scripts/verify-next-machine.py --build-vec
```

The verifier runs:

| Check | Purpose |
|---|---|
| `setup-cloud-link.sh --status` | Verify `drive/` and `raw/` links |
| `drive_secrets.py --check` | Verify `.secrets` is readable without printing values |
| `import-keys.py --check` | Verify cacheable key names can be parsed without writing settings |
| `verify-awiki-ready.py --skip-remote` | Verify hooks, model router, evals, and TODO hygiene |
| `verify-cross-platform.py --build-vec` | Verify Python deps and sqlite-vec rebuild |
| `sync-smoke.py` | Verify sync commit/push logic in temporary repos only |
| Docker probe | Warn when Linux container verification is unavailable |

If Docker is installed, the script only checks Docker availability. It does not
run a container by default because A-Wiki should stay lightweight and avoid
unexpected image pulls.

## Sync Daemon

For daily multi-device use:

```bash
python3 scripts/sync.py --now
python3 scripts/sync.py --daemon --interval 30 --debounce 10
```

`scripts/sync-smoke.py` covers the risky untracked-file path in a temporary repo.
It does not touch the real A-Wiki repository or push real content.

## GitNexus For Dream Projects

Pass explicit local repo paths; A-Wiki never guesses private paths:

```bash
AWIKI_DREAM_REPOS="/path/project-a:/path/project-b" bash scripts/setup-dream-gitnexus.sh
```

