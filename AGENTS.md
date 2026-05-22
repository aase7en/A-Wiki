# Project Instructions — All AI Agents

## 🚫 Solo Wiki — No Branch, No PR

> Wiki นี้มีผู้ใช้คนเดียว — ห้ามสร้าง branch, ห้ามเปิด PR, ห้ามใช้ worktree isolation
> **commit ตรงลง `main` เท่านั้น**

## 🚨 First action every session

1. Read `CLAUDE.md` (ถ้ามี) หรือ `README.md`
2. Read `wiki/context/wiki-overview.md` — context ปัจจุบันของ wiki (ถ้ามี)
3. Read `.local/profile.md` — ข้อมูลเจ้าของ (ถ้ามี, ผ่าน GDrive sync)

## Path conventions per agent

| Concept | Claude Code | Codex / OpenAI |
|---------|-------------|----------------|
| Config dir | `.claude/` | `.codex/` |
| Skills | `.claude/skills/` (symlinked via link-skills.sh) | `.agents/skills/` |