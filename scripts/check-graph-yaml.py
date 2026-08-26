#!/usr/bin/env python3
"""check-graph-yaml.py — the document graph is self-verifying.

Every node must point at a real file and declare read_when triggers.
Exit 1 listing drift. (Document layer only — a-flow owns runtime state.)
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GRAPH = REPO_ROOT / "docs" / "graph" / "PROJECT-GRAPH.yaml"


def load_graph(path: Path) -> dict:
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
    import yaml  # noqa: PyYAML (declared dependency)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_graph(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        data = load_graph(path)
    except Exception as e:
        return [f"graph unparseable: {e}"]
    for name, node in (data.get("nodes") or {}).items():
        f = node.get("file")
        if not f:
            problems.append(f"node {name}: missing 'file'")
            continue
        if not (REPO_ROOT / f).is_file():
            problems.append(f"node {name}: file does not exist: {f}")
        if not node.get("read_when") and not node.get("always_read"):
            problems.append(f"node {name}: needs read_when or always_read")
        if not node.get("purpose"):
            problems.append(f"node {name}: missing purpose")
    return problems


def main() -> int:
    problems = check_graph(GRAPH)
    for p in problems:
        print(f"❌ {p}")
    if not problems:
        print("✅ document graph nodes all resolve")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
