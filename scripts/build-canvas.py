#!/usr/bin/env python3
"""
build-canvas.py — Translate .wiki-graph.json into an Obsidian Canvas file.

Groups nodes by domain, arranges them in neat grids inside group boxes,
and links them with direction-aware edges.
Outputs: brain-map.canvas at repo root.
"""

import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_JSON = REPO_ROOT / ".wiki-graph.json"
OUTPUT_CANVAS = REPO_ROOT / "brain-map.canvas"

# Color mappings (Obsidian colors: 1=red, 2=orange, 3=yellow, 4=green, 5=cyan, 6=purple)
COLOR_MAP = {
    "context": "1",    # Red
    "ai-tools": "2",   # Orange
    "ai": "2",         # Orange
    "iot": "3",        # Yellow
    "pharmacy": "4",   # Green
    "env": "5",        # Cyan
    "it": "5",         # Cyan
    "sources": "6",    # Purple
    "synthesis": "6",  # Purple
    "other": "none",
}

# Layout dimensions
NODE_W = 260
NODE_H = 120
SPACING_X = 340
SPACING_Y = 180

INNER_COLS = 3
DOMAIN_COLS = 3

DOMAIN_GAP_X = 400
DOMAIN_GAP_Y = 300

def get_node_id(path):
    # Normalize ID for canvas compatibility
    return path.replace("/", "-").replace(".", "-").replace(" ", "-")

def build_canvas():
    if not GRAPH_JSON.exists():
        print(f"Error: {GRAPH_JSON} not found. Run scripts/gen-index.py first.", file=sys.stderr)
        return False

    with open(GRAPH_JSON, "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes_data = graph.get("nodes", [])
    edges_data = graph.get("edges", [])

    # Group nodes by domain
    by_domain = {}
    for nd in nodes_data:
        dom = nd.get("domain", "other")
        if dom not in by_domain:
            by_domain[dom] = []
        by_domain[dom].append(nd)

    # Order domains for visual hierarchy
    ordered_domains = sorted(by_domain.keys(), key=lambda d: (d != "context", d != "synthesis", d))

    canvas_nodes = []
    node_positions = {}

    # Initial grid offsets
    domain_start_x = 0
    domain_start_y = 0
    row_max_h = 0
    dom_count = 0

    for dom in ordered_domains:
        dom_nodes = sorted(by_domain[dom], key=lambda n: n.get("title", ""))
        n_count = len(dom_nodes)
        if n_count == 0:
            continue

        # Calculate grid size inside this domain
        cols_present = min(n_count, INNER_COLS)
        rows_present = ((n_count - 1) // INNER_COLS) + 1

        grid_w = (cols_present - 1) * SPACING_X + NODE_W
        grid_h = (rows_present - 1) * SPACING_Y + NODE_H

        padding_x = 40
        padding_top = 80
        padding_bottom = 40

        dom_w = grid_w + 2 * padding_x
        dom_h = grid_h + padding_top + padding_bottom

        # Group ID
        group_id = f"group-domain-{dom}"
        
        # Add group box node
        canvas_nodes.append({
            "id": group_id,
            "type": "group",
            "label": f"{dom.upper()} DOMAIN ({n_count} pages)",
            "x": domain_start_x,
            "y": domain_start_y,
            "width": dom_w,
            "height": dom_h,
            "color": COLOR_MAP.get(dom, "none")
        })

        # Lay out nodes inside the group box
        for i, nd in enumerate(dom_nodes):
            nid = get_node_id(nd["path"])
            col = i % INNER_COLS
            row = i // INNER_COLS

            nx = domain_start_x + padding_x + (col * SPACING_X)
            ny = domain_start_y + padding_top + (row * SPACING_Y)

            canvas_nodes.append({
                "id": nid,
                "type": "file",
                "file": nd["path"],
                "x": nx,
                "y": ny,
                "width": NODE_W,
                "height": NODE_H,
                "color": COLOR_MAP.get(dom, "none")
            })

            node_positions[nid] = (nx, ny, nd.get("domain", "other"))

        # Keep track of max height in the current row of domains
        if dom_h > row_max_h:
            row_max_h = dom_h

        dom_count += 1
        # Advance layout pointer
        if dom_count % DOMAIN_COLS == 0:
            # Wrap to next row
            domain_start_x = 0
            domain_start_y += row_max_h + DOMAIN_GAP_Y
            row_max_h = 0
        else:
            domain_start_x += dom_w + DOMAIN_GAP_X

    # Render edges
    canvas_edges = []
    for edge in edges_data:
        if edge.get("broken", False):
            continue

        from_id = get_node_id(edge["from"])
        to_id = get_node_id(edge["to"])

        if from_id in node_positions and to_id in node_positions:
            fx, fy, fdom = node_positions[from_id]
            tx, ty, _ = node_positions[to_id]

            # Choose optimal sides to avoid overlapping self
            if tx > fx + NODE_W:
                from_side, to_side = "right", "left"
            elif tx < fx - NODE_W:
                from_side, to_side = "left", "right"
            elif ty > fy + NODE_H:
                from_side, to_side = "bottom", "top"
            else:
                from_side, to_side = "top", "bottom"

            canvas_edges.append({
                "id": f"edge-{from_id}-{to_id}",
                "fromNode": from_id,
                "fromSide": from_side,
                "toNode": to_id,
                "toSide": to_side,
                "color": COLOR_MAP.get(fdom, "none")
            })

    canvas_data = {
        "nodes": canvas_nodes,
        "edges": canvas_edges
    }

    # Write file
    with open(OUTPUT_CANVAS, "w", encoding="utf-8") as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Wrote Obsidian Canvas: {OUTPUT_CANVAS.relative_to(REPO_ROOT)} ({len(canvas_nodes)} nodes, {len(canvas_edges)} edges)")
    return True

if __name__ == "__main__":
    build_canvas()
