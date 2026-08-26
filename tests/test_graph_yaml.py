"""PROJECT-GRAPH.yaml — G5c: machine-readable DOCUMENT routing graph.

Distinct layer from a-flow (runtime state machine): this graph only says
which workflow FILE to read for a given state — context economy for any
agent. The checker makes it self-verifying (no dead nodes)."""
from __future__ import annotations

import importlib.util as ilu
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GRAPH = REPO_ROOT / "docs" / "graph" / "PROJECT-GRAPH.yaml"
_spec = ilu.spec_from_file_location("cgy", REPO_ROOT / "scripts" / "check-graph-yaml.py")
cgy = ilu.module_from_spec(_spec)
_spec.loader.exec_module(cgy)


def test_graph_exists_and_parses():
    data = cgy.load_graph(GRAPH)
    assert data["version"] == 1
    nodes = data["nodes"]
    for must in ("entry", "ssot", "defect_memory", "loop_contract"):
        assert must in nodes, f"node missing: {must}"


def test_every_node_points_to_real_file_with_read_when():
    problems = cgy.check_graph(GRAPH)
    assert problems == [], problems


def test_graph_does_not_own_runtime_routing():
    """Layer separation: this graph routes DOCUMENTS; a-flow owns runtime
    execution state — the file must say so and must not reference
    a-flow internals."""
    text = GRAPH.read_text(encoding="utf-8")
    assert "a-flow" in text.lower(), "must declare the layer separation"
    assert "a_flow_state" not in text and "check_a_flow" not in text


def test_cli_exit_zero_when_clean():
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check-graph-yaml.py")],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=REPO_ROOT, timeout=120)
    assert res.returncode == 0, res.stdout + res.stderr
