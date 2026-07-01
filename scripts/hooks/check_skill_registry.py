#!/usr/bin/env python3
"""
Hook: Skill Registry Gate
-------------------------
PreToolUse gate that enforces skills-registry.json as the single source of truth.

Blocks (exit 2) when:
  - Write/MultiEdit creates a SKILL.md whose name is NOT in the registry
    (new skills must be registered first: add to registry → regen → commit).

Warns (stderr, exit 0) when:
  - frontmatter is missing `domain` or `lifecycle_phase` (grandfather legacy)
  - the skill being edited is `status: deprecated` (suggest migrated_to)

Passes through when:
  - tool is not Edit/Write/MultiEdit
  - file_path is empty or not a SKILL.md
  - the skill is already in the registry with valid frontmatter

Override (emergency): HOOK_SKIP=check_skill_registry (handled by hooks_runner).

See: docs/protocols/skill-frontmatter-schema.md
     docs/architecture/skill-architecture-plan.md (Chunk 3)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _emit(msg: str) -> None:
    sys.stderr.write(msg if msg.endswith("\n") else msg + "\n")


def _extract_frontmatter_value(content: str, key: str) -> tuple[bool, str | None]:
    if not content.startswith("---"):
        return False, None
    end = content.find("\n---", 3)
    if end < 0:
        return False, None
    fm = content[3:end]
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*)$", re.MULTILINE)
    m = pat.search(fm)
    if not m:
        return False, None
    return True, m.group(1).strip()


def _extract_frontmatter_all(content: str) -> dict[str, str]:
    """Parse all scalar frontmatter keys (sufficient for domain/lifecycle checks)."""
    out: dict[str, str] = {}
    if not content.startswith("---"):
        return out
    end = content.find("\n---", 3)
    if end < 0:
        return out
    fm = content[3:end]
    for line in fm.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        out[key.strip()] = val.strip()
    return out


def _load_registry_names() -> set[str]:
    """Load all registered skill names + aliases from skills-registry.json."""
    repo_root = Path(__file__).resolve().parents[2]
    registry_path = repo_root / "skills-registry.json"
    if not registry_path.exists():
        return set()  # registry not bootstrapped yet — pass through
    try:
        with open(registry_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return set()
    names: set[str] = set()
    for skill in data.get("skills", []):
        names.add(skill["name"])
        for alias in skill.get("aliases", []) or []:
            names.add(alias)
    return names


def _load_registry_status(name: str) -> str | None:
    """Return the status of a skill by name, or None if not found."""
    repo_root = Path(__file__).resolve().parents[2]
    registry_path = repo_root / "skills-registry.json"
    if not registry_path.exists():
        return None
    try:
        with open(registry_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    for skill in data.get("skills", []):
        if skill["name"] == name:
            return skill.get("status", "canonical")
    return None


def _skill_name_from_path(file_path: str) -> str | None:
    """Extract the skill name (parent dir of SKILL.md) from a file path."""
    p = Path(file_path)
    if p.name != "SKILL.md":
        return None
    return p.parent.name


def _final_write_content(tool_name: str, tool_input: dict, file_path: str) -> str | None:
    """Reconstruct post-edit content (mirrors check_harness_routing.py)."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            current = f.read()
    except OSError:
        return None
    if tool_name == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        if not old:
            return current
        return current.replace(old, new, 1)
    if tool_name == "MultiEdit":
        out = current
        for edit in tool_input.get("edits", []):
            old = edit.get("old_string", "")
            new = edit.get("new_string", "")
            if not old:
                continue
            out = out.replace(old, new, 1)
        return out
    return None


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)
    if not file_path:
        sys.exit(0)

    # Only gate SKILL.md files.
    if not file_path.replace("\\", "/").endswith("/SKILL.md") and Path(file_path).name != "SKILL.md":
        sys.exit(0)

    # SECURITY: reject path-traversal attempts (file_path reaching outside skill dirs).
    # The hook only needs to read SKILL.md under the repo's skill surfaces; reject
    # anything containing ".." segments that could escape those trees.
    normalized = file_path.replace("\\", "/")
    if "/../" in normalized or normalized.startswith("../") or Path(normalized).is_absolute() and ".." in normalized:
        _emit(
            "🚫 [check_skill_registry] Blocked path-traversal in file_path\n"
            f"   path: {file_path}\n"
            "   why: SKILL.md paths must stay within skill directories (no '..' escapes)\n"
            "   override (emergency): HOOK_SKIP=check_skill_registry"
        )
        sys.exit(2)

    skill_name = _skill_name_from_path(file_path)
    if not skill_name:
        sys.exit(0)

    content = _final_write_content(tool_name, tool_input, file_path)
    if content is None:
        sys.exit(0)

    # --- Gate 1: skill must be registered ---
    registered = _load_registry_names()
    if registered and skill_name not in registered:
        _emit(
            "🚫 [check_skill_registry] Blocked Write to unregistered skill\n"
            f"   skill: '{skill_name}' not found in skills-registry.json\n"
            "   fix: register the skill first:\n"
            "     1. Add an entry to skills-registry.json (name, domain, lifecycle_phase, path)\n"
            "     2. Run: python scripts/regen-skill-surfaces.py\n"
            "     3. Re-attempt this edit\n"
            "   why: registry is the single source of truth (skill architecture Chunk 3)\n"
            "   override (emergency): HOOK_SKIP=check_skill_registry"
        )
        sys.exit(2)

    # --- Gate 2: warn on missing domain/lifecycle (grandfather legacy) ---
    fm = _extract_frontmatter_all(content)
    # Also check the name field in frontmatter (authoritative).
    fm_name_present, fm_name = _extract_frontmatter_value(content, "name")
    domain_present, _ = _extract_frontmatter_value(content, "domain")
    lifecycle_present, _ = _extract_frontmatter_value(content, "lifecycle_phase")

    warnings: list[str] = []
    if not domain_present:
        warnings.append("domain")
    if not lifecycle_present:
        warnings.append("lifecycle_phase")
    if warnings:
        _emit(
            f"⚠️  [check_skill_registry] '{skill_name}' frontmatter missing: {', '.join(warnings)}\n"
            "   Registry-conforming skills should declare these fields.\n"
            "   (grandfathered — not blocked; add them when convenient)\n"
            "   see: docs/protocols/skill-frontmatter-schema.md"
        )

    # --- Gate 3: warn on deprecated skill being edited ---
    status = _load_registry_status(skill_name)
    if status == "deprecated":
        _emit(
            f"⚠️  [check_skill_registry] '{skill_name}' is status: deprecated\n"
            "   Consider editing the successor instead. Check its 'migrated_to' field\n"
            "   in skills-registry.json."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
