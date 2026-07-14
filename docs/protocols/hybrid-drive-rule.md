# Hybrid Drive Rule — three-layer storage for A-Wiki

> **Part of**: [USA-1 Universal Skill Architecture](../architecture/universal-skill-architecture.md) §4.
> **ADR**: [0008](../../decisions/0008-universal-skill-architecture.md).
> **Binding**: every agent, every file write.

A-Wiki separates storage into **three layers** so that public-safe knowledge is
shareable, heavy/raw data stays out of git, and per-agent state never pollutes
the repo or other agents.

---

## The Hybrid Rule (binding)

| Data type | Location | Why | Git policy |
|---|---|---|---|
| Public-safe knowledge / skills / code | **repo** (`skills/`, `wiki/`, `docs/`, `scripts/`) | portable, shareable, re-readable | tracked |
| Raw / heavy / personal cross-agent | **shared Drive pool** (`raw/`, `backups/`, `personal/`, `batch-state/`) | one copy, all agents read | gitignored |
| Agent-specific state / memory / heavy | **`.~<agent>/`** on Drive (e.g. `.~codex/`, `.~zcode/`) | isolation, privacy, no cross-pollution | gitignored |
| Secrets (API keys, tokens) | **`drive/.secrets`** (existing) | never in repo | gitignored, read via `scripts/lib/drive_secrets.py` |

---

## Drive topology on `A-Wiki-Data`

```
A-Wiki-Data/                          (Google Drive, gitignored, resolves via .drive-path)
├── raw/                    [shared]  source docs, PDFs, OCR input
├── backups/                [shared]  wiki backups, session exports
├── batch-state/            [shared]  batch ingest queue state
├── hermes-sync/            [shared]  Hermes multi-device sync (→ .~hermes over time)
├── personal/               [shared]  private journals, session-memory
├── pharmacy/               [shared]  pharmacy runtime DB + orders
├── model-roster/           [shared]  scout cache
│
├── .~claude/               [per-agent]  Claude Code agent state
├── .~codex/                [per-agent]  Codex agent state
├── .~gemini/               [per-agent]  Gemini CLI agent state
├── .~zcode/                [per-agent]  ZCode agent state
├── .~hermes/               [per-agent]  (migration target for hermes-sync/)
├── .~kilo/                 [per-agent]  Kilo agent state
├── .~cline/                [per-agent]  Cline agent state
├── .~antigravity/          [per-agent]  Antigravity agent state
├── .~windsurf/             [per-agent]  Windsurf agent state
└── .~openclaw/             [per-agent]  OpenClaw agent state
```

## `.~<agent>/` internal structure

```
.~<agent>/
├── sessions/          session logs, compaction history
├── worktrees/         heavy worktree caches (instead of polluting the repo)
├── memory/            agent-specific long-term memory / context
├── hooks-state/       hook invocation counters, last-run timestamps
└── large-artifacts/   big outputs (HTML renders, screenshots) too heavy for repo
```

---

## Decision checklist — where does a new file go?

Answer in order; first match wins:

1. **Personal data / secret / patient or customer data / machine-specific path or artifact** → `drive/` (gitignored). **Never** the public repo.
2. **Raw source file (PDF, image, OCR input)** → `raw/` (immutable, Iron Law #4) which syncs to `drive/raw/`.
3. **Agent-specific runtime state** (session log, worktree cache, per-agent memory, big agent output) → `drive/.~<agent>/`.
4. **Reusable knowledge / rule / hook / skill / script shared across machines** → repo (public, tracked).
5. **Unsure** → put it in `drive/` first (safer). Promote to repo only after confirming it is public-safe.

## Hard rules

- **Never write machine-specific paths** (`L:\...`, `C:\Users\<user>\...`,
  personal account names) into the public repo. Resolve dynamically via the
  `drive/` junction, `.drive-path`, or `A_WIKI_DRIVE_PATH`.
- A script/tool that exists only to fix one specific machine belongs under
  `drive/` — never at the repo root.
- `.~<agent>/` dirs are **gitignored** (see `.gitignore` `.\~` rule). Never
  commit their contents.
- When in doubt about public-safety, run `python scripts/check-privacy.py`
  before committing.

---

## Setup

Create per-agent skeletons (idempotent):

```bash
bash scripts/setup-agent-drive.sh             # all 9+ agents
bash scripts/setup-agent-drive.sh codex zcode # specific agents
bash scripts/setup-agent-drive.sh --status    # show current state
```

The script resolves the Drive via `.drive-path` / `drive/` junction (same
mechanism as `setup-cloud-link.sh`) and creates the `.~<agent>/{sessions,
worktrees, memory, hooks-state, large-artifacts}` subtree per agent.

## Migration note (Hermes)

`hermes-sync/` predates this rule and is a shared pool. Chunk C4
(optionally, low priority) migrates it to `.~hermes/` over one release
cycle, keeping `hermes-sync/` as an alias for backward compatibility.
