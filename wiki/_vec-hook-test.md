---
type: test
tags: [hook-test, ephemeral]
created: 2026-05-26
---

# Vec Hook Test

This file exists solely to verify that `scripts/hooks/post_wiki_edit.py` triggers
`gen-index.py` → `build-vec-index.py` chain after a wiki write. It should appear
in `wiki_vec_meta` within ~60s of being written, then be deleted.
