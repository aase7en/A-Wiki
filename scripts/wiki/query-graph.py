#!/usr/bin/env python3
"""
query-graph.py — Query the wiki knowledge graph built by build-wiki-graph.py.

Usage:
    python3 scripts/query-graph.py --neighbors wiki/entities/iot/mqtt-protocol.md
    python3 scripts/query-graph.py --orphans
    python3 scripts/query-graph.py --hubs
    python3 scripts/query-graph.py --broken
    python3 scripts/query-graph.py --path wiki/entities/iot/esp32.md wiki/entities/env/...
    python3 scripts/query-graph.py --cross-domain                # bridges between domains
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = REPO_ROOT / ".wiki-graph.json"
BUILDER = REPO_ROOT / "scripts" / "build-wiki-graph.py"


def load_graph() -> dict:
    if not GRAPH_PATH.exists():
        import subprocess
        subprocess.run([sys.executable, str(BUILDER)], check=True)
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def adjacency(graph: dict) -> tuple[dict, dict, dict]:
    """Return (out, in_, domain_of) maps."""
    out = defaultdict(set)
    in_ = defaultdict(set)
    valid_paths = {n["path"] for n in graph["nodes"]}
    domain = {n["path"]: n["domain"] for n in graph["nodes"]}
    for e in graph["edges"]:
        if e["broken"]:
            continue
        if e["to"] not in valid_paths:
            continue
        out[e["from"]].add(e["to"])
        in_[e["to"]].add(e["from"])
    return out, in_, domain


def neighbors(graph: dict, path: str) -> None:
    out, in_, _ = adjacency(graph)
    print(f"## {path}\n")
    print(f"### outgoing ({len(out[path])})")
    for t in sorted(out[path]):
        print(f"  → {t}")
    print(f"\n### incoming ({len(in_[path])})")
    for t in sorted(in_[path]):
        print(f"  ← {t}")


def orphans(graph: dict) -> None:
    for p in graph["stats"]["orphans_list"]:
        print(p)


def hubs(graph: dict) -> None:
    for h in graph["stats"]["hubs"]:
        print(f"{h['score']:3d}  {h['path']}")


def broken(graph: dict) -> None:
    for e in graph["edges"]:
        if e["broken"]:
            print(f"{e['from']}  →  {e['to']}  [{e['type']}]")


def shortest_path(graph: dict, src: str, dst: str) -> None:
    out, _, _ = adjacency(graph)
    if src not in {n["path"] for n in graph["nodes"]}:
        print(f"not in graph: {src}", file=sys.stderr)
        sys.exit(1)
    if dst not in {n["path"] for n in graph["nodes"]}:
        print(f"not in graph: {dst}", file=sys.stderr)
        sys.exit(1)
    # BFS over undirected (treat edges symmetrically for "is connected")
    out_undir = defaultdict(set)
    for k, vs in out.items():
        for v in vs:
            out_undir[k].add(v)
            out_undir[v].add(k)
    seen = {src: None}
    q = deque([src])
    while q:
        cur = q.popleft()
        if cur == dst:
            path = [cur]
            while seen[path[-1]]:
                path.append(seen[path[-1]])
            for p in reversed(path):
                print(p)
            return
        for nxt in out_undir[cur]:
            if nxt not in seen:
                seen[nxt] = cur
                q.append(nxt)
    print(f"(no path between {src} and {dst})")


def cross_domain(graph: dict) -> None:
    out, _, domain = adjacency(graph)
    bridges = []
    for src, targets in out.items():
        d1 = domain.get(src, "?")
        for t in targets:
            d2 = domain.get(t, "?")
            if d1 != d2 and d1 not in ("context", "?") and d2 not in ("context", "?"):
                bridges.append((d1, d2, src, t))
    for d1, d2, src, t in sorted(bridges):
        print(f"{d1:10s} → {d2:10s}  {src}  →  {t}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--neighbors", metavar="PATH")
    p.add_argument("--orphans", action="store_true")
    p.add_argument("--hubs", action="store_true")
    p.add_argument("--broken", action="store_true")
    p.add_argument("--path", nargs=2, metavar=("FROM", "TO"))
    p.add_argument("--cross-domain", action="store_true")
    p.add_argument("--stats", action="store_true")
    args = p.parse_args()

    g = load_graph()

    if args.stats:
        s = g["stats"]
        print(json.dumps({k: v for k, v in s.items() if k not in ("hubs", "orphans_list")}, indent=2))
        return 0
    if args.neighbors:
        neighbors(g, args.neighbors)
    elif args.orphans:
        orphans(g)
    elif args.hubs:
        hubs(g)
    elif args.broken:
        broken(g)
    elif args.path:
        shortest_path(g, args.path[0], args.path[1])
    elif args.cross_domain:
        cross_domain(g)
    else:
        p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
