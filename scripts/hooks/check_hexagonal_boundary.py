#!/usr/bin/env python3
"""
Hook: Hexagonal Boundary Gate (PROTOTYPE — ADR-0012 revisit condition C6)
------------------------------------------------------------------------
PreToolUse gate that enforces the dependency-direction rule of hexagonal
architecture: ports and the application core must not import adapters,
frameworks, or concrete storage technologies.

Scope (intentionally NARROW — see ADR-0012 §ข้อยกเว้น):
  This prototype checks ONLY files that live in a `ports/` directory. It is
  convention-based, not whole-codebase static analysis. The bet is:

    IF a file lives in ports/ THEN it is declaring itself a port, and a port
    that imports an adapter / ORM / web framework / storage primitive is a
    dependency-direction violation by definition.

  Files outside ports/ are NOT checked — the codebase is mid-migration and
  most of it is still monolithic-mixed (ADR-0012 backlog Tier B). A blanket
  'does this look hexagonal?' check would have ~100% false-positive today.

Blocks (exit 2) when a ports/ file imports any of:
  - a sibling `adapters/` package  (adapter → port is forbidden)
  - sqlite3 / sqlalchemy / psycopg2 / redis / pymongo  (storage tech)
  - flask / fastapi / django / requests / httpx / urllib  (transport tech)
  - subprocess  (shelling out = implicit adapter)

Warns (stderr, exit 0) when:
  - the hook itself fails to parse the file (syntax error) — fail open so a
    broken edit doesn't wedge the repo

Passes through when:
  - tool is not Edit/Write/MultiEdit
  - file_path is empty or not under a ports/ directory
  - HOOK_SKIP=check_hexagonal_boundary

Feasibility verdict (C6): this convention-based approach has a LOW
false-positive rate because the scope is tiny (only declared ports). The
harder check — 'does an arbitrary file mix domain + I/O?' — is left out on
purpose; it would need a full type/AST analysis and would over-fire on the
legacy codebase. The ADR's revisit condition C6 (4-week prototype window)
is satisfied by this narrow-but-honest design.

See:
  - decisions/0012-adopt-hexagonal-architecture.md (R13 mitigation, C6)
  - wiki/concepts/ai-tools/hexagonal-architecture.md
  - skills: /hexagonal-architecture
"""
from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path


GATE_TOOLS = {"Write", "Edit", "MultiEdit"}

# Modules that a port must NEVER import — they all represent 'outside'.
# A-Council 2026-08-02 (security-auditor finding): expanded to cover the
# high-risk primitives a malicious/buggy port could pull in. Convention-
# based, not a security boundary (defence in depth) — but the blocklist
# must at least name the dangerous ones.
FORBIDDEN_IN_PORTS = {
    # adapter packages (relative — sibling of ports/)
    "adapters",
    # storage technologies
    "sqlite3", "sqlalchemy", "psycopg2", "redis", "pymongo", "shelve",
    # transport / framework
    "flask", "fastapi", "django", "requests", "httpx", "urllib", "aiohttp",
    "socket", "ssl",
    # process / system = implicit adapter or RCE surface
    "subprocess", "os", "shutil", "multiprocessing", "asyncio",
    # dynamic code execution / deserialization RCE
    "pickle", "marshal", "ctypes", "cffi", "importlib", "builtins",
    # temp-file helpers (ports must not touch disk directly)
    "tempfile",
}


def _emit(msg: str) -> None:
    sys.stderr.write(msg if msg.endswith("\n") else msg + "\n")


def _is_in_ports_dir(file_path: str) -> bool:
    """A file is a 'port' for this hook's purposes if any path component is
    exactly `ports`. This matches both scripts/lib/ports/foo.py and any
    future package that follows the same convention."""
    p = file_path.replace("\\", "/")
    parts = [seg for seg in p.split("/") if seg]
    return "ports" in parts


def _imported_names(source: str) -> set[str]:
    """Return the set of top-level module names imported by `source`.

    Handles `import X`, `import X.Y`, `from X import ...`, `from X.Y import ...`.
    Top-level name = first dotted segment. Raises SyntaxError if the source
    is not parseable — the caller treats that as fail-open."""
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:  # from . import X → module is None, skip
                names.add(node.module.split(".")[0])
    return names


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass

    if "check_hexagonal_boundary" in os.environ.get("HOOK_SKIP", ""):
        _emit("🛡️  Hexagonal boundary: BYPASSED (HOOK_SKIP)\n")
        return 0

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # fail open — malformed input is not a violation

    if data.get("tool_name", "") not in GATE_TOOLS:
        return 0

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    if not file_path or not _is_in_ports_dir(file_path):
        return 0  # out of scope — see hook docstring

    # We only inspect the NEW content being written. For Edit/MultiEdit the
    # full file isn't available in tool_input, so we read the on-disk file
    # post-hoc when possible; otherwise we inspect the `content`/`new_string`
    # field as a partial check. This keeps the check honest without requiring
    # a full re-parse of the whole repo.
    source = ""
    if "content" in tool_input:
        source = tool_input["content"]
    elif "new_string" in tool_input:
        source = tool_input["new_string"]
    else:
        # Try reading the current on-disk content (Edit on existing file).
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 0  # can't read, can't check — fail open

    try:
        imported = _imported_names(source)
    except (SyntaxError, RecursionError, MemoryError, ValueError) as e:
        # A-Council 2026-08-02 (security-auditor): broadened beyond SyntaxError
        # so a deliberately nested expression (parser DoS) or a malformed
        # unicode blob fails OPEN, not closed — never wedge a user's edit.
        _emit(f"⚠️  Hexagonal boundary: could not parse {file_path} ({type(e).__name__}: {e}); failing open\n")
        return 0

    violations = imported & FORBIDDEN_IN_PORTS
    if not violations:
        return 0

    _emit(
        "🛑 HEXAGONAL BOUNDARY VIOLATION — port imports 'outside'\n\n"
        f"  ไฟล์        : {file_path}\n"
        f"  import ต้องห้าม: {', '.join(sorted(violations))}\n\n"
        "กฎเหล็กของ hexagonal: port (ใน ports/) ต้องไม่ import adapter, ORM,\n"
        "framework, หรือ storage tech — dependency direction ชี้เข้าในเสมอ\n"
        "(adapter → port, ไม่ใช่ port → adapter).\n\n"
        "ทางออก:\n"
        "  1. ย้าย import ไปอยู่ใน adapter (scripts/lib/adapters/...)\n"
        "  2. ประกาศ interface แทน แล้วให้ adapter implement\n"
        "  3. ดู skill `/hexagonal-architecture` สำหรับ pattern\n\n"
        "Override (emergency): HOOK_SKIP=check_hexagonal_boundary\n"
        "ดู ADR-0012 §Decision + R13 mitigation\n"
    )
    return 2  # BLOCK


if __name__ == "__main__":
    raise SystemExit(main())
