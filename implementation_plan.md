# Implementation Plan — Cline as Claude Code for A-Wiki

[Overview]
Rewrite `.clinerules` to transform Cline (VS Code extension) into a Claude-Code-equivalent agent for A-Wiki sessions: identical First-action file reads, swarm delegation decision matrix, live dashboard auto-start, and "instruction-driven hook discipline" that runs existing `scripts/hooks/` through `execute_command` and `.vscode/tasks.json`. A-Wiki's hook scripts (`scripts/hooks/*.py`), orchestrator (`scripts/hooks_runner.py`), and live dashboard (`scripts/live-dashboard/server.py`) are already agent-agnostic — this plan creates the missing `.clinerules` wiring and two companion files so Cline knows what to run, when.

The user has confirmed permission to edit `.clinerules` (Iron Law #5 exception) and requested full scope: Phase 1 (First-action session), Phase 2 (swarm delegation), Phase 3 (dashboard auto-start), plus Step 2.5 (Hook Discipline + `.vscode/tasks.json`). Three files are created/modified; no deletions.

[Types]
No new types or data structures introduced. All artifacts are configuration files and one thin shell script. Referenced existing interfaces (not modified):

- **Hook input** (stdin JSON to `hooks_runner.py`): `{"tool_name": str, "tool_input": dict, ...}` — exit 0 = pass, exit 2 = block.
- **Live dashboard event** (`event_logger.py` → `.tmp/live-events.jsonl`): `{"ts": float, "type": str, ...}` — JSONL, capped at 1000 lines auto-rotated.
- **VS Code tasks schema**: `{"version": "2.0.0", "tasks": [{"label": str, "type": "shell", "command": str, "group": str | dict}]}`.

[Files]
Three artifacts; zero deletions. Existing `.vscode/settings.json` (`vscode-autoGit.enabled: true`) is preserved untouched.

**New files:**

| File | Purpose |
|------|---------|
| `.vscode/tasks.json` | 4 VS Code tasks mapping `Cmd+Shift+B` groups to A-Wiki hook groups. Replaces what Claude Code's `SessionStart`/`PreToolUse`/`PostToolUse`/`Stop` hooks do automatically. Each task calls `hooks_runner.py` or the relevant hook script directly. |
| `scripts/live-dashboard/start-cline.sh` | One-command session starter: launches dashboard daemon (idempotent via `is_already_running()`), logs `session_start` event via `event_logger.py`, opens browser. ~20 lines of bash. |

**Modified files:**

| File | Change |
|------|--------|
| `.clinerules` | Full rewrite from 166-line reference card → thin-pointer session protocol (~180–200 lines). Backed up to `.clinerules.bak-2026-06-16` before edit. |

**`.vscode/tasks.json` content specification:**
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "A-Wiki: Session Start (Preflight + Context)",
      "type": "shell",
      "command": "python3 scripts/agent-preflight.py && python3 scripts/verify-awiki-ready.py --skip-evals && python3 scripts/live-dashboard/event_logger.py session_start agent=cline",
      "group": {"kind": "build", "isDefault": true},
      "presentation": {"reveal": "always", "panel": "shared"}
    },
    {
      "label": "A-Wiki: Pre-Edit Hooks (All Guards)",
      "type": "shell",
      "command": "echo '{\"tool_name\":\"Edit\",\"tool_input\":{}}' | python3 scripts/hooks_runner.py",
      "group": "build",
      "presentation": {"reveal": "silent", "panel": "shared"}
    },
    {
      "label": "A-Wiki: Post-Wiki-Edit (Gen Index)",
      "type": "shell",
      "command": "python3 scripts/gen-index.py >/dev/null 2>&1",
      "group": "build",
      "presentation": {"reveal": "silent", "panel": "shared"}
    },
    {
      "label": "A-Wiki: Pre-Commit (Secret Leak + Drift + Provenance)",
      "type": "shell",
      "command": "python3 scripts/hooks/check_secret_leak.py && python3 scripts/hooks/check_external_editor_drift.py && python3 scripts/hooks/check_source_original_file.py",
      "group": "build",
      "presentation": {"reveal": "always", "panel": "shared"}
    }
  ]
}
```

**`.clinerules` new structure (section map):**

| Section | Content | Source / Rationale |
|---------|---------|-------------------|
| Header + pointer | "Read `AGENTS.md` for full brain spec" | Thin-pointer; cuts ~40% of current file |
| `## 🚨 First action every session` | 5 mandatory reads (README, wiki-overview, session-memory, preflight, verify-awiki-ready) + load-on-demand list | Mirrors `CLAUDE.md:11–22` |
| `## 🪝 Hook Discipline` | 4 lifecycle points (SessionStart, Before Edit wiki/sources, After wiki edit, Before commit) with fire-and-forget commands | New — instruction-driven hooks |
| `## 🐝 Swarm Intelligence` | 3-tier decision matrix (L1 delegate.sh, L3 use_subagents, L4 self) + 3 swarm patterns | Expanded from current `.clinerules:103–114` |
| `## 🎛 Live Dashboard` | Auto-start command + what to expect | New — Phase 3 |
| `## ✅ Commit / Branch Rules` | Unchanged core rules | Kept from current `.clinerules:118–124` |
| `## Output Format (3-Layer)` | Unchanged output protocol | Kept from current `.clinerules:153–166` |

