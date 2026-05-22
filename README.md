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
> **A-Wiki transforms that same agent into a meticulous, cost-efficient Senior Software Architect** — one that scouts for zero-cost compute, enforces True TDD with religious conviction, and carries context across every device you own.

---

## ⚡ Three Superpowers. One Repository.

| Superpower | What It Does | Your Win |
|---|---|---|
| **🔍 Dynamic Token Scouting** | Auto-hunts OpenRouter Free tier, Gemini free promotional endpoints, and local Ollama models at runtime — routing boilerplate work to free models and reserving expensive tokens for reasoning that actually matters. | **Massive cost reduction.** You pay for thinking, not for generating getters and setters. |
| **🛡️ Iron Law Process Enforcement** | Hard-blocks any code path that tries to commit production code without a failing test first. Blocks any bug fix that hasn't completed root-cause analysis. If a parallel swarm model violates either rule, its output is **discarded and rewritten** on sight. | **Zero technical debt injection.** The kind of discipline you'd expect from a principal engineer doing code review at 2 AM. |
| **🌐 Cross-Device Context-Aware Solo Wiki** | Commit directly to `main` — no branches, no PR theater. Every session auto-summarizes into `.local/session-memory.md` so when you open the repo on your laptop after a desktop session, your agent already knows exactly where you left off. | **True continuity.** Walk away from any machine and resume on any other without losing a single breadcrumb. |

---

## 🛡️ The Iron Laws

These are **not** guidelines. They are unbreachable execution boundaries enforced by the Primary Agent (Senior Critic). Violations trigger **immediate discard and rewrite**.

| # | Iron Law | Enforced By |
|---|----------|-------------|
| **I** | **NO production code without a FAILING TEST first.** True TDD. If the test passes before the code is written, you are testing the test — not the code. | `scrutinize` skill |
| **II** | **NO bug fixing without ROOT CAUSE INVESTIGATION first.** You will reproduce, trace, falsify, and cross-reference before touching a single line. Superficial patching is forbidden. | `debug-mantra` skill |
| **III** | **If a parallel agent or secondary model violates Iron Law I or II, its output MUST be discarded and rewritten by the Primary Agent.** No exceptions. No "merge anyway." | Primary Agent (Senior Critic) |

> *"Discipline is not optional. Automation without verification is just faster chaos."*

---

## 📦 Prerequisites

Before onboarding, your machine must have:

| Dependency | Why | Check |
|---|---|---|
| **Git** (2.30+) | Version control, direct-to-main workflow | `git --version` |
| **Git Bash** | Required for Windows users running shell scripts | Already bundled with Git for Windows |
| **Node.js** (18+) | Runtime for automation hooks and graph builders | `node --version` |
| **AI Client** | At least one: Claude Code CLI, Cline (VS Code extension), or Codex CLI | `claude --version` or check VS Code extensions |

> **Windows users:** All shell scripts in this repo are written for Bash. Use **Git Bash** (not PowerShell, not CMD) to run them — it ships with Git for Windows and lives at `C:\Program Files\Git\bin\bash.exe`.

---

## 🚀 3-Step Onboarding (Fresh Clone → Fully Armed)

### Step 1: Clone the Repository

```bash
git clone https://github.com/aase7en/A-Wiki.git
cd A-Wiki
```

This is a **solo wiki** — you commit directly to `main`. No branches. No pull requests. No ceremony.

### Step 2: Run Pre-Flight Checks

Open **Git Bash** (Windows) or **Terminal** (macOS/Linux) and run:

```bash
bash agent-skills/automations/run-task.sh pre-flight
```

This validates:
- ✅ Git is configured and you're on the `main` branch
- ✅ No uncommitted drift from the remote
- ✅ All Iron Law enforcement hooks are active
- ✅ Required directories exist (`agent-skills/`, `core-knowledge/`, `scripts/`)

If any check fails, the script halts and tells you exactly what to fix.

### Step 3: Connect the Global Nervous System (Symlink Activation)

```bash
bash scripts/link-my-skills.sh
```

This single command instantly injects all agent skills into your global AI environments:

