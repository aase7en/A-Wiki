# Cross-Agent Handoff — Hermes Cross-Agent Integration + Subagent

> **Resume marker:** ✅ ALL CHUNKS DONE (A + B + C incl. C3' + C4 + D + **E**). chunk(hermes-e) Phase 1+2 (router + 7 command-skills) shipped 2026-07-07 (`eba10df` + `8935ae7`); Phase 3 (Pi5 deploy) is staged and ready but blocked from THIS session by Fortinet-on-Tailscale — see §"CHUNK E (hermes-e) — Phase 3 deploy" below for the one-command resume.
> **Last session:** 2026-07-07 (ZCode, builtin:zai-coding-plan/GLM-5.2) — chunk(hermes-e) Phase 1+2 done + pushed; Phase 3 deploy script written + ready (in `drive/private-tools/hermes-e/`); could not execute because dev box is behind workplace Fortinet blocking Tailscale (same blocker as C4 — switch to home WiFi to resume).
> **Parent architecture:** `docs/architecture/skill-architecture-plan.md` (the 5-layer registry system this extends)
> **To resume:** run Phase 3 deploy when on a Tailscale-friendly network — see §"CHUNK E (hermes-e) — Phase 3 deploy". Also open: `scripts/investment/` promotion review (see §"Promotion candidate").

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

**C4. Telegram smoke test** ✅ DONE 2026-07-02/03 (executed by user from a phone via Telegram, captured by the resuming agent over SSH). **Outcome: Telegram infra WORKS; the A-Wiki slash-command integration does NOT exist.** See §"C4 RESULTS (2026-07-02/03)" below.

**C5. Update runbook + this handoff** ✅ DONE 2026-07-02 (this commit) — added §"LIVE PI5 REALITY" to this doc, corrected the read-only-mount hard constraint, and added a "Live Container Reality (verified 2026-07-02)" reconciliation section to `docs/runbooks/hermes-raspberry-pi5.md`. When C3' + C4 land, append their results to both files.

**Commit:** `chunk(hermes-c): live Pi5 inspect + reconcile docs (C2 done, C3' + C4 remaining)`

---

## ✅ C3' RESULTS (executed 2026-07-02, ZCode session 2)

All 6 sub-steps of C3' landed. Final reconciled state verified:

| Metric | Target | Result |
|--------|--------|--------|
| A-Wiki symlinks → canonical (`/opt/data/A-Wiki`) | all | **25** ✅ |
| A-Wiki symlinks → stale (`/home/A-Wiki`) | 0 | **0** ✅ |
| Broken symlinks | 0 | **0** ✅ |
| Canonical clone HEAD | current main | **`a37e491`** (post Chunk A/B/C) ✅ |
| `hermes.skills.json` on device | present | **39 skills** at `scripts/skills_registry/generated/` ✅ |
| Duplicate `awiki/lifecycle-router` | removed | removed ✅ |
| Orphan `lifecycle/idea-refine` (target deleted from repo) | — | removed (see below) ✅ |

### Sub-step outcomes

- **C3'.0 snapshot** ✅ — `/opt/data/.awiki-symlink-snap-20260702-054957.tar.gz` (6.2 MB, hermes-owned). Plus an extra safety capture at `/opt/data/.c3prime-safety/` (tracked-modifications.patch + untracked-files.tar.gz) and an **off-device backup** at `drive/private-tools/c3prime/safety-backup/pi5-c3prime-safety.tar.gz` (3-layer reversibility).
- **C3'.1 FF canonical clone** ✅ — required **stash + FF + pop** because the canonical clone was NOT clean (see discovery below). Fast-forwarded `ad9331c → a37e491` (23 commits, lands Chunk A/B/C work on-device).
- **C3'.2 repoint** ✅ — all **17** stale `/opt/data/home/A-Wiki`-backed symlinks rewritten to `/opt/data/A-Wiki` (idempotent; matches the planned list exactly).
- **C3'.3 dedupe** ✅ — removed `awiki/lifecycle-router` (redundant name; canonical `awiki/awiki-lifecycle-router` retained).
- **C3'.4 manifest** ✅ — **doc bug fixed:** `hermes.skills.json` lives at `scripts/skills_registry/generated/hermes.skills.json` (NOT `generated/hermes.skills.json` as the original C3'.4 step said). Confirmed present on-device with 39 Hermes-tagged skills.
- **C3'.5 verify** ✅ — final count 0 broken / 0 stale-twin / HEAD at `a37e491`.

