---
type: entity
category: tool
tags: [react, nextjs, static-analysis, code-quality, ci, claude-skill]
sources: [github-react-doctor]
created: 2026-05-28
updated: 2026-05-28
last_verified: 2026-05-28
verify_tool: WebFetch
---

# react-doctor

**ประเภท**: React static-analysis CLI + Claude Code skill
**สถานะ**: optional install via `scripts/setup-local.sh` (`INSTALL_REACT_DOCTOR=1`)
**License**: MIT

## ภาพรวม

react-doctor scan codebase React (Next.js, Vite, TanStack, RN, Expo) → detect issues ใน **state & effects, performance, architecture, security, accessibility** แบบ deterministic (ไม่ใช่ LLM-based) — ใช้ CLI หรือผูกเป็น Claude Code skill ให้ agent เรียกใช้ตอน implement frontend

## คุณสมบัติหลัก

- **Quick audit**: `npx react-doctor@latest`
- **Agent skill**: `npx react-doctor@latest install` → register ใน `~/.claude/skills/`
- **CI/CD**: GitHub Actions + inline PR annotations
- **Framework**: Next.js, Vite, TanStack, React Native, Expo ทุก React framework

## การใช้งานใน A-Wiki

**A-Wiki ตัวเองไม่มี React** (Python + shell + markdown) → tool นี้ **benefit dream projects** เป็นหลัก:

| Dream project | Stack | Benefit |
|---------------|-------|---------|
| Sunday Estate webapp | Next.js (probable) | state/effects audit, security, perf |
| Pharmacy App | TBD (อาจเป็น React Native + Expo) | mobile patterns |
| IoT Dashboard | TBD | dashboard component review |

**Setup เป็น Claude Code skill ระดับ global** → ทุก session ที่เปิด React project จะมี skill นี้ใช้ได้

## Setup

```bash
INSTALL_REACT_DOCTOR=1 bash scripts/setup-local.sh
# หรือ standalone:
npx react-doctor@latest install
```

ตรวจ:
```bash
ls ~/.claude/skills/ | grep react-doctor
```

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Deterministic (ไม่ flaky เหมือน LLM lint) | ครอบคลุมแค่ React ecosystem |
| ทุก React framework | ต้อง Node.js + npx |
| CI/CD integration พร้อมใช้ | A-Wiki ตัวเองไม่ได้ใช้ |
| Free + MIT | static — ไม่จับ runtime bug |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[claude-skills]] — Claude Code skill system
- เกี่ยวข้องกับ: `private-webapp`, `pharmacy-app`, `iot-dashboard` (dream projects)
- เปรียบเทียบกับ: ESLint, Biome — แต่ react-doctor scope แคบ+ลึกกว่า

## แหล่งข้อมูล

- GitHub: https://github.com/millionco/react-doctor
- npm: `npx react-doctor@latest`
- [verified 2026-05-28] WebFetch — 11.3k stars, TypeScript 99.2%
