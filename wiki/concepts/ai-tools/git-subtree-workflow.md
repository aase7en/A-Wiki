---
type: concept
title: "Git Subtree Workflow"
slug: git-subtree-workflow
tags: [git, upstream-refresh, vendor, skills]
sources: []
created: 2026-06-12
updated: 2026-06-12
---

# Git Subtree Workflow

> [wiki] Git subtree-style refresh keeps upstream skill snapshots inside the repo while allowing A-Wiki to maintain local forks with additional safety rules.

## A-Wiki Pattern

| Path | Role |
|---|---|
| `agent-skills/_upstream/` | Read-only upstream mirror |
| `agent-skills/engineering/` | A-Wiki fork with Iron Law additions |
| `scripts/refresh-9arm.sh` | Refresh command for 9arm skills |

## Related

- [[entities/ai-tools/9arm-skills]]
- `docs/runbooks/upstream-refresh.md`

