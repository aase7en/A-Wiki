#!/usr/bin/env python3
"""
dag_eval.py — DAG pipeline composer (S3).

ขยาย pipeline eval (Q4 linear chain) เป็น generic DAG ที่รองรับ:
- sequential stage (default, backward-compat: {prev_output} injection)
- parallel stage (fan-out: multiple branches run concurrently)
- merge stage (fan-in: waits for all depends_on, substitutes {<id>.output})

ใช้สำหรับ council pattern eval: question → N parallel critics → synthesis

Architecture:
  parse_dag()         — normalize + validate stages
  topological_sort()  — Kahn's algorithm, detect cycles
  execute_dag()       — run stages in topo order (parallel within levels)
  judge_stage()       — required/forbidden keyword check (reused from run_subagent_eval)

Backward compatibility: stages ที่ไม่มี `type` field → treated as linear
({prev_output} injection เหมือน _chain_stages เดิม). Existing pipeline suites
(pipeline-finance/medical) ยังทำงานได้ผ่าน run_pipeline_eval.py dispatcher.

Usage (via run_pipeline_eval.py dispatcher):
  python scripts/eval/run_pipeline_eval.py --domain pipeline-council --apply
"""
from __future__ import annotations

import concurrent.futures
from typing import Any, Callable

# DRY: reuse delegate + judge from the single-model runner.
from run_subagent_eval import delegate_to_model, judge


# ---------------------------------------------------------------------------
# DAG parsing + validation
# ---------------------------------------------------------------------------
def parse_dag(stages: list[dict]) -> list[dict]:
    """Normalize + validate DAG stages.

    - ต้องมี `id` (unique) + `prompt`
    - default `type` = "sequential" (backward compat)
    - normalize `depends_on` เป็น list (None → [], str → [str])
    - validate: depends_on อ้างถึง stage ที่มีอยู่จริง

    Returns: normalized stages (deep-ish copy, doesn't mutate input).
    Raises: ValueError ถ้า missing id/prompt หรือ dangling depends_on.
    """
    if not stages:
        return []
    seen_ids = set()
    out = []
    for s in stages:
        if "id" not in s:
            raise ValueError(f"stage missing required 'id' field: {s}")
        sid = s["id"]
        if sid in seen_ids:
            raise ValueError(f"duplicate stage id: {sid}")
        seen_ids.add(sid)
        if "prompt" not in s:
            raise ValueError(f"stage '{sid}' missing required 'prompt' field")
        norm = dict(s)
        norm.setdefault("type", "sequential")
        # normalize depends_on to list
        deps = norm.get("depends_on")
        if deps is None:
            norm["depends_on"] = []
        elif isinstance(deps, str):
            norm["depends_on"] = [deps]
        elif isinstance(deps, list):
            norm["depends_on"] = list(deps)
        else:
            raise ValueError(f"stage '{sid}' has invalid depends_on type: {type(deps)}")
        out.append(norm)
    # validate dangling deps
    for s in out:
        for dep in s["depends_on"]:
            if dep not in seen_ids:
                raise ValueError(f"stage '{s['id']}' depends on unknown stage '{dep}'")
    return out


# ---------------------------------------------------------------------------
# Topological sort (Kahn's algorithm with cycle detection)
# ---------------------------------------------------------------------------
def topological_sort(stages: list[dict]) -> list[dict]:
    """Sort stages topologically by depends_on.

    Pure graph algorithm — does NOT validate prompt/subagent fields (use
    parse_dag() for that). Works on any list of dicts with `id` + optional
    `depends_on`.

    Returns stages in execution order (dependencies before dependents).
    Stages with no inter-dependencies at the same level can run in parallel.

    Raises: ValueError ถ้ามี cycle.
    """
    # Normalize depends_on to list (don't require prompt here)
    norm_stages = []
    seen_ids = set()
    for s in stages:
        sid = s["id"]
        if sid in seen_ids:
            raise ValueError(f"duplicate stage id: {sid}")
        seen_ids.add(sid)
        deps = s.get("depends_on")
        if deps is None:
            deps_list = []
        elif isinstance(deps, str):
            deps_list = [deps]
        else:
            deps_list = list(deps)
        for dep in deps_list:
            if dep not in [x["id"] for x in stages]:
                raise ValueError(f"stage '{sid}' depends on unknown stage '{dep}'")
        ns = dict(s)
        ns["depends_on"] = deps_list
        norm_stages.append(ns)

    by_id = {s["id"]: s for s in norm_stages}
    in_degree = {sid: 0 for sid in by_id}
    dependents = {sid: [] for sid in by_id}
    for s in norm_stages:
        deps = s["depends_on"]
        in_degree[s["id"]] = len(deps)
        for dep in deps:
            dependents[dep].append(s["id"])

    queue = [sid for sid, d in in_degree.items() if d == 0]
    order = []
    while queue:
        sid = queue.pop(0)
        order.append(by_id[sid])
        for child in dependents[sid]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(order) != len(norm_stages):
        cyclic = [sid for sid, d in in_degree.items() if d > 0]
        raise ValueError(f"Cycle detected in DAG (stages stuck: {cyclic})")

    return order


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
def _substitute_placeholders(prompt: str, case: dict, outputs: dict[str, str],
                              prev_output: str = "") -> str:
    """Replace template placeholders in a prompt.

    Supported:
      {<case_field>}     — value from the case dict (e.g. {topic})
      {<stage_id>.output} — output of a specific DAG stage (e.g. {skeptic.output})
      {prev_output}      — output of the previous sequential stage (backward compat)
    """
    result = prompt
    # case fields
    for key, val in case.items():
        if key != "id":
            result = result.replace("{" + key + "}", str(val))
    # stage outputs ({<id>.output})
    for sid, out in outputs.items():
        result = result.replace("{" + sid + ".output}", out)
    # backward-compat {prev_output}
    if prev_output:
        result = result.replace("{prev_output}", prev_output)
    return result


