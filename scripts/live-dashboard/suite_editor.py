"""Suite Editor — eval suite generator (X3).

สร้าง/แก้/load eval suite จาก dashboard form. Validate + atomic write.
ใช้โดย server.py POST/GET routes สำหรับ /api/eval/suite*.

Security:
  - filename: kebab-case only (^[a-z0-9-]+$) — กัน path traversal
  - reject 'stages' key — กันทับ pipeline (DAG) suites
  - atomic write (temp + rename)

Pure functions (no I/O except write_suite/load_suite_by_name/list_subagents).
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SUITES_DIR = REPO_ROOT / "evals" / "subagents"
AGENTS_DIR = REPO_ROOT / "agents" / "subagents"

# Filename: kebab-case lowercase only (no path separators, no traversal).
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")


def validate_suite_name(name: str) -> bool:
    """True ถ้า name เป็น kebab-case ที่ปลอดภัย (no path traversal, no spaces)."""
    if not name or not isinstance(name, str):
        return False
    return bool(_NAME_RE.match(name.strip()))


def parse_comma_list(text: str) -> list[str]:
    """'a, b, c' → ['a', 'b', 'c'] (trim whitespace, drop empty)."""
    if not text:
        return []
    return [s.strip() for s in text.split(",") if s.strip()]


def validate_case(case: dict) -> list[str]:
    """Validate one case. Returns list of error strings (empty = valid)."""
    errors = []
    if not case.get("id"):
        errors.append("case missing 'id'")
    if not case.get("subagent"):
        errors.append(f"case '{case.get('id', '?')}' missing 'subagent'")
    if not case.get("prompt"):
        errors.append(f"case '{case.get('id', '?')}' missing 'prompt'")
    return errors


def validate_suite(suite: dict) -> list[str]:
    """Validate a full suite. Returns list of error strings (empty = valid).

    Rejects 'stages' key (pipeline/DAG suites — กันทับ).
    """
    errors = []
    name = suite.get("suite", "")
    if not validate_suite_name(name):
        errors.append(f"invalid suite name '{name}' (must be kebab-case, e.g. 'medical')")
    if "stages" in suite:
        errors.append("suite has 'stages' key — this is a pipeline (DAG) suite; editor supports single-agent suites only")
    cases = suite.get("cases", [])
    if not isinstance(cases, list):
        errors.append("'cases' must be a list")
        return errors
    if not cases:
        errors.append("suite has no cases (need at least 1)")
    seen_ids = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("case must be a dict")
            continue
        cid = case.get("id", "")
        if cid in seen_ids:
            errors.append(f"duplicate case id: '{cid}'")
        seen_ids.add(cid)
        errors.extend(validate_case(case))
    return errors


def write_suite(suite: dict, suites_dir: Path | str = SUITES_DIR) -> Path:
    """Validate + atomic write suite to <suites_dir>/<suite>.json.

    Raises ValueError ถ้า validation fails.
    Returns the written file path.
    """
    errors = validate_suite(suite)
    if errors:
        raise ValueError("; ".join(errors))
    name = suite["suite"]
    sdir = Path(suites_dir)
    sdir.mkdir(parents=True, exist_ok=True)
    target = sdir / f"{name}.json"
    # Atomic write: temp file in same dir, then rename.
    payload = json.dumps(suite, indent=2, ensure_ascii=False)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(target)
    return target


def load_suite_by_name(name: str, suites_dir: Path | str = SUITES_DIR) -> dict | None:
    """Load a suite by name. Returns None if not found."""
    if not validate_suite_name(name):
        return None
    path = Path(suites_dir) / f"{name}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_subagents(agents_dir: Path | str = AGENTS_DIR) -> list[str]:
    """List subagent names (filenames without .md, excluding README)."""
    adir = Path(agents_dir)
    if not adir.is_dir():
        return []
    return sorted(
        p.stem for p in adir.glob("*.md")
        if p.stem.lower() != "readme"
    )


def list_suites(suites_dir: Path | str = SUITES_DIR) -> list[str]:
    """List existing suite names (single-agent only, exclude pipeline)."""
    sdir = Path(suites_dir)
    if not sdir.is_dir():
        return []
    out = []
    for p in sorted(sdir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "cases" in data and "stages" not in data:
                out.append(p.stem)
        except Exception:
            continue
    return out


__all__ = [
    "validate_suite_name",
    "parse_comma_list",
    "validate_case",
    "validate_suite",
    "write_suite",
    "load_suite_by_name",
    "list_subagents",
    "list_suites",
]
