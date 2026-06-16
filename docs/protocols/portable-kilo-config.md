# Portable Global Kilo Config (Drive-synced, cross-machine)

> One machine-independent Kilo global config that works identically on the
> **home Mac** and the **work Windows/WSL PC**, auto-detecting each machine's
> Google Drive path. Adds Drive file-access (MCP filesystem, `/commands`,
> provider keys, Drive-synced skills) **without changing any AI model/agent/
> permission settings**.

## Why a renderer (not a static file or env vars)

Kilo's global config (`~/.config/kilo/kilo.jsonc`) is static JSONC with **no
`${VAR}` interpolation**. The only robust, cross-OS way to keep one config
consistent across machines with different Google Drive mount paths is a
**template + render** step that substitutes the detected Drive path, repo
path, and provider keys at render time. This mirrors A-Wiki's existing
`setup-local.sh` / `import-keys.py` pattern.

## Three locations

| Location | Path | Role |
|----------|------|------|
| **Source of truth** | `<Drive>/A-Wiki-Data/.config/kilo/kilo.jsonc.template` | Portable, secret-free, path-free template. Edit this. |
| Repo fallback | `scripts/lib/kilo.jsonc.template` | Bundled safety net (git-synced). Used if the Drive template is missing. |
| **Rendered output** | `~/.config/kilo/kilo.jsonc` | Machine-specific; may contain injected keys. Never edited by hand. |

Slash commands live in `<Drive>/A-Wiki-Data/.config/kilo/command/*.md` and are
copied to `~/.config/kilo/command/` at render time. Drive-synced skills live in
`<Drive>/A-Wiki-Data/.config/kilo/skills/`.

## Run on a fresh machine

```bash
git clone <a-wiki> && cd A-Wiki
bash scripts/setup-cloud-link.sh --auto     # detect Drive + create drive/ link
bash scripts/setup-local.sh                 # full setup incl. [9/9] Kilo config render
# — or just the Kilo step alone:
bash scripts/setup-kilo-config.sh           # render (idempotent)
bash scripts/setup-kilo-config.sh --check   # report only, no write
bash scripts/setup-kilo-config.sh --force   # overwrite even if unchanged
```

## Placeholders (resolved at render)

| Token | Becomes |
|-------|---------|
| `__DRIVE_DATA__` | A-Wiki-Data dir on THIS machine |
| `__DRIVE_PERSONAL__` | `<data>/personal` (MCP filesystem target) |
| `__DRIVE_SKILLS__` | `<data>/.config/kilo/skills` |
| `__REPO_ROOT__` | this repository root |
| `__SECRET_<ENV>__` | provider apiKey from Drive `.secrets` (provider dropped if key missing) |

Provider map: `google→GEMINI_API_KEY`, `openrouter→OPENROUTER_API_KEY`,
`anthropic→ANTHROPIC_API_KEY`, `groq→GROQ_API_KEY`, `deepseek→DEEPSEEK_API_KEY`.

## Slash commands (the "shortcut buttons")

`/drive` `/journal` `/goals` `/handoff` `/keys` `/sync-kilo` — defined in
`<Drive>/.config/kilo/command/`, copied to `~/.config/kilo/command/`.

## Security

- The Drive template contains **zero secrets** (placeholders only) — safe to sync.
- Injected keys land only in the **local** `~/.config/kilo/kilo.jsonc` (personal,
  non-synced) — same posture as `.claude/settings.local.json`.
- MCP `drive-files` targets `personal/` only — **never** `.secrets`,
  `personal-tools/`, or `private-tools/`.
- `NEVER_INJECT` secrets (e.g. `WIKI_UNLOCK`) are excluded from provider injection.
- `/keys` lists **names only**, never values.

## What does NOT change

The default `model`, `small_model`, `subagent_model`, `default_agent`, and every
agent's `model`/permission are preserved verbatim from the template. Provider
keys are **additive** (more models become available); they never alter existing
AI behavior.

## Troubleshooting

- **"could not detect A-Wiki-Data"** — set `A_WIKI_DRIVE_PATH=/path/to/A-Wiki-Data`
  or run `bash scripts/setup-cloud-link.sh --auto`.
- **Windows/WSL** — Drive is detected under `%USERPROFILE%\Google Drive\A-Wiki-Data`
  (or a mapped drive). `npx` must be on PATH for the `drive-files` MCP server.
- **Provider not wired** — its key is absent from `.secrets`; add it on the home
  machine and re-run `/sync-kilo` (Google Drive syncs `.secrets` to the work PC).
- **Editing the config** — edit the **Drive template**, then `/sync-kilo`. Never
  hand-edit the rendered `~/.config/kilo/kilo.jsonc` (it is regenerated).

## Tests

`python3 -m pytest tests/test_render_kilo_config.py -q` covers template hygiene,
placeholder resolution, provider drop, AI-config preservation, MCP targeting,
Windows path handling, idempotency, and command copying.
