# claude-code-router (ccr) — multi-provider backend for Claude Code

Route Claude Code to GPT / Z.ai GLM / DeepSeek / Gemini / OpenRouter via one
local proxy. Keys stay in Drive `.secrets`; this folder only holds a public-safe
template.

## Files
- `config.template.json` — committed, placeholders `${SECRET_NAME}` only (no keys)
- `../gen-ccr-config.py` — renders template → `~/.claude-code-router/config.json`
- `../launch-ccr.sh` / `../launch-ccr.ps1` — regen config + `ccr code`

## One-time setup
```bash
npm i -g @anthropic-ai/claude-code @musistudio/claude-code-router
# add the keys you want to drive/.secrets (NAME=value), e.g.:
#   DEEPSEEK_API_KEY=...   OPENROUTER_API_KEY=...   OPENAI_API_KEY=...
# already present in Drive: ZHIPU_API_KEY (Z.ai/GLM), GEMINI_API_KEY
python scripts/gen-ccr-config.py
```

## Launch
```bash
bash scripts/launch-ccr.sh                 # macOS / Linux / WSL / Git Bash
powershell -ExecutionPolicy Bypass -File scripts\launch-ccr.ps1   # Windows
```
Switch model mid-session: `/model deepseek,deepseek-reasoner`, `/model gemini,gemini-2.5-pro`, `/model zai,glm-4.6`, ...

## Router map = Cost-First pyramid
| Router key | meaning | current route |
|---|---|---|
| `background` | small/fast aux calls | gemini-2.5-flash |
| `default` | normal turns | deepseek-chat |
| `think` | reasoning-heavy | deepseek-reasoner |
| `longContext` | >60k tokens | gemini-2.5-pro |

## ⚠️ Values to CONFIRM before relying on them
These are representative; verify against current provider + ccr docs (they drift):
- **Z.ai endpoint/model** — `api_base_url` for the GLM Coding Plan OpenAI-compatible
  endpoint and the exact model ids (`glm-4.6`, `glm-4.5-air`). Confirm on the Z.ai dashboard.
- **DeepSeek model names** — `deepseek-chat` / `deepseek-reasoner` are being migrated
  toward `deepseek-v4-*`; confirm current ids.
- **Gemini / OpenRouter model ids** — pick current ones (use `scripts/model-scout-current.py`).
- **transformer names** — `deepseek`, `gemini`, `openrouter` per ccr README; adjust if upstream renames.

## Desktop app
ccr serves an Anthropic endpoint at `http://127.0.0.1:3456`. Run `ccr start` (background),
then in Desktop → Settings → Claude Code → Local environment set
`ANTHROPIC_BASE_URL=http://127.0.0.1:3456` + a dummy `ANTHROPIC_AUTH_TOKEN`.
If Desktop ignores the override (still hits Anthropic / 401), use the CLI `ccr code` path.
