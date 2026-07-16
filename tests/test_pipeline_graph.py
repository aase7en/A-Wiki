"""Tests for scripts/live-dashboard/pipeline_graph.py — DAG visualizer data (T5).

Iron Law #1: failing tests written FIRST.

T5 แปลง pipeline suite stages → vis-network format (nodes + edges)
เพื่อ render เป็นกราฟใน dashboard. รองรับทั้ง linear (pipeline-finance)
และ DAG (pipeline-council) suites.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

import pipeline_graph  # noqa: E402  -- module under test (created by T5)


# ---------------------------------------------------------------------------
# 1. Linear chain (pipeline-finance style: 3 sequential stages)
# ---------------------------------------------------------------------------
def test_suite_to_vis_data_linear_chain():
    """Linear suite (no type/depends_on) → 3 nodes, 2 edges (chain)."""
    suite = {
        "suite": "test-linear",
        "stages": [
            {"id": "s1", "subagent": "a", "prompt": "Step 1"},
            {"id": "s2", "subagent": "b", "prompt": "Step 2: {prev_output}"},
            {"id": "s3", "subagent": "c", "prompt": "Step 3: {prev_output}"},
        ],
    }
    vis = pipeline_graph.suite_to_vis_data(suite)
    assert len(vis["nodes"]) == 3
    # Linear chain: s1→s2, s2→s3 = 2 edges
    assert len(vis["edges"]) == 2
    node_ids = [n["id"] for n in vis["nodes"]]
    assert "s1" in node_ids and "s2" in node_ids and "s3" in node_ids


# ---------------------------------------------------------------------------
# 2. DAG parallel branches (pipeline-council: question→[2 critics]→synthesis)
# ---------------------------------------------------------------------------
def test_suite_to_vis_data_dag_parallel_branches():
    """DAG suite → nodes + edges reflecting depends_on (fan-out + fan-in)."""
    suite = {
        "suite": "test-dag",
        "stages": [
            {"id": "q", "subagent": "x", "prompt": "Q", "type": "sequential"},
            {"id": "c1", "subagent": "a", "prompt": "C1: {q.output}", "type": "parallel", "depends_on": "q"},
            {"id": "c2", "subagent": "b", "prompt": "C2: {q.output}", "type": "parallel", "depends_on": "q"},
            {"id": "syn", "subagent": "x", "prompt": "Merge", "type": "merge", "depends_on": ["c1", "c2"]},
        ],
    }
    vis = pipeline_graph.suite_to_vis_data(suite)
    assert len(vis["nodes"]) == 4
    # Edges: q→c1, q→c2, c1→syn, c2→syn = 4 edges
    assert len(vis["edges"]) == 4
    # Verify fan-in: syn has 2 incoming edges
    incoming_to_syn = [e for e in vis["edges"] if e["to"] == "syn"]
    assert len(incoming_to_syn) == 2


# ---------------------------------------------------------------------------
# 3. Nodes have correct group (for color coding)
# ---------------------------------------------------------------------------
def test_nodes_have_correct_group():
    """Each node's 'group' field reflects its stage type (sequential/parallel/merge)."""
    suite = {
        "suite": "test-groups",
        "stages": [
            {"id": "s", "prompt": "x", "type": "sequential"},
            {"id": "p", "prompt": "y", "type": "parallel", "depends_on": "s"},
            {"id": "m", "prompt": "z", "type": "merge", "depends_on": ["s", "p"]},
        ],
    }
    vis = pipeline_graph.suite_to_vis_data(suite)
    groups = {n["id"]: n.get("group") for n in vis["nodes"]}
    assert groups["s"] == "sequential"
    assert groups["p"] == "parallel"
    assert groups["m"] == "merge"


def test_linear_nodes_default_to_sequential():
    """Linear suite (no type field) → all nodes group='sequential'."""
    suite = {
        "suite": "linear",
        "stages": [
            {"id": "a", "prompt": "1"},
            {"id": "b", "prompt": "2"},
        ],
    }
    vis = pipeline_graph.suite_to_vis_data(suite)
    for n in vis["nodes"]:
        assert n["group"] == "sequential"


# ---------------------------------------------------------------------------
# 4. Edges reflect depends_on
# ---------------------------------------------------------------------------
def test_edges_reflect_depends_on():
    """Each depends_on entry → one edge (from dep to stage)."""
    suite = {
        "suite": "test-edges",
        "stages": [
            {"id": "root", "prompt": "r"},
            {"id": "child", "prompt": "c", "depends_on": "root"},
            {"id": "multi", "prompt": "m", "depends_on": ["root", "child"]},
        ],
    }
    vis = pipeline_graph.suite_to_vis_data(suite)
    edge_pairs = {(e["from"], e["to"]) for e in vis["edges"]}
    assert ("root", "child") in edge_pairs
    assert ("root", "multi") in edge_pairs
    assert ("child", "multi") in edge_pairs


# ---------------------------------------------------------------------------
# 5. Non-pipeline suite (single-agent, no stages) → empty
# ---------------------------------------------------------------------------
def test_non_pipeline_suite_returns_empty():
    """Suite without 'stages' key → empty vis data (not a pipeline)."""
    suite = {
        "suite": "medical",
        "cases": [{"id": "c1", "prompt": "...", "required": ["x"]}],
    }
    vis = pipeline_graph.suite_to_vis_data(suite)
    assert vis["nodes"] == []
    assert vis["edges"] == []


# ---------------------------------------------------------------------------
# 6. Node label + title (prompt preview) present
# ---------------------------------------------------------------------------
def test_nodes_have_label_and_title():
    """Nodes have 'label' (=id) + 'title' (=prompt preview for tooltip)."""
    suite = {
        "suite": "test-label",
        "stages": [
            {"id": "step1", "subagent": "agent", "prompt": "Do something important here"},
        ],
    }
    vis = pipeline_graph.suite_to_vis_data(suite)
    node = vis["nodes"][0]
    assert node["label"] == "step1"
    assert "title" in node
    assert "Do something" in node["title"]  # prompt preview
