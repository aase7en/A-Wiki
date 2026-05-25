<!--
================================================================================
            █████╗     ██╗    ██╗██╗██╗  ██╗██╗
           ██╔══██╗    ██║    ██║██║██║ ██╔╝██║
           ███████║    ██║ █╗ ██║██║█████╔╝ ██║
           ██╔══██║    ██║███╗██║██║██╔═██╗ ██║
           ██║  ██║    ╚███╔███╔╝██║██║  ██╗██║
           ╚═╝  ╚═╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚═╝
     Autonomous AI Agent Swarm — Solo Wiki with Iron-Law Discipline
================================================================================
-->

# A-Wiki — The AI Operating System That Ships

**A-Wiki doesn't give your AI Agent a "better prompt." It gives it a spine.**

> Most AI coding assistants behave like a caffeinated junior dev on the last day of a sprint — rushing, patching symptoms, and burning your token budget on boilerplate.
>
> **A-Wiki transforms that same agent into a meticulous, cost-efficient Senior Software Architect** — one that scouts for zero-cost compute, enforces True TDD with religious conviction, carries context across every device you own, and works with every AI tool you already pay for.

---

## ⚡ Four Superpowers. One Repository.

| Superpower | What It Does | Your Win |
|---|---|---|
| **🌐 Works With Every AI Tool** | One config file per platform — Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Cline, GitHub Copilot, Aider, and any tool that reads `AGENTS.md`. Your brain is platform-agnostic. | **No lock-in.** Switch AI tools or run them in parallel — they all share the same Iron Laws, wiki, and swarm protocol. |
| **🔍 Dynamic Token Scouting** | Auto-hunts OpenRouter Free tier and promotional endpoints at runtime via `update-model-roster.sh` — routing boilerplate work to free models and reserving expensive tokens for reasoning that actually matters. | **Massive cost reduction.** You pay for thinking, not for generating getters and setters. |
| **🛡️ Iron Law Process Enforcement** | Hard-blocks any code path that tries to commit production code without a failing test first. Blocks any bug fix that hasn't completed root-cause analysis. If a parallel swarm model violates either rule, its output is **discarded and rewritten** on sight. | **Zero technical debt injection.** The kind of discipline you'd expect from a principal engineer doing code review at 2 AM. |
| **🧠 Cross-Device Knowledge Brain** | A 420+ page structured wiki (entities, concepts, synthesis, sources) with offline FTS5 search, knowledge graph, and auto-synced session memory via Google Drive — so your AI picks up exactly where you left off on any machine. | **True continuity.** Walk away from any machine. Resume on any other. Your agent already knows exactly where you stopped. |

---

## 🛡️ The Iron Laws

These are **not** guidelines. They are unbreachable execution boundaries enforced by the Primary Agent (Senior Critic). Violations trigger **immediate discard and rewrite**.

| # | Iron Law | Enforced By |
|---|----------|-------------|
| **I** | **NO production code without a FAILING TEST first.** True TDD. If the test passes before the code is written, you are testing the test — not the code. | `scrutinize` skill |
| **II** | **NO bug fixing without ROOT CAUSE INVESTIGATION first.** You will reproduce, trace, falsify, and cross-reference before touching a single line. Superficial patching is forbidden. | `debug-mantra` skill |
| **III** | **If a parallel agent or secondary model violates Iron Law I or II, its output MUST be discarded and rewritten by the Primary Agent.** No exceptions. No "merge anyway." | Primary Agent (Senior Critic) |
| **IV** | **`raw/` is immutable.** Source documents are never edited or deleted — they are archived forever and summarized into `wiki/`. | Hook: `check_raw_immutable.py` |

> *"Discipline is not optional. Automation without verification is just faster chaos."*

---

## 📦 Prerequisites

Before onboarding, your machine must have:

| Dependency | Why | Check |
|---|---|---|
| **Git** (2.30+) | Version control, direct-to-main workflow | `git --version` |
| **Git Bash** | Required for Windows users running shell scripts | Bundled with Git for Windows |
| **Python** (3.8+) | Wiki index, search, hooks, model scouting | `python --version` |
| **Node.js** (18+) | MCP servers (filesystem, sequential-thinking) | `node --version` |
| **AI Client** | At least one from the Platform Support table below | see table |

