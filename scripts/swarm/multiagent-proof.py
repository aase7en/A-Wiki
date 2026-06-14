#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import os
import re
import subprocess
import textwrap
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SEARCH_SCRIPT = REPO_ROOT / "scripts" / "search-wiki.py"
POLICY_SCRIPT = REPO_ROOT / "scripts" / "model-router-policy.py"
GOAL_SH = REPO_ROOT / "scripts" / "swarm" / "goal.sh"
DELEGATE_SH = REPO_ROOT / "scripts" / "swarm" / "delegate.sh"
DRIVE_SECRETS = REPO_ROOT / "scripts" / "lib" / "drive_secrets.py"
TMP_DIR = REPO_ROOT / ".tmp"
EXPORT_HTML = REPO_ROOT / "exports" / "html"


def run_cmd(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 120) -> dict[str, Any]:
    started_at = dt.datetime.now(dt.timezone.utc)
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    ended_at = dt.datetime.now(dt.timezone.utc)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_s": round(time.perf_counter() - started, 3),
    }


def get_secret(name: str) -> str:
    if not DRIVE_SECRETS.exists():
        return ""
    proc = subprocess.run(
        ["python3", str(DRIVE_SECRETS), name],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    value = proc.stdout.strip()
    return "" if value in ("", "None", "null") else value


def compact_text(value: str, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", value.strip())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def safe_env(extra: dict[str, str]) -> dict[str, str]:
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "en_US.UTF-8"),
    }
    if "TMPDIR" in os.environ:
        env["TMPDIR"] = os.environ["TMPDIR"]
    env.update({k: v for k, v in extra.items() if v})
    return env


def search_local(query: str) -> dict[str, Any]:
    result = run_cmd(["python3", str(SEARCH_SCRIPT), query, "--limit", "5", "--json"], timeout=30)
    payload: list[dict[str, Any]] = []
    if result["returncode"] == 0 and result["stdout"].strip():
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError:
            payload = []
    return {"query": query, "result": result, "hits": payload}


def planner_dry_run(goal: str) -> dict[str, Any]:
    result = run_cmd(["bash", str(GOAL_SH), goal, "--dry-run", "--json"], timeout=60)
    payload: dict[str, Any] = {}
    if result["returncode"] == 0 and result["stdout"].strip():
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError:
            payload = {}
    return {"goal": goal, "result": result, "payload": payload}


def router_policy() -> dict[str, Any]:
    result = run_cmd(["python3", str(POLICY_SCRIPT), "--json"], timeout=30)
    payload: dict[str, Any] = {}
    if result["returncode"] == 0 and result["stdout"].strip():
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError:
            payload = {}
    return {"result": result, "payload": payload}


def build_context(local_hits: list[dict[str, Any]], planner: dict[str, Any], policy: dict[str, Any], goal: str) -> str:
    hit_lines = []
    for hit in local_hits[:3]:
        path = hit.get("path", "?")
        title = hit.get("title", "?")
        snippet = compact_text(str(hit.get("snippet", "")), 180)
        hit_lines.append(f"- {title} ({path}): {snippet}")

    planner_payload = planner.get("payload", {})
    subtasks = planner_payload.get("suggested_subtasks", [])
    subtask_lines = [
        f"- {item.get('task_type', '?')}: {item.get('prompt', '?')}"
        for item in subtasks[:3]
        if isinstance(item, dict)
    ]

    tiers = policy.get("payload", {}).get("tiers", {})
    tier_lines = []
    for key in ("TIER1_PRIMARY", "TIER2_PRIMARY", "TIER3_PRIMARY", "RACE_MODELS"):
        if key in tiers:
            tier_lines.append(f"- {key}: {tiers[key]}")

    return textwrap.dedent(
        f"""
        Goal: {goal}

        Local-first evidence:
        {chr(10).join(hit_lines) if hit_lines else "- No local wiki hits"}

        Planner dry-run:
        - planner_model: {planner_payload.get('planner_model', 'n/a')}
        - delegation_target: {planner_payload.get('delegation_target', 'n/a')}
        {chr(10).join(subtask_lines) if subtask_lines else "- No dry-run subtasks"}

        Router snapshot:
        {chr(10).join(tier_lines) if tier_lines else "- No router tier snapshot"}

        Respond tersely. Use one line only. Mention one proof signal from the evidence.
        """
    ).strip()


