---
type: protocol
adr: 0012
title: G3 — MCP stdio compatibility port spec for mcp-wiki-server.py
status: Frozen (binding for slice A1 refactor)
created: 2026-08-02
updated: 2026-08-02
last_verified: 2026-08-02
verify_tool: char-test (tests/test_mcp_wiki_server.py)
---

# G3 — MCP stdio compatibility port spec

> ADR-0012 prerequisite gate G3. The frozen caller-visible surface of the
> `awiki` MCP server. Slice A1 (port extraction from `mcp-wiki-server.py`)
> MUST preserve every item below — the char-test suite in
> `tests/test_mcp_wiki_server.py` enforces it as a regression floor.

## 1. Transport

- **Wire**: JSON-RPC 2.0 over stdio (MCP stdio transport)
- **Encoding**: UTF-8, one message per line on stdout
- **Notifications**: server emits `notifications/initialized` on startup

## 2. JSON-RPC methods (frozen)

| Method | Request shape | Response shape |
|---|---|---|
| `initialize` | `{id, params:{}}` | `{protocolVersion, capabilities, serverInfo}` |
| `notifications/initialized` | notification (no id) | no response |
| `tools/list` | `{id, params:{}}` | `{tools:[{name,description,inputSchema}]}` |
| `tools/call` | `{id, params:{name, arguments}}` | `{content:[{type:"text", text}], isError}` OR raises MCPError |
| `resources/list` | `{id, params:{}}` | `{resources:[{uri,name,description,mimeType}]}` |
| `resources/read` | `{id, params:{uri}}` | `{contents:[{uri,mimeType,text}]}` |

**Error codes** (raised by handlers as `MCPError(code, msg)`; main loop wraps as JSON-RPC error):
- `-32601` method/tool/resource not found
- `-32602` invalid params (missing required arg)
- `-32000` runtime / I/O failure
- `-32002` resource not found (e.g. missing wiki page)
- `-32700` parse error (malformed stdin line)
- `-32603` internal error (catch-all)

## 3. `serverInfo` (frozen)

```json
{"name": "awiki-server", "version": "1.0.0"}
```

## 4. `capabilities` (frozen)

```json
{
  "tools": {"listChanged": false},
  "resources": {"listChanged": false, "subscribe": false}
}
```

## 5. Tools registry (9 tools — frozen names + schemas)

| Tool | Required args | Result keys |
|---|---|---|
| `wiki_search` | `query` | `results`, `total`, `query` |
| `wiki_semantic_search` | `query` | `results`, `total`, `query` |
| `wiki_graph_neighbors` | `path` | `path`, `domain`, `outgoing`, `incoming`, `out_count`, `in_count` |
| `wiki_graph_hubs` | (none) | `hubs`, `total` |
| `wiki_get_page` | `path` | `path`, `title`, `content`, `length`, `truncated` |
| `wiki_regen_index` | (none) | `status`, `output` |
| `wiki_ingest_route` | (none) | varies (`n_files`+`message` on empty backlog; `tier`+`mode` on success) |
| `wiki_batch_status` | (none) | batch status dict |
| `wiki_batch_collect` | `batch_id` | collection summary |

> ⚠️ **Each tool entry in the TOOLS dict carries `fn`, `description`, `inputSchema` — there is NO `name` key; the dict key IS the name.** `handle_list_tools` synthesises `name` from the key. Char-test pins this.

## 6. Resources registry (3 URIs — frozen)

- `wiki://overview` — auto-generated wiki overview
- `wiki://graph/stats` — knowledge graph statistics
- `wiki://context/now` — current session context

> `RESOURCES` is a DICT keyed by URI (not a list). Each value has `description`, `mimeType`, `fn`.

## 7. Slice A1 refactor constraints (binding)

When extracting ports from `mcp-wiki-server.py`:
1. ✅ The TOOLS dict MUST stay enumerable with the same 9 keys (char-test enforced)
2. ✅ Tool `inputSchema` MUST stay identical (char-test spot-checks `wiki_search`, `wiki_get_page`)
3. ✅ `handle_*` return shape (result dict, NOT wrapped envelope) MUST stay — envelope wrapping stays in `main()`
4. ✅ MCPError codes MUST stay (-32601/-32602/-32000/-32002)
5. ✅ `serverInfo.name == "awiki-server"` MUST stay (every `.mcp.json` config depends on it)
6. ✅ `RESOURCES` dict-keyed-by-URI structure MUST stay

**What MAY change** (internal, not caller-visible):
- How tool `fn` reaches FTS5/sqlite-vec/raw files (the whole point of port extraction)
- Adding NEW tools/resources (additive, non-breaking)
- Internal module layout

## 8. Verification

The char-test suite `tests/test_mcp_wiki_server.py` (21 tests) enforces this spec as a regression floor. Any slice A1 refactor MUST keep that suite green. The mutation test (drop a tool → test fails) confirms the suite is honest.
