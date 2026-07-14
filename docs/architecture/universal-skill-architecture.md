# Universal Skill Architecture (USA-1) — A-Wiki v1.2

> **Status**: Approved 2026-07-14. Implementation: chunks C0–C10.
> **Binding for**: all agents (Codex, Claude Code, Antigravity, ZCode, Hermes, Windsurf, OpenClaw, Kilo, Cline + future).
> **ADR**: [0008-universal-skill-architecture.md](../../decisions/0008-universal-skill-architecture.md)
> **Spec author persona**: World-class architecture design engineer (20+ yr).

This is the authoritative architecture for how every skill in A-Wiki is discovered,
shared, deduplicated, secured, and stored across all current and future agents.

---

## 0. Design Principles (the six "irons" of this spec)

1. **Registry is the single source of truth (SoT)** — `skills-registry.json`
   (schema v2). Every agent surface is **generated**, never hand-edited
   (Iron Law #9 extended to all surfaces).
2. **Plugin generators** — adding an agent = 1 file (`gen_<agent>.py`) + 1 line
   in `GENERATORS`. Zero edits to existing agents.
3. **Alias, don't delete** — dedup uses the registry's existing `status: alias` +
   `canonical:` + `migrated_to:` fields. Old skills stay on disk marked
   deprecated/alias; only confirmed dead-weight gets deleted.
4. **Three-layer storage separation** — repo (public-safe, git-tracked) ·
   Drive shared pool (heavy/raw/personal, gitignored) ·
   Drive `.~<agent>/` (agent-specific state, gitignored).
5. **Defense in depth** — PreToolUse hooks (realtime, all agents) + pre-commit
   gate (local) + CI gate (remote). No single layer is trusted alone.
6. **Non-breaking** — every chunk is independently shippable + reversible.
   No big-bang migration.

---

## 1. Goal coverage matrix

| User goal | Spec section | Implementation chunks |
|---|---|---|
| #1 All 9 + future agents work together | §3 Plugin generator layer | C1, C2 |
| #2 Drive as backup + `.~<agent>` | §4 Hybrid Drive layer | C3, C4 |
| #3 Gitignore secrets/personal, security-skill verified | §5 Security enforcement | C5, C6, C7 |
| #4 Central skill brain | §6 SKILL-INDEX.md brain | C8 |
| #5 Dedup same-job diff-name, reduce count, keep real-use | §7 Strict dedup | C9, C10 |

---

## 2. Current-state audit (what we build on)

| Component | State | Notes |
|---|---|---|
| `skills-registry.json` v2 | ✅ 365 entries, `aliases` + `status: canonical/alias/deprecated` | alias mechanism barely used (5 alias / 1 deprecated) |
| `VALID_DOMAINS` (22) | ✅ covers Goal #5 domains + extensions | code, debug, design, ux-ui, trader, medical, business, data, engineering, security, ai-ops, productivity, wiki, iot, env, pharmacy, thai, logistics, network, media, document, sre |
| `regen-skill-surfaces.py` + generators | ⚠️ 6 generators | **missing: codex, zcode, windsurf, openclaw** |
| `link-agent-configs.sh` | ✅ one linker for 9 agents | works, but doesn't sync Drive `.~<agent>` |
| Drive layer | ✅ `.drive-path` resolves to `A-Wiki-Data`, has `personal/`, `hermes-sync/`, `raw/` | **missing `.~<agent>/` pattern** |
| `check_secret_leak.py` (9 patterns) + `check-privacy.py` | ⚠️ PreToolUse only on Claude/Codex | not cross-agent, no pre-commit/CI |
| Brain | ❌ no readable central brain | registry is machine-SoT, not human/agent-readable |

---

## 3. Plugin Generator Layer (Goal #1 + future agents)

### 3.1 Architecture

```
skills-registry.json (SoT)
        │
        ▼
scripts/regen-skill-surfaces.py  ──── GENERATORS dict ───┐
        │                                                 │
        ├── gen_agents_md.py      → AGENTS.md (universal)
        ├── gen_antigravity.py    → .antigravity/skills.json
        ├── gen_cline.py          → .clinerules/skills.json
        ├── gen_codex.py          → .codex/skills.json          [NEW]
        ├── gen_gemini.py         → .gemini/settings.json
        ├── gen_hermes.py         → lifecycle-config.json
        ├── gen_kilo.py           → kilo.skills-paths.json
        ├── gen_openclaw.py       → .openclaw/skills.json        [NEW]
        ├── gen_windsurf.py       → .windsurfrules.skills.json   [NEW]
        └── gen_zcode.py          → .zcode/skills.manifest.json  [NEW]
```

### 3.2 Generator contract (the plugin interface — every generator obeys)

```python
# scripts/skills_registry/generators/gen_<agent>.py
filename = "<agent>.skills.json"   # consumed by the regen orchestrator

def render(registry: Registry) -> str:
    """Return the agent-specific surface as a string (JSON/JSONC/MD).
    MUST use registry.canonical_for_agent('<agent>') — never hardcode paths."""
```

### 3.3 Agent registration = 3 steps

1. Create `scripts/skills_registry/generators/gen_<agent>.py`
   (copy `_TEMPLATE_gen_agent.py`, ~44 lines).
2. Add one import + one line to `GENERATORS` in `regen-skill-surfaces.py`.
3. Add the agent to `link-agent-configs.sh` linker list + `.~<agent>` Drive rule (§4).

Then `python scripts/regen-skill-surfaces.py` regenerates all surfaces; the new
agent immediately sees the canonical skill set. No other file needs editing.

### 3.4 ZCode drift fix (resolves gap G4)

ZCode currently reads `.zcode/skills/` (330 symlinks; 306 of them point to a
**stale** `~/.claude/skills/` snapshot, drifting from the repo).

**Chosen approach (Option A)**: `gen_zcode.py` emits
`.zcode/skills.manifest.json`; `link-agent-configs.sh` recreates the symlink
farm **pointing into the repo** (`skills/...`), not into `~/.claude/skills/`.
This fixes drift permanently and makes ZCode a first-class registry-driven agent.

---

## 4. Hybrid Drive Layer (Goal #2)

### 4.1 Drive topology on `A-Wiki-Data`

```
A-Wiki-Data/                          (Google Drive, gitignored, resolves via .drive-path)
├── raw/                    [shared]  source docs, PDFs, OCR input (existing)
├── backups/                [shared]  wiki backups, session exports (existing)
├── batch-state/            [shared]  batch ingest queue state (existing)
├── hermes-sync/            [shared]  Hermes multi-device sync (existing; → .~hermes)
├── personal/               [shared]  private journals, session-memory (existing)
├── pharmacy/               [shared]  pharmacy runtime DB + orders (existing)
├── model-roster/           [shared]  scout cache (existing)
│
├── .~claude/               [NEW]     Claude Code agent state
├── .~codex/                [NEW]     Codex agent state
├── .~gemini/               [NEW]     Gemini CLI agent state
├── .~zcode/                [NEW]     ZCode agent state
├── .~hermes/               [NEW]     (migrate hermes-sync/ → .~hermes/ over time)
├── .~kilo/                 [NEW]     Kilo agent state
├── .~cline/                [NEW]     Cline agent state
├── .~antigravity/          [NEW]     Antigravity agent state
├── .~windsurf/             [NEW]     Windsurf agent state
└── .~openclaw/             [NEW]     OpenClaw agent state
```

### 4.2 `.~<agent>/` internal structure (per-agent isolation)

```
.~<agent>/
├── sessions/          session logs, compaction history
├── worktrees/         heavy worktree caches (instead of polluting the repo)
├── memory/            agent-specific long-term memory / context
├── hooks-state/       hook invocation counters, last-run timestamps
└── large-artifacts/   big outputs (HTML renders, screenshots) too heavy for repo
```

### 4.3 The Hybrid Rule (binding)

| Data type | Location | Why |
|---|---|---|
| Public-safe knowledge/skills/code | **repo** (git) | portable, shareable |
| Raw/heavy/personal cross-agent | **shared Drive pool** (`raw/`, `backups/`, `personal/`) | one copy, all agents read |
| Agent-specific state/memory/heavy | **`.~<agent>/`** on Drive | isolation, privacy, no cross-pollution |
| Secrets | **`drive/.secrets`** (existing) | never in repo, read via `scripts/lib/drive_secrets.py` |

`.drive-path` resolution already works — no new mechanism.
`scripts/setup-agent-drive.sh` (new) creates the `.~<agent>/` skeleton on first
run per agent (idempotent).

---

## 5. Security Enforcement (Goal #3, hard hooks)

### 5.1 Three-layer defense (binding)

```
Layer 1 — PreToolUse hooks (realtime, ALL agents)
   ├── check_secret_leak.py        (existing, 9 patterns)  → extend to all agents
   ├── check_privacy.py            (existing, manual)      → wrap as PreToolUse
   ├── check_machine_path.py       [NEW]                   → block L:\, C:\Users\<user>, personal names
   └── check_skill_registry.py     (existing, Iron Law #9) → extend to all agents

Layer 2 — pre-commit git hook (local gate, before push)
   └── scripts/hooks/pre-commit-awiki.sh  [NEW]
       ├── check-privacy.py
       ├── check_secret_leak.py --staged
       └── regen-skill-surfaces.py --check (registry drift)

Layer 3 — CI workflow (remote gate, GitHub Actions)
   └── .github/workflows/awiki-safety.yml  [NEW]
       ├── regen-skill-surfaces.py --check
       ├── check-privacy.py
       └── check_secret_leak.py --staged
```

### 5.2 Cross-agent hook adapter (the non-breaking trick)

Each agent has a different hook config format (`.claude/settings.json` vs
`.codex/hooks.json` vs `.kilo/...`). Spec a **single source** in
`scripts/hooks/` + a thin per-agent adapter:

- `scripts/hooks/_awiki_hooks.py` — shared hook logic (one file).
- `scripts/hooks/adapters/<agent>_adapter.py` — translates the agent's hook
  payload → common schema, calls shared logic, returns a verdict in the agent's
  expected format.
- `link-agent-configs.sh` wires each adapter into the right agent config.

### 5.3 Verified by existing security skills

The hooks' pattern set is reviewed by the security-skill cluster before each
major change:

- `security-and-hardening` (OWASP, three-boundary input validation)
- `hipaa-compliance` + `thai-pdpa` (PHI/PDPA patterns for medical/thai domains)
- `defi-amm-security` + `llm-trading-agent-security` (wallet/tx patterns for trader)
- `security-scan` (AgentShield config audit)

→ `scripts/hooks/security_patterns.yaml` (new) is the single place patterns
live; skills cite it; CI verifies coverage.

---

## 6. Central Skill Brain: `SKILL-INDEX.md` (Goal #4)

### 6.1 The brain file (auto-generated, git-tracked, human+agent readable)

```
wiki/SKILL-INDEX.md   ← generated by scripts/skills_registry/generators/gen_skill_index.py
```

- Generated **from** `skills-registry.json` (never hand-edited — Iron Law #9 extended).
- Sections: (a) per-domain table (Code, Debug, Design, UX/UI, Trader, Medical,
  Business, Data, Engineering + extensions); (b) lifecycle-phase map;
  (c) alias→canonical resolution table; (d) "what to use when" quick-pick.
- Every agent reads it at session start (via the `SessionStart` hook adapter, §5.2)
  — this is the "สมองกลางที่ทุก Agent ต้องเข้ามาอ่าน".

### 6.2 Why an index file

- **vs AGENTS.md**: AGENTS.md is already large and is *config*, not a *skill
  catalog*. The index separates concerns.
- **vs MCP query**: the index works offline + for every agent (some agents have
  no MCP). The MCP `awiki` server can additionally serve the index for realtime
  queries (complementary, not exclusive).
- **vs registry JSON**: the registry is machine-SoT; the index is the readable
  projection.

### 6.3 Refresh trigger

- `gen_skill_index.py` runs inside `regen-skill-surfaces.py` (one command
  regenerates everything).
- Also wired to `PostToolUse` on Write/Edit to `skills-*/SKILL.md`
  (auto-refresh brain).

---

## 7. Strict Dedup (Goal #5)

### 7.1 Dedup rules (binding, strict bar)

A skill is a dedup candidate **only if** ALL of:

1. **Same job** — same trigger intent, same output type (not just same keyword).
2. **Clear winner** — one is canonical (broader / newer / A-Wiki-adapted).
3. **No hard references** — verified via repo-wide grep.
4. **Winner exists + tracked** — confirmed before the loser is touched.

### 7.2 Dedup method = alias, not delete (the non-breaking way)

For each confirmed dup:

1. Edit `skills-registry.json`: loser entry → `status: "alias"` +
   `canonical: "<winner>"` + `migrated_to:` note.
2. Optionally `status: "deprecated"` if the loser should never be invoked
   (keeps the file for history).
3. Re-run `regen-skill-surfaces.py` → all agents now resolve loser → winner
   automatically.
4. Delete loser files **only if** zero hard references AND the winner fully
   covers (the 6-skill precedent already shipped).

### 7.3 Confirmed dedup candidates (strict bar)

Verified during implementation; ~8–10 skills. See chunk C9/C10.

### 7.4 NOT touching (per user decision: keep all domains, strict bar)

- Per-language `*-patterns` + `*-testing` (8 languages × 2) — distinct niches.
- Domain expert skills (trader/medical/business/data) — kept.
- Homelab/Network, Motion/Media — kept.

---

## 8. Implementation chunks

> Each chunk = 1 commit on `main` (trunk-based, Iron Law #6).
> Each has a rollback = revert that commit.

| Chunk | Goal | Risk | Description |
|---|---|---|---|
| C0 | all | LOW | This spec doc + ADR (foundation) |
| C1 | #1 | LOW | Add 4 missing generators (codex, zcode, windsurf, openclaw) |
| C2 | #1 | LOW | Plugin-generator spec doc + `_TEMPLATE_gen_agent.py` |
| C3 | #2 | LOW | Drive `.~<agent>/` skeleton + `setup-agent-drive.sh` |
| C4 | #2 | MED | Migrate `hermes-sync/` → `.~hermes/` (aliased, optional) |
| C5 | #3 | MED | Cross-agent hook adapter framework |
| C6 | #3 | LOW | `check_machine_path.py` + `security_patterns.yaml` |
| C7 | #3 | LOW | pre-commit + CI gates |
| C8 | #4 | LOW | `SKILL-INDEX.md` brain + `gen_skill_index.py` |
| C9 | #5 | MED | Strict dedup batch 1 (~5 skills) |
| C10 | #5 | MED | Strict dedup batch 2 + motion decision |

---

## 9. Scope boundaries (what this spec does NOT do)

- Does NOT change the lifecycle router or Iron Laws (stable).
- Does NOT rebuild registry schema (v2 stays; we use existing alias/status fields).
- Does NOT delete domain skills outside Goal #5 list (user chose keep-all-domains).
- Does NOT move existing Drive data (C4 hermes migration is the only move, aliased).
- Does NOT replace the MCP `awiki` server (`SKILL-INDEX.md` complements it).

---

## 10. Open questions (resolved during implementation, not blocking)

1. Motion trilogy: merge to 1, or keep 3? (decide in C10)
2. `eval-harness` vs `agent-eval`: same job or distinct niche? (investigate in C9)
3. Pre-commit hook install: `core.hooksPath` vs repo-local `.git/hooks/`? (decide in C7)

---

*USA-1 — 2026-07-14 — A-Wiki v1.2*
