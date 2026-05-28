---
type: entity
category: tool
tags: [claude-code, plugin, skills, agents, ecosystem, harness-optimization]
sources: [github-ecc]
created: 2026-05-28
updated: 2026-05-28
last_verified: 2026-05-28
verify_tool: WebFetch
---

# ECC — Everything Claude Code

**ประเภท**: Claude Code plugin + skill ecosystem
**สถานะ**: integrated at `skills/ecosystem/` (232 dirs) — upstream remote `ecc` added
**License**: open

## ภาพรวม

ECC = open-source plugin/framework optimize agent workflow across หลาย harness (Claude Code, Cursor, OpenCode, Codex, Gemini, Zed, GitHub Copilot) — เน้น **harness performance** ไม่ใช่แค่ skill collection ปกติ: coordinate skills + memory persistence + security + quality gates

## คุณสมบัติหลัก

| Component | Count | Role |
|-----------|------:|------|
| **Agents** | 63 | Subagents (code review, build fix, security audit, lang-specific) |
| **Skills** | 249 | Workflows by domain (backend, frontend, TDD, security, ML ops) |
| **Legacy Commands** | 79 | Slash-entry compat during migration |
| **Rule Sets** | 34 | Always-follow guidelines (lang-agnostic + lang-specific) |
| **Hooks** | many | Session lifecycle, memory, compaction, pattern extraction |

**12+ language ecosystems**: TypeScript, Python, Go, Java, Kotlin, C++, Rust, PHP, Swift, Ruby, etc.

## การใช้งานใน A-Wiki

- **skills/ecosystem/** — 232 subdirs (subset ของ 249 skills, +agents จาก ECC)
- **Refresh upstream**: `bash scripts/refresh-ecosystem.sh` — pull จาก ECC remote ผ่าน `git fetch ecc && git checkout ecc/main -- skills/...` (safer than subtree-add over existing path)
- **Rule sets** — A-Wiki ยังไม่ load 34 rule sets (manual; rules ไม่ distribute ผ่าน plugin spec ปัจจุบัน) — ตัดสินใจรายตัวว่าตัวไหนเข้ากับ Iron Laws

## Setup

A-Wiki ทำเสร็จแล้ว (`skills/ecosystem/` bulk-copied):
```bash
# Refresh
git remote add ecc https://github.com/affaan-m/ECC.git   # ครั้งแรก
bash scripts/refresh-ecosystem.sh
```

หรือ install standalone ใน Claude Code:
```bash
/plugin install ecc@ecc
```

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| 249 skills + 63 agents — ครอบคลุมมาก | 232 dirs ใน A-Wiki ใหญ่ — โหลดเลือกตาม domain |
| Battle-tested 10+ months daily | บาง skill ขัด Iron Laws → ต้อง review ก่อน enable |
| Cross-harness (Claude, Cursor, Codex, Gemini) | rule sets manual install |
| Treats harness as first-class optim target | bulk-copy แทน subtree → refresh ต้องระวัง conflict |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[9arm-skills]] — engineering skills overlap (debug, code review) แต่ ECC ครอบคลุมกว่า
- ใช้ร่วมกับ: [[claude-thai-skills]] — Thai skills (orthogonal scope)
- เกี่ยวข้องกับ: [[agents-md-spec]] — ECC follow spec
- ใช้ร่วมกับ: [[claude-skills]] — Claude Code skill system

## แหล่งข้อมูล

- GitHub: https://github.com/affaan-m/ECC
- Author: affaan-m (10+ months daily dogfood)
- [verified 2026-05-28] WebFetch
