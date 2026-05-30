# Mobile and Obsidian Workflow

> Purpose: separate human/mobile editing from AI-agent editing so A-Wiki stays synced across Mac, Work PC, mobile, and Obsidian.

## Rule

Use **one active editor at a time**.

Before switching devices:

```bash
python3 scripts/sync.py --now
git status --short
```

Close the old AI/Obsidian session before editing on another device. This prevents two devices from writing `wiki/`, `log.md`, or generated context at the same time.

## AI-Agent Workflow

Use this for Codex, Claude Code, Gemini CLI, Cline, Cursor, Windsurf, Copilot, or Antigravity.

```bash
git pull --ff-only origin main
python3 scripts/agent-preflight.py
python3 scripts/verify-awiki-ready.py --skip-evals
```

Then work normally. Before ending:

```bash
python3 scripts/gen-index.py
python3 scripts/sync.py --now
```

## Obsidian Workflow

Use Obsidian for reading, light editing, graph navigation, and manual notes.

Recommended order:

1. Open A-Wiki after the AI session is closed.
2. Pull/sync before editing.
3. Avoid editing generated files in `wiki/context/overview-*.md`, `wiki/context/wiki-overview.md`, `wiki/context/knowledge-graph.md`, and `wiki/context/review-report.md`.
4. Do not edit `raw/` or `drive/`.
5. After edits, run:

```bash
python3 scripts/gen-index.py
python3 scripts/sync.py --now
```

## Mobile Workflow

Mobile is best for asking, reading, reviewing, and small note edits.

Avoid on mobile:

- large refactors
- dependency installs
- editing `CLAUDE.md`, `AGENTS.md`, or platform config
- resolving git conflicts
- handling secrets

If mobile edits were made through Obsidian or GitHub web, run this on desktop later:

```bash
git pull --ff-only origin main
python3 scripts/agent-preflight.py
python3 scripts/gen-index.py
```

## Daemon Mode

Use only on one desktop at a time:

```bash
python3 scripts/sync.py --daemon --interval 30 --debounce 10
```

Do not run daemon mode simultaneously on Mac and Work PC.
