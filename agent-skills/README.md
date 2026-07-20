# Agent Skills — Autonomous AI Agent Swarm Repository

> **IRON LAWS enforced at this level.** Every skill file in `engineering/` and `productivity/` embeds
> the uncompromising discipline of Superpowers methodology. These are NOT optional guidelines —
> they are unbreachable execution boundaries.

## Structure

| Directory | Contents |
|-----------|----------|
| `engineering/` | Debug, scrutinize, post-mortem — TDD-enforced engineering discipline |
| `productivity/` | Management talk, non-code workflows |
| `swarm-intelligence/` | Dynamic model scouting, capability routing, swarm allocation |
| `infrastructure/` | Git safety, cross-platform session continuity |
| `automations/` | Hook scripts, task runners, routine automation |
| `extensibility/` | Symlink connectors, global agent integration |

## Iron Laws (Applied to ALL skills below)

1. **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST** — Strict TDD enforcement.
2. **NO BUG FIXING WITHOUT ROOT CAUSE INVESTIGATION FIRST** — Forbid superficial patching;
   use the debug-mantra 4-step process: Reproduce → Trace → Falsify → Cross-reference.
3. **If a parallel or secondary model violates these rules, the primary agent MUST discard
   the output and rewrite it.** No exceptions. No "merge anyway."

## 🔑 Secrets & Multi-Device Sync

API keys, tokens, and other private `.env` files never live in this repo — they live in a
Google Drive-backed folder resolved via the `drive/` link (or `$A_WIKI_DRIVE_PATH`), which
syncs to every device signed into the same Google account. No per-machine key setup needed;
edit the secrets file once on any device and it propagates everywhere.

- Universal keys used by every agent/repo: `<drive>/secrets/global.env`
- Read by Python via `scripts/lib/drive_secrets.py`; auto-sourced into every shell
  (bash/zsh via `scripts/setup-ide-env.sh`, PowerShell via `scripts/setup-ide-env.ps1`)
- Full mechanism, file layout, and per-surface details: `docs/protocols/secrets-global-env.md`
- Never hardcode a machine-specific Drive path (e.g. a drive letter) in any tracked file —
  always resolve dynamically through `drive/` or `$A_WIKI_DRIVE_PATH`.
