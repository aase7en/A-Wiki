# A-Wiki Handoff Priority Plan

> Updated: 2026-05-29
> Purpose: tell the next device or agent exactly what remains, in priority order.

## Start Here On The Next Computer

Run these first:

```bash
git pull origin main
python scripts/agent-preflight.py
python scripts/health_external_data.py
```

If any command fails, fix that before editing wiki/code.

## P0: Secret Safety

Status: **repo guardrails complete; user key rotation still pending**.

Done:

- `scripts/hooks/check_secret_leak.py` exists and is wired through `hooks_runner.py`.
- `scripts/lib/drive_secrets.py --check` reads Drive `.secrets` without printing values.
- Local `.codex/config.toml` on Work PC was sanitized and should not contain API keys.
- Preflight verifies core hook presence and generated context freshness.

Still required:

- User must rotate any API keys that were previously stored in plaintext local Codex config.
- After rotating, update Drive `A-Wiki-Data/.secrets` with new values.
- Run `python scripts/lib/drive_secrets.py --check`.
- Run `python scripts/agent-preflight.py`.

Do not do:

- Do not paste old or new secret values into chat.
- Do not commit `.codex/config.toml`, `.env`, or Drive `.secrets`.

## P1: Cross-Device Verification

Status: **Work PC passes; Mac pending**.

Done on Work PC:

- `python scripts/agent-preflight.py` passes all checks.
- `python scripts/health_external_data.py` resolves `L:\My Drive\A-Wiki-Data`.
- `raw/` contains 54 files through Google Drive.

Still required on Mac:

- Pull `origin/main`.
- Run `python scripts/agent-preflight.py`.
- Run `python scripts/health_external_data.py`.
- If Drive path fails, run `bash scripts/setup-local.sh` or repair the Google Drive mount/link.

## P1: Codex Local Config Sync

Status: **local Work PC config repaired; tracked sync mechanism still pending**.

Done:

- Work PC `.codex/hooks.json` was locally changed to relative hook paths.
- Preflight now audits `.claude/settings.json` and `.codex/hooks.json` hook command paths.

Still required:

- Create a tracked template for ignored `.codex/*`.
- Add a setup/repair command that regenerates `.codex/hooks.json` from the template on each machine.
- Ensure Mac Codex config never contains absolute Work PC paths such as `A:\GitHub\A-Wiki`.

## P2: Dependency Bootstrap Reliability

Status: **pending**.

Known gaps:

- `python scripts/gen-index.py` still warns that `build-vec-index.py` cannot import `apsw`.
- `npx gitnexus detect-changes` failed on Work PC with an internal package error.

Next work:

- Add a bootstrap or preflight repair path for Python dependencies.
- Decide whether vector index is required for baseline preflight or a separate optional health check.
- Document GitNexus repair command once verified.

## P2: Review Noise Reduction

Status: **pending**.

Done:

- Generated context files are excluded from review-check self-input.
- `review-report.md` uses date-only heading to reduce churn.

Still required:

- Add profiles such as `quick`, `links`, `content`, and `strict`.
- Make strict mode actionable instead of producing a huge noisy report.
- Downgrade vendor/imported skill folder checks where appropriate.

## P3: Sync Reliability And Platform Docs

Status: **pending**.

Still required:

- Write a short Mac/PC/mobile workflow: start session, work, verify, commit, push, handoff.
- Add recovery steps for stale git state, missing Drive mount, stale generated context, and broken hooks.
- Final sweep of AGENTS, CLAUDE, GEMINI, Cursor, Cline, Windsurf, Copilot, and Antigravity docs after behavior is stable.

## Current Best Next Step

If the next agent is on the Mac:

1. Run the three start commands above.
2. Fix any Drive/path failures first.
3. Continue with **P1 Codex Local Config Sync** if Codex will be used on Mac.

If the next agent is still on Work PC:

1. Continue with **P1 Codex Local Config Sync**.
2. Then move to **P2 Dependency Bootstrap Reliability**.
