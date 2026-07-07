---
type: concept
tags: [ai-tools, symlinks, ssot, multi-agent, claude-code, configuration]
sources: [ai-agents-integration-guide]
created: 2026-05-17
updated: 2026-07-06
last_verified: 2026-07-06
verify_tool: training
---

# Symlinks — Single Source of Truth สำหรับ Multi-Agent Config

## นิยาม

Symbolic Link (Symlink) คือ "ทางลัด" ระดับ OS ที่ชี้ไปยังไฟล์/โฟลเดอร์ต้นฉบับ เมื่อ AI อ่านไฟล์ผ่าน symlink จะได้เนื้อหาของต้นฉบับเสมอ — แก้ครั้งเดียว ทุก AI เห็นพร้อมกัน

## ทำไมถึงสำคัญกับ Multi-Agent Workflow

AI แต่ละตัวคาดหวัง config ไฟล์คนละชื่อคนละตำแหน่ง:

| AI Agent | Config file |
|----------|-------------|
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Cursor | `.cursorrules` |
| OpenAI Codex | `AGENTS.md` |

**ปัญหา**: ถ้า copy ไฟล์แยก → เนื้อหาแตกต่างกัน → AI แต่ละตัวมีกฎคนละชุด

**แนวทางแก้ด้วย Symlink**: เก็บ source of truth ไว้ที่เดียว (เช่น `.agents/AGENTS.md`) แล้ว symlink ไปทุก path ที่ AI ต้องการ

## วิธีการทำงาน

```python
import os
from pathlib import Path

# ไฟล์ต้นฉบับ (SSOT)
source = Path("/project/.agents/AGENTS.md")

# สร้าง symlink สำหรับแต่ละ AI
Path("/project/CLAUDE.md").symlink_to(source)
Path("/project/GEMINI.md").symlink_to(source)
Path("/project/.github/copilot-instructions.md").symlink_to(source)
```

ตรวจสอบ symlink ด้วย `ls -la` — จะเห็นลูกศร `->` ชี้ไปต้นฉบับ

## ตัวอย่างจาก InW-Wiki

wiki นี้มีไฟล์แยกตาม AI agent (`CLAUDE.md`, `GEMINI.md`, `AISTUDIO.md`, `AGENTS.md`) แต่ละไฟล์ใช้ schema เดียวกัน ถ้าต้องการ SSOT จริงๆ ให้ symlink ทุกไฟล์ไปที่ master config แล้วใช้ include/conditional section แทน

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| แก้ครั้งเดียว ทุก AI sync ทันที | บน Windows ต้องการ Developer Mode หรือ Admin rights |
| ไม่เกิด drift ระหว่าง agent configs | symlink ใน git repo ต้องระวัง — git ติดตาม symlink ไม่ใช่ target |
| ลดงานบำรุงรักษาในโปรเจกต์ multi-agent | ถ้า target ไฟล์หาย symlink กลายเป็น "broken link" |
| ทำงานได้ทันทีบน macOS/Linux | AI บางตัวอาจไม่รองรับ symlink ใน sandbox |

## ข้อควรระวังกับ Git

```bash
# Git track symlink เป็น text pointer ไม่ใช่ไฟล์จริง
git add CLAUDE.md    # บันทึก path ที่ symlink ชี้ไป
git ls-files -s CLAUDE.md  # mode 120000 = symlink
```

ถ้า repo ถูก clone ไปเครื่องอื่น symlink ยังอยู่แต่ต้องตรวจว่า target path ตรงกัน

## Universal Agent-Config Linker [verified 2026-07-06]

ปัญหาที่พบบ่อยกว่า config ไฟล์ (`CLAUDE.md`/`GEMINI.md`/ฯลฯ) คือ **skills + secrets ข้ามหลายเครื่อง**: ผู้ใช้ที่มี agent เดียวกัน (Claude Code, Codex, Hermes, ZCode, Kilo, Cline, Gemini, Antigravity, Windsurf, OpenClaw ฯลฯ) อยู่คนละเครื่อง (บ้าน/ที่ทำงาน/มือถือ) ต้องติดตั้ง skill และกรอก secret ซ้ำทุกครั้งที่ย้ายเครื่อง เพราะแต่ละ agent default ไปอ่านจาก local dir ของตัวเอง (`~/.claude`, `~/.hermes`, ...) ไม่ใช่จาก cloud

A-Wiki แก้ด้วย **hybrid source-of-truth**: skills (git repo, sync ข้ามเครื่องอยู่แล้ว) + secrets/`.env` (Google Drive ผ่าน `drive/` symlink) — ไม่เอา git repo ไปวางใน Drive เพราะ Google Drive for Desktop ไม่ sync/ตาม symlink ได้อย่างน่าเชื่อถือ symlink ต้องชี้**เข้า**ไปหา Drive mount เสมอ ไม่ใช่วางไว้*ใน* Drive แล้วหวังให้ sync ออกมา

**Implementation**: `scripts/link-agent-configs.sh` (auto-detect agent ที่ติดตั้งบนเครื่อง → link skills เข้า repo + `.env` เข้า Drive), เรียกอัตโนมัติจาก `scripts/setup-local.sh` ทุกเครื่องใหม่ ดูรายละเอียดเต็มที่ `agent-skills/extensibility/symlink-connector/SKILL.md`

## ความสัมพันธ์

- [[concepts/ai-tools/hooks-skills-plugins]] — symlinks ใช้ร่วมกับ hooks เพื่อให้ทุก AI เห็น hook config เดียวกัน
- [[concepts/ai-tools/multi-agent-failover]] — multi-agent workflow ที่ symlink ช่วยให้ config consistent ข้าม agents

## แหล่งข้อมูล

- [[sources/ai-agents-integration-guide]] — Section 1: Symbolic Links
