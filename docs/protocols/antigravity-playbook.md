# Antigravity Integration Playbook

This document defines how AI agents running in the **Antigravity** environment interact with A-Wiki. It extends the universal instructions in `AGENTS.md`.

## First 3 Commands

```bash
git pull --ff-only origin main
python3 scripts/agent-preflight.py
python3 scripts/verify-awiki-ready.py --skip-evals
```

## External Data Layer

- Heavy/raw/private files live outside git in Google Drive `A-Wiki-Data`.
- `drive/` and `raw/` are machine-local links created by `bash scripts/setup-local.sh`.
- Verify OS-specific setup with `python3 scripts/verify-cross-platform.py --build-vec`.
- Never edit or commit `raw/`, `drive/`, `.tmp/`, `.mcp.json`, `.codex/`, or `.claude/`.

---

## 1. Multi-Agent & Parallel Delegation (`invoke_subagent`)

Antigravity equips you with the ability to define and invoke subagents to run tasks in the background.

### When to Delegate
- **Heavy Reading**: Researching across multiple files or directories.
- **Background Tasks**: Fetching external docs or web searches while the main agent continues coding.
- **Isolated Tests**: Running sandboxed execution or verification.

### How to Invoke Subagents
Use the `invoke_subagent` tool with specialized roles:

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Web Researcher",
      "Prompt": "Search for the latest MQTT v5.0 features and compile a summary under 500 words.",
      "Workspace": "inherit"
    }
  ]
}
```

### Roster of Subagent Roles
1. **Web Researcher (`research`)**: Best for web search, scraping documentation, and academic literature searches.
2. **Codebase Analyzer (`research`)**: Read-only exploration of index structures and dependency paths.
3. **Database Checker (`research`)**: Reads database formats or executes test queries in read-only mode.

---

## 2. Browser Agent & Testing Guidelines

If a task requires interacting with a web interface, web application testing, or retrieving dynamic JS pages, use the **Chrome DevTools Plugin / Browser Tool** if available.

### Visual Mockups and Iteration
- Use the `generate_image` tool to create UI mocks and design assets during web app construction.
- Present mockups directly in markdown files using absolute file URI links: `![caption](file:///absolute/path/to/image.png)`.

---

## 3. Platform-Agnostic Hooks Runner

Antigravity executes session lifecycle hooks configured in `.gemini/settings.json`. These hooks are managed through the Python-based `hooks_runner.py` to ensure cross-device consistency.

### Active Hooks

- **PreToolUse**:
  - `check-claudemd-lock`: Prevents accidental edits to root `CLAUDE.md` without unlocking.
  - `check-raw-immutable`: Blocks any edit/write operation on files under `raw/`.
  - `check-bash-destructive-git`: Blocks destructive git actions when there are uncommitted changes.
  - `check-bash-no-branch`: Enforces the solo wiki policy (no branches/PRs).
  - `check-secret-leak`: Scans staged changes for secret tokens or keys before allowing commits.

- **SessionStart**:
  - `session-start-git-pull`: Syncs remote repository state.
  - `wiki-context-check`: Verifies the freshness of context files and auto-rebuilds.
  - `session-start-device`: Registers and logs current device properties.

---

## 4. Cross-Platform Sync Daemon (`sync.py`)

To ensure real-time synchronization between Windows, macOS, iPhone (iOS), and Raspberry Pi (UmbrelOS), run the python sync script.

### Single-User Safe Sync Policy
Since this is a solo wiki, we avoid branch merge conflicts by rebase-syncing with automatic local preference:

```bash
# Run a one-time immediate sync
python scripts/sync.py --now

# Run in background daemon mode (watches for file changes, debounces, commits & pushes)
python scripts/sync.py --daemon --interval 10 --debounce 5
```

- **Conflict Resolution**: During a rebase pull, the sync script resolves conflicts using `-Xtheirs` (our local edits being rebased onto remote) to preserve our latest work.
- **iOS/Mobile**: Rely on Obsidian Git plugin automatic sync behavior on mobile opening/closing.