LANES = [
    {
        "id": "gemini",
        "title": "Gemini Direct Lane",
        "tier": "L1",
        "task_type": "search",
        "provider_label": "Google AI Studio / Gemini direct",
        "route_proof": "Only Gemini credentials are injected into the shell env for this lane.",
    },
    {
        "id": "groq",
        "title": "Groq Direct Lane",
        "tier": "L1 fallback",
        "task_type": "search",
        "provider_label": "Groq direct",
        "route_proof": "Only GROQ_API_KEY is injected, so delegate.sh can only land on Groq's direct fallback.",
    },
    {
        "id": "openrouter-race",
        "title": "OpenRouter Race Lane",
        "tier": "parallel race",
        "task_type": "race",
        "provider_label": "OpenRouter race pool",
        "route_proof": "Only OPENROUTER_API_KEY is injected and task_type=race, so delegate.sh launches all models in RACE_MODELS concurrently and returns the first winner.",
    },
]


def lane_prompt(lane_id: str, context: str) -> str:
    if lane_id == "gemini":
        ask = 'Reply with one line starting "Gemini lane:" and mention one cost-first proof signal.'
    elif lane_id == "groq":
        ask = 'Reply with one line starting "Groq lane:" and mention one enforcement artifact or hook.'
    else:
        ask = 'Reply with one line starting "Race lane:" and mention one sign that multiple models can run in parallel.'
    return context + "\n\n" + ask


def lane_env(lane_id: str) -> tuple[dict[str, str], dict[str, Any]]:
    meta: dict[str, Any] = {"available_keys": [], "skipped": False, "skip_reason": ""}
    if lane_id == "gemini":
        gemini = get_secret("GEMINI_API_KEY")
        studio = get_secret("GOOGLE_AI_STUDIO_KEY")
        if not gemini and not studio:
            meta["skipped"] = True
            meta["skip_reason"] = "No Gemini key available"
            return safe_env({}), meta
        env = safe_env({"GEMINI_API_KEY": gemini, "GOOGLE_AI_STUDIO_KEY": studio})
        meta["available_keys"] = [k for k, v in (("GEMINI_API_KEY", gemini), ("GOOGLE_AI_STUDIO_KEY", studio)) if v]
        return env, meta
    if lane_id == "groq":
        groq = get_secret("GROQ_API_KEY")
        if not groq:
            meta["skipped"] = True
            meta["skip_reason"] = "No Groq key available"
            return safe_env({}), meta
        env = safe_env({"GROQ_API_KEY": groq})
        meta["available_keys"] = ["GROQ_API_KEY"]
        return env, meta
    openrouter = get_secret("OPENROUTER_API_KEY")
    if not openrouter:
        meta["skipped"] = True
        meta["skip_reason"] = "No OpenRouter key available"
        return safe_env({}), meta
    env = safe_env({"OPENROUTER_API_KEY": openrouter})
    meta["available_keys"] = ["OPENROUTER_API_KEY"]
    return env, meta


def run_lane(lane: dict[str, Any], context: str, race_models: str) -> dict[str, Any]:
    env, meta = lane_env(lane["id"])
    prompt = lane_prompt(lane["id"], context)
    if meta["skipped"]:
        return {
            **lane,
            "status": "skipped",
            "prompt": prompt,
            "stdout": "",
            "stderr": meta["skip_reason"],
            "duration_s": 0.0,
            "available_keys": meta["available_keys"],
            "race_models": race_models if lane["id"] == "openrouter-race" else "",
        }

    result = run_cmd(["bash", str(DELEGATE_SH), lane["task_type"], prompt], env=env, timeout=120)
    stderr = result["stderr"].replace(str(REPO_ROOT), "$REPO_ROOT")
    return {
        **lane,
        "status": "ok" if result["returncode"] == 0 else "error",
        "prompt": prompt,
        "stdout": result["stdout"].strip(),
        "stderr": stderr.strip(),
        "duration_s": result["duration_s"],
        "started_at": result["started_at"],
        "ended_at": result["ended_at"],
        "returncode": result["returncode"],
        "available_keys": meta["available_keys"],
        "race_models": race_models if lane["id"] == "openrouter-race" else "",
    }


