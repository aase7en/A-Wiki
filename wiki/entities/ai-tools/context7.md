---
type: entity
category: tool
title: "Context7 (upstash)"
tags: [mcp, documentation, knowledge-currency, developer-tools, candidate]
sources: [charliejhills-claude-skills-org-chart-2026]
created: 2026-07-13
updated: 2026-07-13
last_verified: 2026-07-13
verify_tool: WebFetch
---

# Context7 (upstash/context7)

**ประเภท**: MCP server + CLI — ส่ง documentation สด version-specific เข้า LLM prompt
**สถานะ**: ✅ **ติดตั้งได้แล้ว — `--context7` flag ใน `scripts/setup-optional-mcp.sh`** (opt-in, ยังไม่ auto-install; ต้องมี `CONTEXT7_API_KEY` ของผู้ใช้เอง — hosted MCP ไม่ใช่ local/free แบบ gitnexus/graphify)
**License**: open-source (Upstash) · 59k★ [verified 2026-07-13]

## ภาพรวม

แก้ปัญหา LLM ใช้ API ผิด version / hallucinate library docs — ดึงเอกสาร + code examples ปัจจุบันของ library ที่ใช้จริงเข้า prompt ตรง ๆ มีทั้งโหมด MCP และ CLI [verified 2026-07-13]

## ตำแหน่งใน A-Wiki

- **Gap ที่เติม**: A-Wiki มี [[entities/ai-tools/gitnexus]] (code graph ของ repo ตัวเอง) + `knowledge-currency` protocol (กัน stale claims ใน wiki) แต่**ไม่มีชั้น live library docs** สำหรับตอนเขียนโค้ดจริง
- **Cost-first**: ลด loop "เขียนผิด API → รัน error → แก้ใหม่" = ลด token มากกว่าที่ MCP call กิน — เข้าเกณฑ์ gate "automation เบาลงจริง"
- ใช้จังหวะ implement เว็บ/เกม: Phaser 3 / Vite / Tailwind docs สดใน [[synthesis/game-lightweight-highend-capability-hub]] + [[synthesis/design-web-capability-hub]]
- แนวติดตั้ง: เพิ่ม flag `--context7` ใน `scripts/setup-optional-mcp.sh` — ไม่ auto-install

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/ai-tools/gitnexus]] — คนละแกน (repo graph vs library docs)
- เสริม: `docs/protocols/knowledge-currency.md`
- เกี่ยวข้องกับ: [[synthesis/claude-skills-gap-web-game-2026]]

## แหล่งข้อมูล

- GitHub: https://github.com/upstash/context7
- [[sources/charliejhills-claude-skills-org-chart-2026]]
- [verified 2026-07-13] WebFetch — 59k★, MCP/CLI modes
