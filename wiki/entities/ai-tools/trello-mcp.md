---
type: entity
category: tool
tags: [mcp, trello, stdio, atlassian, kanban, task-management, npx]
sources:
  - https://github.com/endlesshoper/trello-mcp
  - https://www.npmjs.com/package/trello-mcp
  - https://github.com/atlassian/trello-mcp-server
created: 2026-08-06
updated: 2026-08-06
last_verified: 2026-08-06
verify_tool: WebFetch
---

# Trello MCP (community stdio edition)

**ประเภท**: MCP server (stdio)
**สถานะ**: registered in `.mcp.json` — `disabled: true` (รอใส่ `TRELLO_API_KEY` + `TRELLO_TOKEN` แล้ว flip เป็น `false`)
**npm**: `trello-mcp` (v1.0.3)
**License**: MIT
**Source**: https://github.com/endlesshoper/trello-mcp

## ภาพรวม

MCP server ที่ให้ AI agents (Claude Code, ZCode, Codex, Hermes, …) จัดการ Trello boards, lists, cards, checklists, labels ผ่าน MCP protocol แบบ **stdio transport** — auth ด้วย API key + token (env vars) ไม่ใช่ OAuth browser flow

เลือกตัวนี้แทน [Atlassian official `trello-mcp-server`](https://github.com/atlassian/trello-mcp-server) ซึ่งเป็น **cloud-hosted HTTP+OAuth bridge** (`https://mcp.trello.com/v1`) เพราะ official ตัวนั้นใช้ไม่ได้กับ headless agents (เช่น Hermes บน Pi5 Docker ที่ทำ OAuth browser consent ไม่ได้) และ ZCode/CLI agents ส่วนใหญ่รองรับแค่ stdio

## การใช้งานใน A-Wiki

เพิ่มใน `.mcp.json` (ดู `.mcp.json.example`):
```json
{
  "mcpServers": {
    "trello": {
      "command": "npx",
      "args": ["-y", "trello-mcp"],
      "env": {
        "TRELLO_API_KEY": "REPLACE_WITH_TRELLO_API_KEY",
        "TRELLO_TOKEN": "REPLACE_WITH_TRELLO_TOKEN"
      },
      "disabled": true,
      "autoApprove": []
    }
  }
}
```

**Enable (หลังใส่ key):** เปลี่ยน `"disabled": true` → `"disabled": false`

## ขอ credentials

1. **API key**: สร้าง Power-Up หรือ API key ที่ https://trello.com/power-ups/admin
2. **Token**: เปิดใน browser
   `https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&key=YOUR_API_KEY`
3. ใส่ key + token ใน `.mcp.json` (gitignored) — **ห้าม** commit key จริงเข้า repo

> ⚠️ Key/token เป็น secret → ต้องอยู่ใน `.mcp.json` (gitignored) เท่านั้น ไม่ใช่ `.mcp.json.example` (tracked template ใช้ placeholder)

## รายละเอียด package

| | |
|---|---|
| Transport | **stdio** (default) — รองรับทุก agent; มี `http` mode ด้วย (`TRANSPORT=http`) |
| Runtime | Node.js (deps แค่ 2 ตัว: `@modelcontextprotocol/sdk`, `zod`) |
| ขนาด | 179.5 kB (unpacked) |
| Scope | boards, lists, cards, checklists, labels แบบ read/write |
| ใช้กับ Pi5 Docker? | ✅ ได้ — env var auth, ไม่ต้อง browser |
| ใช้กับ ZCode? | ✅ ได้ — stdio |

## เปรียบเทียบกับ official Atlassian `trello-mcp-server`

| | **community `trello-mcp`** (เลือก) | **official Atlassian** |
|---|---|---|
| Transport | stdio (default) | HTTP (`https://mcp.trello.com/v1`) |
| Auth | API key + token (env vars) | OAuth 2.0 browser flow |
| ใช้กับ Hermes Pi5 Docker | ✅ | ❌ (headless ทำ OAuth ไม่ได้) |
| ใช้กับ ZCode/Codex/Cline | ✅ | ❌ (ส่วนใหญ่รองรับ stdio เท่านั้น) |
| ใช้กับ Claude Desktop/Cursor/VS Code | ✅ | ✅ |
| Workspace scope | multi (ใส่ key ของ workspace ไหนก็ได้) | one workspace per connection (launch limitation) |
| Maintainer | community (endlesshoper) | Atlassian |

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| stdio + env-var auth → ใช้ได้ทุก agent รวม headless | community-maintained (ไม่ใช่ official Atlassian) |
| deps เบา (2 ตัว, 179kB) → เหมาะ Pi5 | ไม่รองรับ OAuth revoke flow (token ใช้จนกว่าจะ revoke ใน Trello) |
| MIT license | tools จำกัดเทียบ official (35+ tools ของ `@delorenj/mcp-server-trello`) |
| cross-machine: ใส่ key ใน `.mcp.json` ของแต่ละเครื่องได้ | token expiration ต้องจัดการเอง |

## ความสัมพันธ์

- ทางเลือกแทน: official `atlassian/trello-mcp-server` (HTTP+OAuth — ไม่ได้ลง)
- เกี่ยวข้องกับ: [[gbrain]] / [[graphify]] — ตัวอย่าง MCP servers อื่นใน `.mcp.json`
- เกี่ยวข้องกับ: [[ecc]] — ECC มี kanban/task-management patterns ที่ใช้คู่กันได้
