"""Stub for parse_agent_md.read_agents_dir — recover lost source.

.read_agents_dir(agents_dir) → dict[agent_id, entry]
where entry is the YAML frontmatter of `.kilo/agents/<id>.md` flattened.

This module's .pyc was committed without the .py source (Python 3.13 magic
number incompatible with 3.11 runtime). This stub reproduces the documented
contract by parsing the YAML frontmatter directly.

If the original .py source is recovered, delete this file.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Tiny YAML parser sufficient for agent .md frontmatter.

    Supports: scalar `key: value`, nested dict (2-space indent), list (- item).
    Not a full YAML parser — just enough for kilo agent files.
    """
    out: dict[str, Any] = {}
    stack: list[tuple[int, dict]] = [(-1, out)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        # Pop stack to current indent level
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else out
        if line.startswith("- "):
            # List item — parent must be a list, but for our use case we collect
            # as dict with auto-keys (not used by merge_agents which reads scalars)
            value = line[2:].strip()
            # Best-effort: store as string
            key = f"_list_{len(parent)}"
            parent[key] = value
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Try to detect nested dict by next-line indent (simplification: if value
        # empty, treat as nested)
        if value == "":
            new_dict: dict[str, Any] = {}
            parent[key] = new_dict
            stack.append((indent, new_dict))
        else:
            parent[key] = value
    return out


def read_agents_dir(agents_dir: Path) -> dict[str, dict[str, Any]]:
    """Read .kilo/agents/*.md → {agent_id: frontmatter_dict}.

    agent_id is derived from filename (without .md).
    """
    result: dict[str, dict[str, Any]] = {}
    agents_path = Path(agents_dir)
    if not agents_path.is_dir():
        return result
    for md_file in sorted(agents_path.glob("*.md")):
        agent_id = md_file.stem
        content = md_file.read_text(encoding="utf-8")
        m = _FRONTMATTER_RE.match(content)
        if not m:
            continue
        frontmatter = _parse_simple_yaml(m.group(1))
        # Ensure 'options.id' is the canonical id if present
        options = frontmatter.get("options", {})
        if isinstance(options, dict) and options.get("id"):
            agent_id = str(options["id"])
        result[agent_id] = frontmatter
    return result


__all__ = ["read_agents_dir"]
