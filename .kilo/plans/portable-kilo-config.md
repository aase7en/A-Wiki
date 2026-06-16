# Plan — Portable Global Kilo Config (Drive-synced, cross-machine)

> Goal: one machine-independent Kilo global config that works identically on the **home Mac** and the **work Windows/WSL PC**, auto-detecting each machine's Google Drive path. Adds consistent Drive file-access (MCP filesystem, `/commands`, provider keys, Drive-synced skills) **without changing any existing AI behavior** (default model, agents, permissions stay verbatim).

## Decisions confirmed with user
- **Work machine**: Windows / WSL (different Google Drive mount path).
- **Drive conveniences (all)**: MCP filesystem → Drive · custom `/commands` · provider keys from `.secrets` · Drive-synced skills.
- **Mechanism**: **Template + render per machine** (mirrors existing `setup-local.sh` / `import-keys.py`).

## Key technical facts (verified)
- Kilo global config = static JSONC at `~/.config/kilo/kilo.jsonc` — **no `${VAR}` interpolation** (per `kilo-config` skill). Portability must come from **render-time substitution**, not env refs.
- Current global config is **pure AI settings** (models/agents/permissions) — no paths, no secrets — but contains stale `.kilocode` text in the `code-skeptic` prompt.
- A-Wiki already has battle-tested cross-OS Drive detection: `scripts/lib/drive_secrets.py::_glob_cloudstorage_drive()` finds Google Drive/OneDrive/Dropbox/iCloud on **macOS/Linux/WSL/Windows** with **no hardcoded account names** (works standalone — does NOT require the `drive/` symlink to exist first). `scripts/drive_path.py::get_drive_root()` is the symlink-based resolver.
- Drive `A-Wiki-Data/` holds: `.secrets` (KEY=VALUE), `personal/journal/{goals.md,handoff.md,log.md,session-memory.md}`, `personal/{exports,wiki-archive}`, `personal-tools/`, `private-tools/`, `raw/`.
- Repo scripts are git-synced → the render script is present on every machine after clone; Drive holds the portable template/commands; the local `~/.config/kilo/` holds the rendered output.

## Architecture (three locations)
```
REPO (git-synced, both machines)        DRIVE/A-Wiki-Data/.config/kilo/ (synced)     ~/.config/kilo/ (local, per-machine)
scripts/setup-kilo-config.sh    ──read──▶ kilo.jsonc.template   ──render──▶  kilo.jsonc  (machine-specific)
scripts/lib/render_kilo_config.py        command/*.md          ──copy────▶  command/*.md
                                          skills/                            skills/  (paths point here)
                                          (source of truth)                  (rendered output, never edited by hand)
```
- **Source of truth** lives in Drive → travels with you, contains NO secrets (placeholders only).
- **Render script** lives in repo → present on every machine.
- **Output** is local + machine-specific + may contain injected keys (personal, never committed).

---

## Phase A — Establish portable source-of-truth in Drive
Create under `<Drive>/A-Wiki-Data/.config/kilo/`:

1. **`kilo.jsonc.template`** — the canonical config. Seed it from the current `~/.config/kilo/kilo.jsonc` (models/agents/permissions verbatim), then:
   - **Fix stale text**: replace `.kilocode/**/*.md` → `AGENTS.md`/`.kilo/` in the `code-skeptic` prompt; drop the generic TS/actor-system rules that don't apply to A-Wiki (ties to the dashboard plan's Phase 3b).
   - **Add `provider` block** (additive) with each entry `"apiKey": "__SECRET_<ENVNAME>__"` for: `google` (`__SECRET_GEMINI_API_KEY__`), `openrouter` (`__SECRET_OPENROUTER_API_KEY__`), `anthropic` (`__SECRET_ANTHROPIC_API_KEY__`), `groq` (`__SECRET_GROQ_API_KEY__`), `deepseek` (`__SECRET_DEEPSEEK_API_KEY__`). Default `model`/`small_model`/`subagent_model`/agent models stay **unchanged** (still `kilo/` + `zai-coding-plan/`).
   - **Add `mcp.drive-files`** filesystem server: `command: ["npx","-y","@modelcontextprotocol/server-filesystem","__DRIVE_PERSONAL__"]`, `enabled: true`. Targets `personal/` only (see Security).
   - **Add `skills.paths`**: `["__REPO_ROOT__/agent-skills","__REPO_ROOT__/skills/claude-code","__REPO_ROOT__/skills/engineering","__REPO_ROOT__/skills/productivity","__DRIVE_SKILLS__"]`.
   - All real paths are placeholders (`__DRIVE_DATA__`, `__DRIVE_PERSONAL__`, `__DRIVE_SKILLS__`, `__REPO_ROOT__`, `__SECRET_*__`). **No literal secrets, no literal user paths.**

