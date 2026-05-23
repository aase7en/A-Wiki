# A-Wiki — Multi-Agent Configuration (Claude / Codex / Gemini)

> **Single source of truth**: [`CLAUDE.md`](CLAUDE.md) — schema หลักของระบบ
> AGENTS.md สำหรับ agent-specific paths + delegation rules

---

## 🚫 Solo Wiki — Branch Rules (บังคับทุก agent)

> **commit ตรงลง `main` เท่านั้น** — ห้ามสร้าง branch, ห้ามเปิด PR, ห้าม worktree isolation

---

## 🚨 First action every session

1. Read `CLAUDE.md` (root) — Active Rules
2. Read `wiki/context/wiki-overview.md` — wiki stats + synthesis
3. Read `wiki/context/session-memory.md` — cross-session TODOs

---

## Agent-Specific Paths

| Concept | Claude Code | Codex / OpenAI | Gemini CLI |
|---------|-------------|----------------|------------|
| Config dir | `.claude/` | `.codex/` | `.gemini/` |
| Skills | `skills/claude-code/` | `skills/claude-code/` | `skills/claude-code/` |
| Thai skills | `skills/claude-thai/` | `skills/claude-thai/` | `skills/claude-thai/` |
| Ecosystem skills | `skills/ecosystem/` | `skills/ecosystem/` | `skills/ecosystem/` |
| Agent skills (swarm) | `agent-skills/` | `agent-skills/` | `agent-skills/` |
| Scripts (wiki) | `scripts/wiki/` | `scripts/wiki/` | `scripts/wiki/` |
| Scripts (swarm) | `scripts/swarm/` | `scripts/swarm/` | `scripts/swarm/` |
| Hooks | `.claude/hooks/` | `.codex/hooks/` | `.gemini/hooks/` |

---

## 🧠 Swarm Roles (Optional — สำหรับ OpenRouter multi-model)

| Role | Model | Tool | Responsibility |
|------|-------|------|----------------|
| **Architect** | OpenRouter free reasoning/CoT | `scripts/swarm/delegate.sh` | Planning, root cause, design |
| **Executioner** | OpenRouter free flash/coder | `scripts/swarm/delegate.sh` | Code writing, tests, refactoring |
| **Senior Critic** | Primary Agent (you) | — | Validate ALL outputs — NOT delegatable |

**Trigger**: `bash scripts/swarm/delegate.sh architect "query"` หรือ `bash scripts/swarm/delegate.sh executioner "task"`

---

## 🛡️ Hooks Config

Hooks เหมือนกันทุก agent — ใช้ Python hook runner `scripts/hooks_runner.py`

```
.claude/hooks/   ← Claude hooks (primary)
.codex/hooks/    ← Codex hooks (symlink to .claude/hooks/)
.gemini/hooks/   ← Gemini hooks (symlink to .claude/hooks/)
```

---

## 🐍 Scripts Index

| Script Path | Function |
|-------------|----------|
| `scripts/wiki/gen-index.py` | Regen wiki overviews + FTS5 + graph + canvas |
| `scripts/wiki/search-wiki.py "query"` | Local FTS5 search (Level -1) |
| `scripts/wiki/ask-notebooklm.py --domain X` | Cross-file synthesis via Gemini API |
| `scripts/wiki/query-graph.py --hubs` | Knowledge graph queries |
| `scripts/swarm/agent-switch.sh` | Switch agent mid-session |
| `scripts/swarm/delegate.sh` | Delegate to subagent / OpenRouter |
| `scripts/ecosystem/link-my-skills.sh` | Symlink ecosystem skills |

---

## ❌ Do NOT Delegate (Primary Agent ONLY)

- Reasoning ลึก / decision making
- การเขียน wiki entity/concept ใหม่
- การแก้ CLAUDE.md หรือ AGENTS.md
- งาน sensitive (security review, schema edits)

---

*Last updated: 2026-05-24 — A-Wiki Hybrid v1.0*