---
type: entity
category: tool
tags: [claude-code, skills, knowledge-graph, graphrag, code-analysis, python]
sources: []
created: 2026-06-09
updated: 2026-06-09
last_verified: 2026-06-09
verify_tool: WebFetch
---

# Graphify

**ประเภท**: Claude Code skill + Python CLI + MCP server
**สถานะ**: external install (`pip install graphifyy`) — ติดตั้งผ่าน `scripts/install-graphify.sh`
**License**: MIT
**PyPI**: `graphifyy` (สองตัว y)

## ภาพรวม

Graphify แปลงไฟล์หลากหลาย (code, PDF, markdown, ภาพ, whiteboard) เป็น interactive knowledge graph ที่ query ได้ ลด token ใช้งานได้ถึง **71.5x** เทียบกับอ่านไฟล์ดิบ [verified 2026-06-09]

ใช้ tree-sitter parse AST ของ 16+ ภาษา + Claude vision สำหรับ document/image + Leiden algorithm สำหรับ community detection

## คุณสมบัติหลัก

| Component | รายละเอียด |
|-----------|-----------|
| **File detection** | code, PDF, markdown, ภาพ, diagram, whiteboard |
| **AST extraction** | tree-sitter: Python, JS, TS, Go, Rust, Java, C/C++, Ruby, C#, Kotlin, PHP+ |
| **Graph construction** | NetworkX + confidence-labeled edges (EXTRACTED/INFERRED/AMBIGUOUS) |
| **Community detection** | Leiden algorithm via graspologic — ค้นหา god nodes, surprises |
| **Output formats** | HTML interactive, JSON (GraphRAG), Markdown report, Obsidian vault |
| **MCP server** | stdio + HTTP — query_graph, get_node, shortest_path, get_neighbors |

## การใช้งานใน A-Wiki

```bash
# ติดตั้งครั้งแรก
bash scripts/install-graphify.sh

# build knowledge graph ของ A-Wiki
graphify wiki/        # graph จากทุก wiki pages
graphify .            # graph จากทั้ง repo
graphify wiki/ --mode deep  # + inferred connections

# query
graphify query "pharma entity extraction"
graphify path "IoT" "pharmacy"
graphify explain "knowledge-graph"
```

## MCP Server Setup

เพิ่มใน `.mcp.json` (ดู `.mcp.json.example`):
```json
{
  "mcpServers": {
    "graphify": {
      "command": "graphify",
      "args": ["serve", "--mode", "stdio"]
    }
  }
}
```

**MCP tools ที่ได้:**
- `query_graph` — semantic search ใน graph
- `get_node` — รายละเอียด node + metadata
- `get_neighbors` — explore connections
- `shortest_path` — หาเส้นทางระหว่าง node

## เปรียบกับ GitNexus (ที่ใช้อยู่แล้ว)

| | **GitNexus** | **Graphify** |
|-|-------------|-------------|
| เน้น | Code call graph + symbol navigation | Knowledge graph จากทุก file type |
| Input | Source code เท่านั้น | Code + PDF + markdown + ภาพ |
| Output | 16 MCP tools, execution flows | HTML viz + JSON + Obsidian |
| Token reduction | N/A | 71.5x |
| License | PolyForm Noncommercial | MIT |
| ใช้คู่กันได้? | ✅ ใช้คู่ได้ — คนละ dimension |

## ติดตั้ง

```bash
# macOS/Linux
bash scripts/install-graphify.sh

# Windows (PowerShell)
pip install graphifyy
graphify install

# macOS (managed Python — ใช้ pipx)
pipx install graphifyy
graphify install
```

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| 71.5x token reduction สำหรับ mixed corpora | ต้อง pip install แยก (ไม่ใช่ drop-in SKILL.md) |
| รองรับ image + whiteboard + code ในที่เดียว | dependency หนัก (tree-sitter, graspologic) |
| MIT license — ใช้ได้ทุก use case | SKILL.md ต้องผ่าน `graphify install` |
| MCP server ready | Python 3.10+ เท่านั้น |
| Obsidian-compatible output | |

## ความสัมพันธ์

- ใช้คู่กับ: [[gitnexus]] — Graphify ครอบคลุม doc/image; GitNexus ครอบคลุม code call graph
- เกี่ยวข้องกับ: [[ecc]] — ECC มี GraphRAG patterns ที่เข้ากันได้
- เกี่ยวข้องกับ: [[anthropic-skills]] — ใช้ Claude API สำหรับ vision extraction
