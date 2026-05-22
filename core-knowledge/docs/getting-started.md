# Getting Started with A-Wiki

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Aase7en/A-Wiki.git
cd A-Wiki
```

### 2. Link skills for Claude Code
```bash
bash scripts/link-skills.sh
```
This creates symlinks from `~/.claude/skills/<name>` → `skills/<category>/<name>/`.

### 3. Setup local data (Google Drive)
A-Wiki keeps sensitive/personal data out of git. Set up a Google Drive folder:

```bash
# Create .local and raw directories
mkdir -p .local raw exports

# Create symlink to GDrive (Windows example)
# mklink /J A:\GitHub\A-Wiki\.local C:\Users\<user>\Google Drive\A-Wiki-Data\.local
# mklink /J A:\GitHub\A-Wiki\raw C:\Users\<user>\Google Drive\A-Wiki-Data\raw
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Folder Structure

| Path | What goes here | Git? |
|------|----------------|------|
| `wiki/` | Knowledge pages (concepts, entities, synthesis) | ✅ |
| `skills/` | AI agent skills | ✅ |
| `scripts/` | Utility scripts | ✅ |
| `docs/` | Protocols, guides | ✅ |
| `.local/` | Profile, session memory, secrets | ❌ |
| `raw/` | Source documents, data files | ❌ |
| `exports/` | NotebookLM bundles | ❌ |
| `log.md` | Wiki edit history | ❌ |

## Working with the Wiki

### Adding new knowledge
1. Drop source document into `raw/` (or paste URL/text)
2. Use `ingest-source` skill to autoclassify and create pages
3. Review generated pages and link to related content

### Searching
```bash
# Local search (FTS5)
python scripts/search-wiki.py "ESP32 power consumption"

# Cross-file synthesis (Gemini API)
python scripts/ask-notebooklm.py --domain iot --query "compare LoRa vs WiFi for sensor networks"
```

### Quick Commands for AI Agents
- `/search <query>` — Local wiki search
- `/lint` — Wiki health check
- `/snapshot-nb [domain]` — Export for NotebookLM
- `/compact` — Reduce context mid-session

## For Contributors

See [docs/architecture.md](./architecture.md) for system overview.
See [docs/protocols/](./protocols/) for detailed workflows.