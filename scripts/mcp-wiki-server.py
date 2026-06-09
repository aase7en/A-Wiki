#!/usr/bin/env python3
"""
mcp-wiki-server.py — MCP stdio server that exposes the A-Wiki knowledge base
as MCP tools and resources.

Protocol: JSON-RPC 2.0 over stdin/stdout (MCP stdio transport).

Tools exposed:
  - wiki_search          — FTS5 full-text search
  - wiki_semantic_search — Hybrid FTS5 + embedding similarity
  - wiki_graph_neighbors — Knowledge graph neighbors for a page
  - wiki_graph_hubs      — Top connected pages
  - wiki_get_page        — Read raw wiki page content
  - wiki_regen_index     — Rebuild wiki index + graph + embeddings
  - wiki_ingest_route    — Universal cost-aware ingestion (Tier 1/2/3)
  - wiki_batch_status    — Poll pending Tier 2/3 batches
  - wiki_batch_collect   — Collect completed batch and write wiki/sources/

Resources exposed:
  - wiki://overview      — Auto-generated wiki overview (slim)
  - wiki://graph/stats   — Knowledge graph statistics
  - wiki://context/now   — Current session context

Usage (in .mcp.json):
  {
    "mcpServers": {
      "awiki": {
        "command": "python3",
        "args": ["scripts/mcp-wiki-server.py"],
        "env": {},
        "disabled": false,
        "autoApprove": ["wiki_search", "wiki_semantic_search", "wiki_get_page"]
      }
    }
  }
"""
from __future__ import annotations
import json
import os
import sqlite3
import subprocess
import sys
import traceback
from pathlib import Path

# ── Repo paths ─────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / ".wiki-index.db"
GRAPH_PATH = REPO_ROOT / ".wiki-graph.json"
CONTEXT_DIR = REPO_ROOT / "wiki" / "context"
GEN_INDEX = REPO_ROOT / "scripts" / "gen-index.py"
BUILDER = REPO_ROOT / "scripts" / "build-wiki-index.py"
VEC_BUILDER = REPO_ROOT / "scripts" / "build-vec-index.py"
QUERY_RAG = REPO_ROOT / "scripts" / "wiki" / "query-rag.py"

# ── JSON-RPC helpers ──────────────────────────────────────────────────


class MCPError(Exception):
    def __init__(self, code: int, message: str, data: object = None):
        self.code = code
        self.message = message
        self.data = data


def send(msg: dict) -> None:
    """Write a JSON message to stdout for the MCP transport."""
    line = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def error(id_: int | None, code: int, message: str, data: object = None) -> None:
    send({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message, "data": data}})


def ok(id_: int | None, result: object) -> None:
    send({"jsonrpc": "2.0", "id": id_, "result": result})


def notify(method: str, params: dict = None) -> None:
    """Send a notification (no id)."""
    msg = {"jsonrpc": "2.0", "method": method}
    if params:
        msg["params"] = params
    send(msg)


# ── Tool implementations ──────────────────────────────────────────────


def _ensure_db() -> None:
    if not DB_PATH.exists():
        subprocess.run([sys.executable, str(BUILDER)], check=True, capture_output=True)


def _ensure_graph() -> dict:
    if not GRAPH_PATH.exists():
        subprocess.run([sys.executable, str(GEN_INDEX)], check=True, capture_output=True)
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def tool_wiki_search(args: dict) -> dict:
    """FTS5 full-text search across wiki pages.

    Args:
        query (str): Search query
        limit (int, optional): Max results. Default 10.
        json_output (bool, optional): Return structured JSON. Default true.
    """
    query = args.get("query", "")
    limit = min(args.get("limit", 10), 50)
    if not query:
        raise MCPError(-32602, "query is required")

    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        sql = (
            "SELECT path, title, "
            "snippet(wiki, 3, '«', '»', '…', 16) AS snip, "
            "bm25(wiki) AS score "
            "FROM wiki WHERE wiki MATCH ? "
            "ORDER BY score LIMIT ?"
        )
        rows = conn.execute(sql, (query, limit)).fetchall()
    except sqlite3.OperationalError as e:
        raise MCPError(-32000, f"FTS5 query error: {e}")
    finally:
        conn.close()

    results = []
    for path, title, snip, score in rows:
        results.append({
            "path": path,
            "title": title,
            "snippet": " ".join(snip.split()),
            "score": round(score, 4),
        })
    return {"results": results, "total": len(results), "query": query}


