# Cross-Agent Handoff — Hermes Cross-Agent Integration + Subagent

> **Resume marker:** ✅ Chunk A + B + D DONE · 🔶 Chunk C PARTIAL — C2 (inspect) DONE, C3 (re-seed) REDIRECTED to C3' (fix symlink split-brain), C4 (Telegram smoke) DEFERRED (needs bot access)
> **Last session:** 2026-07-02 (ZCode, builtin:zai-coding-plan/GLM-5.2)
> **Parent architecture:** `docs/architecture/skill-architecture-plan.md` (the 5-layer registry system this extends)
> **To resume:** `git pull origin main` → read THIS file → see §"Chunk C — live Pi5" below. Remaining live work = C3' (fix 17 stale symlinks) + C4 (Telegram smoke, needs bot token).

This handoff covers the Hermes-specific work that extends the Universal Skill
Architecture (already shipped, 11 commits `41e2e2e`→`06746cb`) to the Hermes
agent running 24/7 on Raspberry Pi 5.

---

## 🔒 SECURITY — Step 0 (DONE 2026-07-02)

The previous session had Umbrel SSH + Portainer credentials pasted directly in
chat (now in conversation logs). Rotation + verification performed 2026-07-02.

**⚠️ Mechanism correction (was wrong in this doc):** secrets are NOT stored in a
per-tool `drive/.secrets/hermes.env` file. `scripts/lib/drive_secrets.py` reads a
single flat KEY=VALUE file at `drive/.secrets` (which symlinks to
`<Drive>/A-Wiki-Data/.secrets`). The keys live as top-level entries there:

```
UMBREL_HOST=<your-tailscale-host>      # stored as full URL e.g. http://umbrel-1.tail<id>.ts.net/
UMBREL_SSH_USER=<rotated>
UMBREL_SSH_PASS=<rotated>
PORTAINER_USER=<rotated>
PORTAINER_PASS=<rotated>
# + DEEPSEEK_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY, ... (9 API keys)
```

**Verified 2026-07-02:** `.secrets` mtime = today, all 5 required keys PRESENT
and non-empty. Resolve via `python scripts/lib/drive_secrets.py --check` (never
read values from chat). If a key is missing, STOP and ask the user.

**⚠️ Residual concern to confirm with user:** the sudo password echoed during
PTY sessions looked like a weak/default value (`Admin1234!`-style). Confirm with
the user whether the Umbrel admin password was actually rotated, or whether only
the SSH account was changed.

---

## 🔴 LIVE PI5 REALITY (verified 2026-07-02, read-only — OVERRIDES several RCA assumptions)

> Read this BEFORE touching the Pi5. Several "hard constraints" in the RCA
> section below were theory; the live container differs materially.

### Container & install (containerized Umbrel, NOT native venv)

| Fact | Value | Evidence |
|------|-------|----------|
| Container | `hermes-agent_web_1` | `docker ps` |
| Image | `ghcr.io/getumbrel/hermes-agent-umbrel:v2026.6.19-1` | inspect |
| Uptime | 3 days (since 2026-06-29T02:46Z) | inspect |
| `HERMES_HOME` | `/opt/data` (NOT `$HOME/.hermes`) | container ENV |
| Mode | **`freeforall`** (not ECO/PRO) | `/opt/data/.hermes-mode` |
| Telegram gateway | **connected/running** (PID 143) | `gateway_state.json` |
| Mounts | **only** `…/hermes-agent/data/hermes → /opt/data` (rw) | inspect |

**⚠️ The "read-only `~/A-Wiki:/A-Wiki:ro` mount" assumed in RCA + the runbook DOES NOT EXIST.** A-Wiki is git-cloned *inside* the persistent data volume, writable.

### A-Wiki clones — TWO, split-brain (root cause of C3' work)

Two independent clones (different inodes) live in the container:

| Clone | Path | Remote | HEAD | Role |
|-------|------|--------|------|------|
| **CANONICAL** | `/opt/data/A-Wiki` | `git@github.com:` (SSH) | `ad9331c` | config `cwd`, boot script paths, **35 commits ahead** |
| stale | `/opt/data/home/A-Wiki` | `https://` (HTTPS) | `df564bd` | merge-base of the two; frozen |

Evidence the canonical one is `/opt/data/A-Wiki`: `config.yaml:74 cwd: /opt/data/A-Wiki` and `.start-hermes.sh` references `model-roster.conf`, `model-pool.json`, and `cd /opt/data/A-Wiki`. `home/A-Wiki` is a strict ancestor (`git merge-base --is-ancestor` YES), 0 commits ahead of the merge-base.

