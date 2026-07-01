# Per-Agent Private Storage Convention

> **Status:** Active (Chunk 4 of the Universal Skill Architecture)
> **Implements:** `scripts/drive_path.py` `resolve_agent_dir(agent)`
> **Storage rule:** all agent-local private state lives under `drive/.agents/<agent>/`

Each AI agent (ZCode, Claude, Codex, Hermes, Kilo, Cline, Windsurf, OpenClaw,
Gemini, and future agents) gets an **isolated directory** under `drive/.agents/`
on the external Google Drive (`A-Wiki-Data`). This keeps agent state:

- **Private** — gitignored, never committed to the public repo
- **Isolated** — agents never overwrite each other's state
- **Portable** — synced across machines via Google Drive
- **Discoverable** — one canonical location per agent

## Directory layout

```
drive/  (→ A-Wiki-Data on Google Drive)
  └─ .agents/
      ├─ zcode/        ← .zcode local state, history, cache
      ├─ claude/       ← .claude/settings.local.json, todos, history
      ├─ codex/        ← .codex local overrides
      ├─ hermes/       ← .hermes plans, desktop-attachments
      ├─ kilo/         ← .kilo plans, worktrees, agent-manager
      ├─ cline/        ← .clinerules local state
      ├─ windsurf/     ← .windsurfrules local state
      ├─ openclaw/     ← OpenClaw local state
      ├─ gemini/       ← .gemini/settings.local.json
      └─ [new-agent]/  ← convention: 1 folder per agent (add to _KNOWN_AGENTS)
```

## Usage in scripts

```python
import sys; sys.path.insert(0, "scripts")
from drive_path import resolve_agent_dir

# Get this agent's private dir (auto-created)
agent_state = resolve_agent_dir("zcode")
secrets_file = agent_state / ".secrets"
```

## Adding a new agent

1. Add the agent name to `_KNOWN_AGENTS` in `scripts/drive_path.py`.
2. (If it needs a skill surface) Add a generator module in
   `scripts/skills_registry/generators/` + one line in the `GENERATORS` dict
   in `scripts/regen-skill-surfaces.py`.
3. (Optional) Create a symlink from `.[agent]/` in the repo root →
   `drive/.agents/[agent]/` during `setup-local.sh`.

## What belongs here

| Belongs in `drive/.agents/<agent>/` | Belongs in the repo (public) |
|--------------------------------------|------------------------------|
| Machine-specific settings overrides | Shared skill definitions |
| History / cache / logs | Protocol docs |
| Per-agent secrets (`.secrets`) | `.example` templates |
| Desktop attachments, screenshots | Public hooks + scripts |
| Agent-local working memory | Wiki knowledge pages |

## Security

- The `.agents/` directory is gitignored via the `drive/` rule.
- `scripts/check-privacy.py` scans git-tracked files for personal paths.
- `scripts/lib/drive_secrets.py` reads secrets without printing values.
- Never symlink an agent's `.agents/<agent>/.secrets` into the repo root.
