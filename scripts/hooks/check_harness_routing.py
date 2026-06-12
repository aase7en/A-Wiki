#!/usr/bin/env python3
"""
Hook: Harness Routing Gate
--------------------------
Block Write/Edit/MultiEdit on `wiki/sources/<slug>.md` if the page lacks
`routed_via: harness@v\\d+` in its YAML frontmatter.

This enforces the documented routing rule (AGENTS.md §Universal Cost-First
Routing): every A-Wiki agent must ingest sources through the cost-aware
harness (CLI `scripts/batch/route.py`, MCP `wiki_ingest_route`, or shell
wrappers `route.sh` / `route.ps1`). Direct LLM calls that bypass the
harness lose the tier discount and the quality_gate guarantees — and
make per-tier cost reporting impossible.

Strict mode (block) — fails if:
  1. frontmatter has no `routed_via:` key
  2. value does not match `^harness@v\\d+$`

Skip / pass-through when:
  - tool_name not in (Edit, Write, MultiEdit)
  - file_path not under wiki/sources/ OR matches a non-entry filename
    (CLAUDE.md, README.md, AGENTS.md, GEMINI.md, index*.md)
  - HOOK_SKIP includes "check_harness_routing" (handled by hooks_runner)
  - Edit/MultiEdit of an existing file that was already missing the
    marker (grandfather clause — legacy sources stay editable)

See: docs/protocols/universal-routing.md
     wiki/context/cost-routing.conf  (single source of truth)
"""
import sys
import json
import os
import re


_NON_ENTRY_NAMES = {"CLAUDE.md", "README.md", "AGENTS.md", "GEMINI.md"}
_ROUTED_VIA_RE = re.compile(r"^harness@v\d+$")


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


def _is_source_entry(file_path: str, repo_root: str) -> bool:
    if os.path.isabs(file_path):
        abs_path = os.path.realpath(file_path)
    else:
        abs_path = os.path.realpath(os.path.join(repo_root, file_path))

    sources_dir = os.path.realpath(os.path.join(repo_root, "wiki", "sources"))
    try:
        if os.path.commonpath([sources_dir, abs_path]) != sources_dir:
            return False
    except ValueError:
        return False

    name = os.path.basename(abs_path)
    if not name.endswith(".md"):
        return False
    if name in _NON_ENTRY_NAMES:
        return False
    if name.startswith("index"):
        return False
    return True


def _final_write_content(tool_name: str, tool_input: dict, file_path: str, repo_root: str) -> str | None:
    if tool_name == "Write":
        return tool_input.get("content", "")

    abs_path = file_path if os.path.isabs(file_path) else os.path.join(repo_root, file_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            current = f.read()
    except OSError:
        return None

    if tool_name == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        if not old:
            return current
        replace_all = tool_input.get("replace_all", False)
        return current.replace(old, new) if replace_all else current.replace(old, new, 1)

    if tool_name == "MultiEdit":
        out = current
        for edit in tool_input.get("edits", []):
            old = edit.get("old_string", "")
            new = edit.get("new_string", "")
            if not old:
                continue
            if edit.get("replace_all"):
                out = out.replace(old, new)
            else:
                out = out.replace(old, new, 1)
        return out

    return None


def _evaluate(present: bool, raw_value: str | None) -> str | None:
    """Return None if valid, else a reason string."""
    if not present:
        return "frontmatter has no `routed_via:` key"
    v = (raw_value or "").strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1].strip()
    if not _ROUTED_VIA_RE.match(v):
        return f"`routed_via:` must match `harness@v\\d+`, got {v!r}"
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

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    if not _is_source_entry(file_path, repo_root):
        sys.exit(0)

    content = _final_write_content(tool_name, tool_input, file_path, repo_root)
    if content is None:
        sys.exit(0)

    present, raw_value = _extract_frontmatter_value(content, "routed_via")

    # Grandfather: existing legacy sources without the marker stay editable.
    if tool_name in ("Edit", "MultiEdit"):
        abs_target = file_path if os.path.isabs(file_path) else os.path.join(repo_root, file_path)
        if os.path.isfile(abs_target):
            try:
                with open(abs_target, "r", encoding="utf-8") as f:
                    prior = f.read()
                prior_present, prior_value = _extract_frontmatter_value(prior, "routed_via")
                if _evaluate(prior_present, prior_value) is not None:
                    sys.exit(0)  # legacy non-compliant — grandfathered
            except OSError:
                pass

    reason = _evaluate(present, raw_value)
    if reason is None:
        sys.exit(0)

    slug = os.path.basename(file_path)
    _emit(
        "🚫 [check_harness_routing] Blocked "
        f"{tool_name} to wiki/sources/{slug}\n"
        f"   reason: {reason}\n"
        "   fix: route ingestion through the harness — one of:\n"
        "        • CLI:   python scripts/batch/route.py --file raw/<slug>.md\n"
        "        • MCP:   wiki_ingest_route({\"file\": \"raw/<slug>.md\"})\n"
        "        • shell: scripts/batch/route.sh --file raw/<slug>.md\n"
        "   why: cost-aware routing + quality_gate + tier discounts\n"
        "        (see docs/protocols/universal-routing.md)\n"
        "   override (emergency): HOOK_SKIP=check_harness_routing"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