### Skill symlinks — SPLIT (10 canonical / 17 stale)

Hermes loads skills from `/opt/data/skills/` (37 dirs). The A-Wiki-backed ones are symlinks; they point at TWO different clones depending on when they were created:

- **10 symlinks (Jun 23+) → `/opt/data/A-Wiki`** (canonical, up-to-date): `awiki/{awiki-lifecycle-router, define, plan, verify, review, ship}`, `software-development/{debug-mantra, scrutinize, post-mortem, management-talk}`
- **17 symlinks (Jun 20) → `/opt/data/home/A-Wiki`** (stale, 35 commits behind): ALL of `/opt/data/skills/lifecycle/*` (13 lifecycle skills) + `awiki/{lifecycle-router, native/{debug-mantra, scrutinize, post-mortem}}`
- **0 broken symlinks** (both clones still present), so nothing visibly errors — but skill *content* on the stale side lags.
- **Duplicate entries**: e.g. `awiki-lifecycle-router` (→ canonical) vs `lifecycle-router` (→ stale) = same skill loaded twice under two names.

**No `hermes.skills.json` exists on the Pi5** in either clone — Chunk A's manifest has not been shipped to the device yet.

### Model pool + mode

- `default: cohere/north-mini-code:free`, provider openrouter, `fallback_providers: ["deepseek","gemini"]`
- Pool (19 models, 10–60 RPM each): gemini-2.5/3-flash family, glm-4.6v/4.7-flash, deepseek-v4-flash-lite, llama-4-maverick:free, mixtral-8x7b, grok-3-mini, Qwen3-32B, etc.
- `rate-limit-state.json`: 1 active 60s cooldown on `gemini/gemini-3-flash-preview` at inspection time. **No `restrict-state.json`** (referenced in original RCA — does not exist).

### SSH access notes (for the resuming agent)

- Host: `umbrel-1.tail<id>.ts.net` (Tailscale, `100.111.37.13`), ports 22/443/80 open.
- `umbrel` user SSH works with rotated password; **not in `docker` group** → must `sudo docker`. Sudo is **passwordful** (`sudo -n` fails). Use `sudo -S` with the password piped via stdin (paramiko `chan.sendall`).
- No `sshpass`/`plink` on the Windows dev box; `paramiko` was pip-installed for non-interactive SSH. Reuse the paramiko idiom from the 2026-07-02 session.

### Implications for the remaining work

1. **C3 as originally written is WRONG** — `awiki-init-pi5.sh` assumes a native-venv `$HOME/.hermes` layout that does not exist here. Do NOT run it on this Pi5.
2. The real task is **C3' — fix the symlink split-brain**: repoint the 17 stale `home/A-Wiki`-backed symlinks at the canonical `/opt/data/A-Wiki`, remove the duplicate `lifecycle-router` entry, and fast-forward the canonical clone to current `main` so Chunk A/B work lands.
3. **C4 (Telegram smoke) needs bot access** the dev box doesn't have → deferred; commands documented below.
4. `awiki-hermes-integration` skill (v2.0.0, Jun 30, lives at `/opt/data/skills/awiki-hermes-integration/`) is a separate, pre-existing integration path pursued directly on-device — do not confuse it with this handoff's lifecycle-skill approach.

---

## RCA findings (theory — gathered pre-inspection; superseded by §"LIVE PI5 REALITY" above where they conflict)

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

### Hard constraints (design within these; ⚠️ = revised by live inspection)
| Constraint | Evidence | Implication |
|-----------|----------|-------------|
| **No native subagent/fan-out** | No `/task` command; `parallel_fan_out` in lifecycle-config.json is aspirational; `.kilo/plans/awiki-lifecycle-skills.md:530` checkbox unchecked | "Subagent" must be sequential persona passes via wrapper |
| **Free-tier models** (DeepSeek-V4-Flash, Gemini-Flash-Lite) | `scripts/hermes/model-pool/model-pool.json`, `dual-mode-router.py:7-31`; 15-30 RPM, weaker tool-calling | Don't route all 331 skills; tag only lifecycle + Telegram-relevant |
| ⚠️ ~~**Read-only A-Wiki mount**~~ **REVISED → writable clone(s) in volume** | ~~Pi5 Docker: `~/A-Wiki:/A-Wiki:ro`~~ → reality: clone(s) inside rw `/opt/data` (see §LIVE PI5 REALITY) | Hermes is **not** read-only consumer; the container's clone is writable. Still shouldn't be the commit source — use the dev box for commits. |
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

