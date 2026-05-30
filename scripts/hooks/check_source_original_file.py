#!/usr/bin/env python3
"""
Hook: Source-Page Provenance Gate
---------------------------------
Block Write/Edit/MultiEdit on `wiki/sources/<slug>.md` if the page lacks a
working `original_file:` pointing to an existing file under `raw/`.

This enforces the documented ingest flow:
    WebFetch / paste → save to raw/<slug>.md FIRST
                   → then create wiki/sources/<slug>.md with
                     original_file: raw/<slug>.md

Strict mode (block) — fails if ANY of:
  1. frontmatter has no `original_file:` key
  2. value is null / empty / literal "null"
  3. value does not start with `raw/`
  4. value resolves to a path that does not exist on disk (symlinks
     through drive/raw → GDrive are honored via os.path.realpath)

Skip / pass-through when:
  - tool_name not in (Edit, Write, MultiEdit)
  - file_path not under wiki/sources/ OR matches a non-entry filename
    (CLAUDE.md, README.md, index*.md)
  - HOOK_SKIP includes "check_source_original_file" (handled by hooks_runner)

See: wiki/sources/CLAUDE.md (rule: "frontmatter บังคับ ... original_file"),
     wiki/CLAUDE.md template, decisions/0006-source-ingestion-synthesis-rag.md
Memory: ingest-flow-raw-first.md
Plan:   .claude/plans/ingest-lazy-treehouse.md (2026-05-30)
"""
import sys
import json
import os
import re

# Filenames inside wiki/sources/ that are NOT source-entry pages.
_NON_ENTRY_NAMES = {"CLAUDE.md", "README.md", "AGENTS.md", "GEMINI.md"}


def _emit(msg: str) -> None:
    sys.stderr.write(msg if msg.endswith("\n") else msg + "\n")


def _extract_frontmatter_value(content: str, key: str) -> tuple[bool, str | None]:
    """Return (key_present, raw_value_string_or_None).

    Parses a minimal YAML-ish frontmatter block (first --- ... ---).
    raw_value is the trimmed string after the colon, or None if absent.
    """
    if not content.startswith("---"):
        return False, None
    # Find closing ---
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
    """True iff file_path is wiki/sources/<something>.md and not a meta file."""
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
    """Reconstruct the content the tool is about to commit.

    - Write: tool_input['content'] is the full new file.
    - Edit:  apply old_string→new_string to current file (if file exists).
    - MultiEdit: apply edits[] in order.

    Returns None when we can't determine final content (treat as pass to avoid
    false positives — Write is the high-value case, that one we always catch).
    """
    if tool_name == "Write":
        return tool_input.get("content", "")

    abs_path = file_path if os.path.isabs(file_path) else os.path.join(repo_root, file_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            current = f.read()
    except OSError:
        # Editing a file that doesn't exist yet is an Edit-as-create — can't reconstruct.
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
        # Could not reconstruct final content — be lenient (avoid false positives).
        sys.exit(0)

    present, raw_value = _extract_frontmatter_value(content, "original_file")

    def _evaluate(present: bool, raw_value: str | None) -> str | None:
        """Return None if valid, else a reason string."""
        if not present:
            return "frontmatter has no `original_file:` key"
        v = (raw_value or "").strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1].strip()
        if v == "" or v.lower() in ("null", "~"):
            return "`original_file:` is null/empty"
        if v.startswith("./"):
            v = v[2:]
        if not v.startswith("raw/"):
            return f"`original_file:` must start with raw/ (got: {v!r})"
        abs_p = os.path.realpath(os.path.join(repo_root, v))
        if not os.path.isfile(abs_p):
            return f"`original_file:` points to a missing file: {v} (resolved: {abs_p})"
        return None

    # Grandfather clause: for Edit/MultiEdit on an existing file, only block if
    # the edit DEGRADES a previously-valid state. Legacy sources that were
    # already broken stay editable for typo fixes etc. — they just can't be
    # made worse, and new Writes must always be clean.
    if tool_name in ("Edit", "MultiEdit"):
        abs_target = file_path if os.path.isabs(file_path) else os.path.join(repo_root, file_path)
        if os.path.isfile(abs_target):
            try:
                with open(abs_target, "r", encoding="utf-8") as f:
                    prior = f.read()
                prior_present, prior_value = _extract_frontmatter_value(prior, "original_file")
                if _evaluate(prior_present, prior_value) is not None:
                    # Pre-existing file was already non-compliant — grandfathered.
                    sys.exit(0)
            except OSError:
                pass

    def _block(reason: str) -> None:
        slug = os.path.basename(file_path)
        # Fresh-clone hint: if raw/ symlink itself is broken, the real fix
        # is to run setup-cloud-link.sh — not to "save raw first".
        raw_link = os.path.join(repo_root, "raw")
        link_hint = ""
        if os.path.islink(raw_link) and not os.path.exists(raw_link):
            link_hint = (
                "\n   ⚠️  raw/ symlink is BROKEN (target not reachable).\n"
                "      → run: bash scripts/setup-cloud-link.sh\n"
                "      (then re-try the ingest)\n"
            )
        elif not os.path.exists(raw_link):
            link_hint = (
                "\n   ⚠️  raw/ does not exist on this machine.\n"
                "      → run: bash scripts/setup-cloud-link.sh   (one-time per device)\n"
            )
        _emit(
            "🚫 [check_source_original_file] Blocked "
            f"{tool_name} to wiki/sources/{slug}\n"
            f"   reason: {reason}\n"
            "   fix: 1) save raw fetched content to raw/<slug>.md first\n"
            "        2) set frontmatter: original_file: raw/<slug>.md\n"
            "   why: provenance is mandatory per wiki/sources/CLAUDE.md"
            f"{link_hint}\n"
            "   override (emergency): HOOK_SKIP=check_source_original_file"
        )
        sys.exit(2)

    reason = _evaluate(present, raw_value)
    if reason is not None:
        _block(reason)

    sys.exit(0)


if __name__ == "__main__":
    main()
