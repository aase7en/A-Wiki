# Cross-Agent Handoff — Hermes Cross-Agent Integration + Subagent

> **Resume marker:** planning DONE · next: `chunk(hermes-a)` (build gen_hermes.py)
> **Last session:** 2026-07-02 (ZCode, builtin:zai-coding-plan/GLM-5.2)
> **Parent architecture:** `docs/architecture/skill-architecture-plan.md` (the 5-layer registry system this extends)
> **To resume:** `git pull origin main` → read THIS file → execute Chunk A → B → C → D in order.

This handoff covers the Hermes-specific work that extends the Universal Skill
Architecture (already shipped, 11 commits `41e2e2e`→`06746cb`) to the Hermes
agent running 24/7 on Raspberry Pi 5.

---

## 🔒 SECURITY — do this BEFORE any live work (Step 0)

The previous session had Umbrel SSH + Portainer credentials pasted directly in
chat (now in conversation logs). **Before Chunk C (any live Pi5 work):**

1. **Rotate** ALL credentials on the Umbrel + Portainer admin interfaces (the
   ones exposed in chat are compromised).
2. **Save** the NEW credentials to `drive/.secrets/hermes.env` (gitignored):
   ```
   UMBREL_HOST=<your-tailscale-host>
   UMBREL_SSH_USER=<rotated>
   UMBREL_SSH_PASS=<rotated>
   PORTAINER_USER=<rotated>
   PORTAINER_PASS=<rotated>
   ```
3. Agents read via `scripts/lib/drive_secrets.py` — NEVER from chat. If
   `drive/.secrets/hermes.env` is missing, STOP and ask the user to create it.

---

## RCA findings (already gathered, evidence-backed — do NOT re-investigate)

### Privacy warning verdict: FALSE-POSITIVE + 2 low-severity real leaks
- `/home/node/` ×10, `/home/pi/` ×7 → Docker `node` user + RPi OS `pi` user. **System users, NOT personal.** `check-privacy.py` HOME_PATH_PATTERNS regex is too broad (no system-user allowlist).
- **Real leaks (low severity)**: a personal macOS username literal (`/Users/<personal>`) in `scripts/hermes/export-macbook-config.sh:114` + `scripts/hermes/IMPORT-NOTES.md:43`. Fix = replace with `/Users/<you>`.
- **0 real secrets, 0 emails leaked.** Secrets are correctly fetched at runtime from Drive.

### 3 gaps preventing cross-agent skill use
| # | Gap | Evidence |
|---|-----|----------|
| 1 | **No `gen_hermes.py`** — registry covers 9 agents but Hermes generator never built | `scripts/regen-skill-surfaces.py:52-71` (no hermes), `scripts/skills_registry/generators/` (no gen_hermes), `generated/` (no hermes.*) |
| 2 | **All 331 skills are `agents:["all"]`** — no per-agent targeting | `skills-registry.json` (grep `'"hermes"'` = 0 hits) |
| 3 | **Hermes has no auto-discovery** — `awiki-init-pi5.sh` symlinks only ~18 lifecycle skills | `scripts/hermes/awiki-init-pi5.sh:53-90`; 313 of 331 skills invisible to Hermes |

### Hard constraints (CANNOT be worked around — design within these)
| Constraint | Evidence | Implication |
|-----------|----------|-------------|
| **No native subagent/fan-out** | No `/task` command; `parallel_fan_out` in lifecycle-config.json is aspirational; `.kilo/plans/awiki-lifecycle-skills.md:530` checkbox unchecked | "Subagent" must be sequential persona passes via wrapper |
| **Free-tier models** (DeepSeek-V4-Flash, Gemini-Flash-Lite) | `scripts/hermes/model-pool/model-pool.json`, `dual-mode-router.py:7-31`; 15-30 RPM, weaker tool-calling | Don't route all 331 skills; tag only lifecycle + Telegram-relevant |
| **Read-only A-Wiki mount** | Pi5 Docker: `~/A-Wiki:/A-Wiki:ro` (`docs/runbooks/hermes-raspberry-pi5.md:182-184`) | Hermes is read-only consumer; can't commit back |
| **Heavy context preload** | SOUL.md + MEMORY.md + USER.md + skills metadata upfront (`wiki/entities/ai-tools/hermes-agent.md:94`) | Small-context free models (8k-32k) struggle; keep tagged skill set small |

---

## Design decisions (user-approved, all Recommended)