2. **`command/`** — portable slash commands (the "shortcut buttons"), see Phase C.

3. **`skills/`** — empty dir (mkdir) for user's Drive-synced custom skills (`skills/<name>/SKILL.md`).

---

## Phase B — Render script (repo, git-synced)
**Files (new):** `scripts/setup-kilo-config.sh` (thin bash wrapper) + `scripts/lib/render_kilo_config.py` (pure logic, unit-testable).

`render_kilo_config.py` does, in order:
1. **Detect Drive data root** via `drive_secrets._glob_cloudstorage_drive()` (standalone — works before any symlink). Map to `A-Wiki-Data` dir. Fall back to `drive_path.get_drive_root()`, then `A_WIKI_DRIVE_PATH` env. Fail loudly with guidance if none (esp. Windows `%USERPROFILE%\Google Drive\A-Wiki-Data` / WSL `/mnt/...`).
2. **Detect repo root** (`Path(__file__).resolve().parents[2]`) — never hardcode `/Users/aase7en/...`.
3. **Resolve placeholders**:
   - `__DRIVE_DATA__` = A-Wiki-Data dir, `__DRIVE_PERSONAL__` = `<data>/personal`, `__DRIVE_SKILLS__` = `<data>/.config/kilo/skills`, `__REPO_ROOT__` = repo.
   - `__SECRET_<NAME>__` → value parsed from `<data>/.secrets` (reuse `drive_secrets.parse_secrets_file`). If a key is absent, **drop that provider entry** (don't leave a dangling placeholder).
4. **Load template** from `<data>/.config/kilo/kilo.jsonc.template`. If missing (first run on a machine before seeding), fall back to the repo-bundled `scripts/lib/kilo.jsonc.template` so it still works, and warn to sync from Drive.
5. **Render** to `~/.config/kilo/kilo.jsonc` (create `~/.config/kilo/` if absent; cross-OS: `Path.home()/".config"/"kilo"`). Paths in MCP args use **OS-native form** (`str(p)`) so Windows backslash paths work for `npx`.
6. **Copy commands**: `<data>/.config/kilo/command/*.md` → `~/.config/kilo/command/` (overwrite, idempotent).
7. **Idempotent + safe**: re-running yields the same output; never touches `node_modules`/`package.json` in `~/.config/kilo/`; writes atomically (temp + rename).

`setup-kilo-config.sh`: `python3 scripts/lib/render_kilo_config.py "$@"` with flags `--check` (print resolved Drive + which keys/commands would render, no write), `--force` (overwrite even if unchanged).

---

## Phase C — Slash commands (the "shortcut buttons")
Create in `<Drive>/.config/kilo/command/` (synced, copied to local by render). Frontmatter per Kilo command spec (`description`, optional `agent`). Suggested set:
- `/drive` — print the resolved Drive root + personal/journal path for THIS machine (debug aid on a new machine).
- `/journal` — open/read `drive/personal/journal/log.md` (append today's entry).
- `/goals` — read `drive/personal/journal/goals.md`.
- `/handoff` — read `drive/personal/journal/handoff.md`.
- `/keys` — list **names** of available secrets from `.secrets` (never values) + which providers are wired.
- `/sync-kilo` — re-run `setup-kilo-config.sh` then report what changed.

Each command body instructs the agent to use the resolved Drive path (commands are text; the agent resolves `drive/` via repo symlink at runtime, so commands themselves stay machine-independent).

---

## Phase D — Integration
- **`scripts/setup-local.sh`**: add step **[9/9]** `setup-kilo-config.sh` (after key sync), bumping the `[1/8]…[8/8]` counters to `[1/9]…[9/9]`.
- **`scripts/verify-next-machine.py`**: add a Kilo-config health check (template resolves, `~/.config/kilo/kilo.jsonc` present + parses, Drive path detected).
- **Docs**: new `docs/protocols/portable-kilo-config.md` — what lives where, how to run on a fresh Windows/WSL machine (`git clone` → `setup-cloud-link.sh --auto` → `setup-local.sh`), security notes, troubleshooting (Drive not detected on Windows).

---

## Phase E — Security (critical)
- `.secrets` **never** exposed to the model as files: MCP filesystem targets `personal/` only — **not** `.secrets`, `personal-tools/`, or `private-tools/`.
- The Drive-synced **template contains zero secrets** (placeholders only) — safe to sync across accounts.
- Injected keys land only in the **local** `~/.config/kilo/kilo.jsonc` (personal, non-synced) — same posture as existing `.claude/settings.local.json`.
- `NEVER_CACHE`-style high-sensitivity keys (e.g. `WIKI_UNLOCK`) are **excluded** from provider injection (mirror `import-keys.py`).
- `/keys` command lists names only.

---

## Phase F — Tests (Iron Law #1 — failing tests first)
**File (new):** `tests/test_render_kilo_config.py`
- `test_template_has_no_literal_secrets` — template file contains no `__SECRET_*__` resolution and no real key patterns.
- `test_template_parses_as_jsonc` — template is valid JSONC.
- `test_placeholders_resolved_in_output` — rendered output has zero `__*_PLACEHOLDER` tokens.
- `test_missing_secret_drops_provider` — if `.secrets` lacks a key, that provider entry is absent (no dangling placeholder).
- `test_default_model_and_agents_unchanged` — rendered `model`/`agent.*.model` equal the template's (AI behavior preserved).
- `test_mcp_targets_personal_not_secrets` — `mcp.drive-files` path ends with `personal`, never contains `.secrets`.
- `test_kilocode_stale_text_removed` — no `.kilocode` substring in rendered config.
- `test_windows_path_handling` — feed a Windows `%USERPROFILE%` Drive fixture → MCP arg is a native Windows path.
- `test_idempotent_rerender` — two consecutive renders produce byte-identical output.
- `test_commands_copied` — `command/*.md` present in output dir.

---

## Validation
1. `python3 -m pytest tests/test_render_kilo_config.py -q` → green.
2. Home Mac: `bash scripts/setup-kilo-config.sh --check` → shows detected Drive path + keys + commands; `--force` renders; `kilo` picks up new providers/commands/skills; `/drive` prints correct path; MCP `drive-files` lists `personal/` files.
3. Simulate work machine: run render with a Windows-style `A_WIKI_DRIVE_PATH` fixture + `%USERPROFILE%` → output paths are Windows-native, no Mac paths leak.
4. Confirm existing AI behavior intact: default agent/model unchanged; `code-skeptic` no longer references `.kilocode`.
5. `grep -rn "/Users/aase7en" ~/.config/kilo/kilo.jsonc` after render on a path-fixture run → none (no hardcoded home path).

## Iron Laws / guardrails
- **#1** failing test first (Phase F).
- **#5** no `AGENTS.md`/`CLAUDE.md` edits; only repo scripts, Drive template/commands, local `~/.config/kilo/`, docs.
- No `raw/` mutation; secrets never printed/logged; `drive/`/`raw/` external-layer preserved; no hardcoded personal paths in any committed file.

## Out of scope
- Touching the project `.kilo/kilo.jsonc` (repo-level) — this plan is about the **global** `~/.config/kilo/`.
- Auto-installing Node/`npx` on the work machine (documented prerequisite only).
- Editing the global config's existing agent prompts beyond the `.kilocode` correctness fix.
- The broader dashboard-overhaul plan (separate file `kilo-compatibility-dashboard-overhaul.md`) — this plan is complementary (shares the `.kilocode` fix).
