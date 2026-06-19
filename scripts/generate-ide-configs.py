#!/usr/bin/env python3
"""
generate-ide-configs.py — Generate cross-IDE config files from .kilo/ source.

Reads .kilo/agents/*.md, .kilo/kilo.jsonc, and AGENTS.md to produce:
  - .cursorrules       (Cursor)
  - .windsurfrules     (Windsurf)
  - .clinerules        (Cline)
  - .github/copilot-instructions.md  (GitHub Copilot)

All configs reference .kilo/ as the source of truth (not duplicates).
Idempotent, re-runnable.

CLI:
  python3 scripts/generate-ide-configs.py             # write all configs
  python3 scripts/generate-ide-configs.py --check     # report only, no write
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".kilo" / "agents"
COMMANDS_DIR = REPO_ROOT / ".kilo" / "command"
KILO_CONFIG = REPO_ROOT / ".kilo" / "kilo.jsonc"


# ── Data sources ──────────────────────────────────────────────────────────

def get_agent_list() -> list[dict[str, str]]:
    """Read .kilo/agents/*.md frontmatter and return agent info."""
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
    from parse_agent_md import read_agents_dir  # type: ignore
    agents = read_agents_dir(AGENTS_DIR)
    result = []
    for agent_id, entry in sorted(agents.items()):
        result.append({
            "id": agent_id,
            "name": entry.get("options", {}).get("displayName", agent_id),
            "description": entry.get("description", ""),
        })
    return result


def get_commands() -> list[str]:
    """Return sorted list of command filenames from .kilo/command/."""
    if not COMMANDS_DIR.is_dir():
        return []
    return sorted(p.name for p in COMMANDS_DIR.glob("*.md"))


# ── Templates ─────────────────────────────────────────────────────────────

SHARED_HEADER = """# A-Wiki — {ide_name}

> This project uses **A-Wiki** as its knowledge brain.
> Full brain specification: read `AGENTS.md` in the repo root.
> Source of truth for agents: `.kilo/agents/` — edit prompts there.
> Source of truth for commands: `.kilo/command/` — edit handlers there.

## First 3 Commands

```bash
git pull --ff-only origin main
python3 scripts/agent-preflight.py
python3 scripts/verify-awiki-ready.py --skip-evals
```

## External Data Layer

- Heavy/raw/private files live outside git in Google Drive.
- `drive/` and `raw/` are machine-local links created by `bash scripts/setup-local.sh`.
- Verify OS-specific setup with `python3 scripts/verify-cross-platform.py --build-vec`.
- Never edit or commit `raw/`, `drive/`, `.tmp/`, `.mcp.json`, `.codex/`, or `.claude/`.

## Brain Improvement Gate

Before changing A-Wiki brain capabilities, agent rules, skills, hooks, plugins, scripts, sync, or public-safe data policy, follow `docs/protocols/brain-improvement-gate.md`.

- Clear gain for A-Wiki as a second brain
- Lightweight reusable shape first: hook, skill, plugin, GitHub Action, symlink, script, protocol, local index, or multi-model parallel workflow
- Cost-first, cross-platform, cross-device
- Private/raw/secrets stay in gitignored `drive/`/`raw/`

## Cross-Agent Plan Handoff

- Before multi-step work or Plan Mode output, follow `docs/protocols/cross-agent-plan-handoff.md`
- Split work into resumable chunks with ID/status/files/verify/handoff note
- Read/update local `handoff.md` before pause, limit, or Agent/IDE switch

## About This Project

**A-Wiki** = Hybrid swarm intelligence + knowledge wiki brain.
Core directories: `wiki/` (knowledge) · `raw/` (immutable sources) · `agent-skills/` (swarm protocol + Iron Laws) · `scripts/` (automation)

### Agents (defined in `.kilo/agents/`)

{agent_table}

### Commands (defined in `.kilo/command/`)

{command_list}

## Iron Laws (UNBREACHABLE)

1. NO production code without a failing test first
2. NO bug fixing without root cause investigation first (debug-mantra 4-step)
3. If a parallel model violates #1 or #2 → DISCARD and REWRITE
4. `raw/` is immutable — never edit or delete files inside it
5. Config files (AGENTS.md, CLAUDE.md) must not be edited without explicit permission

## Wiki Conventions

- `wiki/` filenames: kebab-case English only (e.g. `mqtt-broker.md`)
- Confidence markers required on all factual claims: `[training]` / `[verified YYYY-MM-DD]`
- Update `log.md` and `wiki/context/` after every significant edit
- Plan before implementing if change affects >3 files — list them first
- For Plan Mode or multi-step work, chunk the plan and checkpoint local `handoff.md`

## Cost Pyramid (always start at lowest level)

- **Level -1** (free, offline): `python scripts/wiki/search-wiki.py "query"`
- **Level 1** (free API): `bash scripts/swarm/delegate.sh "query"`
- **Level 4** (current AI): complex reasoning only — use sparingly

Model selection is dynamic — never hard-code model names.
Check current free models: `cat wiki/context/model-roster.conf`

## Commit Rules

- Commit directly to `main` — **NO branch, NO PR, NO worktree**
- Format: `type(scope): description`
  - Types: `feat` · `fix` · `docs` · `wiki` · `refactor` · `test` · `chore`
- One logical change per commit

## Do Not

- Edit or delete anything in `raw/`
- Create git branches or open PRs
- Hard-code API keys or model names anywhere
- Skip writing a failing test before adding production code
"""

COPILOT_FOOTER = """
*Generated by scripts/generate-ide-configs.py — {date}*
"""


def format_agents_table(agents: list[dict[str, str]]) -> str:
    lines = ["| Agent | Description |", "|-------|-------------|"]
    for a in agents:
        lines.append(f"| `{a['id']}` | {a['description']} |")
    return "\n".join(lines)


def format_command_list(commands: list[str]) -> str:
    if not commands:
        return "(no custom commands yet)"
    return "\n".join(f"- `/\"{c.replace('.md', '')}\"` — see `.kilo/command/{c}`" for c in commands)


# ── Generators ────────────────────────────────────────────────────────────

def build_content(ide_name: str, agents: list[dict[str, str]], commands: list[str],
                  is_copilot: bool = False) -> str:
    agent_table = format_agents_table(agents)
    command_list = format_command_list(commands)
    content = SHARED_HEADER.format(
        ide_name=ide_name,
        agent_table=agent_table,
        command_list=command_list,
    )
    # Copilot uses Markdown separators; others use blank lines
    if is_copilot:
        content += COPILOT_FOOTER.format(date=date.today().isoformat())
    return content


def generate_all(agents: list[dict[str, str]], commands: list[str],
                 dry_run: bool = False) -> list[tuple[Path, str]]:
    configs: list[tuple[Path, str]] = [
        (REPO_ROOT / ".cursorrules",
         build_content("Cursor Rules", agents, commands)),
        (REPO_ROOT / ".windsurfrules",
         build_content("Windsurf Rules", agents, commands)),
        (REPO_ROOT / ".clinerules" / "rules.md",
         build_content("Cline Rules", agents, commands)),
        (REPO_ROOT / ".github" / "copilot-instructions.md",
         build_content("GitHub Copilot Instructions", agents, commands, is_copilot=True)),
    ]
    for path, content in configs:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not dry_run:
            path.write_text(content, encoding="utf-8")
    return configs


# ── CLI ───────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Generate cross-IDE configs from .kilo/ source")
    ap.add_argument("--check", action="store_true", help="report only; do not write")
    args = ap.parse_args(argv)

    try:
        agents = get_agent_list()
    except Exception as exc:
        print(f"ERROR reading agents: {exc}", file=sys.stderr)
        return 1

    commands = get_commands()
    configs = generate_all(agents, commands, dry_run=args.check)

    for path, _ in configs:
        rel = path.relative_to(REPO_ROOT)
        status = "would write" if args.check else "wrote"
        print(f"  {status} {rel}")

    if args.check:
        return 0

    print(f"\nOK — {len(configs)} IDE config(s) generated from .kilo/ source")
    print(f"  Agents: {len(agents)} from .kilo/agents/")
    print(f"  Commands: {len(commands)} from .kilo/command/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