| Decision | Choice | Why |
|----------|--------|-----|
| Subagent realization | **Sequential persona passes via wrapper script** | Hermes has no native fan-out; sequential `hermes chat -q` per persona is realistic on free-tier |
| Skill scope | **Build `gen_hermes.py` + per-agent tagging** | Closes Gap #1+#2; generator emits `hermes.skills.json` filtered by `agents` containing `"hermes"` |
| Session handoff | **This doc + numbered resumable steps** | Context was large; fresh session resumes cleanly |
| Claude guideline | **Pending** — user pastes artifact text in new session | webReader couldn't load client-side React SPA at https://claude.ai/public/artifacts/5461ce71-1168-43e3-a6af-4df88941e322 |

---

## Execution — 4 chunks (do in order, commit + push each boundary)

### Chunk A — `chunk(hermes-a)`: gen_hermes.py + tagging + privacy fix (SAFE, repo-only)

**Goal:** Close the skill-architecture Hermes gap + fix privacy false-positives.

**A1. Build `scripts/skills_registry/generators/gen_hermes.py`**
- Mirrors `gen_cline.py` / `gen_antigravity.py` structure: `render(registry)` + `filename`.
- Emits `hermes.skills.json` listing skills where `agents` array contains `"hermes"`.
- Wire into `GENERATORS` dict in `scripts/regen-skill-surfaces.py:52-71`.
- Wire into `SURFACES` dict in `scripts/verify-skill-surfaces.py:38-52`.
- Add Hermes to the agent list in `tests/test_cross_agent_visibility.py`.

**A2. Tag relevant skills in `skills-registry.json`** with `agents:["all","hermes"]`
- Heuristic for WHICH skills to tag (keep set small — free-tier context budget):
  - All lifecycle skills (`lifecycle_phase` != none) — ~13 skills
  - Telegram-relevant domains: `wiki`, `pharmacy`, `thai` — ~20 skills
  - Meta-skills: `awiki-lifecycle-router`, `a-wiki-telegram`, `wiki-search-local`, `ingest-source`, `lint-wiki`, `delegate-subagent`, `debug-mantra`, `scrutinize`, `post-mortem`
- Target: ~40-50 skills tagged for Hermes (NOT all 331).
- Run `python scripts/skills_registry/consolidate.py` is NOT needed (no dedup); just edit registry JSON directly or write a one-shot tagger.

**A3. Privacy fix**
- Replace personal macOS username literal (`/Users/<personal>`) → `/Users/<you>` in:
  - `scripts/hermes/export-macbook-config.sh:114`
  - `scripts/hermes/IMPORT-NOTES.md:43`
- (Optional) Add system-user allowlist to `scripts/check-privacy.py` HOME_PATH_PATTERNS handling: skip `/home/(node|pi|umbrel|ubuntu|root|nobody)/`. This silences the 17 false-positives.

**A4. Verify + commit**
- `python scripts/regen-skill-surfaces.py` (regen all surfaces including new hermes.skills.json)
- `python scripts/regen-skill-surfaces.py --check` (0 drift)
- `python scripts/verify-skill-surfaces.py` (now shows 6 surfaces)
- `python -m pytest tests/test_skills_registry.py tests/test_check_skill_registry.py tests/test_cross_agent_visibility.py -q` (all green)
- `python scripts/check-privacy.py` (hermes false-positives gone or reduced)
- **Commit:** `chunk(hermes-a): gen_hermes.py + per-agent tagging + privacy fix`

### Chunk B — `chunk(hermes-b)`: sequential persona orchestrator (SAFE, repo-only)

