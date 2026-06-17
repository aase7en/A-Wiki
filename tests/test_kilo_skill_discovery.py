"""
Tests for Kilo skill discovery wiring + de-dup correctness (non-destructive).

Ensures the project exposes its A-Wiki skills to Kilo via kilo.jsonc skills.paths,
that no .kilo/agents/*.md reference the non-existent .kilocode path, and that the
ECC link-script whitelist only names directories that actually exist.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KILO_JSONC = REPO_ROOT / ".kilo" / "kilo.jsonc"
AGENTS_DIR = REPO_ROOT / ".kilo" / "agents"
LINK_SCRIPT = REPO_ROOT / "scripts" / "ecosystem" / "link-my-skills.sh"


def _strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments outside of string literals."""
    out = []
    i, n = 0, len(text)
    in_str = esc = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
        elif c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _load_jsonc(path: Path) -> dict:
    """Strip JSONC comments + trailing commas (before } or ]), then json.loads."""
    text = _strip_jsonc_comments(path.read_text(encoding="utf-8"))
    text = re.sub(r",(\s*[}\]])", r"\1", text)  # strip trailing commas before closers
    return json.loads(text)


def test_kilo_jsonc_parses_and_declares_skill_paths():
    cfg = _load_jsonc(KILO_JSONC)
    paths = cfg.get("skills", {}).get("paths")
    assert isinstance(paths, list) and paths, "kilo.jsonc must declare skills.paths"


def test_declared_skill_paths_exist():
    cfg = _load_jsonc(KILO_JSONC)
    for p in cfg.get("skills", {}).get("paths", []):
        rel = p.lstrip("./")
        target = REPO_ROOT / rel
        assert target.is_dir(), f"skills.paths entry does not exist: {p} -> {target}"


def test_no_kilocode_references_in_kilo_agents():
    assert AGENTS_DIR.is_dir()
    offenders = []
    for f in AGENTS_DIR.glob("*.md"):
        if ".kilocode" in f.read_text(encoding="utf-8"):
            offenders.append(f.name)
    assert not offenders, f"agents still reference stale .kilocode: {offenders}"


def test_link_my_skills_whitelist_exists():
    """Every name in the ECC_INCLUDE array must map to an existing skills/ecosystem dir."""
    if not LINK_SCRIPT.is_file():
        return
    text = LINK_SCRIPT.read_text(encoding="utf-8")
    m = re.search(r"ECC_INCLUDE=\(\s*(.*?)\)", text, re.S)
    assert m, "link-my-skills.sh must define an ECC_INCLUDE array"
    names = re.findall(r'"([a-z0-9-]+)"', m.group(1))
    assert names, "ECC_INCLUDE is empty"
    eco = REPO_ROOT / "skills" / "ecosystem"
    missing = [n for n in names if not (eco / n).is_dir()]
    assert not missing, f"link-my-skills whitelist names missing from ecosystem/: {missing}"