| Agent | Symlink Target | Purpose |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | Auto-loaded into every Claude session |
| **Cline / Roo** | `~/.cline/skills/` | Available in VS Code Cline extension |
| **Codex / OpenAI** | `~/.codex/skills/` | Available in Codex CLI |

The symlinks mean you update the central repo and **every agent picks up the changes instantly** — no copying, no drift, no "which version am I running?".

> **Tip:** Run `bash scripts/link-my-skills.sh --list` to see every skill that will be linked before activating.

---

## 🧠 Daily Workflow — How to Operate with the Swarm

Once onboarded, your AI agent is no longer a generic chatbot. It's a disciplined swarm. Here's how you direct it:

### 🏗️ Designing a Feature? Invoke `scrutinize`.

```
"Before we write any code, scrutinize this plan."
```

The agent will:
1. Question whether the feature should exist at all (is there a simpler way?)
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
4. Cross-reference every experiment against a running breadcrumb ledger

Only after all four steps pass does it present a root cause and a fix.

### 📊 Summarizing for Leadership? Use `management-talk`.

```
"Translate this incident report into management-talk for a JIRA comment."
```

The agent strips function names, file paths, and code identifiers, then rewrites everything in plain-English cause-and-effect — keeping JIRA keys, product names, and customer identifiers intact.

### 🔍 Want to Scout for Free Compute?

```bash
bash agent-skills/automations/run-task.sh scout-models
```

The `model-scouter` queries OpenRouter's free tier, checks for Gemini promotional endpoints, and scans any local Ollama instances — producing a ranked JSON allocation recommendation within 30 seconds.

---

## 🗺️ Repository Architecture

```
A-Wiki/
├── agent-skills/               ← ACTIVE LAYER — The Swarm Brain
│   ├── engineering/            ← debug-mantra, scrutinize, post-mortem
│   ├── productivity/           ← management-talk
│   ├── swarm-intelligence/     ← model-scouter, agile-swarm
│   ├── infrastructure/         ← git-safety protocol
│   ├── automations/            ← hooks.py, run-task.sh
│   └── extensibility/          ← symlink-connector
├── core-knowledge/             ← SAFEGUARDED ARCHIVE (read-only)
│   ├── wiki/                   ← Knowledge synthesis pages
│   ├── docs/                   ← Protocols, architecture, guides
│   ├── decisions/              ← Architecture Decision Records
│   └── journal/                ← Daily engineering journals
├── skills/                     ← Legacy skills (backward compatible)
├── scripts/                    ← Utility scripts (link-my-skills, agent-switch, delegates)
├── tools/                      ← Prompt templates
└── .local/                     ← [GDrive] Profile, secrets, session memory
```

> **Golden Rule:** `core-knowledge/` is **read-only**. All new content, skills, and automations live in `agent-skills/`. This separation ensures your knowledge archive is never polluted by experimental agent behavior.

---

## 🧪 Quick Sanity Check

After completing the 3-step onboarding, verify everything works:

```bash
# 1. Confirm pre-flight passes cleanly
bash agent-skills/automations/run-task.sh pre-flight

# 2. List all linked skills
bash scripts/link-my-skills.sh --list

# 3. Run a test-driven cycle (Iron Law I demo)
cd test-zone
# The failing test validates the discipline chain — fix greet.py if needed
python -m pytest test_greet.py -v
```

---

## 🔗 Quick Links

| Resource | Description |
|---|---|
| [AGENTS.md](AGENTS.md) | Agent instruction manifest — read by all AI agents |
| [CLAUDE.md](CLAUDE.md) | Session rules and Iron Law reference |
| [agent-skills/README.md](agent-skills/README.md) | Full skill catalog with enforcement details |
| [core-knowledge/README.md](core-knowledge/README.md) | Safeguarded knowledge archive index |
| [LICENSE](LICENSE) | MIT — use it, fork it, ship it |

---

## 📜 License

MIT © 2025-2026 — See [LICENSE](LICENSE).

---

<p align="center">
  <strong>Stop prompting. Start enforcing.</strong><br>
  <em>A-Wiki — Because your AI agent should work like a principal engineer, not an intern.</em>
</p>