---
type: source
title: "คู่มือการบูรณาการ AI Agents ขั้นสูง: Symlink, Hooks, Skills, Plugins และ NotebookLM"
slug: ai-agents-integration-guide
date_ingested: 2026-05-17
original_file: paste-text
tags: [ai-tools, claude-code, hooks, skills, plugins, symlinks, notebooklm]
---

# คู่มือการบูรณาการ AI Agents ขั้นสูง

**ประเภท**: article (guide)
**วันที่**: unknown
**ผู้เขียน**: unknown

## ประเด็นหลัก

1. **Symlinks เป็น SSOT** — ใช้ symbolic link ให้ AI หลายตัว (Claude Code, Copilot, Cursor) อ่าน config ไฟล์เดียวกัน แทนการ copy ซ้ำ
2. **Hooks = การควบคุมเชิงรับ** — สคริปต์ที่รันอัตโนมัติตาม lifecycle events (PreToolUse, PostToolUse) โดย AI ไม่รู้ตัว ตัวอย่าง: auto-format ด้วย prettier หลัง Edit
3. **Skills = การขยายความสามารถเชิงรุก** — แพ็กเกจ `SKILL.md` ที่ AI ดึงมาปฏิบัติเมื่อ description ตรงกับความต้องการ ตัวอย่าง: `review-pr`
4. **Plugins = ตำราอาหารรวม** — รวม Skills + Hooks + MCP Servers ไว้ใน `plugin.json` manifest เพื่อแชร์และติดตั้งได้ง่าย
5. **notebooklm-py** — ไลบรารี Python (`pip install "notebooklm-py[browser]"`) ที่ใช้ Playwright ควบคุม NotebookLM ผ่าน API เพื่อ automate RAG pipeline
6. ~~Claude Code + OpenAI Codex~~ — ⚠️ **ข้อมูลผิด** ดู §ข้อโต้แย้ง

## ข้อมูลที่น่าสนใจ

- Symlinks บน macOS/Linux: `os.symlink(src, dst)` หรือ `Path(dst).symlink_to(src)` ผ่าน Python
- บน Windows ต้องการ Developer Mode หรือสิทธิ์ Admin
- Hooks สามารถเขียนเป็น Python แทน Bash ได้ เพื่อ error handling ที่ซับซ้อน (เช่น block access ไฟล์ `.env`)
- SKILL.md frontmatter ต้องการ `name` และ `description` — AI ใช้ description ในการตัดสินใจเรียก skill
- notebooklm-py ต้อง login Google ครั้งแรกด้วย `notebooklm login` ก่อนใช้งาน

## ข้อโต้แย้งหรือความขัดแย้ง

⚠️ **Section 6 เป็น hallucinated content — ห้ามใช้**

คู่มือกล่าวว่า Claude Code มี plugin marketplace จาก OpenAI และ command เหล่านี้:
- `/plugin marketplace add openai/codex-plugin-cc`
- `/plugin install codex@openai-codex`
- `/reload-plugins`, `/codex:rescue`, `/codex:review`

**ข้อเท็จจริง** [training]: Claude Code ไม่มี plugin marketplace จาก OpenAI ไม่มี `/plugin` commands เหล่านี้ ไม่มีการ integrate กับ OpenAI Codex ผ่าน slash commands ข้อมูลทั้ง Section 6 ไม่มีอยู่จริง อย่านำไปใช้

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/ai-tools/hooks-skills-plugins]] — สร้างใหม่จาก Section 2-4
- [[concepts/ai-tools/symlinks-ssot]] — สร้างใหม่จาก Section 1
