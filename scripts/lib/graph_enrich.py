"""graph_enrich.py — auto-enrich .wiki-graph.json from Memory Ledger.

Tier 2 #6. Makes the knowledge graph grow itself from agent work:
  - Ledger entries with files: [...] → file nodes + edges
  - Files linked together in same entry → co-change edges
  - Idempotent — re-running doesn't duplicate

Result: knowledge graph (.wiki-graph.json) tracks what files agents actually
touch, not just wiki page links. Surfaces 'these files change together'
patterns for refactoring decisions.

API:
  extract_file_references(ledger_path) → list[str] (unique file paths)
  enrich_graph(graph_path, ledger_path) → {nodes_added, edges_added}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atomic_json  # noqa: E402
import memory_ledger  # noqa: E402


def extract_file_references(ledger_path: Path | str) -> list[str]:
    """Return unique file paths referenced across all ledger entries."""
    ledger = memory_ledger.MemoryLedger(ledger_path)
    entries = ledger._load_all()
    seen: set[str] = set()
    for e in entries:
        for f in e.get("files", []):
            if isinstance(f, str) and f:
                seen.add(f)
    return sorted(seen)


def enrich_graph(
    graph_path: Path | str,
    ledger_path: Path | str,
) -> dict[str, int]:
    """Add file nodes + edges from ledger to .wiki-graph.json.

    Idempotent: only adds nodes/edges that don't already exist.
    Returns {nodes_added, edges_added}.
    """
    graph_path = Path(graph_path)
    ledger_path = Path(ledger_path)
    if not ledger_path.is_file():
        return {"nodes_added": 0, "edges_added": 0}

    files = extract_file_references(ledger_path)
    if not files:
        return {"nodes_added": 0, "edges_added": 0}

    # Read current graph (or init empty)
    if graph_path.is_file():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    else:
        graph = {"generated_at": "", "stats": {}, "nodes": [], "edges": []}
    graph.setdefault("nodes", [])
    graph.setdefault("edges", [])

    existing_node_paths = {n["path"] for n in graph["nodes"] if "path" in n}
    existing_edge_keys = {
        (e.get("from"), e.get("to"), e.get("type"))
        for e in graph["edges"]
    }

    nodes_added = 0
    edges_added = 0

    # Add file nodes that don't exist yet
    for f in files:
        if f not in existing_node_paths:
            graph["nodes"].append({
                "path": f,
                "title": Path(f).name,
                "domain": "ledger-tracked",
            })
            existing_node_paths.add(f)
            nodes_added += 1

    # Add edges: link each file to a virtual 'ledger' anchor + co-change links
    # Anchor node represents "tracked by agent work"
    anchor = "ledger://agent-work"
    if anchor not in existing_node_paths:
        graph["nodes"].append({
            "path": anchor,
            "title": "Agent Work (ledger)",
            "domain": "ledger-tracked",
        })
        existing_node_paths.add(anchor)

    for f in files:
        edge_key = (anchor, f, "ledger-file")
        if edge_key not in existing_edge_keys:
            graph["edges"].append({
                "from": anchor,
                "to": f,
                "type": "ledger-file",
                "broken": False,
                "external": False,
            })
            existing_edge_keys.add(edge_key)
            edges_added += 1

    # Co-change edges: files mentioned in the SAME ledger entry change together
    ledger = memory_ledger.MemoryLedger(ledger_path)
    for e in ledger._load_all():
        entry_files = e.get("files", [])
        if len(entry_files) < 2:
            continue
        for i, f1 in enumerate(entry_files):
            for f2 in entry_files[i + 1:]:
                if f1 == f2:
                    continue
                edge_key = (f1, f2, "co-change")
                if edge_key not in existing_edge_keys:
                    graph["edges"].append({
                        "from": f1,
                        "to": f2,
                        "type": "co-change",
                        "broken": False,
                        "external": False,
                    })
                    existing_edge_keys.add(edge_key)
                    edges_added += 1

    # Update stats
    graph["stats"] = {
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
    }

    # Atomic write
    if nodes_added > 0 or edges_added > 0:
        atomic_json.atomic_write(graph_path, graph)

    return {"nodes_added": nodes_added, "edges_added": edges_added}