> **Windows:** All shell scripts use Bash. Use **Git Bash** (not PowerShell, not CMD).
> **Google Drive (optional):** Mount at `L:\My Drive\A-Wiki-Data\` (Windows) or `~/Library/CloudStorage/` (Mac) for raw source sync and API key storage.

---

## 🚀 3-Step Quick Start

### Step 1: Clone

```bash
git clone https://github.com/aase7en/A-Wiki.git
cd A-Wiki
```

This is a **solo wiki** — commit directly to `main`. No branches, no pull requests, no ceremony.

### Step 2: Run Setup (once per machine)

```bash
bash scripts/setup-local.sh
```

This single command does everything:

| Sub-step | What Happens |
|---|---|
| **[1/5] raw/ link** | Creates symlink (Mac) or junction (Windows) pointing to Google Drive raw sources |
| **[2/5] .mcp.json** | Generates from `.mcp.json.example` with your machine's correct paths |
| **[3/5] API keys** | Reads `L:\My Drive\A-Wiki-Data\.secrets` → injects into `.claude/settings.local.json` |
| **[4/5] Wiki index** | Builds SQLite FTS5 search index from all 420+ wiki pages |
| **[5/5] .codex/ hooks** | Links `.codex/hooks/` → `.claude/hooks/` so Codex uses the same enforcement hooks |

#### Optional: Local Semantic Search (sqlite-vec + fastembed)

Adds embedding-based search alongside FTS5 — same `.wiki-index.db`, hybrid query via [scripts/wiki/query-rag.py](scripts/wiki/query-rag.py). Pure offline once the model is cached. Cross-platform (macOS / Linux / Windows wheels).

```bash
pip install -r requirements.txt          # sqlite-vec, fastembed, apsw
python scripts/build-vec-index.py        # ~80MB model + ~30s embed on first run
python scripts/wiki/query-rag.py "mqtt vs lorawan"
```

> **macOS note:** if `pip install` succeeded but `build-vec-index.py` fails with an extension-loading error, your Python is from Apple's system or a python.org build with `--disable-loadable-sqlite-extensions`. The `apsw` package bypasses that and is already in `requirements.txt` — re-run `pip install -r requirements.txt`. If it still fails, install Python via Homebrew (`brew install python@3.12`) or pyenv.

> **Google Drive `.secrets` file format** (create once, syncs to all your machines):
> ```
> export OPENROUTER_API_KEY=sk-or-...
> export GROQ_API_KEY=gsk_...
> export GOOGLE_AI_STUDIO_KEY=AIza...
> export DEEPSEEK_API_KEY=sk-...
> ```

### Step 3: Open Any AI Tool — Brain Is Ready

Open your preferred AI client in the repo directory. The brain loads automatically:

- **Claude Code / Cline / Cursor / Windsurf** → reads the config file for your platform
- **Gemini CLI** → reads `GEMINI.md`
- **Codex** → reads `AGENTS.md`
- **All platforms** → Iron Laws, Cost Pyramid, Swarm Protocol, Wiki access

---

## 🌐 Platform Support

A-Wiki works out-of-the-box with **9+ AI platforms**. Each reads a dedicated config file — no setup required beyond `git clone` + `setup-local.sh`.

| Platform | Config File | Description |
|---|---|---|
| **Claude Code** (Anthropic) | [`CLAUDE.md`](CLAUDE.md) | Full config: hooks, /commands, session protocol |
| **OpenAI Codex** | [`AGENTS.md`](AGENTS.md) | Universal master brain |
| **Gemini CLI** (Google) | [`GEMINI.md`](GEMINI.md) | Gemini-specific + model roster pointer |
| **Cursor** (Microsoft) | [`.cursorrules`](.cursorrules) | Coding rules + Cost Pyramid |
| **Windsurf** (Codeium) | [`.windsurfrules`](.windsurfrules) | Same as Cursor rules |
| **Cline** (VSCode ext.) | [`.clinerules`](.clinerules) | Full brain context for Cline |
| **GitHub Copilot** | [`.github/copilot-instructions.md`](.github/copilot-instructions.md) | Core rules + AGENTS.md |
| **Aider** (terminal) | [`.aider.conf.yml`](.aider.conf.yml) | `read: [AGENTS.md]` directive |
| **Jules / Devin / Zed / Warp** | [`AGENTS.md`](AGENTS.md) | Industry standard — auto-detected |

> **The hierarchy**: `AGENTS.md` = universal brain shared by most platforms. `CLAUDE.md` / `GEMINI.md` = platform-specific extensions that add tool-specific commands on top.

---

## 🧠 Wiki Brain

The `wiki/` directory is a structured knowledge base maintained entirely by AI agents — no manual editing required.

| Metric | Value |
|---|---|
| **Total pages** | 420+ |
| **Domains** | IoT, Environmental Health, AI Tools, Pharmacy |
| **Page types** | Entities, Concepts, Sources, Synthesis |
| **Search** | SQLite FTS5 (offline, instant) |
| **Graph** | Knowledge graph with hub detection |

### Wiki Commands

```bash
# Search wiki (Level -1: free, offline, no API required)
python scripts/search-wiki.py "MQTT broker"

# Find hub pages (most connected knowledge nodes)
python scripts/query-graph.py --hubs

# Rebuild index after editing wiki pages
python scripts/gen-index.py
```

### Dynamic Model Roster

Model availability changes daily — free models become paid, new ones appear, old ones get deprecated. A-Wiki never hardcodes model names.

```bash
# Refresh the free model roster from OpenRouter API
bash scripts/update-model-roster.sh

