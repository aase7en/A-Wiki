# Plan — A-Wiki Live: Universal Real-Time Monitoring Across All Agents

## Problem

A-Wiki Live dashboard only works for Claude Code and Codex (via hooks). Other agents (Kilo, Cursor, Windsurf, Cline, Copilot, Aider, Antigravity) don't auto-start the dashboard or emit `session_start` events, so real-time monitoring doesn't work.

## Current State

| Agent | Hooks | Session Start | Dashboard Auto-Start |
|-------|-------|---------------|---------------------|
| Claude Code | ✅ `.claude/settings.json` → `session_start.py` | ✅ `_emit_session_start()` | ✅ `_ensure_dashboard()` |
| Codex | ✅ `.codex/hooks.json` → `session_start.py` | ✅ `_emit_session_start()` | ✅ `_ensure_dashboard()` |
| Kilo | ❌ No hooks | ⚠️ Manual `/awiki-session-start` | ⚠️ Manual `/awiki-dashboard` |
| Cursor | ❌ No hooks | ❌ None | ❌ None |
| Windsurf | ❌ No hooks | ❌ None | ❌ None |
| Cline | ❌ No hooks | ❌ None | ❌ None |
| Copilot | ❌ No hooks | ❌ None | ❌ None |
| Aider | ❌ No hooks | ❌ None | ❌ None |
| Antigravity | ❌ Unknown | ❌ None | ❌ None |

**VS Code-based editors** (Kilo, Cursor, Windsurf, Cline): `.vscode/tasks.json` exists with `runOn: folderOpen` → `dashboard-ensure.sh` — but this only starts the dashboard, doesn't emit `session_start`.

## Solution

### Phase 1: Universal Init Script

Create `scripts/live-dashboard/awiki-live-init.sh`:
```bash
#!/usr/bin/env bash
# Universal A-Wiki Live initializer — idempotent, safe to call multiple times
# 1. Ensure dashboard daemon is running
# 2. Emit session_start event
# Usage: bash scripts/live-dashboard/awiki-live-init.sh [agent_name]

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AGENT="${1:-unknown}"

# Ensure dashboard
bash "$REPO_ROOT/scripts/dashboard-ensure.sh" --no-browser

# Emit session_start
python3 "$REPO_ROOT/scripts/live-dashboard/event_logger.py" session_start agent="$AGENT"

echo "✅ A-Wiki Live initialized (agent=$AGENT)"
```

### Phase 2: Per-Agent Configuration

#### 2.1 Kilo (`.kilo/command/awiki-session-start.md`)
Already created. Verify it calls `awiki-live-init.sh kilo` instead of separate commands.

#### 2.2 Cursor (`.cursorrules`)
Add to end of file:
```markdown
## A-Wiki Live Dashboard

At session start, run:
```bash
bash scripts/live-dashboard/awiki-live-init.sh cursor
```
This ensures the real-time monitor is running and emits your session event.
```

#### 2.3 Windsurf (`.windsurfrules`)
Same as Cursor — add identical section.

#### 2.4 Cline (`.clinerules`)
Create new file with A-Wiki instructions + dashboard init.

#### 2.5 GitHub Copilot (`.github/copilot-instructions.md`)
Add section:
```markdown
## A-Wiki Live Dashboard

Run at session start:
```bash
bash scripts/live-dashboard/awiki-live-init.sh copilot
```
```

#### 2.6 Aider (`.aider.conf.yml`)
Add instruction comment:
```yaml
# At session start, run: bash scripts/live-dashboard/awiki-live-init.sh aider
```

#### 2.7 Antigravity
Research config format. If it uses a rules file, add similar instruction.

### Phase 3: Enhanced Event Logging (Optional)

Add `task_start`/`task_complete` events for planning:

1. **TodoWrite hook**: Emit `task_start` when TodoWrite is called
2. **Plan file creation**: Emit `task_start` when agent creates a plan file
3. **Code writing**: Already emitted as `hook_check` events via `hooks_runner.py`

This requires:
- Adding `PostToolUse` hook for `TodoWrite` in Claude/Codex settings
- Adding instruction for other agents to call `event_logger.py task_start`

### Phase 4: Verification

Test each agent:
1. Open new session in each editor
2. Verify dashboard auto-starts (check `lsof -i :7790`)
3. Verify `session_start` event appears in dashboard
4. Verify tool use events appear in real-time
5. Verify planning events appear (if Phase 3 implemented)

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/live-dashboard/awiki-live-init.sh` | Create | Universal init script |
| `.cursorrules` | Edit | Add dashboard init instruction |
| `.windsurfrules` | Edit | Add dashboard init instruction |
| `.clinerules` | Create | Cline rules + dashboard init |
| `.github/copilot-instructions.md` | Edit | Add dashboard init instruction |
| `.aider.conf.yml` | Edit | Add dashboard init comment |
| `.kilo/command/awiki-session-start.md` | Edit | Use `awiki-live-init.sh` |
| `.claude/settings.json` | Verify | Already has `session_start.py` |
| `.codex/hooks.json` | Verify | Already has `session_start.py` |
| `.vscode/tasks.json` | Verify | Already has `runOn: folderOpen` |

## Success Criteria

1. ✅ Dashboard auto-starts in all 8 agents
2. ✅ `session_start` event emitted in all 8 agents
3. ✅ Real-time events visible in dashboard for all agents
4. ✅ No mock data — all events are real

## Risks

1. **Antigravity config unknown** — need to research
2. **Aider may not support bash commands** — may need alternative approach
3. **Copilot may not support session start** — may need manual trigger
4. **Performance** — emitting events on every tool use could slow down agents (mitigated by `hooks_runner.py` being fast)

## Rollback

If any agent breaks, remove the added instruction from its config file. Dashboard auto-start is idempotent and safe.
