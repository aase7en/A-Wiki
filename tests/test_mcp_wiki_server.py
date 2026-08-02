"""tests/test_mcp_wiki_server.py — characterization tests for the awiki MCP server.

ADR-0012 prerequisite G1 (2026-08-01): BEFORE any port extraction begins on
mcp-wiki-server.py (slice A1), we must pin its current caller-visible
behaviour so a refactor cannot silently break the ~9 agents that depend on
this Iron-Law-protected Layer 3 server.

What is characterized:
  - The TOOLS registry (9 tools) and RESOURCES registry (3 resources) — names,
    input shapes, presence of description/schema. This is the frozen caller
    contract (R8): a refactor must not rename tools or change their schemas.
  - The JSON-RPC dispatch surface: initialize, tools/list, tools/call,
    resources/list, resources/read, notifications/initialized.
  - Behaviour of the pure-logic / no-I/O tools (wiki_graph_neighbors uses a
    fixture graph; wiki_get_page uses a fixture file) — these are the ones
    that are cheap to test offline.
  - Behaviour that requires the real DB/subprocess (wiki_search, semantic
    search, regen_index, ingest) is pinned at the SHAPE level only: the
    contract is "returns a dict with these keys" / "raises MCPError with a
    negative code". A future slice A1 will introduce mockable ports; until
    then we do NOT characterise the deep internals.

Why not stdio end-to-end for everything?
  Spawning the server needs a populated .wiki-index.db and is slow. We test
  the same dispatch logic at the function level (handle_*) — same code path,
  100x faster, no DB dependency. Stdio is covered by one smoke test only.

These tests are the floor; they are intentionally NOT exhaustive on internal
implementation details. Add tests here as regressions surface.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Filename has dashes (mcp-wiki-server.py) so a normal `import` won't work.
# Load it as a module via its path instead.
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "mcp_wiki_server", REPO_ROOT / "scripts" / "mcp-wiki-server.py",
)
srv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(srv)


# ── 1. Caller contract: TOOLS registry shape ─────────────────────────────
EXPECTED_TOOLS = {
    "wiki_search", "wiki_semantic_search",
    "wiki_graph_neighbors", "wiki_graph_hubs",
    "wiki_get_page", "wiki_regen_index",
    "wiki_ingest_route", "wiki_batch_status", "wiki_batch_collect",
}


def test_tools_registry_has_expected_tool_names():
    """Pin the tool list. A refactor (slice A1) must not rename or drop tools
    — that would break every agent's MCP client config."""
    actual = set(srv.TOOLS.keys())
    missing = EXPECTED_TOOLS - actual
    assert not missing, f"tools vanished from registry: {missing}"


def test_each_tool_entry_has_fn_description_inputSchema():
    """Every entry must carry fn + description + inputSchema. Char-test
    finding 2026-08-01: there is NO `name` key in the tool spec — the dict
    KEY is the name. handle_list_tools synthesises `name` from the key."""
    for name, spec in srv.TOOLS.items():
        assert "fn" in spec and callable(spec["fn"]), f"{name}: missing/callable fn"
        assert isinstance(spec.get("description"), str) and spec["description"], \
            f"{name}: description"
        schema = spec.get("inputSchema")
        assert isinstance(schema, dict) and schema.get("type") == "object", \
            f"{name}: inputSchema must be an object"


def test_wiki_search_schema_documents_query_and_limit():
    """wiki_search is the most-called tool — its schema is the most important
    caller contract. Pin the documented args."""
    props = srv.TOOLS["wiki_search"]["inputSchema"]["properties"]
    assert "query" in props and props["query"]["type"] == "string"
    assert "limit" in props
    # query must be required (the docstring says it is)
    assert "query" in srv.TOOLS["wiki_search"]["inputSchema"].get("required", [])


def test_wiki_get_page_schema_documents_path_and_max_chars():
    props = srv.TOOLS["wiki_get_page"]["inputSchema"]["properties"]
    assert "path" in props and props["path"]["type"] == "string"
    assert "max_chars" in props
    assert "path" in srv.TOOLS["wiki_get_page"]["inputSchema"].get("required", [])


# ── 2. Caller contract: RESOURCES registry ──────────────────────────────
EXPECTED_RESOURCES = {"wiki://overview", "wiki://graph/stats", "wiki://context/now"}


def test_resources_registry_has_expected_uris():
    """Resources are read by agents via resources/read. URI renames break
    callers, so pin them.

    Char-test finding 2026-08-01: RESOURCES is a DICT keyed by URI, not a
    list. Each value has `description`, `mimeType`, `fn`. There is no
    per-entry `uri`/`name` key — handle_list_resources synthesises them."""
    assert isinstance(srv.RESOURCES, dict)
    actual = set(srv.RESOURCES.keys())
    assert EXPECTED_RESOURCES <= actual, \
        f"missing resource URIs: {EXPECTED_RESOURCES - actual}"


