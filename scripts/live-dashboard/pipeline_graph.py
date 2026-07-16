"""Pipeline Graph — DAG visualizer data for vis-network (T5).

แปลง pipeline suite stages → vis-network format (nodes + edges) เพื่อ
render เป็นกราฟใน dashboard. รองรับทั้ง:
- Linear suites (pipeline-finance/medical): {prev_output} chain → linear edges
- DAG suites (pipeline-council): depends_on → fan-out/fan-in edges

Node groups (สำหรับ color coding ใน frontend):
  - sequential (teal)
  - parallel (amber)
  - merge (red)

Pure function — no I/O except loading suite (caller provides parsed suite dict).
"""
from __future__ import annotations

from typing import Any


def suite_to_vis_data(suite: dict[str, Any]) -> dict[str, list]:
    """แปลง pipeline suite → vis-network {nodes, edges}.

    Args:
      suite: parsed suite dict (ต้องมี 'stages' key สำหรับ pipeline).

    Returns:
      {nodes: [{id, label, group, title, subagent}], edges: [{from, to, arrows}]}
      Empty ถ้า suite ไม่ใช่ pipeline (ไม่มี 'stages').
    """
    stages = suite.get("stages")
    if not stages or not isinstance(stages, list):
        return {"nodes": [], "edges": []}

    nodes = []
    edges = []
    has_dag_features = any(s.get("type") or s.get("depends_on") for s in stages)

    # Build nodes
    for stage in stages:
        sid = stage.get("id", "?")
        stype = stage.get("type", "sequential")
        if stype not in ("sequential", "parallel", "merge"):
            stype = "sequential"
        subagent = stage.get("subagent", "")
        prompt = stage.get("prompt", "")
        # Title = tooltip: subagent + prompt preview (first 80 chars)
        prompt_preview = prompt[:80] + ("…" if len(prompt) > 80 else "")
        title = f"[{subagent}] {prompt_preview}" if subagent else prompt_preview
        nodes.append({
            "id": sid,
            "label": sid,
            "group": stype,
            "title": title,
            "subagent": subagent,
        })

    # Build edges
    if has_dag_features:
        # DAG: use depends_on
        for stage in stages:
            sid = stage.get("id", "?")
            deps = stage.get("depends_on", [])
            if isinstance(deps, str):
                deps = [deps]
            for dep in deps:
                edges.append({"from": dep, "to": sid, "arrows": "to"})
    else:
        # Linear: chain consecutive stages (s0→s1, s1→s2, ...)
        for i in range(len(stages) - 1):
            edges.append({
                "from": stages[i].get("id", f"s{i}"),
                "to": stages[i + 1].get("id", f"s{i+1}"),
                "arrows": "to",
            })

    return {"nodes": nodes, "edges": edges}


def build_graph_payload(suite_name: str, suites_dir: str | None = None) -> dict[str, Any]:
    """Load a suite by name + return vis-network payload.

    Args:
      suite_name: suite name (e.g. "pipeline-council").
      suites_dir: directory containing suite JSONs (default: evals/subagents/).

    Returns:
      {suite, nodes, edges} or {suite, error} ถ้า suite not found / not pipeline.
    """
    import json
    from pathlib import Path
    repo_root = Path(__file__).resolve().parent.parent.parent
    sdir = Path(suites_dir) if suites_dir else repo_root / "evals" / "subagents"
    suite_path = sdir / f"{suite_name}.json"
    if not suite_path.is_file():
        return {"suite": suite_name, "error": "suite not found", "nodes": [], "edges": []}
    try:
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"suite": suite_name, "error": f"invalid JSON: {e}", "nodes": [], "edges": []}
    vis = suite_to_vis_data(suite)
    if not vis["nodes"]:
        return {"suite": suite_name, "error": "not a pipeline suite (no stages)", "nodes": [], "edges": []}
    return {"suite": suite_name, **vis}


def list_pipeline_suites(suites_dir: str | None = None) -> list[str]:
    """List all pipeline suite names (suites with 'stages' key)."""
    import json
    from pathlib import Path
    repo_root = Path(__file__).resolve().parent.parent.parent
    sdir = Path(suites_dir) if suites_dir else repo_root / "evals" / "subagents"
    out = []
    if not sdir.is_dir():
        return out
    for path in sorted(sdir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "stages" in data:
                out.append(path.stem)
        except Exception:
            continue
    return out


__all__ = ["suite_to_vis_data", "build_graph_payload", "list_pipeline_suites"]
