"""Tests for scripts/lib/graph_enrich.py — auto-enrich wiki graph from ledger.

Iron Law #1: failing tests written FIRST.

graph_enrich อ่าน memory_ledger entries และเพิ่ม edges เข้า .wiki-graph.json:
  - ถ้า ledger entry มี files: [...] → link แต่ละ file เป็น node + edge
  - ถ้า entry tag ตรงกับ wiki page → edge type='ledger-tag'
  - ทำให้ knowledge graph โตเองจากการทำงานของ agent

Schema (.wiki-graph.json):
  nodes: [{path, title, domain}]
  edges: [{from, to, type, broken, external}]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import memory_ledger as ml  # noqa: E402
import graph_enrich as ge  # noqa: E402 -- module under test (created here)


def _make_graph(tmp_path: Path) -> Path:
    """Create a minimal .wiki-graph.json for testing."""
    g = {
        "generated_at": "2026-01-01",
        "stats": {"nodes": 1, "edges": 0},
        "nodes": [{"path": "wiki/test.md", "title": "Test", "domain": "test"}],
        "edges": [],
    }
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(g), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. extract_file_references — pull file paths from ledger entries
# ---------------------------------------------------------------------------
def test_extract_file_references_returns_unique_files(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = ml.MemoryLedger(ledger_path)
    ledger.append(session_id="s", type="decision", summary="x",
                  files=["scripts/a.py", "scripts/b.py"])
    ledger.append(session_id="s", type="failure", summary="y",
                  files=["scripts/a.py", "scripts/c.py"])
    files = ge.extract_file_references(ledger_path)
    assert set(files) == {"scripts/a.py", "scripts/b.py", "scripts/c.py"}


def test_extract_file_references_empty_when_no_files(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="decision", summary="no files here")
    assert ge.extract_file_references(ledger_path) == []


def test_extract_file_references_empty_when_no_ledger(tmp_path):
    assert ge.extract_file_references(tmp_path / "missing.jsonl") == []


# ---------------------------------------------------------------------------
# 2. enrich_graph — adds file nodes + edges to graph
# ---------------------------------------------------------------------------
def test_enrich_graph_adds_nodes_for_new_files(tmp_path):
    graph_path = _make_graph(tmp_path)
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="decision", summary="x",
        files=["scripts/new.py"])
    added = ge.enrich_graph(graph_path, ledger_path)
    assert added["nodes_added"] >= 1
    g = json.loads(graph_path.read_text(encoding="utf-8"))
    paths = [n["path"] for n in g["nodes"]]
    assert "scripts/new.py" in paths


def test_enrich_graph_adds_edges(tmp_path):
    graph_path = _make_graph(tmp_path)
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="decision", summary="linked to test",
        files=["wiki/test.md", "scripts/new.py"])
    added = ge.enrich_graph(graph_path, ledger_path)
    assert added["edges_added"] >= 1
    g = json.loads(graph_path.read_text(encoding="utf-8"))
    assert any(e["type"] == "ledger-file" for e in g["edges"])


def test_enrich_graph_idempotent(tmp_path):
    """Running enrich twice should not duplicate nodes/edges."""
    graph_path = _make_graph(tmp_path)
    ledger_path = tmp_path / "ledger.jsonl"
    ml.MemoryLedger(ledger_path).append(
        session_id="s", type="decision", summary="x",
        files=["scripts/new.py"])
    first = ge.enrich_graph(graph_path, ledger_path)
    second = ge.enrich_graph(graph_path, ledger_path)
    assert first["nodes_added"] >= 1
    assert second["nodes_added"] == 0, "second run should not re-add nodes"
    assert second["edges_added"] == 0, "second run should not re-add edges"


def test_enrich_graph_no_op_when_ledger_empty(tmp_path):
    graph_path = _make_graph(tmp_path)
    ledger_path = tmp_path / "ledger.jsonl"  # missing
    added = ge.enrich_graph(graph_path, ledger_path)
    assert added["nodes_added"] == 0
    assert added["edges_added"] == 0
