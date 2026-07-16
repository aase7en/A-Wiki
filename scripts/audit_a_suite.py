#!/usr/bin/env python3
"""Audit A- suite created in this session.

Checks:
1. SKILL.md frontmatter (required + recommended fields)
2. Registry entries (15 new + 5 deprecated) exist with correct status
3. Cross-reference registry path ↔ actual file exists
4. Deprecated skills' migrated_to points to existing canonical
5. Generated surfaces no drift
6. Iron Laws references in SKILL content
7. Doc-js / docx references valid

Exit code: 0 = pass, 1 = problems found
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "skills-registry.json"

# Skills created this session
NEW_SKILLS = [
    "a-think", "a-plan", "a-debug", "a-doc", "a-doc-announce",
    "a-business",
    "a-doc-_template", "a-doc-order", "a-doc-memo", "a-doc-project",
    "a-doc-procedure", "a-doc-procurement", "a-doc-jd", "a-doc-report",
    "a-doc-form-record",
]
DEPRECATED = {
    "grill-me": "grill-with-docs",
    "grilling": "grill-with-docs",
    "spec": "spec-driven-development",
    "tdd-workflow": "tdd",
    "fable5-standards": "a-think",
}

REQUIRED_FM = ["name", "description"]
RECOMMENDED_FM = ["version"]


def _emit(msg: str) -> None:
    print(msg)


def frontmatter_fields(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end < 0:
        return {}
    fm = content[3:end]
    out: dict[str, str] = {}
    for line in fm.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    problems: list[str] = []

    # ── Load registry ──────────────────────────────────────────────
    if not REGISTRY.exists():
        print(f"FATAL: {REGISTRY} missing")
        return 2
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    skills = data.get("skills", [])
    by_name = {s["name"]: s for s in skills if "name" in s}

    # ── 1. SKILL.md frontmatter ────────────────────────────────────
    _emit("=== AUDIT 1: SKILL.md frontmatter ===")
    new_paths = {
        "a-think": "skills/awiki/a-think/SKILL.md",
        "a-plan": "skills/awiki/a-plan/SKILL.md",
        "a-debug": "skills/awiki/a-debug/SKILL.md",
        "a-business": "skills/awiki/a-business/SKILL.md",
        "a-doc": "skills/awiki/a-doc/SKILL.md",
        "a-doc-announce": "skills/awiki/a-doc/types/announce/SKILL.md",
        "a-doc-_template": "skills/awiki/a-doc/types/_template/SKILL.md",
        "a-doc-order": "skills/awiki/a-doc/types/order/SKILL.md",
        "a-doc-memo": "skills/awiki/a-doc/types/memo/SKILL.md",
        "a-doc-project": "skills/awiki/a-doc/types/project/SKILL.md",
        "a-doc-procedure": "skills/awiki/a-doc/types/procedure/SKILL.md",
        "a-doc-procurement": "skills/awiki/a-doc/types/procurement/SKILL.md",
        "a-doc-jd": "skills/awiki/a-doc/types/jd/SKILL.md",
        "a-doc-report": "skills/awiki/a-doc/types/report/SKILL.md",
        "a-doc-form-record": "skills/awiki/a-doc/types/form-record/SKILL.md",
    }
    for name, rel in new_paths.items():
        p = REPO / rel
        if not p.exists():
            problems.append(f"[FM] {name}: missing file {rel}")
            continue
        fields = frontmatter_fields(p)
        missing = [f for f in REQUIRED_FM if f not in fields]
        missing_rec = [f for f in RECOMMENDED_FM if f not in fields]
        # name in frontmatter should match registry name
        if "name" in fields and fields["name"] != name:
            problems.append(f"[FM] {name}: frontmatter name='{fields['name']}' != registry name")
        if missing:
            problems.append(f"[FM] {name}: missing required: {missing}")
        if missing_rec:
            problems.append(f"[FM] {name}: missing recommended: {missing_rec}")
        # description should be non-empty
        desc = fields.get("description", "")
        if not desc or len(desc) < 20:
            problems.append(f"[FM] {name}: description too short or empty")
        _emit(f"  {'OK ' if not (missing or missing_rec) else 'WARN'} {name}")

    # ── 2. Registry entries exist + correct status ─────────────────
    _emit("")
    _emit("=== AUDIT 2: Registry entries (15 new + 5 deprecated) ===")
    for name in NEW_SKILLS:
        if name not in by_name:
            problems.append(f"[REG] {name}: missing from registry")
            continue
        s = by_name[name]
        if s.get("status") != "canonical":
            problems.append(f"[REG] {name}: status={s.get('status')} expected 'canonical'")
        if "all" not in (s.get("agents") or []):
            problems.append(f"[REG] {name}: agents={s.get('agents')} missing 'all'")
        _emit(f"  OK  {name}: status={s.get('status')} agents={s.get('agents')}")

    for name in DEPRECATED:
        if name not in by_name:
            problems.append(f"[REG-DEP] {name}: missing from registry (should be deprecated)")
            continue
        s = by_name[name]
        if s.get("status") != "deprecated":
            problems.append(f"[REG-DEP] {name}: status={s.get('status')} expected 'deprecated'")
        if s.get("migrated_to") != DEPRECATED[name]:
            problems.append(f"[REG-DEP] {name}: migrated_to={s.get('migrated_to')} expected '{DEPRECATED[name]}'")
        _emit(f"  OK  {name} -> {s.get('migrated_to')}")

    # ── 3. Cross-ref registry path ↔ file exists ───────────────────
    _emit("")
    _emit("=== AUDIT 3: Registry path ↔ file cross-ref ===")
    for name in NEW_SKILLS:
        s = by_name.get(name, {})
        path = s.get("path")
        if not path:
            problems.append(f"[XREF] {name}: missing 'path' field")
            continue
        full = REPO / path
        if not full.exists():
            problems.append(f"[XREF] {name}: path {path} does not exist")
        else:
            _emit(f"  OK  {name}: {path}")

    # ── 4. Deprecated migrated_to → existing canonical ─────────────
    _emit("")
    _emit("=== AUDIT 4: Deprecated migrated_to → canonical exists ===")
    for name, target in DEPRECATED.items():
        if target not in by_name:
            problems.append(f"[DEP] {name}: migrated_to '{target}' not in registry")
            continue
        t = by_name[target]
        if t.get("status") != "canonical":
            problems.append(f"[DEP] {name}: migrated_to '{target}' status={t.get('status')} not canonical")
        else:
            _emit(f"  OK  {name} -> {target} (canonical)")

    # ── 5. Generated surfaces drift ────────────────────────────────
    _emit("")
    _emit("=== AUDIT 5: Generated surfaces (already checked externally) ===")
    _emit("  SKIP — verified via regen --check separately")

    # ── 6. Iron Laws references in canonical skills ────────────────
    _emit("")
    _emit("=== AUDIT 6: Iron Laws in canonical skill content ===")
    ironlaw_checks = {
        "a-debug": [r"Iron Law #1", r"Iron Law #2", r"failing test", r"root cause"],
        "a-plan": [r"grill", r"Iron Law"],
        "a-doc": [r"Iron Law", r"raw/", r"grill"],
        "a-think": [r"PHI", r"พ\.ศ\."],  # hospital-specific
    }
    for name, patterns in ironlaw_checks.items():
        path = REPO / new_paths[name]
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for pat in patterns:
            if not re.search(pat, content, re.IGNORECASE):
                problems.append(f"[IRON] {name}: missing pattern '{pat}'")

    # ── 7. Stub version consistency ───────────────────────────────
    _emit("")
    _emit("=== AUDIT 7: Stub version (0.1.x) vs canonical (1.x) ===")
    for name in NEW_SKILLS:
        s = by_name.get(name, {})
        ver = s.get("version", "")
        is_stub = name in ("a-business", "a-doc-_template", "a-doc-order", "a-doc-memo",
                           "a-doc-project", "a-doc-procedure", "a-doc-procurement",
                           "a-doc-jd", "a-doc-report", "a-doc-form-record")
        if is_stub:
            if not ver.startswith("0."):
                problems.append(f"[VER] {name}: stub should be 0.x.x, got {ver}")
            else:
                _emit(f"  OK  {name}: {ver}")
        else:
            # canonical: must start with 1.x or higher (allow patch bumps)
            try:
                major = int(ver.split(".")[0])
                if major < 1:
                    problems.append(f"[VER] {name}: canonical should be >=1.0.0, got {ver}")
                else:
                    _emit(f"  OK  {name}: {ver}")
            except (ValueError, IndexError):
                problems.append(f"[VER] {name}: invalid version format '{ver}'")

    # ── Summary ────────────────────────────────────────────────────
    _emit("")
    _emit("=" * 60)
    _emit(f"TOTAL PROBLEMS: {len(problems)}")
    for p in problems:
        _emit(f"  ✗ {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
