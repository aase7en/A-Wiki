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
    python3 scripts/query-graph.py --typed-out depends           # outgoing edges of type
    python3 scripts/query-graph.py --typed-in implements wiki/entities/...  # incoming edges of type
    python3 scripts/query-graph.py --typed-hubs --type depends   # hubs weighted by type
    python3 scripts/query-graph.py --type-summary               # edge type distribution
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import defaultdict, deque, Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = REPO_ROOT / ".wiki-graph.json"
BUILDER = REPO_ROOT / "scripts" / "build-wiki-graph.py"

VALID_TYPES = ("wikilink", "mdlink", "depends", "extends", "implements")


def load_graph() -> dict:
    if not GRAPH_PATH.exists():
        import subprocess
        subprocess.run([sys.executable, str(BUILDER)], check=True)
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def adjacency(graph: dict) -> tuple[dict, dict, dict]:
    """Return (out, in_, domain_of) maps. out is {path -> {target_path}}."""
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


def typed_adjacency(graph: dict, etype: str) -> tuple[dict, dict, dict]:
    """
    Return (typed_out, typed_in, domain_of) maps.
    Only includes edges with matching type.
    """
    typed_out = defaultdict(set)
    typed_in = defaultdict(set)
    valid_paths = {n["path"] for n in graph["nodes"]}
    domain = {n["path"]: n["domain"] for n in graph["nodes"]}
    for e in graph["edges"]:
        if e["broken"]:
            continue
        if e["type"] != etype:
            continue
        if e["to"] not in valid_paths:
            continue
        typed_out[e["from"]].add(e["to"])
        typed_in[e["to"]].add(e["from"])
    return typed_out, typed_in, domain


def neighbors(graph: dict, path: str) -> None:
    out, in_, _ = adjacency(graph)
    print(f"## {path}\n")
    print(f"### outgoing ({len(out[path])})")
    for t in sorted(out[path]):
        print(f"  → {t}")
    print(f"\n### incoming ({len(in_[path])})")
    for t in sorted(in_[path]):
        print(f"  ← {t}")


def typed_neighbors(graph: dict, path: str, etype: str, direction: str = "out") -> None:
    """Show neighbors filtered by edge type."""
    if direction not in ("out", "in", "both"):
        direction = "both"
    typed_out, typed_in, _ = typed_adjacency(graph, etype)

    if direction in ("out", "both"):
        print(f"### {etype} → outgoing ({len(typed_out[path])})")
        for t in sorted(typed_out[path]):
            print(f"  → {t}")
    if direction in ("in", "both"):
        print(f"\n### {etype} → incoming ({len(typed_in[path])})")
        for t in sorted(typed_in[path]):
            print(f"  ← {t}")


def orphans(graph: dict) -> None:
    for p in graph["stats"]["orphans_list"]:
        print(p)


def hubs(graph: dict) -> None:
    for h in graph["stats"]["hubs"]:
        print(f"{h['score']:3d}  {h['path']}")


def typed_hubs(graph: dict, etype: str, top: int = 10) -> None:
    """Compute hubs weighted by a specific edge type."""
    typed_out, typed_in, _ = typed_adjacency(graph, etype)
    all_paths = {n["path"] for n in graph["nodes"]}
    scores: Counter[str] = Counter()
    for p in all_paths:
        scores[p] = len(typed_out.get(p, set())) + len(typed_in.get(p, set()))
    for p, s in scores.most_common(top):
        if s > 0:
            print(f"{s:3d} [{etype:10s}]  {p}")


def type_summary(graph: dict) -> None:
    ebt = graph["stats"].get("edges_by_type", {})
    total = sum(ebt.values()) or 1
    print("Edge type distribution:\n")
    for etype in sorted(VALID_TYPES):
        count = ebt.get(etype, 0)
        pct = count / total * 100
        bar = "#" * int(pct / 2)
        print(f"  {etype:10s}  {count:5d}  ({pct:5.1f}%)  {bar}")
    print(f"\n  {'Total':10s}  {sum(ebt.values()):5d}")


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
    p.add_argument("--type-summary", action="store_true",
                   help="Show edge type distribution")
    p.add_argument("--typed-out", metavar="TYPE",
                   help="Show outgoing edges of specific type (requires --neighbors)")
    p.add_argument("--typed-in", metavar="TYPE",
                   help="Show incoming edges of specific type (requires --neighbors)")
    p.add_argument("--typed-hubs", action="store_true",
                   help="Hubs weighted by a specific edge type (use with --type)")
    p.add_argument("--type", metavar="TYPE", choices=VALID_TYPES,
                   help="Edge type filter for --typed-* queries")
    p.add_argument("--semantic", metavar="QUERY",
                   help="Hybrid FTS5+semantic search via query-rag.py")
    p.add_argument("--fts5-only", action="store_true",
                   help="Pure FTS5 search via query-rag.py")
    p.add_argument("--provider", choices=("local", "openrouter"),
                   help="Embedding provider for --semantic")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    # Delegate semantic/FTS5 search to query-rag.py
    if args.semantic or args.fts5_only:
        import subprocess
        rag = REPO_ROOT / "scripts" / "wiki" / "query-rag.py"
        if not rag.exists():
            print(f"query-rag.py not found at {rag}", file=sys.stderr)
            return 1
        cmd = [sys.executable, str(rag), args.semantic or args.fts5_only]
        if args.fts5_only:
            cmd.append("--fts5-only")
        else:
            cmd.append("--semantic")
        if args.provider:
            cmd.extend(["--provider", args.provider])
        cmd.extend(["--limit", str(args.limit)])
        if args.json:
            cmd.append("--json")
        return subprocess.call(cmd)

    g = load_graph()

    if args.stats:
        s = g["stats"]
        print(json.dumps({k: v for k, v in s.items() if k not in ("hubs", "orphans_list")}, indent=2))
        return 0

    if args.type_summary:
        type_summary(g)
        return 0

    if args.typed_hubs:
        etype = args.type or "wikilink"
        typed_hubs(g, etype)
        return 0

    if args.neighbors:
        # Support typed neighbor queries
        if args.typed_out or args.typed_in:
            etype = args.typed_out or args.typed_in
            direction = "out" if args.typed_out else "in"
            if args.typed_out and args.typed_in:
                direction = "both"
            typed_neighbors(g, args.neighbors, etype, direction)
        else:
            neighbors(g, args.neighbors)
        return 0
    if args.orphans:
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