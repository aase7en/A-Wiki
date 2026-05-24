# Getting Started with A-Wiki

## Prerequisites

| Dependency | Why | Check |
|---|---|---|
| **Git** (2.30+) | Direct-to-main workflow | `git --version` |
| **Node.js** (18+) | Automation hooks, graph builders | `node --version` |
| **Python** (3.10+) | Wiki scripts, search, embeddings | `python3 --version` |
| **AI Client** | Claude Code CLI, Cline (VS Code), or Codex CLI | `claude --version` or check VS Code extensions |

> **Windows users:** All shell scripts require **Git Bash** (ships with Git for Windows).

---

## 🚀 3-Step Onboarding

### Step 1: Clone & Enter

```bash
git clone https://github.com/aase7en/A-Wiki.git
cd A-Wiki
```

This is a **solo wiki** — commit directly to `main`. No branches. No PRs. No ceremony.

### Step 2: Run Pre-Flight Checks

```bash
bash agent-skills/automations/run-task.sh pre-flight
```

Validates:
- ✅ Git configured, on `main` branch
- ✅ No uncommitted drift from remote
- ✅ Iron Law hooks active
- ✅ Required directories exist

### Step 3: Connect the Global Nervous System

```bash
bash scripts/link-my-skills.sh
```

Symlinks all agent skills into your global AI environments:

| Agent | Symlink Target | Purpose |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | Auto-loaded every Claude session |
| **Cline / Roo** | `~/.cline/skills/` | Available in VS Code Cline extension |
| **Codex / OpenAI** | `~/.codex/skills/` | Available in Codex CLI |

> `bash scripts/link-my-skills.sh --list` to preview before activating.

---

## 📁 Folder Structure

| Path | Contents | Git? |
|------|----------|------|
| `wiki/` | Knowledge pages (sources, synthesis, concepts, entities) | ✅ |
| `skills/` | Agent skill definitions | ✅ |
| `agent-skills/` | Active skill layer (swarm brain) | ✅ |
| `scripts/` | Utility scripts (wiki, swarm, ecosystem) | ✅ |
| `docs/` | Protocols, guides, runbooks | ✅ |
| `core-knowledge/` | Safeguarded archive (read-only) | ✅ |
| `raw/` | Source documents (symlinked to Google Drive) | ❌ |
| `.local/` | Profile, secrets, session memory | ❌ |
| `exports/` | NotebookLM bundles | ❌ |
| `log.md` | Wiki edit history | ❌ |
| `session-memory.md` | Cross-session context | ❌ |

---

## 🧠 Daily Workflow

### Ingesting New Knowledge

1. Place raw file (markdown, PDF, or text) into `raw/` (Google Drive symlink)
2. Run the conversion pipeline:
   ```bash
   # Convert raw/ → wiki/sources/ (standardised frontmatter)
   python3 scripts/wiki/raw-to-source.py

   # Generate synthesis stubs for uncovered sources
   python3 scripts/wiki/raw-to-synth.py

   # Regenerate indexes and knowledge graph
   python3 scripts/wiki/gen-index.py
   ```
3. Use the `ingest-source` skill to create proper synthesis pages from stubs

### Searching the Wiki

```bash
# FTS5 keyword search (fast, offline)
python3 scripts/wiki/search-wiki.py "ESP32 LoRa power consumption"

# Cross-file synthesis via Gemini API (deep analysis)
python3 scripts/wiki/ask-notebooklm.py --domain iot --query "Compare LoRa vs WiFi for sensor networks"

# Query the knowledge graph
python3 scripts/wiki/query-graph.py --hubs
```

### Quick Commands for AI Agents

| Command | Action |
|---------|--------|
| `/search <query>` | Local FTS5 wiki search |
| `/lint` | Wiki health check (frontmatter, broken links) |
| `/snapshot-nb [domain]` | Export domain for NotebookLM |
| `/compact` | Reduce context mid-session |

---

## 🛡️ The Iron Laws

| # | Law | Enforced By |
|---|-----|-------------|
| **I** | NO production code without a FAILING TEST first | `scrutinize` skill |
| **II** | NO bug fixing without ROOT CAUSE first | `debug-mantra` skill |
| **III** | Parallel agent violating #1 or #2 → DISCARD & REWRITE | Primary Agent |

> *"Discipline is not optional. Automation without verification is just faster chaos."*

---

## 🧪 Sanity Check

```bash
# 1. Confirm pre-flight passes
bash agent-skills/automations/run-task.sh pre-flight

# 2. List all linked skills
bash scripts/link-my-skills.sh --list

# 3. Verify Iron Law enforcement (test-driven cycle)
cd test-zone
python -m pytest test_greet.py -v
```

---

## 🔗 Quick Links

| Resource | Link |
|---|---|
| README (full onboarding) | [README.md](../../README.md) |
| Agent instruction manifest | [AGENTS.md](../../AGENTS.md) |
| Session rules | [CLAUDE.md](../../CLAUDE.md) |
| Architecture overview | [docs/architecture.md](../architecture.md) |
| Protocols | [docs/protocols/](../protocols/) |
| Runbooks | [docs/runbooks/](../runbooks/) |

---

## 📜 License

MIT © 2025-2026 — See [LICENSE](../../LICENSE).

> **Commit directly to main. No branches. No PRs. Just discipline.**