def tool_wiki_semantic_search(args: dict) -> dict:
    """Hybrid FTS5 + sqlite-vec semantic search via query-rag.py.

    Args:
        query (str): Search query
        limit (int, optional): Max results. Default 10.
        alpha (float, optional): FTS weight 0-1 (0=pure vec, 1=pure FTS). Default 0.5.
    """
    query = args.get("query", "")
    limit = min(args.get("limit", 10), 50)
    alpha = args.get("alpha", 0.5)
    if not query:
        raise MCPError(-32602, "query is required")

    cmd = [
        sys.executable, str(QUERY_RAG), query,
        "--limit", str(limit),
        "--alpha", str(alpha),
        "--json",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise MCPError(-32000, f"query-rag.py failed: {result.stderr.strip()}")
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise MCPError(-32000, f"Failed to parse query-rag output: {e}")
    except subprocess.TimeoutExpired:
        raise MCPError(-32000, "Semantic search timed out (60s)")

    return {"results": raw, "total": len(raw), "query": query}


def tool_wiki_graph_neighbors(args: dict) -> dict:
    """Get knowledge graph neighbors of a wiki page.

    Args:
        path (str): Relative path to wiki page (e.g. wiki/entities/iot/mqtt-protocol.md)
    """
    page_path = args.get("path", "")
    if not page_path:
        raise MCPError(-32602, "path is required")

    graph = _ensure_graph()
    out = {}
    in_ = {}
    valid = {n["path"] for n in graph["nodes"]}
    domain_map = {n["path"]: n["domain"] for n in graph["nodes"]}

    for e in graph["edges"]:
        if e["broken"]:
            continue
        if e["to"] not in valid:
            continue
        if e["from"] == page_path:
            out[e["to"]] = {
                "type": e["type"],
                "domain": domain_map.get(e["to"], "?"),
            }
        if e["to"] == page_path:
            in_[e["from"]] = {
                "type": e["type"],
                "domain": domain_map.get(e["from"], "?"),
            }

    return {
        "path": page_path,
        "domain": domain_map.get(page_path, "?"),
        "outgoing": out,
        "incoming": in_,
        "out_count": len(out),
        "in_count": len(in_),
    }


def tool_wiki_graph_hubs(args: dict) -> dict:
    """Get top connected (hub) pages in the knowledge graph.

    Args:
        limit (int, optional): Max results. Default 10.
    """
    limit = min(args.get("limit", 10), 50)
    graph = _ensure_graph()
    hubs = graph.get("stats", {}).get("hubs", [])
    return {"hubs": hubs[:limit], "total": len(hubs)}


def tool_wiki_get_page(args: dict) -> dict:
    """Read raw content of a wiki page.

    Args:
        path (str): Relative path to wiki page
        max_chars (int, optional): Truncate to N chars. Default 0 (no truncate).
    """
    page_path = args.get("path", "")
    max_chars = args.get("max_chars", 0)
    if not page_path:
        raise MCPError(-32602, "path is required")

    full_path = REPO_ROOT / page_path
    if not full_path.exists():
        raise MCPError(-32002, f"Page not found: {page_path}")
    if not full_path.suffix == ".md":
        raise MCPError(-32002, f"Not a markdown file: {page_path}")

    text = full_path.read_text(encoding="utf-8", errors="replace")
    truncated = False
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars]
        truncated = True

    return {
        "path": page_path,
        "title": full_path.stem.replace("-", " ").title(),
        "content": text,
        "length": len(text),
        "truncated": truncated,
    }


