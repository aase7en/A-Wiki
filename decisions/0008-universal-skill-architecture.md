---
adr: 0008
title: Universal Skill Architecture (USA-1) for all current and future agents
status: Accepted
date: 2026-07-14
tags: [architecture, skills, multi-agent, security, storage]
related_journal: []
supersedes: []
superseded_by: []
---

# ADR-0008: Universal Skill Architecture (USA-1) for all current and future agents

## Status
**Accepted** — 2026-07-14. Implementation in chunks C0–C10 (non-breaking).

## Context

A-Wiki is a live second-brain used daily across **9 agents**: Codex, Claude Code,
Antigravity, ZCode, Hermes, Windsurf, OpenClaw, Kilo, Cline. The user
commissioned a world-class architecture engineer to design how every skill —
present and future — can work across all of them.

Audit findings driving this decision:

1. `skills-registry.json` (schema v2, 365 entries) is a solid SoT but its
   generator layer covers only **6/9 agents** — Codex, ZCode, Windsurf, and
   OpenClaw have no generator surface.
2. The `aliases` + `status: canonical/alias/deprecated` mechanism exists but is
   barely used (5 alias / 1 deprecated). Dedup is currently "delete files"
   instead of "alias in registry".
3. The Drive layer (`A-Wiki-Data`) has shared pools (`raw/`, `personal/`,
   `hermes-sync/`) but **no per-agent `.~<agent>/` isolation**. Agent state
   pollutes the repo or mixes with other agents.
4. Security hooks (`check_secret_leak.py`, `check-privacy.py`) run only on
   Claude/Codex PreToolUse. Other agents are unenforced; there is no
   pre-commit or CI gate.
5. There is **no readable central "skill brain"** — the registry is a machine
   blob, AGENTS.md is config (too large to also be a catalog).
6. ZCode reads a `.zcode/skills/` symlink farm where 306/330 links point to a
   **stale** `~/.claude/skills/` snapshot, drifting from the repo.

Constraints:

- **Non-breaking** (live system, used daily).
- **Keep all skill domains** (user chose not to drop homelab/motion/media/etc.).
- **Strict dedup only** (no aggressive per-language merging).
- **Future-proof** (a new agent must be addable in 3 steps).

## Decision

Adopt the **Universal Skill Architecture (USA-1)**, defined in
[`docs/architecture/universal-skill-architecture.md`](../docs/architecture/universal-skill-architecture.md).
Six binding principles:

1. **Registry is the SoT** — `skills-registry.json` drives every surface.
2. **Plugin generators** — new agent = `gen_<agent>.py` + 1 line in `GENERATORS`.
3. **Alias, don't delete** — dedup uses registry `status: alias` + `canonical:`.
4. **Three-layer storage** — repo · shared Drive pool · `.~<agent>/` Drive.
5. **Defense in depth** — PreToolUse (all agents) + pre-commit + CI.
6. **Non-breaking** — each chunk is one atomic, reversible commit on `main`.

Implementation proceeds in 11 chunks (C0–C10), each independently shippable.

## Alternatives Considered

### Option A: Greenfield registry v3 rebuild
- **Pros:** cleanest schema, no legacy baggage.
- **Cons:** high migration risk on a live system; throws away a working v2 SoT.
- **Why not chosen:** violates the user's "non-breaking" requirement.

### Option B: Hand-edit per-agent config (current approach, extended)
- **Pros:** no new generator code; explicit.
- **Cons:** doesn't scale; adding the 10th agent means editing N files; drift
  guaranteed.
- **Why not chosen:** violates "future-proof / plugin generator" requirement.

### Option C (chosen): USA-1 — registry-driven + plugin generators + alias dedup
- **Pros:** reuses the existing v2 SoT; adds agents additively; dedup is
  reversible (alias, not delete); three-layer defense for security; readable
  brain for all agents.
- **Cons:** more moving parts (generators, adapters, `.~<agent>/`); requires
  careful per-chunk validation.
- **Why chosen:** satisfies all six user goals + all constraints; non-breaking;
  each chunk has a clean rollback.

## Consequences

### Positive
- All 9 agents (and any future agent) see the **same canonical skill set**,
  generated from one SoT.
- Dedup becomes safe and reversible (alias in registry; `regen` propagates).
- Per-agent Drive isolation (`.~<agent>/`) stops state pollution and protects
  privacy between agents.
- Security is enforced at three layers; no agent can bypass the secret/privacy
  gate by being "less integrated".
- A readable `SKILL-INDEX.md` becomes the shared brain every agent reads at
  session start.
- Adding agent #10 is a 3-step, ~44-line task.

### Negative / Trade-offs
- More files to maintain (4 new generators, adapter framework, `.~<agent>/`
  skeletons, security YAML, CI workflow).
- The cross-agent hook adapter is the most complex piece (C5) — each agent's
  hook payload format differs.
- ZCode drift fix (C1) changes how `.zcode/skills/` is populated; needs a
  one-time linker re-run on each machine.

### Risks
- A generator emitting the wrong format could break one agent's skill discovery.
  Mitigation: `--validate` + `--check` (drift CI) before each merge; rollback =
  revert one commit.
- Hook adapters could mis-translate a tool payload. Mitigation: adapters are
  thin translators; shared logic is the already-working `check_secret_leak.py`;
  per-agent smoke test in C5.
- Drive `.~<agent>/` not synced on a machine without Drive. Mitigation:
  `setup-agent-drive.sh` is idempotent + optional; agents degrade gracefully.

## Revisit Conditions

- If a 10th agent cannot be added in the 3-step plugin workflow → revisit §3.
- If the alias-based dedup causes an agent to silently resolve to the wrong
  canonical → revisit §7.2 (add a hard-reference scanner to the registry
  validator).
- If the three-layer security defense produces too many false-positive blocks
  → revisit §5 (tune `security_patterns.yaml`, add allowlist mechanism).
- If `SKILL-INDEX.md` grows too large to read at session start → split by domain
  or switch to MCP-served index (§6.2 option).

## References

- [`docs/architecture/universal-skill-architecture.md`](../docs/architecture/universal-skill-architecture.md) — the full spec.
- [`scripts/skills_registry/__init__.py`](../scripts/skills_registry/__init__.py) — `VALID_DOMAINS`, `Registry`, alias resolution.
- [`scripts/regen-skill-surfaces.py`](../scripts/regen-skill-surfaces.py) — `GENERATORS` dict, regen/check/bootstrap/validate commands.
- ADR-0007 (graph hygiene vs capability map) — precedent for SoT discipline.
- Iron Law #9 (skill registry is the single source of truth).