**A4. Verify + commit** ✅ DONE 2026-07-02
- `python scripts/regen-skill-surfaces.py` (regen all surfaces including new hermes.skills.json) — ✅ 6 surfaces, hermes 21KB
- `python scripts/regen-skill-surfaces.py --check` (0 drift) — ✅ no drift
- `python scripts/verify-skill-surfaces.py` (now shows 6 surfaces) — ✅ 325 canonical visible
- `python -m pytest tests/test_skills_registry.py tests/test_check_skill_registry.py tests/test_cross_agent_visibility.py -q` (all green) — ✅ 66 passed (+7 new)
- `python scripts/check-privacy.py` (hermes false-positives gone or reduced) — ✅ home_path 31→6 (17 system-user FPs silenced, 2 personal-username leaks fixed)
- **Result:** 38 skills tagged for Hermes (13 lifecycle + 20 telegram-domain + 9 meta, deduped). `gen_hermes.py` + `tag_hermes.py` (idempotent heuristic tagger) shipped. **Commit:** `chunk(hermes-a): gen_hermes.py + per-agent tagging + privacy fix`

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

**B4. Tests** ✅ DONE 2026-07-02
- `tests/test_persona_orchestrator.py` — **16 tests, all pure** (no subprocess, no Hermes call). Covers `build_plan` argv shape + sleep math + empty case, `load_personas` from `lifecycle-config.json`, `run` with injectable stub runner, `merge_report` severity sort. Import via `importlib.util` (hermetic to the active venv, which may shadow the module name).
- Added to the test suite: 82 targeted tests pass (66 from Chunk A + 16 new).

**Architecture deviations from original spec (user-approved):**
- **Python module + thin .sh wrapper** (not pure bash). Mirrors `scripts/batch/route.{sh,py}`. Rationale: unit-testable pure functions (`build_plan`, `run`, `merge_report`), Iron Law #1 clean, Pi5-deployable (wrapper calls python3 which exists on Pi5 OS). Handoff wrote `.sh` because its author hadn't seen the repo's `route.sh`/`route.py` pattern.
- **`lifecycle_phase: meta`** (not `review`). User-approved — `skill-frontmatter-schema.md:66` defines `meta` as "Routers, gates, orchestration"; a fan-out dispatcher IS orchestration. Matches the one precedent (`awiki-lifecycle-router`).
- **Pure unit test, no stub hermes binary** (not subprocess test). User-approved — `--dry-run` returns a JSON plan dict, tests assert the plan + merge logic directly. CI-safe, fast, deterministic.

**Result:** `scripts/hermes/persona-orchestrator.py` (pure logic + CLI, dry-run default) + `persona-orchestrator.sh` (route.sh-style wrapper) + `skills/awiki/hermes-fan-out/SKILL.md` (registered as 39th Hermes skill, `domain: [ai-ops]`, `lifecycle_phase: meta`). 16/16 tests green, 0 drift, 326 canonical visible.

**Commit:** `chunk(hermes-b): sequential persona orchestrator + fan-out skill`

### Chunk C — `chunk(hermes-c)`: live Pi5 verification + doc reconciliation

**C1. Secrets** ✅ DONE 2026-07-02 — `drive/.secrets` present, all 5 keys non-empty, mtime today. (Note: mechanism is flat `drive/.secrets`, not `hermes.env` — see Step 0.)

**C2. Container + pool inspect** ✅ DONE 2026-07-02 (read-only) — full findings in §"LIVE PI5 REALITY" above. Summary: containerized Umbrel install, `freeforall` mode, Telegram gateway connected, canonical clone `/opt/data/A-Wiki` (`ad9331c`, SSH remote) with stale twin `/opt/data/home/A-Wiki` (`df564bd`, HTTPS), 10/17 symlink split, no `hermes.skills.json` on device, 1 transient rate-limit cooldown.

**C3 → C3'. Fix the symlink split-brain** 🔶 NOT DONE — the real task, redirected from the (wrong) original C3.

> ⚠️ Do NOT run `awiki-init-pi5.sh` here — it targets a native-venv `$HOME/.hermes` layout that does not exist on this containerized install and would create a third, conflicting link tree.