def tool_wiki_regen_index(args: dict) -> dict:
    """Rebuild the full wiki index: overviews + FTS5 + graph + vector embeddings.

    Args:
        no_embeddings (bool, optional): Skip vector embedding rebuild. Default false.
    """
    no_emb = args.get("no_embeddings", False)
    try:
        result = subprocess.run(
            [sys.executable, str(GEN_INDEX)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise MCPError(-32000, f"gen-index.py failed: {result.stderr.strip()}")
        outputs = [result.stdout.strip()]
        if not no_emb:
            vec = subprocess.run(
                [sys.executable, str(VEC_BUILDER)],
                capture_output=True, text=True, timeout=300,
            )
            if vec.returncode != 0:
                raise MCPError(-32000, f"build-vec-index.py failed: {vec.stderr.strip()}")
            outputs.append(vec.stdout.strip())
        return {"status": "ok", "output": [line for chunk in outputs for line in chunk.split("\n") if line]}
    except subprocess.TimeoutExpired:
        raise MCPError(-32000, "Index rebuild timed out")


# ── Universal Ingest Harness tools (cost-aware routing) ───────────────


def _harness_import():
    """Lazy import of batch harness — keeps MCP server startup fast and
    isolates failures (e.g. missing openai/anthropic SDK) to the call site."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))
    from batch.collect import collect_batch, write_results  # noqa: E402
    from batch.config import load_conf  # noqa: E402
    from batch.poll import _refresh_one  # noqa: E402
    from batch.router import (  # noqa: E402
        build_requests, discover_backlog, dispatch, estimate_cost, select_tier,
    )
    from batch.state import get_batch, list_batches  # noqa: E402
    return {
        "collect_batch": collect_batch,
        "write_results": write_results,
        "load_conf": load_conf,
        "_refresh_one": _refresh_one,
        "build_requests": build_requests,
        "discover_backlog": discover_backlog,
        "dispatch": dispatch,
        "estimate_cost": estimate_cost,
        "select_tier": select_tier,
        "get_batch": get_batch,
        "list_batches": list_batches,
    }


def tool_wiki_ingest_route(args: dict) -> dict:
    """Universal cost-aware ingestion router.

    Args:
        tier (int, optional): Force tier 1/2/3.
        backend (str, optional): "deepseek" | "openai" | "anthropic".
        domain (str, optional): Domain hint (iot|env|ai-tools|pharmacy|it|general).
        limit (int, optional): Max files to ingest.
        slugs (list[str], optional): Restrict to specific slugs.
        file (str, optional): Single raw/<file> path.
        estimate (bool, optional): Only return cost estimate; no API call.
        dry_run (bool, optional): Build requests + select tier; no API call.
    """
    h = _harness_import()
    try:
        paths = h["discover_backlog"](
            domain_hint=args.get("domain"),
            limit=args.get("limit"),
            slugs=args.get("slugs"),
            file=args.get("file"),
        )
    except FileNotFoundError as e:
        raise MCPError(-32000, str(e))

    if not paths:
        return {"n_files": 0, "message": "no files to ingest (raw/ scan empty)"}

    conf = h["load_conf"]()
    provisional = h["build_requests"](paths, 1, domain_hint=args.get("domain"))
    tier, tier_reason = h["select_tier"](
        paths,
        cli_tier=args.get("tier"),
        cli_backend=args.get("backend"),
        conf=conf,
        requests=provisional,
    )
    requests = h["build_requests"](paths, tier, domain_hint=args.get("domain"))

    if args.get("estimate"):
        return {
            "n_files": len(paths),
            "selected_tier": tier,
            "tier_reason": tier_reason,
            "tiers": {
                t: h["estimate_cost"](requests, t, conf)
                for t in (0, 1, 2, 3)
                if conf.has_section(f"tier_{t}")
            },
        }

    if args.get("dry_run"):
        return {
            "tier": tier,
            "tier_reason": tier_reason,
            "n_requests": len(requests),
            "sample_slugs": [r.slug for r in requests[:5]],
            "truncated": len(requests) > 5,
        }

    try:
        submitted = h["dispatch"](requests, tier)
    except RuntimeError as e:
        raise MCPError(-32000, str(e))

    if submitted.get("mode") == "realtime":
        summary = h["write_results"](submitted["results"])
        return {"tier": tier, "tier_reason": tier_reason, "mode": "realtime", **summary}
    return {
        "tier": tier,
        "tier_reason": tier_reason,
        "mode": "batch",
        "batch_id": submitted["batch_id"],
        "input_path": submitted.get("input_path"),
        "next_step": "call wiki_batch_status, then wiki_batch_collect when ready",
    }


def tool_wiki_batch_status(args: dict) -> dict:
    """Refresh and return pending Tier 2/3 batch status.

    Args:
        batch_id (str, optional): If provided, poll one batch only.
        all (bool, optional): Include completed/collected batches.
    """
    h = _harness_import()
    if args.get("batch_id"):
        rec = h["get_batch"](args["batch_id"])
        if rec is None:
            raise MCPError(-32002, f"Unknown batch: {args['batch_id']}")
        return h["_refresh_one"](rec)
    records = h["list_batches"]() if args.get("all") else [
        r for r in h["list_batches"]() if r.get("status") in ("pending", "in_progress")
    ]
    return {"batches": [h["_refresh_one"](r) for r in records], "count": len(records)}


def tool_wiki_batch_collect(args: dict) -> dict:
    """Download a completed batch, validate, and write wiki/sources/.

    Args:
        batch_id (str): The batch_id to collect.
        no_gen_index (bool, optional): Skip gen-index.py rebuild.
    """
    h = _harness_import()
    if not args.get("batch_id"):
        raise MCPError(-32602, "batch_id is required")
    try:
        return h["collect_batch"](args["batch_id"], run_gen_index=not args.get("no_gen_index", False))
    except (ValueError, RuntimeError) as e:
        raise MCPError(-32000, str(e))


# ── Resource implementations ──────────────────────────────────────────


def resource_wiki_overview() -> tuple[str, str]:
    path = CONTEXT_DIR / "wiki-overview.md"
    if path.exists():
        return ("text/markdown", path.read_text(encoding="utf-8"))
    return ("text/plain", "Wiki overview not generated yet. Run gen-index.py.")


def resource_wiki_graph_stats() -> tuple[str, str]:
    if GRAPH_PATH.exists():
        graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
        s = graph.get("stats", {})
        text = (
            f"# Knowledge Graph Stats\n\n"
            f"- **Nodes**: {s.get('nodes', 0)}\n"
            f"- **Edges**: {s.get('edges', 0)}\n"
            f"- **Broken links**: {s.get('broken_links', 0)}\n"
            f"- **Orphans**: {s.get('orphans', 0)}\n"
            f"- **Generated**: {graph.get('generated_at', '?')}\n"
        )
        return ("text/markdown", text)
    return ("text/plain", "Graph not generated yet.")


def resource_wiki_context_now() -> tuple[str, str]:
    path = CONTEXT_DIR / "now.md"
    if path.exists():
        return ("text/markdown", path.read_text(encoding="utf-8"))
    return ("text/plain", "No now.md context file.")


# ── MCP Dispatcher ────────────────────────────────────────────────────

TOOLS = {
    "wiki_search": {
        "fn": tool_wiki_search,
        "description": "FTS5 full-text search across wiki pages. Returns matching pages with snippets and BM25 scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
    "wiki_semantic_search": {
        "fn": tool_wiki_semantic_search,
        "description": "Hybrid FTS5 + sqlite-vec semantic search over A-Wiki, fused with weighted RRF. Runs fully offline (fastembed multilingual model).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10},
                "alpha": {"type": "number", "description": "FTS weight 0-1 (0=pure vec, 1=pure FTS, default 0.5)", "default": 0.5},
            },
            "required": ["query"],
        },
    },
    "wiki_graph_neighbors": {
        "fn": tool_wiki_graph_neighbors,
        "description": "Get incoming and outgoing neighbor pages of a wiki page in the knowledge graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Wiki page path (e.g. wiki/entities/iot/mqtt-protocol.md)"},
            },
            "required": ["path"],
        },
    },
    "wiki_graph_hubs": {
        "fn": tool_wiki_graph_hubs,
        "description": "List top most-connected (hub) pages in the knowledge graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10},
            },
        },
    },
    "wiki_get_page": {
        "fn": tool_wiki_get_page,
        "description": "Read the raw Markdown content of a wiki page.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Wiki page path (e.g. wiki/entities/iot/mqtt-protocol.md)"},
                "max_chars": {"type": "integer", "description": "Max chars to return (0 = no limit)", "default": 0},
            },
            "required": ["path"],
        },
    },
    "wiki_regen_index": {
        "fn": tool_wiki_regen_index,
        "description": "Rebuild all wiki indexes: overviews, FTS5, knowledge graph, and embeddings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "no_embeddings": {"type": "boolean", "description": "Skip embedding rebuild", "default": False},
            },
        },
    },
    "wiki_ingest_route": {
        "fn": tool_wiki_ingest_route,
        "description": "Universal cost-aware ingestion router. Selects Tier 1 (DeepSeek realtime), Tier 2 (OpenAI batch), or Tier 3 (Anthropic batch) based on backlog size, configured policy, and overrides. Every A-Wiki agent ingests through this tool — bypassing it triggers the check_harness_routing.py hook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tier": {"type": "integer", "description": "Force tier 1/2/3"},
                "backend": {"type": "string", "enum": ["deepseek", "openai", "anthropic"]},
                "domain": {"type": "string", "description": "Domain hint"},
                "limit": {"type": "integer", "description": "Max files this run"},
                "slugs": {"type": "array", "items": {"type": "string"}, "description": "Restrict to specific slugs"},
                "file": {"type": "string", "description": "Single raw/<file> path"},
                "estimate": {"type": "boolean", "description": "Return cost estimate only", "default": False},
                "dry_run": {"type": "boolean", "description": "Build requests but skip the API call", "default": False},
            },
        },
    },
    "wiki_batch_status": {
        "fn": tool_wiki_batch_status,
        "description": "Refresh and return pending Tier 2/3 batch status (poll provider). Use after wiki_ingest_route returns a batch_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "Specific batch_id (optional)"},
                "all": {"type": "boolean", "description": "Include completed/collected", "default": False},
            },
        },
    },
    "wiki_batch_collect": {
        "fn": tool_wiki_batch_collect,
        "description": "Download a completed batch, validate output against the source provenance hook, and write wiki/sources/<slug>.md. Idempotent — safe to re-run.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "batch_id": {"type": "string", "description": "batch_id from state.jsonl"},
                "no_gen_index": {"type": "boolean", "description": "Skip gen-index.py rebuild", "default": False},
            },
            "required": ["batch_id"],
        },
    },
}

RESOURCES = {
    "wiki://overview": {
        "fn": resource_wiki_overview,
        "description": "Auto-generated wiki overview with stats and domain pointers.",
        "mimeType": "text/markdown",
    },
    "wiki://graph/stats": {
        "fn": resource_wiki_graph_stats,
        "description": "Knowledge graph statistics (nodes, edges, broken links, orphans).",
        "mimeType": "text/markdown",
    },
    "wiki://context/now": {
        "fn": resource_wiki_context_now,
        "description": "Current session context from now.md.",
        "mimeType": "text/markdown",
    },
}


def handle_initialize(req: dict) -> dict:
    """MCP initialize: return server capabilities."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {
                "listChanged": False,
            },
            "resources": {
                "listChanged": False,
                "subscribe": False,
            },
        },
        "serverInfo": {
            "name": "awiki-server",
            "version": "1.0.0",
        },
    }