**Goal:** Realize "subagent" via sequential persona wrapper (per user's choice).

**B1. Read the Claude subagent guideline** (user pastes artifact text at session start).
- The artifact URL is a client-side React SPA — webReader can't extract it.
- User will paste the text. Adapt its principles to Hermes's sequential-only reality.

**B2. Build `scripts/hermes/persona-orchestrator.sh`**
- Sequential `hermes chat -q --persona <name> "$TASK"` per persona.
- Personas from `agents/`: `code-reviewer.md`, `test-engineer.md`, `security-auditor.md` (from lifecycle-config.json `parallel_fan_out`).
- Capture each output to a temp file, merge to a single report.
- `--dry-run` flag: parse personas, print the commands it WOULD run, exit 0 (for tests, no Hermes call).
- Rate-limit awareness: sleep between calls (configurable, default respects 15-30 RPM free-tier).
- Honest in comments: "this is SEQUENTIAL, not parallel — Hermes has no native fan-out."

**B3. New skill `skills/awiki/hermes-fan-out/SKILL.md`**
- Documents the sequential-fan-out pattern.
- Honest about no-concurrency limit.
- How to invoke via Telegram: `/review <task>` → triggers orchestrator.
- Frontmatter: `name: hermes-fan-out`, `domain: [ai-ops]`, `lifecycle_phase: review`, `agents: ["all","hermes"]` (tag for Hermes).

**B4. Tests**
- `tests/test_persona_orchestrator.py` — dry-run mode validates persona parsing + command construction without calling Hermes.
- Add to the test suite run.

**Commit:** `chunk(hermes-b): sequential persona orchestrator + fan-out skill`

### Chunk C — `chunk(hermes-c)`: live Pi5 verification (NEEDS SSH + secrets)

**⚠️ Prerequisite:** Step 0 (rotate + save credentials to `drive/.secrets/hermes.env`) MUST be done first.

**C1. Read secrets** via `scripts/lib/drive_secrets.py` — NEVER from chat.
- If `drive/.secrets/hermes.env` missing → STOP, ask user.

**C2. SSH + Portainer inspect**
- SSH to `<UMBREL_HOST from drive/.secrets/hermes.env>` (user/pass from secrets).
- Portainer API (creds from secrets): GET `/api/endpoints`, `/api/containers`, inspect Hermes container.
- Capture: container state, mode (ECO/PRO), model-pool state (`rate-limit-state.json`, `restrict-state.json`), RPM headroom.

**C3. Re-seed skills on Pi5**
- `bash scripts/hermes/awiki-init-pi5.sh` — re-creates symlinks. Now reads `hermes.skills.json` (from Chunk A) to know which skills to symlink (if A also updated awiki-init-pi5.sh to read the manifest; otherwise manual).
- Verify Hermes sees the tagged skills: `hermes skills list` or equivalent.

**C4. Telegram smoke test**
- `/wiki <query>` → FTS5 search reply.
- `/search <query>` → same.
- `/review <task>` → confirm persona-orchestrator fires (sequential personas).
- Capture timing: how long does a 3-persona sequential pass take on free-tier?

**C5. Update runbook**
- `docs/runbooks/hermes-raspberry-pi5.md`: add findings (actual model in use, RPM headroom, orchestrator timing).
- Note any free-tier throttling observed.

**Commit:** `chunk(hermes-c): live Pi5 verification + runbook update`

### Chunk D — `chunk(hermes-d)`: this handoff doc (DONE in this session)

✅ This file.

---

## Resume checklist (run at start of new session)

```bash
git pull origin main
# Verify parent architecture intact
python scripts/regen-skill-surfaces.py --check      # 0 drift
python -m pytest tests/test_skills_registry.py tests/test_check_skill_registry.py tests/test_cross_agent_visibility.py -q
# Read this handoff
cat docs/architecture/hermes-cross-agent-handoff.md
# Check prerequisites for the chunk you're starting
ls drive/.secrets/hermes.env 2>/dev/null && echo "secrets ready for Chunk C" || echo "secrets MISSING — needed for Chunk C"
```

---

## Key file map (for the resuming agent)

| File | Purpose | Chunk |
|------|---------|-------|
| `scripts/skills_registry/generators/gen_hermes.py` | NEW — Hermes surface generator | A |
| `skills-registry.json` | EDIT — add `"hermes"` to agents[] on ~40-50 skills | A |
| `scripts/hermes/export-macbook-config.sh:114` | EDIT — privacy fix | A |
| `scripts/hermes/IMPORT-NOTES.md:43` | EDIT — privacy fix | A |
| `scripts/check-privacy.py` | EDIT (optional) — system-user allowlist | A |
| `scripts/hermes/persona-orchestrator.sh` | NEW — sequential fan-out wrapper | B |
| `skills/awiki/hermes-fan-out/SKILL.md` | NEW — fan-out skill doc | B |
| `tests/test_persona_orchestrator.py` | NEW — dry-run test | B |
| `scripts/hermes/awiki-init-pi5.sh` | EDIT — read hermes.skills.json for symlinks | C |
| `docs/runbooks/hermes-raspberry-pi5.md` | EDIT — live findings | C |
| `drive/.secrets/hermes.env` | NEW (private) — rotated credentials | Step 0 |

---

## What this plan does NOT do (honest limits)

- ❌ Does NOT give Hermes native concurrency (impossible — framework limitation).
- ❌ Does NOT let Hermes commit to A-Wiki (read-only mount by design).
- ❌ Does NOT route all 331 skills to Hermes (free-tier context budget; only ~40-50 tagged).
- ❌ Does NOT use chat-supplied credentials (security; live work reads `drive/.secrets/`).
- ❌ Does NOT build the orchestrator before reading the Claude guideline (Chunk B1 prerequisite).

---

*Generated 2026-07-02 · Resumable via `git pull` + this file · Parent: skill-architecture-plan.md*