**C3'.0 Snapshot (safety):** before touching symlinks, capture current state so it's reversible.
```bash
# inside container, as hermes user
docker exec --user hermes hermes-agent_web_1 bash -lc '
  SNAP=/opt/data/.awiki-symlink-snap-$(date +%Y%m%d-%H%M%S).tar.gz
  tar czf "$SNAP" -C /opt/data/skills . 2>/dev/null
  echo "snapshot: $SNAP"
'
```

**C3'.1 Fast-forward canonical clone to current `main`** (lands Chunk A/B work on-device):
```bash
docker exec --user hermes -e GIT_CONFIG_GLOBAL=/tmp/gitcfg hermes-agent_web_1 bash -lc '
  git config --global --add safe.directory "*"
  cd /opt/data/A-Wiki
  git fetch origin main
  git log --oneline -1 HEAD; echo "→ main:"; git log --oneline -1 origin/main
  # fast-forward only; if non-ff, STOP and surface to user (local commits diverged)
  git merge --ff-only origin/main && echo "FF OK" || echo "NON-FF — investigate before forcing"
'
```

**C3'.2 Repoint the 17 stale symlinks** at the canonical clone (idempotent — only rewrites links whose target contains `/home/A-Wiki`):
```bash
docker exec --user hermes hermes-agent_web_1 bash -lc '
  cd /opt/data/skills
  while IFS= read -r link; do
    cur=$(readlink "$link")
    new=${cur//\/opt\/data\/home\/A-Wiki/\/opt\/data\/A-Wiki}
    [ "$cur" = "$new" ] && continue
    ln -sfn "$new" "$link" && echo "relinked: $link -> $new"
  done < <(find . -maxdepth 3 -type l -lname "*home*A-Wiki*")   # matches /opt/data/home/A-Wiki (stale twin); avoids the canonical /opt/data/A-Wiki
'
```

**C3'.3 Remove duplicate entries** that are the same skill under two names (e.g. `awiki/lifecycle-router` is the stale twin of `awiki/awiki-lifecycle-router`):
```bash
# After C3'.2 both point at the same target; drop the redundant name.
docker exec --user hermes hermes-agent_web_1 bash -lc '
  for dup in /opt/data/skills/awiki/lifecycle-router; do
    [ -L "$dup" ] && rm "$dup" && echo "removed duplicate: $dup"
  done
'
```
(Audit first with `find /opt/data/skills -type l -lname "*awiki-lifecycle-router*"` to see all names pointing at the router before deleting.)

**C3'.4 Ship `hermes.skills.json` to device** (from Chunk A; gives Hermes the tagged manifest to consume, and closes the original Gap #3):
```bash
# from the dev box, after the canonical clone is at current main
docker cp generated/hermes.skills.json hermes-agent_web_1:/opt/data/A-Wiki/generated/hermes.skills.json
# or, since the clone is now FF'd, it already contains the file from the repo
```

**C3'.5 Verify** Hermes sees the reconciled set (does not require a restart — Hermes scans skill dirs lazily, but a gateway restart clears any cache if a skill is missing):
```bash
docker exec --user hermes hermes-agent_web_1 bash -lc '
  echo "=== symlinks now point at ==="
  find /opt/data/skills -maxdepth 3 -type l -printf "%l\n" | grep -oE "/opt/data/(home/)?A-Wiki" | sort | uniq -c
  echo "=== broken links ==="; find /opt/data/skills -xtype l | wc -l
  echo "=== canonical HEAD ==="; cd /opt/data/A-Wiki && git log --oneline -1
'
# If a Hermes restart is needed to re-scan:
# docker exec hermes-agent_web_1 bash -lc 'kill -HUP $(cat /opt/data/gateway.pid 2>/dev/null) 2>/dev/null; echo signalled'
```
Expected: all A-Wiki symlinks → `/opt/data/A-Wiki`, 0 broken, HEAD at current main (post Chunk B = `00ee3fd` or newer).

**C4. Telegram smoke test** ⏸ DEFERRED — the dev box has no Telegram bot token. Run these on a machine with bot access (or on the Pi5 itself via the gateway), and record timing for the runbook:

```
/wiki mqtt broker            → expect FTS5 search reply from A-Wiki
/search esp32 temperature    → same search path
/review <paste a small task> → expect persona-orchestrator to fire (3 sequential personas)
```
Capture: did `/review` invoke `scripts/hermes/persona-orchestrator.py`? How long did a 3-persona sequential pass take on free-tier (target: within rate-limit budget at 15-30 RPM/model)? Any throttling observed (check `rate-limit-state.json` cooldowns before/after)?