def handle_list_tools() -> dict:
    return {
        "tools": [
            {
                "name": name,
                "description": info["description"],
                "inputSchema": info["inputSchema"],
            }
            for name, info in TOOLS.items()
        ]
    }


def handle_call_tool(req: dict) -> dict:
    name = req["params"]["name"]
    args = req["params"].get("arguments", {})
    if name not in TOOLS:
        raise MCPError(-32601, f"Tool not found: {name}")
    result = TOOLS[name]["fn"](args)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
                if isinstance(result, dict) else str(result),
            }
        ],
        "isError": False,
    }


def handle_list_resources() -> dict:
    return {
        "resources": [
            {
                "uri": uri,
                "name": uri.split("://")[1].replace("/", " ").title(),
                "description": info["description"],
                "mimeType": info["mimeType"],
            }
            for uri, info in RESOURCES.items()
        ]
    }


def handle_read_resource(req: dict) -> dict:
    uri = req["params"]["uri"]
    if uri not in RESOURCES:
        raise MCPError(-32602, f"Resource not found: {uri}")
    mime, text = RESOURCES[uri]["fn"]()
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": mime,
                "text": text,
            }
        ]
    }


# ── Main loop ─────────────────────────────────────────────────────────


def main() -> int:
    # Signal that server is ready (MCP uses notifications)
    notify("initialized")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            error(None, -32700, "Parse error")
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        try:
            if method == "initialize":
                ok(req_id, handle_initialize(req))
            elif method == "initialized":
                ok(req_id, {})  # ack
            elif method == "tools/list":
                ok(req_id, handle_list_tools())
            elif method == "tools/call":
                ok(req_id, handle_call_tool(req))
            elif method == "resources/list":
                ok(req_id, handle_list_resources())
            elif method == "resources/read":
                ok(req_id, handle_read_resource(req))
            elif method == "notifications/initialized":
                pass  # no response needed
            else:
                error(req_id, -32601, f"Method not found: {method}")
        except MCPError as e:
            error(req_id, e.code, e.message, e.data)
        except Exception:
            error(req_id, -32603, "Internal error", traceback.format_exc())

    return 0


if __name__ == "__main__":
    sys.exit(main())