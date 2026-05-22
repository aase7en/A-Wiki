# Google Drive Sync Setup

> Setup document for syncing `.local/`, `raw/`, `exports/`, `log.md`, and `journal/` across devices via Google Drive.

## Structure

```
Google Drive/
└── A-Wiki-Data/
    ├── .local/           ← profile, secrets, session-memory
    ├── raw/              ← source documents, data files
    ├── exports/          ← NotebookLM bundles
    ├── log.md            ← wiki edit history
    └── journal/          ← daily journal entries
```

## Windows Setup

### Using Google Drive Desktop (Stream)

1. Install Google Drive for Desktop
2. Sign in and let it sync
3. Navigate to the Google Drive folder (e.g., `C:\Users\<user>\Google Drive\`)
4. Create `A-Wiki-Data/` structure
5. Create directory junctions:

```cmd
:: As Administrator
mklink /J A:\GitHub\A-Wiki\.local C:\Users\<user>\Google Drive\A-Wiki-Data\.local
mklink /J A:\GitHub\A-Wiki\raw C:\Users\<user>\Google Drive\A-Wiki-Data\raw
mklink /J A:\GitHub\A-Wiki\exports C:\Users\<user>\Google Drive\A-Wiki-Data\exports
```

### For log.md and journal (copy, not symlink)

These files must be inside the repo for scripts to find them, but gitignored:

```bash
# First time only: copy from GDrive
copy C:\Users\<user>\Google Drive\A-Wiki-Data\log.md A:\GitHub\A-Wiki\log.md

# Sync script handles the rest
python scripts/sync.py --now
```

## Mac Setup

```bash
# Using Google Drive for Desktop (Mirror mode)
ln -s ~/Library/CloudStorage/GoogleDrive-<user>/.shortcut-targets-by-id/<id>/A-Wiki-Data/.local .local
ln -s ~/Library/CloudStorage/GoogleDrive-<user>/.shortcut-targets-by-id/<id>/A-Wiki-Data/raw raw
ln -s ~/Library/CloudStorage/GoogleDrive-<user>/.shortcut-targets-by-id/<id>/A-Wiki-Data/exports exports
```

## Verification

After setup, verify:

```bash
# .local should exist
ls -la .local/profile.md

# raw should exist
ls -la raw/

# These should be gitignored
git check-ignore .local raw exports log.md
# Should output: .local/
#               raw/
#               exports/
#               log.md