# See current free models
cat wiki/context/model-roster.conf

# Route a task to the best available free model
bash scripts/swarm/delegate.sh "summarize this module"
```

---

## 🤖 Daily Workflow — How to Operate with the Swarm

Once onboarded, your AI agent is a disciplined swarm. Here's how you direct it:

### 🏗️ Designing a Feature? Invoke `scrutinize`.

```
"Before we write any code, scrutinize this plan."
```

The agent will:
1. Question whether the feature should exist at all
2. Trace every proposed code path end-to-end
3. **Refuse to proceed** if no failing test exists first (Iron Law I)

### 🐛 Caught a Bug? Enforce `debug-mantra`.

```
"This is a bug report. Apply debug-mantra before proposing anything."
```

The agent will **not** suggest a fix. It will instead:
1. Reproduce the bug deterministically
2. Trace the fail path with a debugger or instrumentation
3. Generate 3-5 falsifiable hypotheses and try to **disprove** each
4. Cross-reference experiments against a running breadcrumb ledger

Only after all four steps pass does it present a root cause and a fix.

### 📊 Summarizing for Leadership? Use `management-talk`.

```
"Translate this incident report into management-talk for a JIRA comment."
```

Strips function names, file paths, and code identifiers — rewrites everything in plain-English cause-and-effect.

### 🔍 Want to Scout for Free Compute?

```bash
bash scripts/update-model-roster.sh
cat wiki/context/model-roster.conf
```

Queries OpenRouter's free tier and produces a ranked allocation recommendation — Architect role, Executioner role, race models.

---

## 🗺️ Repository Architecture

```
A-Wiki/
│
├── AGENTS.md                    ← Universal brain (20+ AI platforms)
├── CLAUDE.md                    ← Claude Code edition
├── GEMINI.md                    ← Gemini CLI edition
├── .cursorrules                 ← Cursor
├── .windsurfrules               ← Windsurf
├── .clinerules                  ← Cline (VSCode extension)
├── .github/copilot-instructions.md  ← GitHub Copilot
├── .aider.conf.yml              ← Aider
│
├── wiki/                        ← CORE KNOWLEDGE (420+ pages)
│   ├── context/                 ← ⚡ Fast-load overviews + session memory
│   ├── entities/{iot,env,ai-tools,pharmacy}/
│   ├── concepts/{iot,env,ai-tools,pharmacy}/
│   ├── sources/                 ← Source summaries
│   └── synthesis/               ← Cross-domain analysis
│
├── agent-skills/                ← ACTIVE LAYER — Swarm Brain
│   ├── engineering/             ← debug-mantra, scrutinize, post-mortem
│   ├── productivity/            ← management-talk
│   ├── swarm-intelligence/      ← model-scouter, agile-swarm
│   ├── infrastructure/          ← git-safety protocol
│   └── automations/             ← hooks, run-task.sh
│
├── skills/                      ← Ecosystem skills
│   ├── claude-code/             ← InW-Wiki skills (ingest-source, lint-wiki)
│   ├── claude-thai/             ← Thai language skills (fuzzy-search, thai-ocr)
│   └── ecosystem/               ← ECC skills (everything-claude-code)
│
├── scripts/                     ← Automation
│   ├── setup-local.sh           ← First-time machine setup (run once)
│   ├── search-wiki.py           ← FTS5 wiki search
│   ├── update-model-roster.sh   ← Dynamic free model discovery
│   └── swarm/delegate.sh        ← Route task to free model
│
├── raw/                         ← Symlink/Junction → Google Drive (immutable)
└── .local/                      ← Machine-local (gitignored): profile, session memory
```

> **Key principle**: `raw/` is **immutable** — source documents are never edited. All AI-generated knowledge lives in `wiki/`. This ensures your source archive is never polluted by agent behavior.

---

## 🔗 Quick Links

| Resource | Description |
|---|---|
| [AGENTS.md](AGENTS.md) | Universal brain — read by 20+ AI platforms |
| [CLAUDE.md](CLAUDE.md) | Claude Code full config: hooks, /commands, session protocol |
| [GEMINI.md](GEMINI.md) | Gemini CLI config |
| [agent-skills/README.md](agent-skills/README.md) | Full skill catalog with enforcement details |
| [wiki/context/wiki-overview.md](wiki/context/wiki-overview.md) | Wiki stats, domain index, session memory |
| [scripts/setup-local.sh](scripts/setup-local.sh) | First-time machine setup script |
| [LICENSE](LICENSE) | MIT — use it, fork it, ship it |

---

## 📜 License

MIT © 2025-2026 — See [LICENSE](LICENSE).

---

<p align="center">
  <strong>Stop prompting. Start enforcing.</strong><br>
  <em>A-Wiki — Works with every AI tool you pay for. Enforces the discipline none of them come with.</em>
</p>