### 🔴 Key discovery (NOT in original plan): canonical clone was a dirty working tree

The "canonical" clone on the device was **not** the read-only consumer the inspection assumed — it was a live working tree with **19 modified tracked files + 22 untracked files existing ONLY on the device** (not in git, not on the dev box). Headline items:

- **`scripts/investment/`** — a complete value-investing system (Piotroski F-Score, Altman Z-Score, Graham criteria, DCF 3-scenario, 3-tier news scanner, TTS audio reports, gold/bitcoin analyzers using CoinGecko/metals.live free APIs). Created 2026-06-27.
- 17 auto-generated indexes (`wiki/context/*`, `.wiki-graph.json`, `brain-map.canvas`, per-subdir `CLAUDE.md`) that conflicted on `stash pop` (auto-gen content from device's 2026-06-29 gen-index run vs the FF'd 2026-06-24 versions) — **resolved via `--theirs`** since these are all machine-regenerated by `gen-index.py` (verified via file headers).
- Wiki summaries: `wiki/context/glmic-{english,thai}-summary-*`, `wiki/synthesis/synth-thai-tax-deduction-document-guide.md`.
- Skill docs: `skill-manage-headroom.md`, `scripts/hermes/enhanced-gemini-integration.md`.

**Secret scan: CLEAN.** Two independent pattern scans (regex for sk-/AKIA/private keys/Bearer + a broader pass for os.environ/api_key=/financial APIs) found **zero hardcoded secrets**. The investment scripts read API keys from env at runtime; the only `GEMINI_API_KEY` references are env-var *names* in docs, not values. **`scripts/investment/` is public-safe and worth keeping.**

**Resolution (user-approved: "Stash+FF+restore แล้ววางแผน promote"):** `git stash --include-untracked` → FF → `git stash pop` → resolved the 17 auto-gen conflicts with `--theirs` (device-side content kept; will be regenerated on next `gen-index.py` run regardless). All 22 untracked files + the clean modified files restored intact. Stash then dropped.

### Orphan symlink: `lifecycle/idea-refine`

After C3'.2 one symlink showed broken — `lifecycle/idea-refine`. Investigation: the target skill `engineering-lifecycle/define/idea-refine/` **existed in the stale twin** (2026-06-20) but **was deleted from main** (replaced by `spec-driven-development`; the DEFINE phase now only contains that one skill). So this was a **pre-existing orphan**, not a C3' regression. Removed it to leave a clean 0-broken state.

### Promotion candidate (deferred follow-up)

`scripts/investment/` (40-entry tarball, 50 KB) + the 3 wiki summaries + 2 skill docs were pulled off-device to `drive/private-tools/c3prime/promote-untracked.tar.gz` (gitignored). **Recommended next step:** review and commit the public-safe subset to the real repo so this work isn't trapped on one device. Note `scripts/investment/output/` contains run-generated sample data (news scans, example analyses) that probably should NOT be committed — just the `.py`/`.md` source.

### Paramiko helper (reusable)

A non-interactive `sudo docker exec --user hermes` helper was written at `drive/private-tools/c3prime/pi5_exec.py` (gitignored, reads credentials from `drive/.secrets` only). Reuse it for any future live-Pi5 work: `python pi5_exec.py "remote-cmd"` or `python pi5_exec.py --check`. Key design points: uses `exec_command` + `sudo -S -p ''` (deterministic, no PTY parsing), `--user hermes` to preserve uid 1000 file ownership, sentinel-based exit-code capture.

---

## 🔴 C4 RESULTS (executed 2026-07-02/03)

User ran the smoke test from a phone via Telegram (the dev box had been blocked from Tailscale by workplace Fortinet; user switched the dev box to home WiFi + Tailscale so the resuming agent could capture device logs over SSH in parallel). Verdict: **the gateway + Telegram path works; the A-Wiki lifecycle slash-command layer does NOT exist on this device.**

### What WORKED ✅

| Input | Result | Evidence |
|-------|--------|----------|
| plain message `สวัสดี` | LLM replied (model `cohere/north-mini-code:free`) | gateway_state telegram=connected, PID 140 alive |
| `/status` | full status block (session id, model, context 91,069/256,000 = 36%, agent-running, connected platforms) | **the only native slash command exercised that worked** |
| cron job `news-analysis-evening` (auto) | full evening news brief in Thai | cron scheduler healthy |

