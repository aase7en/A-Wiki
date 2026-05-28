---
type: entity
category: tool
tags: [code-graph, mcp, ai-tools, dev-tools, ast, tree-sitter, ladybugdb]
sources: [github-gitnexus]
created: 2026-05-28
updated: 2026-05-28
last_verified: 2026-05-28
verify_tool: WebFetch
---

# GitNexus

**ประเภท**: Code Intelligence MCP Server
**สถานะ**: integrated as optional MCP (`.mcp.json.example`)
**License**: PolyForm Noncommercial (personal/wiki = OK, commercial = ซื้อ license)

## ภาพรวม

GitNexus สร้าง **knowledge graph ระดับโค้ด** ของ repo (functions, calls, imports, heritage) แล้ว expose ผ่าน Model Context Protocol (MCP) ให้ AI agent ใช้ — แก้ปัญหา "AI แก้ `UserService.validate()` โดยไม่รู้ว่ามี 47 functions พึ่งพา return type" ทำให้ Claude/Cursor/Codex เข้าใจ blast radius **ก่อน** แก้

## คุณสมบัติหลัก

- **Languages**: TypeScript, JavaScript, Python, Java, Kotlin, C#, Go, Rust, PHP, Ruby, Swift, C, C++, Dart
- **Parser**: Tree-sitter (native + WASM)
- **Graph DB**: LadybugDB (in-process, vector + graph)
- **Search**: Hybrid BM25 + semantic + RRF ranking
- **Clustering**: Graphology + Leiden community detection
- **16 MCP tools**: `query`, `impact`, `context`, `detect_changes`, `rename`, `cypher`, ฯลฯ

## การใช้งานใน A-Wiki

- **A-Wiki repo ตัวเอง** — index `scripts/` (Python) เพื่อให้ Claude เข้าใจ call graph ของ `hooks_runner.py`, `gen-index.py`, `build-vec-index.py`
- **Dream projects** — Sunday Estate (Next.js), Pharmacy App (Python), IoT Dashboard (TBD) ใช้ index แยกต่อ repo
- **Cost Pyramid Level -1 extension** — เสริมจาก FTS5 + sqlite-vec + wiki-graph → +code-graph เมื่อ MCP active

## Setup

```bash
# A-Wiki repo
bash scripts/setup-gitnexus.sh        # analyze + ผูก MCP

# Dream project (เช่น Sunday Estate)
cd ~/projects/sunday-estate
npx gitnexus analyze
npx gitnexus setup                    # ผูก MCP ใน Claude Code
```

หลัง setup → Claude เห็น 16 tools: `gitnexus.query`, `gitnexus.impact`, `gitnexus.context`, ฯลฯ

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Code-level graph ที่ wiki-graph ทำไม่ได้ | License PolyForm — non-commercial เท่านั้น |
| Privacy-first (local CLI, in-browser web) | ต้อง Node.js 18+ |
| 14 languages | A-Wiki scripts น้อย → benefit ต่ำกว่า dream projects |
| Hybrid BM25 + semantic + RRF | LadybugDB ใหม่ ยังไม่ battle-tested เท่า Neo4j |
| MCP native — Claude Code ใช้ได้ทันที | `.gitnexus/` cache เพิ่ม disk ~50-500MB/repo |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[mcp]] — protocol สำหรับ expose tools
- ใช้ร่วมกับ: [[turbovec]] — alternate vector backend ใน scale ใหญ่
- เปรียบเทียบกับ: A-Wiki's [[knowledge-graph]] — wiki-level (markdown links) vs. code-level (function calls)
- เกี่ยวข้องกับ: [[ecc]], [[claude-skills]] — ecosystem AI dev tools

## แหล่งข้อมูล

- GitHub: https://github.com/abhigyanpatwari/GitNexus
- Web demo: https://gitnexus.vercel.app
- [verified 2026-05-28] WebFetch — 40.6k stars, 339+ releases
