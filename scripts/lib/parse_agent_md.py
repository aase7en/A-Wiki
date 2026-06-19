"""Parse Kilo agent definitions from .kilo/agents/*.md files.

Each .md file has YAML frontmatter (--- delimited) with fields:
  mode, description, options, permission

The body after frontmatter is the agent prompt.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def parse_agent_md(file_path: Path) -> dict[str, Any] | None:
    """Parse a single agent .md file. Returns dict with frontmatter + prompt, or None."""
    content = file_path.read_text(encoding="utf-8")
    m = re.match(r'^---\s*\n(.*?)\n(?:---|\.\.\.)\s*\n(.*)', content, re.DOTALL)
    if not m:
        return None

    raw_frontmatter = m.group(1)
    prompt_body = m.group(2).strip()

    frontmatter = yaml.safe_load(raw_frontmatter) or {}

    result: dict[str, Any] = {
        "prompt": prompt_body,
    }

    for key in ("mode", "description", "options", "permission", "name"):
        if key in frontmatter:
            result[key] = frontmatter[key]

    agent_id = None
    if "options" in result and isinstance(result["options"], dict):
        agent_id = result["options"].get("id")
    if not agent_id:
        agent_id = file_path.stem
    result["_agent_id"] = agent_id

    return result


def read_agents_dir(agents_dir: Path) -> dict[str, dict[str, Any]]:
    """Read all .kilo/agents/*.md files, return {agent_id: {parsed entry}}."""
    agents: dict[str, dict[str, Any]] = {}
    if not agents_dir.is_dir():
        return agents
    for f in sorted(agents_dir.glob("*.md")):
        parsed = parse_agent_md(f)
        if parsed is not None:
            agent_id = parsed.pop("_agent_id")
            agents[agent_id] = parsed
    return agents
