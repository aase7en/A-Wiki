---
type: entity
category: tool
title: "Claude-Mem (thedotmack)"
tags: [claude-skills, memory, second-brain, hooks, candidate]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-13
updated: 2026-07-13
last_verified: 2026-07-13
verify_tool: WebFetch
---

# Claude-Mem (thedotmack/claude-mem)

**ประเภท**: Persistent memory system สำหรับ AI agents (lifecycle hooks + SQLite + vector search)
**สถานะ**: **candidate — ประเมินก่อน ไม่ auto-install** (ทับซ้อนปรัชญากับ memory เดิมของ A-Wiki)
**License**: Apache-2.0 · ผู้ดูแล: Alex Newman (@thedotmack) · 87k★ [verified 2026-07-13]

## ภาพรวม

Capture ทุกอย่างที่ agent ทำระหว่าง session → compress ด้วย AI → inject context ที่เกี่ยวข้องกลับเข้า session ถัดไปอัตโนมัติ ผ่าน lifecycle hooks ของ Claude Code [verified 2026-07-13]

- เก็บใน SQLite + vector search; ค้นแบบ full-text + semantic
- Multi-agent: Claude Code, OpenClaw, Codex, Gemini, Copilot
- Privacy: `<private>` tags กันเนื้อหาไม่ให้เข้า memory
- ติดตั้ง: `npx claude-mem install`

## ตำแหน่งใน A-Wiki — ทำไมต้อง "ประเมินก่อน"

| มุม | A-Wiki เดิม | claude-mem |
|---|---|---|
| ปรัชญา | **explicit curation** — session-memory.md + wiki + log.md เลือกเองว่าจำอะไร | **auto-capture ทุกอย่าง** แล้วให้ AI compress |
| Storage | Markdown tracked/gitignored + FTS5/sqlite-vec | SQLite DB นอก git |
| ความเสี่ยง | ควบคุม public-safe ได้ตรง ๆ | private data ไหลเข้า DB อัตโนมัติ — ขัด External Data Layer policy ถ้าไม่ config ดี |

ข้อสรุป gap analysis: ถ้าจะลอง ให้ปฏิบัติแบบ [[entities/ai-tools/gbrain]] — tool-shaped, opt-in ผ่าน `setup-optional-mcp.sh` pattern, sandbox ก่อน ไม่ผูกกับ hooks จริงจนกว่าจะผ่าน [Brain Improvement Gate]

## การตัดสินใจ (2026-07-13)

**ไม่ adopt ตอนนี้** — `npx claude-mem install` แก้ lifecycle-hook config ระดับ global (นอก repo scope นี้), ยากต่อการ revert, และเสี่ยง auto-capture ข้อมูลส่วนตัวเข้า SQLite ตรงตามที่ตารางด้านบนเตือนไว้ — เกินขอบเขตความเสี่ยงที่ควรทำแบบไม่มีใครกำกับ (unattended session)

- session-memory.md + wiki + gbrain (opt-in) ครอบคลุม memory-layer need อยู่แล้วในปรัชญา explicit-curation
- จะกลับมาพิจารณาใหม่ก็ต่อเมื่อมี gap เจาะจงที่ 2 ระบบเดิมตอบไม่ได้จริง
- ถ้าทดลองในอนาคต: ต้องผ่าน Brain Improvement Gate + sandbox ก่อน (แบบ gbrain) ห้ามผูก global hooks ตรง ๆ

## ความสัมพันธ์

- แข่งขันกับ: [[entities/ai-tools/gbrain]] (memory/synthesis layer, PGLite) — เทียบกันก่อนเลือก
- ทับซ้อน: `wiki/context/session-memory.md` + hooks #10/#16 ของ A-Wiki
- เกี่ยวข้องกับ: [[synthesis/claude-skills-gap-web-game-2026]]

## แหล่งข้อมูล

- GitHub: https://github.com/thedotmack/claude-mem
- [[sources/charliejhills-claude-skills-org-chart-2026]]
- [verified 2026-07-13] WebFetch — 87k★, Apache-2.0, feature set