### What did NOT work ❌

| Input | Result | Meaning |
|-------|--------|---------|
| `/search esp32 temperature` | `Unknown command /search. Type /commands...` | **NOT wired** — runbook was wrong |
| `/wiki mqtt broker` | `Unknown command /wiki` | **NOT wired** |
| `/review <task>` | `Unknown command /review` | **NOT wired** |

**Root cause:** The runbook table claiming `/spec /plan /build /review /ship /wiki /search` map to lifecycle skills (runbook §"Slash Commands in Hermes Chat") was **aspiration, never implemented on this device.** Hermes gateway only knows its own native commands (`/status`, cron job management). The A-Wiki lifecycle skills shipped in Chunk A/B/C exist as symlinks + manifest on the device but have **no Telegram trigger** — there is no integration layer mapping `/<cmd>` → skill invocation. Persona-orchestrator likewise is a standalone script with no Telegram entrypoint.

### Secondary observations

- **Model in use:** `cohere/north-mini-code:free` via openrouter (matches `config.yaml` default).
- **Free-tier instability:** 06:51 UTC the gateway logged 3 consecutive API failures (`ReadError`, `Connection reset by peer`, `APIConnectionError`) on `cohere/north-mini-code:free` — context was 35 msgs / ~39,125 tokens. Recovered on retry schedule. No `restrict-state.json` cooldown persisted.
- **Gateway restarted several times** 2026-07-02 (05:19, 06:02, 12:03, 18:04 UTC) — at least the 18:04 one coincided with the `/search`-unknown sequence; cause not pinned (could be container manager or `--replace` self-restart).
- **`rate-limit-state.json` empty before AND after** — no cooldowns observed.

### Implications / what this means for the plan

1. **The handoff's original Gap #3 framing was incomplete.** It assumed symlink + manifest = "skills visible to Hermes." That is true for Hermes' *background* skill loader (evidence: the gateway log shows Hermes patching its own SKILL.md files via self-improvement review). But there is **no user-facing slash-command surface** for A-Wiki lifecycle skills. Closing that gap is a *new* chunk, not part of C3'.
2. **Chunk A/B/C delivered the substrate** (generator, manifest, symlinks, persona-orchestrator script). The missing piece is a **command-router / Telegram handler** that maps `/<cmd>` → `scripts/hermes/persona-orchestrator.py` (or → `scripts/wiki/search-wiki.py` for `/wiki`/`/search`).
3. **Telegram path itself is healthy** — adding the command layer is a pure additive integration, not infra repair. The bot token + webhook + gateway are all confirmed working.

### Honest limits confirmed