**C5. Update runbook + this handoff** ✅ DONE 2026-07-02 (this commit) — added §"LIVE PI5 REALITY" to this doc, corrected the read-only-mount hard constraint, and added a "Live Container Reality (verified 2026-07-02)" reconciliation section to `docs/runbooks/hermes-raspberry-pi5.md`. When C3' + C4 land, append their results to both files.

**Commit:** `chunk(hermes-c): live Pi5 inspect + reconcile docs (C2 done, C3' + C4 remaining)`

### Chunk D — `chunk(hermes-d)`: this handoff doc (DONE in this session)

✅ This file.

---

## Resume checklist (run at start of new session)

```bash
git pull origin main
# Verify parent architecture intact
python scripts/regen-skill-surfaces.py --check      # 0 drift
python -m pytest tests/test_skills_registry.py tests/test_check_skill_registry.py tests/test_cross_agent_visibility.py tests/test_persona_orchestrator.py -q
# Read this handoff — esp. §"LIVE PI5 REALITY"
sed -n '/LIVE PI5 REALITY/,/^---$/p' docs/architecture/hermes-cross-agent-handoff.md
# Check secrets (flat drive/.secrets, NOT hermes.env)
python scripts/lib/drive_secrets.py --check
python scripts/lib/drive_secrets.py --list | grep -E 'UMBREL|PORTAINER'   # names only, never values
# Check Pi5 reachability (read-only)
python -c "import socket; h='umbrel-1.tail<id>.ts.net'; print('SSH', 'open' if socket.socket().connect_ex((h,22))==0 else 'closed')"
```

If proceeding to C3' (live symlink fix): start the paramiko session, run C3'.0 snapshot FIRST, then C3'.1–.5 in order, committing results back here + to the runbook. If proceeding to C4: ensure Telegram bot access is available on the working machine.

---

## Key file map (for the resuming agent)

| File | Purpose | Chunk |
|------|---------|-------|
| `scripts/skills_registry/generators/gen_hermes.py` | Hermes surface generator | A ✅ |
| `skills-registry.json` | `agents:["hermes"]` on ~38 skills | A ✅ |
| `scripts/hermes/export-macbook-config.sh` / `IMPORT-NOTES.md` | privacy fix (macOS user literal) | A ✅ |
| `scripts/hermes/persona-orchestrator.{py,sh}` | sequential fan-out (pure logic + wrapper) | B ✅ |
| `skills/awiki/hermes-fan-out/SKILL.md` | fan-out skill doc (39th Hermes skill) | B ✅ |
| `tests/test_persona_orchestrator.py` | 16 dry-run tests | B ✅ |
| `docs/architecture/hermes-cross-agent-handoff.md` | THIS file | C ✅ (D) |
| `docs/runbooks/hermes-raspberry-pi5.md` | EDIT — add "Live Container Reality (2026-07-02)" section | C ✅ |
| `drive/.secrets` (gitignored) | rotated credentials — flat file, NOT `hermes.env` | Step 0 ✅ |
| `scripts/hermes/awiki-init-pi5.sh` | ⚠️ DO NOT RUN on this containerized Pi5 (wrong layout) | — |
| **ON DEVICE** `/opt/data/A-Wiki` | canonical clone (SSH, `ad9331c`→FF to main) | C3' 🔶 |
| **ON DEVICE** `/opt/data/home/A-Wiki` | stale twin (HTTPS, `df564bd`) — candidate for removal after C3' | C3' 🔶 |
| **ON DEVICE** `/opt/data/skills/*` symlinks | 17 to repoint at canonical; 1 duplicate to drop | C3' 🔶 |

---

## What this plan does NOT do (honest limits)

- ❌ Does NOT give Hermes native concurrency (impossible — framework limitation).
- ❌ Does NOT let Hermes commit to A-Wiki (read-only mount by design).
- ❌ Does NOT route all 331 skills to Hermes (free-tier context budget; only ~40-50 tagged).
- ❌ Does NOT use chat-supplied credentials (security; live work reads `drive/.secrets/`).
- ❌ Does NOT build the orchestrator before reading the Claude guideline (Chunk B1 prerequisite).

---

*Generated 2026-07-02 · Resumable via `git pull` + this file · Parent: skill-architecture-plan.md*
