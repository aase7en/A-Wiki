# Runbook: Version and Upstream Refresh

> Purpose: keep A-Wiki lightweight while tracking upstream capability changes
> from integrated repositories and AI model providers.
> Last updated: 2026-05-30

---

## Version files

| File | Role |
|---|---|
| `VERSION` | Current A-Wiki capability version |
| `CHANGELOG.md` | Human-readable change history and verification evidence |
| `docs/runbooks/upstream-refresh.md` | How to review and refresh upstream integrations |

Rule: update `VERSION` and `CHANGELOG.md` when a change adds or removes a repo-level capability, workflow, setup path, or agent rule.

---

## Upstream integrations

| Upstream | Local path / command | Review rule |
|---|---|---|
| `affaan-m/ECC` | `bash scripts/refresh-ecosystem.sh` | Keep only useful skills/tools; do not vendor heavy assets unless needed |
| `thananon/9arm-skills` | `bash scripts/refresh-9arm.sh` | Review skill behavior before exposing it to agents |
| `microsoft/SkillOpt` | `bash scripts/refresh-skillopt.sh` | Keep snapshot lightweight; install runnable code only in ignored local paths |
| `OpenRouter free models` | `bash scripts/update-model-roster.sh` | Review model routing diff before committing |
| `react-doctor` | `INSTALL_REACT_DOCTOR=1 bash scripts/setup-local.sh` | Optional per-machine install only |

---

## Refresh checklist

1. Check repo is clean enough for the intended work:

```bash
git status --short
```

2. Refresh only the upstream you need:

```bash
bash scripts/refresh-ecosystem.sh
bash scripts/refresh-9arm.sh
bash scripts/refresh-skillopt.sh
bash scripts/update-model-roster.sh
```

3. Review the diff. Reject large binaries, private paths, raw data, generated noise, and upstream files that do not directly improve A-Wiki.

```bash
git diff --stat
git diff
```

4. Verify locally:

```bash
python3 scripts/check-privacy.py
python3 scripts/verify-awiki-ready.py --skip-remote --skip-evals
python3 -m pytest -q
```

5. Update release tracking when the refresh changes capability:

```bash
$EDITOR VERSION
$EDITOR CHANGELOG.md
```

6. Commit directly to `main` with one logical commit:

```bash
git add <changed-files>
git commit -m "chore(upstream): refresh <name>"
git push origin main
```

---

## What must stay out of git

- `drive/`, `raw/`, `.tmp/`, virtualenvs, local MCP configs, local hooks, secrets
- heavy upstream assets unless they are intentionally curated and documented
- personal Google Drive paths or account-specific mount paths
- generated model-intel cache under `.tmp/model-intel/`

---

## Review standards

- Prefer lightweight adapters over vendoring whole tools.
- Prefer upstream links and refresh scripts over copied snapshots.
- Prefer issue/report workflows for volatile data such as model pricing and free tiers.
- If a refresh changes agent behavior, verify it with tests or a deterministic smoke check before committing.