def test_each_resource_entry_has_description_mime_and_fn():
    for uri, spec in srv.RESOURCES.items():
        assert isinstance(spec.get("description"), str) and spec["description"], \
            f"{uri}: missing description"
        assert "mimeType" in spec, f"{uri}: missing mimeType"
        assert callable(spec.get("fn")), f"{uri}: fn must be callable"


# ── 3. JSON-RPC dispatch — function level (fast, no DB) ─────────────────
# Char-test finding 2026-08-01: handle_* functions return the RESULT dict
# directly (no {jsonrpc, id, result} envelope). The envelope wrapping happens
# in main()'s read/dispatch loop, which we cover with one stdio smoke test.
def test_handle_initialize_returns_server_info_and_capabilities():
    """initialize must declare the server name/version and capabilities dict
    that MCP clients validate on connect."""
    result = srv.handle_initialize({"id": 1, "params": {}})
    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "awiki-server"
    assert "version" in result["serverInfo"]
    assert isinstance(result.get("capabilities"), dict)
    assert result["capabilities"]["tools"]["listChanged"] is False


def test_handle_list_tools_returns_all_expected_tools():
    """tools/list must enumerate every entry in the TOOLS registry, and each
    entry must carry the synthesised `name` key (from the dict key)."""
    out = srv.handle_list_tools()
    tools = out["tools"]
    names = {t["name"] for t in tools}
    assert EXPECTED_TOOLS <= names
    # every listed tool must also carry description + inputSchema
    for t in tools:
        assert t["name"] and t.get("description") and t.get("inputSchema")


def test_handle_call_tool_unknown_raises_mcperror():
    """Calling an unknown tool raises MCPError -32601 (method not found).
    The main loop converts this to a JSON-RPC error envelope — at the
    handler level it is a raised exception, NOT a returned error dict."""
    with pytest.raises(srv.MCPError) as exc:
        srv.handle_call_tool({"id": 9, "params": {"name": "no_such_tool", "arguments": {}}})
    assert exc.value.code == -32601


def test_handle_call_tool_returns_content_array_with_text():
    """Successful tool calls wrap the result as a single text content item
    (MCP tools/call response shape). Pin this — callers parse content[0].text."""
    # wiki_graph_hubs with a stubbed graph is a safe, no-DB call
    monkeypatch_target = "_ensure_graph"
    orig = getattr(srv, monkeypatch_target)
    setattr(srv, monkeypatch_target,
            lambda: {"stats": {"hubs": [{"path": "h1"}]}})
    try:
        out = srv.handle_call_tool({
            "id": 1, "params": {"name": "wiki_graph_hubs", "arguments": {"limit": 5}},
        })
    finally:
        setattr(srv, monkeypatch_target, orig)
    assert out["isError"] is False
    assert isinstance(out["content"], list) and out["content"]
    assert out["content"][0]["type"] == "text"
    # The text field is the JSON-serialised result
    import json as _json
    parsed = _json.loads(out["content"][0]["text"])
    assert parsed["total"] == 1


def test_handle_list_resources_returns_expected_uris():
    out = srv.handle_list_resources()
    uris = {r["uri"] for r in out["resources"]}
    assert EXPECTED_RESOURCES <= uris
    for r in out["resources"]:
        assert r["uri"] and r.get("name") and r.get("description") and r.get("mimeType")


# ── 4. Behaviour: pure-logic tools (no DB / no subprocess) ──────────────
def test_wiki_graph_neighbors_returns_documented_shape(tmp_path, monkeypatch):
    """Pin the neighbour-map contract against a fixture graph. No DB needed."""
    graph = {
        "nodes": [
            {"path": "wiki/a.md", "domain": "iot"},
            {"path": "wiki/b.md", "domain": "iot"},
            {"path": "wiki/c.md", "domain": "env"},
        ],
        "edges": [
            {"from": "wiki/a.md", "to": "wiki/b.md", "type": "ref", "broken": False},
            {"from": "wiki/c.md", "to": "wiki/a.md", "type": "ref", "broken": False},
            {"from": "wiki/a.md", "to": "wiki/missing.md", "type": "ref", "broken": False},
        ],
        "stats": {"hubs": []},
    }
    # Bypass the file-read path so we don't need the real .wiki-graph.json
    monkeypatch.setattr(srv, "_ensure_graph", lambda: graph)

    out = srv.TOOLS["wiki_graph_neighbors"]["fn"]({"path": "wiki/a.md"})
    assert out["path"] == "wiki/a.md"
    assert out["domain"] == "iot"
    assert "wiki/b.md" in out["outgoing"]      # a → b
    assert "wiki/c.md" in out["incoming"]       # c → a
    assert out["out_count"] == 1                # broken edge to missing.md filtered
    assert out["in_count"] == 1


