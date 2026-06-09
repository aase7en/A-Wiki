---
type: entity
category: tool
tags: [claude-code, skills, anthropic, document-processing, creative, cross-agent]
sources: []
created: 2026-06-09
updated: 2026-06-09
last_verified: 2026-06-09
verify_tool: WebFetch
---

# Anthropic Skills

**ประเภท**: Claude Code skill collection (official, Anthropic)
**สถานะ**: integrated at `skills/anthropic-skills/` (17 skills) — upstream remote `anthropic-skills` added
**License**: source-available (LICENSE.txt ต่อ skill)

## ภาพรวม

`anthropics/skills` คือ repo ทางการของ Anthropic ที่รวบรวม 17 curated skills แบ่งเป็น 3 กลุ่ม: document-skills (Office/PDF), example-skills (creative + dev tools), และ claude-api (API reference) [verified 2026-06-09]

Skills เหล่านี้เป็น SKILL.md format เดียวกับ A-Wiki ecosystem — Claude Code load จาก `~/.claude/skills/` หรือผ่าน plugin marketplace

## Skills Inventory

### document-skills — Office & PDF Processing

| Skill | หน้าที่ | โหลดใน harness แล้ว? |
|-------|---------|:---:|
| `docx` | สร้าง/อ่าน/แก้ไข Word documents (.docx) | ✅ |
| `pdf` | อ่าน/สร้าง/merge/split/fill PDF | ✅ |
| `pptx` | สร้าง/แก้ไข PowerPoint presentations | ✅ |
| `xlsx` | สร้าง/วิเคราะห์ Excel spreadsheets | ✅ |

### example-skills — Creative & Dev Tools

| Skill | หน้าที่ | โหลดใน harness แล้ว? |
|-------|---------|:---:|
| `algorithmic-art` | Generative art สร้างด้วย code | ➕ ใหม่ |
| `brand-guidelines` | สร้าง brand identity system | ➕ ใหม่ |
| `canvas-design` | Visual design/poster/art ออกเป็น PNG+PDF | ✅ |
| `doc-coauthoring` | เขียน document ร่วมกับผู้ใช้แบบ interactive | ➕ ใหม่ |
| `frontend-design` | Web UI/UX design + implementation | ➕ ใหม่ |
| `internal-comms` | เขียนสื่อสารภายในองค์กร (memo, update) | ➕ ใหม่ |
| `mcp-builder` | สร้าง MCP server จาก spec | ✅ |
| `skill-creator` | สร้าง/ปรับปรุง skills ใหม่ (meta-skill) | ✅ |
| `slack-gif-creator` | สร้าง animated GIF สำหรับ Slack | ➕ ใหม่ |
| `theme-factory` | สร้าง color theme + design system | ➕ ใหม่ |
| `web-artifacts-builder` | สร้าง web component / interactive artifact | ➕ ใหม่ |
| `webapp-testing` | Test web application อัตโนมัติ | ➕ ใหม่ |

### claude-api — API Reference

| Skill | หน้าที่ | โหลดใน harness แล้ว? |
|-------|---------|:---:|
| `claude-api` | Claude API/SDK reference — model IDs, pricing, streaming, tool use, MCP, agents | ✅ |

> หมายเหตุ: `consolidate-memory`, `schedule`, `setup-cowork` คือ Anthropic internal skills ที่ไม่อยู่ใน public repo แต่โหลดผ่าน harness

## การใช้งานใน A-Wiki

- **`skills/anthropic-skills/`** — 17 skill directories (extracted จาก upstream)
- **Refresh upstream**: `bash scripts/refresh-anthropic-skills.sh`
- **Link to Claude Code**: `bash scripts/link-skills.sh` (auto-discovers SKILL.md ใน `skills/`)
- **Cross-agent distribution**: `bash scripts/link-my-skills.sh` (Claude + Codex + Cline)

```bash
# Initial setup (already done)
git remote add anthropic-skills https://github.com/anthropics/skills.git
bash scripts/refresh-anthropic-skills.sh

# ใช้งาน
bash scripts/link-skills.sh
```

## Plugin Marketplace (alternative install)

```bash
# ไม่ต้องทำถ้ามีไฟล์ใน skills/anthropic-skills/ แล้ว
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Official Anthropic — คุณภาพสูง มี test coverage | source-available ไม่ใช่ fully open-source |
| Cross-agent: Claude, Codex, Cline ใช้ได้ | 4 document skills ต้องการ third-party tools (LibreOffice/WeasyPrint ฯลฯ) |
| document-skills ครอบคลุม Office suite ทั้งหมด | บาง example-skills ต้องการ MCP (preview, canvas) |
| SKILL.md format เดียวกับ A-Wiki | ต้อง refresh manual — ไม่มี auto-update |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[ecc]] — ECC 249 skills complement เพิ่ม language-specific workflows
- ใช้ร่วมกับ: [[9arm-skills]] — Thai language skills
- เกี่ยวข้องกับ: [[agents-md-spec]] — SKILL.md format standard