**`scripts/live-dashboard/start-cline.sh` content specification:**
```bash
#!/usr/bin/env bash
# Cline session starter — dashboard + session-start event
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 "$REPO_ROOT/scripts/live-dashboard/server.py" --daemonize --no-browser
python3 "$REPO_ROOT/scripts/live-dashboard/event_logger.py" session_start agent=cline
echo "🎛  Dashboard: http://localhost:7790"
echo "📡  Session event logged (.tmp/live-events.jsonl)"
```

[Functions]
No production functions added/modified. One shell wrapper created; existing scripts called as-is.

**`start-cline.sh` (new, ~15 lines):**
- Resolve REPO_ROOT from script location (portable, no git dependency).
- Idempotent dashboard start: `server.py --daemonize` returns early if PID file alive (`is_already_running()` at `server.py:107`).
- Session-start event: `event_logger.py session_start agent=cline` → JSONL line in `.tmp/live-events.jsonl`.
- Echo confirmation + URL.
- Always exit 0 (session starter must never block work).

**Existing executables invoked (no modifications):**
- `scripts/hooks_runner.py` — orchestrator; `main()` at line 125; reads stdin JSON, exits 0/2.
- `scripts/live-dashboard/event_logger.py` — `log()` at line 23; CLI `python3 event_logger.py <type> [k=v ...]`.
- `scripts/live-dashboard/server.py` — `is_already_running()` at line 107; `Handler._sse()` at line 450.
- `scripts/agent-preflight.py` — portable safety check.
- `scripts/verify-awiki-ready.py` — wiki health verifier.

[Classes]
No class changes. All hooks and dashboard server classes are consumed as-is.

[Dependencies]
Zero new dependencies. All invoked commands (`python3`, `git`, `bash`, `open`) are available on the target macOS environment. No `requirements.txt`, `package.json`, or `pyproject.toml` changes.

Soft dependency: Cline must read and follow `.clinerules`. Cline loads `.clinerules` automatically as system context (like Claude Code loads `CLAUDE.md`). The Hook Discipline section relies on Cline's obedience to `.clinerules` instructions; this is documented as a known limitation (no hard enforcement, unlike Claude Code hooks).

[Testing]
Configuration artifacts + thin wrapper; Iron Law #1 (failing test first) covers production code, not session automation. Validation is manual verification:

1. `.clinerules` has First-action section: `grep -c "First action every session" .clinerules` → ≥ 1
2. `.clinerules` has Hook Discipline section: `grep -c "Hook Discipline" .clinerules` → ≥ 1
3. `.vscode/tasks.json` is valid JSON: `python3 -c "import json; json.load(open('.vscode/tasks.json'))"` → exit 0
4. `.vscode/tasks.json` has 4 tasks: `python3 -c "import json; print(len(json.load(open('.vscode/tasks.json'))['tasks']))"` → 4
5. `start-cline.sh` is executable: `test -x scripts/live-dashboard/start-cline.sh` → true
6. `start-cline.sh` idempotent: run twice → second run exits 0, no error
7. Dashboard responds: `curl -s http://localhost:7790/status | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])"` → `running`
8. Session-start event logged: `tail -1 .tmp/live-events.jsonl | python3 -c "import sys,json; print(json.load(sys.stdin)['type'])"` → `session_start`
9. Preflight passes: `python3 scripts/agent-preflight.py`
10. Backup exists: `test -f .clinerules.bak-2026-06-16` → true

**Existing tests (no changes):**
- `tests/test_hooks.py` — existing hook tests still pass.
- `tests/test_agent_preflight.py` — existing preflight tests still pass.

[Implementation Order]
Ordered by dependency; each step is complete and verifiable before proceeding.

1. **Backup `.clinerules`** — `cp .clinerules .clinerules.bak-2026-06-16`
2. **Create `.vscode/tasks.json`** — no dependencies; creates the VS Code task shortcuts.
3. **Create `scripts/live-dashboard/start-cline.sh`** — no dependencies; standalone shell wrapper.
4. **Make `start-cline.sh` executable** — `chmod +x scripts/live-dashboard/start-cline.sh`
5. **Rewrite `.clinerules`** — depends on understanding of all sections from plan; uses thin-pointer pattern. Must include all 7 sections in order.
6. **Verify all 10 manual checks** — run the verification checklist.
7. **Commit to main** — `git add .clinerules .vscode/tasks.json scripts/live-dashboard/start-cline.sh && git commit -m "feat(cline): rewrite .clinerules as thin-pointer with First-action session protocol, swarm delegation matrix, live dashboard auto-start, and instruction-driven hook discipline"`