def test_wiki_graph_hubs_respects_limit_and_returns_list(monkeypatch):
    monkeypatch.setattr(srv, "_ensure_graph",
                        lambda: {"stats": {"hubs": [{"path": f"h{i}"} for i in range(20)]}})
    out = srv.TOOLS["wiki_graph_hubs"]["fn"]({"limit": 5})
    assert len(out["hubs"]) == 5
    assert out["total"] == 20  # total counts the full set, not the slice


def test_wiki_graph_neighbors_rejects_missing_path_with_mcperror(monkeypatch):
    """No path → MCPError -32602 (params error), NOT a Python exception."""
    monkeypatch.setattr(srv, "_ensure_graph", lambda: {"nodes": [], "edges": [], "stats": {}})
    with pytest.raises(srv.MCPError) as exc:
        srv.TOOLS["wiki_graph_neighbors"]["fn"]({})
    assert exc.value.code == -32602


def test_wiki_get_page_reads_markdown_and_reports_length(tmp_path, monkeypatch):
    """Pin the page-read contract: returns path/title/content/length/truncated.
    Uses a real temp file under the repo-root-mapped path."""
    fake_page = tmp_path / "wiki" / "fixture.md"
    fake_page.parent.mkdir(parents=True)
    fake_page.write_text("# Fixture\n\nbody text here", encoding="utf-8")
    monkeypatch.setattr(srv, "REPO_ROOT", tmp_path)

    out = srv.TOOLS["wiki_get_page"]["fn"]({"path": "wiki/fixture.md"})
    assert out["path"] == "wiki/fixture.md"
    assert "Fixture" in out["title"]
    assert "body text here" in out["content"]
    assert out["length"] == len("# Fixture\n\nbody text here")
    assert out["truncated"] is False


def test_wiki_get_page_truncates_when_max_chars_set(tmp_path, monkeypatch):
    fake_page = tmp_path / "wiki" / "long.md"
    fake_page.parent.mkdir(parents=True)
    fake_page.write_text("x" * 500, encoding="utf-8")
    monkeypatch.setattr(srv, "REPO_ROOT", tmp_path)

    out = srv.TOOLS["wiki_get_page"]["fn"]({"path": "wiki/long.md", "max_chars": 50})
    assert out["length"] == 50
    assert out["truncated"] is True


def test_wiki_get_page_missing_file_raises_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(srv, "REPO_ROOT", tmp_path)
    with pytest.raises(srv.MCPError) as exc:
        srv.TOOLS["wiki_get_page"]["fn"]({"path": "wiki/does-not-exist.md"})
    assert exc.value.code == -32002   # resource-not-found style code


def test_wiki_get_page_rejects_non_markdown(tmp_path, monkeypatch):
    other = tmp_path / "wiki" / "data.csv"
    other.parent.mkdir(parents=True)
    other.write_text("a,b,c", encoding="utf-8")
    monkeypatch.setattr(srv, "REPO_ROOT", tmp_path)
    with pytest.raises(srv.MCPError) as exc:
        srv.TOOLS["wiki_get_page"]["fn"]({"path": "wiki/data.csv"})
    assert exc.value.code == -32002


# ── 5. Behaviour: shape-only on I/O-dependent tools ─────────────────────
# These pin the caller-visible RESULT shape without depending on a populated
# DB. They will gain real fixtures once slice A1 introduces mockable ports.
def test_wiki_search_missing_query_raises_mcperror():
    """Empty query is a -32602 params error, never a silent empty result."""
    with pytest.raises(srv.MCPError) as exc:
        srv.TOOLS["wiki_search"]["fn"]({})
    assert exc.value.code == -32602


def test_wiki_semantic_search_missing_query_raises_mcperror():
    with pytest.raises(srv.MCPError) as exc:
        srv.TOOLS["wiki_semantic_search"]["fn"]({})
    assert exc.value.code == -32602


def test_wiki_ingest_route_empty_backlog_returns_zero_files(monkeypatch, tmp_path):
    """When raw/ scan finds nothing, the contract is a friendly message
    (n_files: 0), not an exception. Pin the shape."""
    # Stub the heavy import path so we don't pull in optional SDKs.
    def fake_harness():
        def discover_backlog(**kwargs):
            return []
        return {"discover_backlog": discover_backlog}
    monkeypatch.setattr(srv, "_harness_import", fake_harness)

    out = srv.TOOLS["wiki_ingest_route"]["fn"]({})
    assert out["n_files"] == 0
    assert "message" in out
