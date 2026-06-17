---
tags: [readme]
type: source
title: "README"
slug: readme
date_ingested: 2026-05-24
original_file: raw/README.md
---

```yaml
---
---
```

# raw/

**Immutable — do not edit files in this directory.**

This directory stores original source documents ingested from external sources.
Use `scripts/wiki/ingest-source` or equivalent to add new sources.

Rules:
- Files in `raw/` are NEVER modified after ingestion
- To sanitize, copy the file outside `raw/` and edit the copy
- To re-ingest, run the ingest process again to create a fresh copy
- The `check_raw_immutable.py` hook blocks all edit/write/delete operations on `raw/`

Structure:
```
raw/
  /
    .md
    .pdf
    ...
