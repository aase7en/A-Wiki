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

[![A-Wiki CI](https://github.com/aase7en/A-Wiki/actions/workflows/ci.yml/badge.svg)](https://github.com/aase7en/A-Wiki/actions/workflows/ci.yml)
[![Cross-Platform Smoke](https://github.com/aase7en/A-Wiki/actions/workflows/cross-platform.yml/badge.svg)](https://github.com/aase7en/A-Wiki/actions/workflows/cross-platform.yml)
[![Model Roster Refresh](https://github.com/aase7en/A-Wiki/actions/workflows/model-roster-refresh.yml/badge.svg)](https://github.com/aase7en/A-Wiki/actions/workflows/model-roster-refresh.yml)
[![Weekly Health Digest](https://github.com/aase7en/A-Wiki/actions/workflows/wiki-health-digest.yml/badge.svg)](https://github.com/aase7en/A-Wiki/actions/workflows/wiki-health-digest.yml)

**A-Wiki doesn't give your AI Agent a "better prompt." It gives it a spine.**

> Most AI coding assistants behave like a caffeinated junior dev on the last day of a sprint — rushing, patching symptoms, and burning your token budget on boilerplate.
>
> **A-Wiki transforms that same agent into a meticulous, cost-efficient Senior Software Architect** — one that scouts for zero-cost compute, enforces True TDD with religious conviction, carries context across every device you own, and works with every AI tool you already pay for.

---

## What Is A-Wiki?

A-Wiki is a repo-based operating system for AI agents. It combines a structured knowledge wiki, cross-agent instruction files, safety hooks, model-cost routing, and reusable skills so Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Cline, Copilot, Aider, and other agents behave like one coordinated team instead of isolated chat windows.

In practical terms, A-Wiki helps you:

| Need | How A-Wiki Helps |
|---|---|
| Keep AI context across sessions | Stores decisions, sources, summaries, TODOs, and domain knowledge in Markdown files that agents can re-read. |
| Stop repeating instructions | Puts durable rules in `AGENTS.md`, `CLAUDE.md`, platform config files, hooks, and protocol docs. |
| Search your own knowledge offline | Builds local FTS5 and optional vector indexes for fast wiki search without spending tokens. |
| Control AI cost | Uses a Cost-First Pyramid: local search and hooks first, free/current model roster next, cheap capable models after that, primary models only when needed. |
| Make agents safer | Blocks raw-source edits, secret leaks, destructive git commands, missing source provenance, and several format mistakes through hooks. |
| Work across machines | Uses a lightweight repo plus external `drive/` data layer so Mac, Windows, WSL, and Linux can share the same brain safely. |
| Coordinate many AI tools | Gives each platform its own entry file while keeping `AGENTS.md` as the shared source of truth. |

## What Can You Build With It?

A-Wiki is useful when your work benefits from long-lived memory, strict process, and repeatable AI workflows:

| Use Case | Example |
|---|---|
| Personal second brain | Convert notes, source docs, and decisions into searchable wiki pages with provenance. |
| AI-assisted software work | Enforce test-first implementation, root-cause debugging, reviews, and handoffs across agents. |
| Research and synthesis | Keep raw sources immutable, summarize them into `wiki/sources/`, and connect them through concepts/entities. |
| Multi-agent experimentation | Route lightweight tasks to free or cheap models while reserving primary models for judgment and validation. |
| Cross-device continuity | Stop a task on one machine and resume on another with session memory, git history, and generated indexes. |
| Domain operating manuals | Maintain structured knowledge for IoT, AI tools, pharmacy, environmental health, or your own domain. |

If you fork A-Wiki, you are not just copying prompts. You are copying a working pattern for turning AI agents into a persistent, searchable, policy-driven workspace.

---

## ⚡ Four Superpowers. One Repository.

| Superpower | What It Does | Your Win |
|---|---|---|
| **🌐 Works With Every AI Tool** | One config file per platform — Claude Code, Codex, Gemini CLI, Cursor, Windsurf, Cline, GitHub Copilot, Aider, and any tool that reads `AGENTS.md`. Your brain is platform-agnostic. | **No lock-in.** Switch AI tools or run them in parallel — they all share the same Iron Laws, wiki, and swarm protocol. |
| **🔍 Dynamic Token Scouting** | Auto-hunts OpenRouter Free tier and promotional endpoints via `update-model-roster.sh` plus a weekly GitHub Actions scout — routing boilerplate work to free models and reserving expensive tokens for reasoning that actually matters. | **Massive cost reduction.** You pay for thinking, not for generating getters and setters. |
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
> **External data layer:** `drive/` points to each user's own cloud/local `A-Wiki-Data` path. Do not hardcode personal Google Drive account paths.

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
| **[1/8] drive/ + raw/** | Creates symlink/junction/fallback pointing to your external `A-Wiki-Data` |
| **[2/8] .mcp.json** | Generates from `.mcp.json.example` with your machine's correct paths |
| **[3/8] API keys** | Reads `drive/.secrets` → injects cacheable keys into local settings without printing values |
| **[4/8] Private journal** | Creates/links local `log.md` and `wiki/context/session-memory.md` from Drive or `.example` |
| **[5/8] Wiki index** | Builds SQLite FTS5 search index from all wiki pages |
| **[6/8] Codex hooks** | Generates local `.codex/hooks.json` with portable relative commands |
| **[7/8] Model router** | Prepares local model-intel/router cache |
| **[8/8] Optional tools** | SkillOpt/react-doctor install only when explicitly enabled |

#### Optional: Local Semantic Search (sqlite-vec + fastembed)

Adds embedding-based search alongside FTS5 — same `.wiki-index.db`, hybrid query via [scripts/wiki/query-rag.py](scripts/wiki/query-rag.py). Pure offline once the model is cached. Cross-platform (macOS / Linux / Windows wheels).

```bash
pip install -r requirements.txt          # sqlite-vec, fastembed, apsw
python scripts/build-vec-index.py        # ~80MB model + ~30s embed on first run
python scripts/wiki/query-rag.py "mqtt vs lorawan"
```

> **macOS note:** if `pip install` succeeded but `build-vec-index.py` fails with an extension-loading error, your Python is from Apple's system or a python.org build with `--disable-loadable-sqlite-extensions`. The `apsw` package bypasses that and is already in `requirements.txt` — re-run `pip install -r requirements.txt`. If it still fails, install Python via Homebrew (`brew install python@3.12`) or pyenv.

---

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

### CI / Cross-Platform Proof

GitHub Actions runs a fake external data layer so tests never touch your real Google Drive secrets:

```bash
python scripts/check-privacy.py
python -m pytest -q
python scripts/verify-awiki-ready.py --skip-remote --skip-evals
python scripts/verify-cross-platform.py
```

- `A-Wiki CI` runs on every push to `main`.
- `A-Wiki Cross-Platform Smoke` runs manually or weekly across Ubuntu, macOS, and Windows.
- The Linux job additionally runs `verify-cross-platform.py --build-vec`.
- `A-Wiki Model Roster Refresh` runs every Monday and manually on demand. It checks whether OpenRouter's free model roster changed, uploads a report artifact, and opens/updates an issue for review instead of auto-committing routing changes.
- `A-Wiki Weekly Health Digest` runs every Wednesday and manually on demand. It publishes a repo/wiki health report artifact without touching real `drive/` data or committing generated files.

---

## 🔐 Public-Safe by Construction

A-Wiki is a public repo with a private brain layered on top — never the other way around. `scripts/check-privacy.py` is the gate that keeps the two from mixing:

| Check | Catches |
|---|---|
| Binary skip | Sniffs for a NUL byte in the first 8KB so `.xlsx`/images are never scanned as text — no false positives. |
| Tracked-but-gitignored | Files that got `git add -f`'d once and stayed tracked even after `.gitignore` said they shouldn't be — a real leak class, not a hypothetical one. |
| Personal-data patterns | Hardcoded paths, personal emails, live API keys, cloud-account folder names — plus extra P0 regexes loaded at runtime from gitignored `drive/personal/privacy-patterns.txt`, never hardcoded in the tracked scanner itself. |

Everything private — journals, session memory, secrets, raw sources — lives in the gitignored `drive/` layer. Git history itself was rewritten to strip identity and business-data leakage that had crept into earlier commits, before this repo went public.

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

## 🔧 One Skill, Every Agent — The Universal Skill Registry

Skills used to fork per-tool — a Claude skill here, a Cursor rule there, a Codex prompt somewhere else. A-Wiki collapses that into one **agentskills.io-standard** registry.

| Layer | What It Is |
|---|---|
| **Source of truth** | `skills-registry.json` — 367 registered skills (361 canonical, 5 aliases, 1 deprecated), each tagged with `domain`, `lifecycle_phase`, and `status`. |
| **Generators** | 6 scripts in `scripts/skills_registry/generators/` turn the registry into native surfaces: AGENTS.md, Antigravity, Cline, Gemini CLI, Hermes, Kilo. |
| **One command, every harness** | `bash scripts/link-agent-configs.sh` symlinks the whole skill set into **9 agent runtimes** — Claude, Codex, Cline, Hermes, Gemini CLI, ZCode, **Antigravity**, Windsurf, OpenClaw — in one idempotent pass. |
| **Enforcement** | A dedicated hook blocks any `SKILL.md` that isn't registered, so agent surfaces can never silently drift from what's on disk. |

```bash
bash scripts/link-agent-configs.sh --status      # verify all 9 harnesses are linked
```

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

### Weekly Model Roster Scout

The GitHub Actions workflow [`model-roster-refresh.yml`](.github/workflows/model-roster-refresh.yml) runs every Monday. Its job is to protect the Cost Pyramid:

| Step | What it does |
|---|---|
| 1 | Reads `OPENROUTER_API_KEY` from GitHub Secrets if available |
| 2 | Runs `scripts/update-model-roster.sh --ci-ok --no-backup --report ...` |
| 3 | Builds a candidate `wiki/context/model-roster.conf` from current free OpenRouter models |
| 4 | Compares the candidate against the tracked roster |
| 5 | Uploads a Markdown report/artifact for audit |
| 6 | Opens or updates a GitHub issue when routing changes need human/Primary Agent review |

It intentionally does **not** auto-commit changes. Model routing affects every agent, so roster updates should be reviewed before landing on `main`.

### 🎛 Live Dashboard — watch the swarm in real time

```bash
python3 scripts/live-dashboard/server.py     # → http://localhost:7790/
```

A real-time monitor showing **which AI is working, on what, in which workflow, how many models in parallel, and which hooks fire/block** — streamed live via SSE as you issue any A-Wiki command.

- **⚙️ Settings → Models** — toggle any model on/off and edit its `model_id`. Each card shows a **capability scorecard** (SWE-bench · Terminal-Bench · NL2Repo · reasoning · speed). If you change nothing, sensible **defaults** apply.
- **⚙️ Settings → API Keys** — paste a provider key (incl. **GLM 5.2 / Z.ai**). Keys are stored gitignored in `.tmp/` + `drive/.secrets` (never in the repo, never shown back).
- **Capability-aware routing** — the router ranks models by leaderboard capability **within each cost class**, so `cost_rank` always wins: a paid model never jumps ahead of a free one. Capability only breaks ties among models you've enabled.

Opt-out / config: no setup needed; the dashboard reads `.tmp/model-config.json` (written by the panel) and `wiki/context/model-capability-scores.json`. See [`scripts/live-dashboard/README.md`](scripts/live-dashboard/README.md).

---

## 📡 Autonomous Brain Sync — A Pi5 Telegram Bot That Never Falls Behind

The knowledge brain doesn't stop at your laptop. `scripts/hermes/pi5-brain-sync.py` keeps a Raspberry Pi 5 running the Hermes agent gateway in lockstep with `main` — fully unattended, no SSH babysitting.

| Stage | What Happens |
|---|---|
| **Safe fast-forward** | `git stash push --include-untracked` protects device-only files inside the container before the FF merge, then pops the stash back. |
| **Self-healing conflicts** | Auto-generated files that conflict on stash-pop are silently restored from `HEAD` (they regenerate anyway). Any other conflict aborts safely, leaving the stash intact for a human. |
| **Live rescan** | The gateway gets `SIGHUP`'d after every sync so newly linked skills load without a container restart. |
| **Scheduling** | Two systemd timers on the Pi5 — sync every 6h (+5 min after boot), plus a weekly Sunday 04:30 Asia/Bangkok reboot to keep the host healthy. |
| **Remote control** | The same Pi5 runs a Telegram bot (`scripts/hermes/telegram-command-router.py`) exposing `/wiki`, `/search`, `/review`, `/spec`, `/plan`, `/build`, `/ship` as slash commands from your phone. |

Push to `main` from any machine — the Pi5 catches up on its own schedule, or instantly on `/wiki` demand.

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

### 🧭 Non-Trivial Technical Task? `fable5-standards` Kicks In.

Any multi-step plan, security-sensitive design, or data migration pulls in `agent-skills/engineering/fable5-standards` — one `SKILL.md`, registered once, available on **every agentskills.io-compatible tool** you run. It forces: restate the real problem, generate ≥2 approaches with trade-offs, root-cause before symptom-patching, and a pre-mortem before you ship.

### 🔍 Want to Scout for Free Compute?

```bash
bash scripts/update-model-roster.sh
cat wiki/context/model-roster.conf
```

Queries OpenRouter's free tier and produces a ranked allocation recommendation — Architect role, Executioner role, race models.

---

## Session Lifecycle — The Four Workflows

A-Wiki now exposes the four operational workflows as a local interactive map:
[awiki-workflow-map.html](exports/html/awiki-workflow-map.html)

This HTML artifact is intentionally local-only and gitignored. It is a human-review leaf under the output-format policy, not a tracked source-of-truth document.

| Workflow | What it does | Main surfaces |
|---|---|---|
| Session Start | Pull latest `main`, check Drive/external data, refresh context, show TODOs, prepare cost-first routing | `.claude/settings.json`, `.codex/hooks.json`, `scripts/hooks/session_start.py` |
| Plan Mode / Handoff | Split work into resumable chunks, checkpoint `handoff.md`, allow safe cross-agent resume | `docs/protocols/cross-agent-plan-handoff.md`, `scripts/agent-switch.sh` |
| Advisor / Swarm | Keep the top model as planner/validator while routing low-risk work to cheaper lanes | `scripts/swarm/delegate.sh`, `scripts/crew-dispatch.py`, `docs/protocols/crew.md` |
| Cost-First Pyramid | Push local search and free/cheap routes first, then escalate to primary models only when justified | `docs/protocols/cost-gate.md`, `scripts/model-router-policy.py`, `scripts/hooks/check_cost_tier.py` |

### Codex Guarded Full-Auto + AG2

Codex in A-Wiki is designed for `approval_policy="never"` + `sandbox_mode="danger-full-access"` only inside a trusted repo with hook guardrails active. That combination is fast, but it is only acceptable because the repo layers file/write gates, delegation gates, secret scanning, source-provenance checks, and cost declarations on top.

AG2 sits above the existing router as a goal orchestrator. It does not replace `delegate.sh`.

| Layer | Owner | Why it stays there |
|---|---|---|
| Goal planning / chunking | `scripts/swarm/ag2-goal.py` | Lets Codex or Claude turn a goal into resumable work |
| Free/cheap routing | `scripts/swarm/delegate.sh` | Single source of truth for provider fallback and cost-first dispatch |
| Local-first retrieval | `scripts/search-wiki.py`, graph/search scripts | Zero-cost evidence before any external LLM call |
| Final judgment | Primary model | Iron Law III: validation is not delegated |

## Cost-First Enforcement Modes

A-Wiki enforces the Cost-First Pyramid at two practical points, but the enforcement strength is intentionally uneven:

| Mode | Status | What It Covers |
|---|---|---|
| Session start | Active | Hooks remind the agent to load current context, check API/model scout freshness, and start from the lowest-cost route. |
| Tool calls during a session | Active | `PreToolUse` and routing scripts apply gates when the agent edits files, writes files, runs shell commands, or delegates model work. |
| Continuous always-on monitor | Not enabled by default | A separate background process could watch the repo and model cache even when no AI tool is being used. |

### Enforcement Reality

The current cost gate is a **nudge**, not a hard wall:

| Behavior | Reality today |
|---|---|
| Tier declaration | Required before `Edit` / `Write` / `Agent`, and invalid tiers are now blocked |
| Model-vs-tier validation | Not enforced; the hook cannot see the actual model route |
| Scope of declaration | Per-day, not per-task |
| Bypass visibility | `CI=true` and `HOOK_SKIP=check_cost_tier` still bypass, but now emit warnings |

That tradeoff is deliberate for a solo repo. It forces the agent to stop and declare intent, but it avoids the friction of per-task re-approval or background daemons.

### Continuous Monitor Tradeoff

An always-on Cost-First monitor is possible, but it should be adopted only if the extra operational complexity is worth it.

| Benefit | Cost / Risk |
|---|---|
| Catches stale model pricing before the next tool call. | Needs a daemon, launch agent, cron job, or file watcher per machine. |
| Can refresh `.tmp/model-scout-current.json` on a schedule. | May trigger network/API calls when you are not actively working. |
| Can warn earlier when model IDs expire or prices change. | Adds another moving part that can fail differently on macOS, Windows, WSL, and Linux. |
| Useful for shared/team repos with many agents active at once. | Less valuable for a solo repo where hooks already run at session start and tool use. |
| Can centralize budget policy across tools that do not support hooks well. | If implemented too aggressively, it can create noise, lock files, or surprise edits in `.tmp/`. |

Default recommendation: keep the current hook-based enforcement for solo/personal use. Add an always-on monitor only when A-Wiki is used by multiple agents or machines at the same time, or when model-cost drift has caused real failures often enough to justify the maintenance cost.

---

## 🗺️ Repository Architecture

```
A-Wiki/
│
├── AGENTS.md                    ← Universal brain (20+ AI platforms)
├── CLAUDE.md                    ← Claude Code edition
├── GEMINI.md                    ← Gemini CLI edition
├── skills-registry.json         ← Single source of truth — 367 registered skills
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
│   ├── link-agent-configs.sh    ← One command: link 367 skills into 9 harnesses
│   ├── search-wiki.py           ← FTS5 wiki search
│   ├── update-model-roster.sh   ← Dynamic free model discovery
│   ├── hermes/                  ← Pi5 cross-device brain sync + Telegram bot
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
| [skills-registry.json](skills-registry.json) | Single source of truth for all 367 registered skills |
| [scripts/link-agent-configs.sh](scripts/link-agent-configs.sh) | One command — link skills into all 9 agent harnesses |
| [wiki/context/wiki-overview.md](wiki/context/wiki-overview.md) | Wiki stats, domain index, session memory |
| [scripts/setup-local.sh](scripts/setup-local.sh) | First-time machine setup script |
| [docs/runbooks/setup-new-machine.md](docs/runbooks/setup-new-machine.md) | Cross-platform onboarding runbook for Mac, Windows, Linux, and GitHub Actions |
| [docs/runbooks/upstream-refresh.md](docs/runbooks/upstream-refresh.md) | Version tracking and upstream refresh runbook |
| [CHANGELOG.md](CHANGELOG.md) / [VERSION](VERSION) | Current capability version and release history |
| [scripts/wiki-health-digest.py](scripts/wiki-health-digest.py) | Weekly repo/wiki health digest generator |
| [LICENSE](LICENSE) | MIT — use it, fork it, ship it |

---

## 📜 License

MIT © 2025-2026 — See [LICENSE](LICENSE).

---

<p align="center">
  <strong>Stop prompting. Start enforcing.</strong><br>
  <em>A-Wiki — Works with every AI tool you pay for. Enforces the discipline none of them come with.</em>
</p>