def execute_dag(
    stages: list[dict],
    model: str,
    case: dict,
    overrides: dict[str, str],
    max_workers: int = 4,
) -> str:
    """Execute a DAG pipeline for one case. Returns the terminal stage's output.

    Stages run in topological order. Stages at the same dependency level
    (all deps satisfied simultaneously) run concurrently via ThreadPool.

    The terminal stage = the last stage in topo order with no downstream
    dependents (or explicitly marked judge:true). Its output is returned.

    For backward compatibility (no `type` field on any stage), falls back to
    linear {prev_output} chaining identical to _chain_stages.
    """
    parsed = parse_dag(stages)
    ordered = topological_sort(parsed)
    outputs: dict[str, str] = {}
    prev_output = ""

    # Check if this is a legacy linear pipeline (no type fields anywhere)
    has_types = any(s.get("type", "sequential") != "sequential" or s.get("depends_on") for s in parsed)

    if not has_types:
        # Backward compat: pure linear chain with {prev_output}
        for stage in ordered:
            prompt = _substitute_placeholders(stage["prompt"], case, outputs, prev_output)
            subagent = stage.get("subagent", "")
            use_model = overrides.get(subagent, model)
            prev_output = delegate_to_model(use_model, prompt)
            outputs[stage["id"]] = prev_output
        return prev_output

    # DAG execution: group by dependency levels, run each level concurrently
    by_id = {s["id"]: s for s in parsed}
    completed = set()
    remaining = list(ordered)

    while remaining:
        # Find stages whose deps are all completed
        ready = [s for s in remaining if all(d in completed for d in s.get("depends_on", []))]
        if not ready:
            # Shouldn't happen (cycle check passed), but guard anyway
            raise ValueError(f"Deadlock: no ready stages (completed: {completed})")

        # Build prev_output for backward-compat stages (output of last completed)
        last_completed_output = outputs.get(ordered[-1]["id"], "") if completed else ""

        # Run all ready stages concurrently
        def _run_one(stage):
            # For backward compat in DAG mode: if no {id.output} refs, use prev_output
            prev_for_stage = ""
            if stage.get("type") == "sequential" and not stage.get("depends_on"):
                # first stage or linear-style — use last completed as prev
                prev_for_stage = last_completed_output
            prompt = _substitute_placeholders(stage["prompt"], case, outputs, prev_for_stage)
            subagent = stage.get("subagent", "")
            use_model = overrides.get(subagent, model)
            return stage["id"], delegate_to_model(use_model, prompt)

        if len(ready) == 1:
            sid, out = _run_one(ready[0])
            outputs[sid] = out
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(_run_one, s) for s in ready]
                for fut in concurrent.futures.as_completed(futures):
                    sid, out = fut.result()
                    outputs[sid] = out

        for s in ready:
            completed.add(s["id"])
            remaining.remove(s)

    # Terminal stage = last in topo order
    return outputs.get(ordered[-1]["id"], "")


# ---------------------------------------------------------------------------
# Judging (reuse from run_subagent_eval, exposed for DAG stage-level judging)
# ---------------------------------------------------------------------------
def judge_stage(stage: dict, response: str) -> bool:
    """Judge a single stage's output against its required/forbidden keywords.

    Wrapper around run_subagent_eval.judge for clarity in DAG context.
    Only terminal/merge stages are typically judged.
    """
    return judge(stage, response)


__all__ = [
    "parse_dag",
    "topological_sort",
    "execute_dag",
    "judge_stage",
]
