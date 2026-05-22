# Journal

> Daily journal entries. The actual journal entries are stored locally and synced via Google Drive (NOT in git).
> See `scripts/sync.py` for the sync workflow.

## Structure

```
journal/
├── README.md              ← this file
├── _template.md           ← template for new entries
└── YYYY/
    └── YYYY-MM-DD.md      ← daily entries (gitignored)
```

## Usage

To create a new entry, copy the template:

```bash
cp journal/_template.md journal/2026/2026-$(date +%m-%d).md