# PixelLab MCP Setup for Codex, Claude, and Cline

## Purpose

Set up PixelLab MCP so an AI coding agent can generate pixel art characters, animations, map objects, and tiles while building the Trading RPG prototype.

## Secret rule

Never paste the PixelLab API token into chat, tracked files, screenshots, or wiki pages. Store it as `PIXELLAB_API_TOKEN` in local environment or `drive/.secrets`.

## Get and store token safely

1. Open PixelLab account settings and create/copy the API token:

```bash
open https://pixellab.ai/account
```

2. Paste the token only into the terminal prompt below. It uses silent input and updates `drive/.secrets`.

```bash
read -rsp "PixelLab API token: " PIXELLAB_API_TOKEN && printf "\n"
export PIXELLAB_API_TOKEN
python3 - <<'PY'
import os
from pathlib import Path

repo = Path.cwd()
secrets = repo / "drive" / ".secrets"
token = os.environ.get("PIXELLAB_API_TOKEN", "").strip()
if not token:
    raise SystemExit("PIXELLAB_API_TOKEN was empty")

lines = []
if secrets.exists():
    lines = secrets.read_text(encoding="utf-8").splitlines()

out = []
written = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith("PIXELLAB_API_TOKEN=") or stripped.startswith("export PIXELLAB_API_TOKEN="):
        out.append(f"PIXELLAB_API_TOKEN={token}")
        written = True
    else:
        out.append(line)

if not written:
    if out and out[-1].strip():
        out.append("")
    out.append(f"PIXELLAB_API_TOKEN={token}")

secrets.write_text("\n".join(out) + "\n", encoding="utf-8")
secrets.chmod(0o600)
print("Stored PIXELLAB_API_TOKEN in drive/.secrets without printing its value")
PY
unset PIXELLAB_API_TOKEN
```

3. Verify names only. This must print the key name, not the value.

```bash
python3 scripts/lib/drive_secrets.py --list | rg PIXELLAB_API_TOKEN
```

4. Export it for the current terminal when needed.

```bash
export PIXELLAB_API_TOKEN="$(python3 scripts/lib/drive_secrets.py PIXELLAB_API_TOKEN)"
```

## Codex Desktop / Codex CLI

Codex supports external MCP servers through `codex mcp`.

```bash
codex mcp add pixellab \
  --url https://api.pixellab.ai/mcp \
  --bearer-token-env-var PIXELLAB_API_TOKEN
```

Check:

```bash
codex mcp list
```

If Codex Desktop is opened from the Dock, it may not inherit shell env vars. Use one of these:

```bash
export PIXELLAB_API_TOKEN="paste-token-here"
open -a Codex
```

or:

```bash
launchctl setenv PIXELLAB_API_TOKEN "paste-token-here"
open -a Codex
```

## Claude Code

PixelLab's documented pattern:

```bash
claude mcp add pixellab https://api.pixellab.ai/mcp -t http -H "Authorization: Bearer $PIXELLAB_API_TOKEN"
```

Use a shell env var. Do not put the literal token in command history if avoidable.

## Cline / VS Code

If the extension supports remote HTTP MCP with headers, use:

```json
{
  "mcpServers": {
    "pixellab": {
      "url": "https://api.pixellab.ai/mcp",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer ${PIXELLAB_API_TOKEN}"
      }
    }
  }
}
```

If env interpolation is unsupported, use the extension's secret store instead of a checked-in config file.

## First asset test

After tools appear, ask the agent:

```text
Use PixelLab MCP to create an original anime pirate trading captain.
Do not copy One Piece, Luffy, copyrighted characters, logos, costumes, or world terms.
Style: retro 16-bit pixel art, transparent background, low top-down RPG view.
Use 8 directions, humanoid, heroic proportions, size 64.
Name: captain_trader_01.
```

Then queue:

```text
Animate captain_trader_01 with idle and walking animations only.
Keep the same outfit, palette, silhouette, and transparent background.
Export spritesheets suitable for Phaser.
```

## Troubleshooting

- If no PixelLab tools appear, restart the client after adding the MCP server.
- If auth fails, confirm `PIXELLAB_API_TOKEN` exists in the same process environment as the client.
- If jobs stay processing, wait 2-5 minutes and call the corresponding `get_*` tool.
- If output style is wrong, generate fewer assets first and lock one approved style reference before batch generation.
