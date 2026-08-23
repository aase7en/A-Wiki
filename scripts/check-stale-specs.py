#!/usr/bin/env python3
"""check-stale-specs.py — Slice D1: plans/ADRs own files via `scope:`.

A spec file (docs/plans/*.md, decisions/*.md) with frontmatter

    ---
    scope:
      - src/app.py
      - scripts/lib/x.py
    ---

OWNS those paths. If a scoped path's last commit is newer than the
spec's last commit, the spec is stale -> exit 1 (CI gate, community
spec-kit pattern). `plan-frozen: true` exempts (historical records).

Usage: python scripts/check-stale-specs.py [--root DIR]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_SPEC_GLOBS = ("docs/plans/*.md", "decisions/*.md")
FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=root, capture_output=True,
                         text=True, encoding="utf-8", errors="replace",
                         timeout=60)
    return out.stdout.strip() if out.returncode == 0 else ""


def _last_commit_ts(root: Path, path: Path) -> int:
    rel = path.relative_to(root).as_posix()
    ts = _git(root, "log", "-1", "--format=%ct", "--", rel)
    try:
        return int(ts)
    except ValueError:
        return 0  # never committed -> ignore (untracked scratch)


def _parse_spec(text: str) -> tuple[dict, list[str]]:
    m = FM_RE.match(text)
    if not m:
        return {}, []
    frozen = False
    scope: list[str] = []
    in_scope = False
    for line in m.group(1).splitlines():
        if re.match(r"^scope:\s*$", line):
            in_scope = True; continue
        if in_scope:
            mm = re.match(r"^\s+-\s*(\S+)\s*$", line)
            if mm:
                scope.append(mm.group(1)); continue
            if line and not line.startswith((" ", "\t", "-")):
                in_scope = False
        if re.match(r"^plan-frozen:\s*true\s*$", line.strip()):
            frozen = True
    return ({"frozen": frozen}, scope)


def check_repo(root: Path) -> list[str]:
    problems: list[str] = []
    for pattern in _SPEC_GLOBS:
        for spec in (root / ".").glob(pattern) if pattern.startswith("docs") \
                else (root / ".").glob(pattern):
            if not spec.is_file():
                continue
            meta, scope = _parse_spec(spec.read_text(encoding="utf-8"))
            if not scope or meta.get("frozen"):
                continue
            spec_ts = _last_commit_ts(root, spec)
            for rel in scope:
                target = root / rel
                if not target.exists():
                    continue
                if _last_commit_ts(root, target) > spec_ts:
                    problems.append(
                        f"{spec.relative_to(root).as_posix()} is stale: "
                        f"scoped file {rel} has newer commits than the spec "
                        f"(update the spec, or mark plan-frozen: true)")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    problems = check_repo(Path(args.root).resolve())
    for p in problems:
        print(f"❌ {p}")
    if problems:
        return 1
    print("✅ no stale specs (scoped files are covered by their plans)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