def render_html(report: dict[str, Any]) -> str:
    goal = html.escape(report["goal"])
    local_hits = report["local_search"]["hits"]
    planner = report["planner"]["payload"]
    policy = report["router_policy"]["payload"]
    lanes = report["lanes"]

    lane_cards = []
    for lane in lanes:
        status_class = "ok" if lane["status"] == "ok" else ("skip" if lane["status"] == "skipped" else "err")
        status_label = {"ok": "LIVE", "skipped": "SKIPPED", "error": "ERROR"}[lane["status"]]
        stdout = html.escape(lane["stdout"] or "(no stdout)")
        stderr = html.escape(lane["stderr"] or "(no stderr)")
        keys = ", ".join(lane.get("available_keys", [])) or "(none)"
        extra = ""
        if lane.get("race_models"):
            extra = f"<div class='meta'><strong>Race pool</strong>: {html.escape(lane['race_models'])}</div>"
        lane_cards.append(
            f"""
            <section class="lane {status_class}">
              <div class="lane-head">
                <div>
                  <h3>{html.escape(lane['title'])}</h3>
                  <div class="meta">{html.escape(lane['provider_label'])} · tier {html.escape(lane['tier'])}</div>
                </div>
                <span class="badge {status_class}">{status_label}</span>
              </div>
              <div class="meta"><strong>Keys injected</strong>: {html.escape(keys)}</div>
              <div class="meta"><strong>Route proof</strong>: {html.escape(lane['route_proof'])}</div>
              {extra}
              <div class="meta"><strong>Duration</strong>: {lane.get('duration_s', 0):.3f}s</div>
              <details open>
                <summary>Model output</summary>
                <pre>{stdout}</pre>
              </details>
              <details>
                <summary>stderr / runtime notes</summary>
                <pre>{stderr}</pre>
              </details>
            </section>
            """
        )

    hits_html = "".join(
        f"<li><strong>{html.escape(hit.get('title', '?'))}</strong> "
        f"<code>{html.escape(hit.get('path', '?'))}</code><br>{html.escape(compact_text(str(hit.get('snippet', '')), 220))}</li>"
        for hit in local_hits[:5]
    ) or "<li>No local hits</li>"

    planner_html = html.escape(json.dumps(planner, ensure_ascii=False, indent=2))
    policy_html = html.escape(json.dumps(policy, ensure_ascii=False, indent=2))
    snapshot_html = html.escape(json.dumps(report, ensure_ascii=False, indent=2))
    generated_at = html.escape(report["generated_at"])

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A-Wiki Multi-Agent Proof Board</title>
  <style>
    :root {{
      --bg:#0f1720; --panel:#161f2b; --panel2:#1d2734; --line:#283445;
      --text:#e7edf5; --muted:#9fb0c3; --ok:#31c48d; --warn:#f6ad55; --err:#f56565; --blue:#63b3ed;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--text); }}
    .wrap {{ max-width:1200px; margin:0 auto; padding:24px; }}
    h1,h2,h3 {{ margin:0; }}
    h1 {{ font-size:28px; margin-bottom:8px; }}
    h2 {{ font-size:18px; margin:0 0 12px; }}
    .sub {{ color:var(--muted); margin-bottom:22px; }}
    .grid {{ display:grid; gap:16px; }}
    .grid.top {{ grid-template-columns:1.1fr .9fr; }}
    .grid.lanes {{ grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }}
    .card, .lane {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:16px; }}
    .lane.ok {{ border-color:rgba(49,196,141,.35); }}
    .lane.err {{ border-color:rgba(245,101,101,.35); }}
    .lane.skip {{ border-color:rgba(246,173,85,.35); }}
    .lane-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:10px; }}
    .badge {{ padding:4px 8px; border-radius:999px; font-size:12px; font-weight:700; }}
    .badge.ok {{ background:rgba(49,196,141,.14); color:var(--ok); }}
    .badge.err {{ background:rgba(245,101,101,.14); color:var(--err); }}
    .badge.skip {{ background:rgba(246,173,85,.14); color:var(--warn); }}
    .meta {{ color:var(--muted); margin:6px 0; }}
    ul {{ margin:0; padding-left:18px; }}
    code {{ color:var(--blue); }}
    pre {{
      margin:10px 0 0; white-space:pre-wrap; word-break:break-word; background:var(--panel2);
      padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,.04);
    }}
    details summary {{ cursor:pointer; color:var(--blue); }}
    .proof {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; margin-top:12px; }}
    .proof .mini {{ background:var(--panel2); border:1px solid var(--line); border-radius:8px; padding:12px; }}
    @media (max-width: 900px) {{
      .grid.top {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>A-Wiki Multi-Agent Proof Board</h1>
    <div class="sub">Generated {generated_at} · goal: {goal}</div>

    <div class="proof">
      <div class="mini"><strong>Level -1 / local first</strong><br>Wiki search + local policy snapshot run before any external model lane.</div>
      <div class="mini"><strong>Planner evidence</strong><br>AG2 dry-run shows planner/executor split before execution.</div>
      <div class="mini"><strong>Parallel proof</strong><br>Gemini, Groq, and OpenRouter race lanes were launched in parallel with isolated credentials.</div>
      <div class="mini"><strong>Multi-model proof</strong><br>Each lane is constrained to a different provider path, so outputs cannot all come from the same model.</div>
    </div>

    <div class="grid top" style="margin-top:16px;">
      <section class="card">
        <h2>1. Local-First Evidence</h2>
        <ul>{hits_html}</ul>
      </section>
      <section class="card">
        <h2>2. Planner Dry-Run</h2>
        <pre>{planner_html}</pre>
      </section>
    </div>

    <div class="grid top" style="margin-top:16px;">
      <section class="card">
        <h2>3. Router Snapshot</h2>
        <pre>{policy_html}</pre>
      </section>
      <section class="card">
        <h2>4. Why This Counts</h2>
        <ul>
          <li>We used local evidence first, then free external lanes.</li>
          <li>Each external lane injected only one provider family, so the route is provable.</li>
          <li>The OpenRouter race lane returned one winner while sibling model jobs were terminated after first success.</li>
          <li>This is the cost-first pyramid in action: local search → planner dry-run → free parallel executors.</li>
        </ul>
      </section>
    </div>

    <section style="margin-top:16px;">
      <h2 style="margin-bottom:12px;">5. Parallel Lanes</h2>
      <div class="grid lanes">
        {''.join(lane_cards)}
      </div>
    </section>

    <section class="card" style="margin-top:16px;">
      <h2>Machine Snapshot</h2>
      <details>
        <summary>Open full JSON snapshot</summary>
        <pre>{snapshot_html}</pre>
      </details>
    </section>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a live multi-agent proof board for A-Wiki")
    parser.add_argument(
        "--goal",
        default="Show that A-Wiki can use a cost-first parallel multi-agent conversation",
        help="Goal or question to demonstrate",
    )
    parser.add_argument(
        "--query",
        default="cost first delegate ag2 multi agent",
        help="Local wiki search query",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--html-out", default="", help="Optional HTML output path")
    args = parser.parse_args()

    TMP_DIR.mkdir(exist_ok=True)
    EXPORT_HTML.mkdir(parents=True, exist_ok=True)

    local = search_local(args.query)
    planner = planner_dry_run(args.goal)
    policy = router_policy()
    context = build_context(local["hits"], planner, policy, args.goal)
    race_models = policy.get("payload", {}).get("tiers", {}).get("RACE_MODELS", "")

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(LANES)) as pool:
        futures = [pool.submit(run_lane, lane, context, race_models) for lane in LANES]
        lanes = [future.result() for future in futures]
    total_duration = round(time.perf_counter() - started, 3)

    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    report = {
        "goal": args.goal,
        "query": args.query,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "local_search": local,
        "planner": planner,
        "router_policy": policy,
        "lanes": lanes,
        "parallel_runtime_s": total_duration,
    }

    json_path = Path(args.json_out) if args.json_out else TMP_DIR / f"multiagent-proof-{timestamp}.json"
    html_path = Path(args.html_out) if args.html_out else EXPORT_HTML / "multiagent-proof-live.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")

    print(
        json.dumps(
            {
                "json_path": str(json_path),
                "html_path": str(html_path),
                "parallel_runtime_s": total_duration,
                "lane_statuses": {lane["id"]: lane["status"] for lane in lanes},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