- ❌ This plan does NOT (and now we've verified, cannot) expose A-Wiki lifecycle skills via Telegram without additional integration work.
- ❌ Persona-orchestrator has never been invoked over Telegram (no log evidence; the `/review` it was meant to back never reached the orchestrator).
- ✅ All other chunks remain valid: C3' substrate is on-device and reconciled; the command layer can build on it whenever prioritized.

### Follow-up chunk proposal (DONE — see §"CHUNK E (hermes-e)" below)

~~`chunk(hermes-e)`: build a `scripts/hermes/telegram-command-router.{py,sh}` that the gateway can register, mapping `/search`/`/wiki` → `search-wiki.py` and `/review`/`/spec`/`/plan`/`/build`/`/ship` → `persona-orchestrator.py`. Requires understanding Hermes' native command-registration API (not yet investigated). Tracked here so it is not forgotten.~~

**RESOLVED 2026-07-07** — mechanism investigated, Phase 1+2 shipped, Phase 3 ready. See §"CHUNK E (hermes-e)".

### Chunk D — `chunk(hermes-d)`: this handoff doc (DONE in this session)

✅ This file.

---

## CHUNK E (hermes-e) — Telegram Command Router + 7 Command-Skills

> **Status:** Phase 1+2 ✅ DONE + pushed (`eba10df` + `8935ae7`, 2026-07-07). Phase 3 (Pi5 deploy) ⏳ READY but blocked from the authoring session by workplace Fortinet blocking Tailscale (same blocker as C4). Phase 4 (Telegram smoke) ⏳ PENDING Phase 3.

Closes the C4 gap end-to-end: `/wiki /search /review /spec /plan /build /ship` return `Unknown command` on the live Pi5 → after Phase 3+4 they will route to A-Wiki scripts.

### Mechanism investigation (the "not yet investigated" unknown — RESOLVED)

Hermes exposes **two** command-registration paths (verified via upstream docs at `hermes-agent.nousresearch.com/docs/`):

1. **Skills-as-Commands** ✅ (chosen, reliable today): every skill dir under `~/.hermes/skills/` (or `/opt/data/skills/` on the container) is auto-exposed as `/<dirname>` on every messaging platform. LLM interprets the message → invokes a script. Cost: ~1000 free-tier tokens/call.
2. **`quick_commands type:exec`** in `config.yaml`: zero-LLM shell exec. BLOCKED by upstream bug #44718 (the `{args}` placeholder never substitutes) + security concern #5125 (shell injection). Tracked as future optimization.

**Design decision (user-approved):** Skills-as-Commands (Option A) + 7 thin wrapper skills (one per command). The `quick_commands exec` optimization swaps in later when #44718 is fixed in the container's Hermes version.

### Phase 1 — `telegram-command-router.{py,sh}` + tests + command map ✅ DONE

Commit `eba10df`. Mirrors `persona-orchestrator.{py,sh}` architecture exactly (pure router + injectable executor + dry-run default + fail-soft).

| File | Purpose |
|------|---------|
| `scripts/hermes/telegram-command-router.py` | Pure router (`resolve_command`, `build_route`, `load_command_map`) + injectable `execute()` + CLI. Dry-run default (CI-safe). |
| `scripts/hermes/telegram-command-router.sh` | POSIX wrapper (python3 → python → py -3 fallback). 21 lines, copy of persona wrapper. |
| `scripts/hermes/telegram-commands.json` | Route map: 7 commands → `{script, kind, phase}`. Edit to add a command. |
| `tests/test_telegram_command_router.py` | 22 pure tests (Iron Law #1: RED → GREEN). No subprocess, no hermes/search-wiki call. |

**Verified:** 22/22 tests green; end-to-end dry-run + `--apply` sanity (`/wiki mqtt broker` → search-wiki.py → 5 JSON hits, exit 0). 104 tests green total (router + persona + skills registry + cross-agent visibility).

### Phase 2 — 7 command-skills + registry ✅ DONE

Commit `8935ae7`. Each `skills/awiki/<cmd>/SKILL.md` auto-exposes as `/<cmd>` on Telegram.

| Skill | Phase | Routes to |
|-------|-------|-----------|
| `wiki`, `search` | none | `search-wiki.py` (FTS5, Level -1) |
| `review` | review | `persona-orchestrator.py` (3-persona fan-out) |
| `spec` | define | `persona-orchestrator.py` (single-pass draft) |
| `plan` | plan | `persona-orchestrator.py` (single-pass decomposition) |
| `build` | build | `persona-orchestrator.py` (single-pass TDD guidance) |
| `ship` | ship | `persona-orchestrator.py` (fan-out + pre-launch gate) |

- Registry: 7 entries added to `skills-registry.json` (`agents: ["all","hermes"]`). Hermes-tagged count **39 → 46**.
- All 6 surfaces regenerated, 0 drift. `verify-skill-surfaces` OK (358 canonical).
- **Gotcha fixed:** `.gitignore:82` global `build/` rule matched `skills/awiki/build/SKILL.md`. Force-added + added negation `!skills/awiki/build/` so `/build` isn't silently dropped from the Pi5 clone.

### CHUNK E (hermes-e) — Phase 3 deploy ⏳ READY (blocked by Fortinet, not by code)

**Blocker (same as C4):** the dev box used to author chunk(hermes-e) is behind workplace Fortinet which blocks Tailscale. Cannot reach `umbrel-1.tail<id>.ts.net:22` (DNS fail + direct-IP timeout). Switch to home WiFi to resume.

**Resume command (when on a Tailscale-friendly network):**

```bash
# 1. Verify secrets + helper present
python scripts/lib/drive_secrets.py --check
ls drive/private-tools/c3prime/pi5_exec.py drive/private-tools/hermes-e/deploy-pi5.py

# 2. Read-only connectivity check
python drive/private-tools/hermes-e/deploy-pi5.py --check

# 3. Preview the plan (no writes)
python drive/private-tools/hermes-e/deploy-pi5.py --dry-run

# 4. Execute: snapshot → FF clone → 7 symlinks → verify
python drive/private-tools/hermes-e/deploy-pi5.py --apply
```

**What the deploy does (4 steps, all reversible):**
1. `tar czf /opt/data/.hermes-e-skills-snap-<ts>.tar.gz` of `/opt/data/skills/` (rollback anchor)
2. `git fetch origin main && git merge --ff-only` on `/opt/data/A-Wiki` (stash+pop if dirty, C3' pattern) — lands Phase 1+2 on-device (`a37e491` → `8935ae7`)
3. `ln -sfn` 7 entries in `/opt/data/skills/awiki/` → `/opt/data/A-Wiki/skills/awiki/<name>` (idempotent; verifies SKILL.md exists before linking)
4. Verify: each symlink resolves + SKILL.md readable, 0 broken links, HEAD reported

**If `/<cmd>` returns Unknown after deploy** (skill present but gateway didn't rescan):
```bash
python drive/private-tools/hermes-e/deploy-pi5.py --apply --no-ff --rescan
# or restart the container via Umbrel UI
```

**Rollback:** see `drive/private-tools/hermes-e/README.md` (gitignored) for per-step rollback commands.

### Phase 4 — Telegram smoke test ⏳ PENDING Phase 3

After deploy, send from a phone via Telegram and capture the gateway log over SSH in parallel (same pattern as C4):

```
/wiki mqtt broker          → expect 5 FTS5 hits
/search esp32              → same backend as /wiki
/status                    → already worked (native, negative control)
/foobar                    → expect "Unknown command" (negative control)
/review review this PR     → expect sequential fan-out report (~30-60s)
/spec /plan /build /ship   → expect single-pass or fan-out per phase
```

Append results here as §"CHUNK E Phase 4 RESULTS" when done (mirror the C4 RESULTS format).

### Open follow-ups (low priority, separate commits)

- **`quick_commands exec` optimization**: when Hermes bug #44718 is fixed in the container's image, add `quick_commands:` entries to `/opt/data/profiles/<name>/config.yaml` that bypass the LLM (zero-token route). The skill layer remains as graceful fallback. Docs: Hermes "quick commands are checked before skill commands, so you can override skill names."
- **Legacy skill cleanup**: `skills/awiki/a-wiki-commands/SKILL.md` + `skills/awiki/a-wiki-telegram/SKILL.md` declare the command table as aspiration; now that the 7 per-command skills exist, mark them "superseded — see skills/awiki/<cmd>/" and correct the ASPIRATION warning.

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
| **ON DEVICE** `/opt/data/A-Wiki` | canonical clone — **FF'd to `a37e491` 2026-07-02** (C3'.1) | C3' ✅ |
| **ON DEVICE** `/opt/data/home/A-Wiki` | stale twin (HTTPS, `df564bd`) — **orphaned now**; all symlinks repointed away. Candidate for removal. | C3' ✅ |
| **ON DEVICE** `/opt/data/skills/*` symlinks | **25 all → canonical, 0 broken** (was 10 canonical / 17 stale / 1 dup) | C3' ✅ |
| `scripts/skills_registry/generated/hermes.skills.json` | **(corrected path)** 39 skills tagged for Hermes, present on device post-FF | A/C3'.4 ✅ |
| `drive/private-tools/c3prime/pi5_exec.py` | paramiko `sudo docker exec --user hermes` helper (gitignored) | C3' tooling |
| `drive/private-tools/c3prime/promote-untracked.tar.gz` | off-device copy of `scripts/investment/` + wiki summaries (gitignored, 50 KB) | promotion candidate |

---

## What this plan does NOT do (honest limits)

- ❌ Does NOT give Hermes native concurrency (impossible — framework limitation).
- ❌ Does NOT let Hermes commit to A-Wiki (read-only mount by design).
- ❌ Does NOT route all 331 skills to Hermes (free-tier context budget; only ~40-50 tagged).
- ❌ Does NOT use chat-supplied credentials (security; live work reads `drive/.secrets/`).
- ❌ Does NOT build the orchestrator before reading the Claude guideline (Chunk B1 prerequisite).

---

*Generated 2026-07-02 · Resumable via `git pull` + this file · Parent: skill-architecture-plan.md*
