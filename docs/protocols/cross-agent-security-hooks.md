# Cross-Agent Security Hooks Protocol (USA-1 §5.2)

> **Part of**: [USA-1 Universal Skill Architecture](../architecture/universal-skill-architecture.md) §5.
> **ADR**: [0008](../../decisions/0008-universal-skill-architecture.md).
> **Binding**: every agent that supports PreToolUse hooks.

This is the contract for how A-Wiki's PreToolUse security hooks
(`check_secret_leak`, `check_machine_path`, `check_skill_registry`, ...) run
across **every supporting agent** — not just Claude/Codex.

---

## The shared spine: `scripts/hooks_runner.py`

Every supporting agent funnels its PreToolUse events into a single Python
orchestrator at [`scripts/hooks_runner.py`](../../scripts/hooks_runner.py).
That orchestrator:

1. Auto-discovers every `scripts/hooks/*.py` (alphabetical).
2. Runs each hook with the agent's hook payload on stdin.
3. Exits `0` (pass), `2` (block), or non-zero (warning, non-blocking).

Two invocation styles:

| Style | Used by | Behaviour |
|---|---|---|
| **Specific** — `hooks_runner.py <hook-name>` | Claude, Codex | Runs only the named hook. Each agent config lists every hook explicitly. |
| **Run-all** — `hooks_runner.py` (no args) | Gemini, Cline | Runs EVERY hook in `scripts/hooks/`. Adding a new hook file = automatic coverage. |

This means: **dropping a new `check_*.py` into `scripts/hooks/`** immediately
covers Gemini + Cline. Claude + Codex need one explicit line each (see below).

---

## Agent × hook-mechanism matrix (verified 2026-07-14)

| Agent | Native hooks? | Config file | Invocation style | Wired into? |
|---|---|---|---|---|
| **Claude Code** | ✅ | `.claude/settings.json` → `hooks.PreToolUse` | Specific | `check-machine-path`, `check-secret-leak` (+ all existing) |
| **Codex** | ✅ | `.codex/hooks.json` → `hooks.PreToolUse` | Specific | `check-machine-path`, `check-secret-leak` (+ all existing) |
| **Gemini CLI** | ✅ | `.gemini/settings.json` → `hooks.BeforeTool` | Run-all | Auto (every `scripts/hooks/*.py`) |
| **Cline** | ✅ (via adapter) | `.clinerules/hooks/PreToolUse` → `scripts/cline-hooks/adapter.sh` | Run-all | Auto (adapter forwards to `hooks_runner.py`) |
| **Kilo** | ❌ | `kilo.jsonc` (skills only, no hooks) | — | Layer 2 (pre-commit) + Layer 3 (CI) |
| **ZCode** | ❌ | `config.json` (mcp only, no hooks) | — | Layer 2 + Layer 3 |
| **Antigravity** | ❌ (absent on this machine) | — | — | Layer 2 + Layer 3 |
| **Windsurf** | ❌ (absent on this machine) | — | — | Layer 2 + Layer 3 |
| **OpenClaw** | ❌ (absent on this machine) | — | — | Layer 2 + Layer 3 |

**Agents without native hook support** (Kilo, ZCode, Antigravity, Windsurf,
OpenClaw) rely on:
- **Layer 2**: `scripts/hooks/pre-commit-awiki.sh` (catches on commit).
- **Layer 3**: `.github/workflows/ci.yml` (catches on push).

These are weaker (not realtime), but the only option for agents without a
PreToolUse event. A future agent that adds native hooks should follow the
adapter pattern below.

---

## Adding a new agent that supports hooks

If the new agent exposes a PreToolUse event:

1. **If its payload schema matches `hooks_runner.py`'s stdin contract**
   (`{"tool_name": "...", "tool_input": {...}, ...}`), point its config
   directly at `python3 scripts/hooks_runner.py` (run-all style → automatic
   coverage of every hook).
2. **If its payload schema differs**, write a thin adapter at
   `scripts/<agent>-hooks/adapter.sh` (see `scripts/cline-hooks/adapter.sh`
   as the reference). The adapter translates the agent's payload to the
   `hooks_runner.py` contract, then forwards via stdin.

No other file needs changing — `hooks_runner.py` is the single integration point.

## Adding a new security hook

1. Create `scripts/hooks/check_<thing>.py` following the stdin/stdout
   contract (see `check_machine_path.py` for the template).
2. For Claude + Codex (specific-style), add one entry to each config's
   `PreToolUse` → `Edit|Write|MultiEdit` matcher:
   ```json
   { "type": "command", "command": "python3 scripts/hooks_runner.py check-<thing>" }
   ```
3. Gemini + Cline pick it up automatically (run-all style).
4. Kilo/ZCode/etc. catch it at Layer 2/3.

---

## The three-layer defense (recap)

```
Layer 1 — PreToolUse (realtime, supporting agents)
   Claude + Codex: specific (config lists every hook)
   Gemini + Cline: run-all (auto-covers new hooks)
   Kilo/ZCode/others: NOT supported natively

Layer 2 — pre-commit (local gate, ALL agents via git)
   scripts/hooks/pre-commit-awiki.sh

Layer 3 — CI (remote gate, ALL agents via GitHub)
   .github/workflows/ci.yml → Security pattern scan step
```

No single layer is trusted alone. Layer 1 is realtime but agent-limited;
Layer 2 catches what slips through on commit; Layer 3 is the last line on push.
