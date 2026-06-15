"""
scripts/swarm/ag2_tools.py — Tool wrappers for AG2 agents in A-Wiki.

These functions are registered as AG2 tools for the Planner and Executor agents.
All tools are cost-first: they prefer local FTS5/file reads before any API call.

Available tools:
  wiki_search(query, limit=5)           → FTS5 search via scripts/search-wiki.py
  wiki_get_page(path)                   → read a wiki page (relative to repo root)
  wiki_graph_neighbors(node, limit=10)  → knowledge graph neighbors
  delegate_task(task_type, prompt)      → route to free model via scripts/swarm/delegate.sh
  cost_declare(tier, task, reason)      → write .tmp/cost-tier-YYYY-MM-DD.txt
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
TMP_DIR = REPO_ROOT / ".tmp"
SEARCH_SCRIPT = REPO_ROOT / "scripts" / "search-wiki.py"
GRAPH_SCRIPT = REPO_ROOT / "scripts" / "query-graph.py"
DELEGATE_SCRIPT = REPO_ROOT / "scripts" / "swarm" / "delegate.sh"


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT),
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"timeout after {timeout}s"
    except FileNotFoundError as e:
        return 1, "", str(e)


def wiki_search(query: str, limit: int = 5) -> str:
    """
    Search the local A-Wiki knowledge base using FTS5.
    Returns a JSON string with list of {title, path, snippet} results.
    Cost: free (local sqlite).
    """
    if not SEARCH_SCRIPT.exists():
        return json.dumps({"error": f"{SEARCH_SCRIPT} not found"})
    code, out, err = _run(
        [sys.executable, str(SEARCH_SCRIPT), query, "--limit", str(limit), "--json"],
        timeout=15,
    )
    if code != 0:
        # Fallback: older search-wiki without --json → tab-separated lines
        code, out, err = _run(
            [sys.executable, str(SEARCH_SCRIPT), query, "--limit", str(limit)],
            timeout=15,
        )
        return json.dumps(
            {"results": out.strip().splitlines()[:limit], "error": err.strip() or None},
            ensure_ascii=False,
        )
    # search-wiki.py --json emits a JSON LIST; normalize to {"results": [...]}
    # so callers can always rely on a dict shape (closes shape-mismatch at source).
    raw = out.strip()
    if not raw:
        return json.dumps({"results": []})
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps({"results": [], "error": "unparseable search output"})
    if isinstance(parsed, list):
        return json.dumps({"results": parsed}, ensure_ascii=False)
    if isinstance(parsed, dict):
        parsed.setdefault("results", [])
        return json.dumps(parsed, ensure_ascii=False)
    return json.dumps({"results": []})


def wiki_get_page(path: str) -> str:
    """
    Read a wiki page by path (relative to repo root).
    Cost: free (local file read).
    """
    target = REPO_ROOT / path
    # Security: prevent directory traversal outside repo
    try:
        target = target.resolve()
        target.relative_to(REPO_ROOT)
    except ValueError:
        return json.dumps({"error": f"Path outside repo: {path}"})
    if not target.exists():
        return json.dumps({"error": f"File not found: {path}"})
    try:
        content = target.read_text(encoding="utf-8")
        return json.dumps({"path": path, "content": content[:8000]})  # cap at 8k chars
    except Exception as e:
        return json.dumps({"error": str(e)})


def wiki_graph_neighbors(node: str, limit: int = 10) -> str:
    """
    Get knowledge graph neighbors for a node.
    Cost: free (local sqlite graph).
    """
    if not GRAPH_SCRIPT.exists():
        return json.dumps({"error": f"{GRAPH_SCRIPT} not found"})
    # query-graph.py takes the node via --neighbors PATH (NOT a positional arg).
    code, out, err = _run(
        [sys.executable, str(GRAPH_SCRIPT), "--neighbors", node, "--limit", str(limit)],
        timeout=10,
    )
    if code != 0:
        return json.dumps({"error": err.strip() or "graph query failed"})
    return json.dumps({"node": node, "neighbors": out.strip().splitlines()}, ensure_ascii=False)


def delegate_task(task_type: str, prompt: str) -> str:
    """
    Route a task to a free/cheap model via scripts/swarm/delegate.sh.
    task_type: search | lookup | summarize | reason | compare | scan | race
    Cost: free tier first (OpenRouter/Gemini/Groq), paid only on fallback.
    """
    if not DELEGATE_SCRIPT.exists():
        return json.dumps({"error": f"{DELEGATE_SCRIPT} not found"})
    valid_types = {"search", "lookup", "summarize", "reason", "compare", "scan", "race"}
    if task_type not in valid_types:
        return json.dumps({"error": f"Invalid task_type '{task_type}'. Must be: {sorted(valid_types)}"})

    # Prompt to English if possible (delegate.sh saves ~30% tokens on non-English)
    code, out, err = _run(
        ["bash", str(DELEGATE_SCRIPT), task_type, prompt],
        timeout=90,
    )
    if code != 0:
        return json.dumps({"error": err.strip() or "delegate failed", "code": code})
    return json.dumps({"result": out.strip()})


def cost_declare(tier: str, task: str, reason: str) -> str:
    """
    Write cost tier declaration (.tmp/cost-tier-YYYY-MM-DD.txt).
    tier: L1 | L2 | L3 | L4
    Must be called before any Edit/Write/Agent tool use.
    Cost: free (local file write).
    """
    valid_tiers = {"L1", "L2", "L3", "L4"}
    tier = tier.upper()
    if tier not in valid_tiers:
        return json.dumps({"error": f"Invalid tier '{tier}'. Must be: L1, L2, L3, L4"})
    TMP_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    decl_path = TMP_DIR / f"cost-tier-{today}.txt"
    content = f"{tier}|{task}|{reason}"
    decl_path.write_text(content, encoding="utf-8")
    return json.dumps({"declared": content, "path": str(decl_path)})


# Tool metadata for AG2 registration
TOOL_REGISTRY: list[dict[str, Any]] = [
    {
        "name": "wiki_search",
        "description": (
            "Search the local A-Wiki knowledge base using FTS5 full-text search. "
            "Free, offline, fast. Use this FIRST before any API call."
        ),
        "func": wiki_search,
    },
    {
        "name": "wiki_get_page",
        "description": (
            "Read a wiki page by path relative to the repo root. "
            "Free, offline. Use for context on specific topics."
        ),
        "func": wiki_get_page,
    },
    {
        "name": "wiki_graph_neighbors",
        "description": (
            "Get knowledge graph neighbors for a concept node. "
            "Free, offline. Use to discover related topics."
        ),
        "func": wiki_graph_neighbors,
    },
    {
        "name": "delegate_task",
        "description": (
            "Route a task to a free/cheap model via the cost-tier router. "
            "task_type must be: search | lookup | summarize | reason | compare | scan | race. "
            "Prefers free tier (OpenRouter/Gemini/Groq). Use for all non-primary-model work."
        ),
        "func": delegate_task,
    },
    {
        "name": "cost_declare",
        "description": (
            "Declare the cost tier for this task before any Edit/Write. "
            "tier: L1=free/local, L2=cheap, L3=low-scout, L4=primary model. "
            "Required by the cost-tier hook."
        ),
        "func": cost_declare,
    },
]
