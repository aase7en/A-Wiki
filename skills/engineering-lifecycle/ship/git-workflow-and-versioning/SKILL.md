---
name: git-workflow-and-versioning
description: Trunk-based development with atomic commits, change sizing, and clean history. Use when making any code change to ensure proper commit discipline. Use before every commit to verify the change is atomic and well-described.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Git Workflow and Versioning

## Overview

Git history is a communication tool. Clean, atomic commits make the project easier to review, debug, and roll back. This skill defines the commit discipline that keeps the history readable and the project maintainable — matching A-Wiki's existing commit rules (direct to main, atomic commits, no force push).

## When to Use

- Before every commit (verify atomicity and message quality)
- When planning a series of changes
- When rebasing or reorganizing commits
- Before merging (verify clean history)

## The Rules

### Atomic Commits

Each commit is one logical change:
```
✓ Good: "feat(api): add createTask endpoint"
✓ Good: "fix(auth): handle expired refresh tokens"
✗ Bad: "fix stuff" (multiple unrelated changes)
✗ Bad: "WIP" (incomplete change)
```

A commit is atomic when:
- It does one thing and does it completely
- The project builds and tests pass after this commit
- The commit message explains the change to a future reader
- Rolling back this commit removes the feature cleanly without side effects

### Change Sizing

- Target ~100 lines changed per commit
- Split large changes into logical commits
- Refactoring and features are separate commits
- No commit should mix formatting changes with logic changes

### Trunk-Based Development

A-Wiki rule: commit directly to `main`, no branches, no PRs:
```
✓ Good: commit to main after every increment
✓ Good: push after each feature or bug fix
✗ Bad: long-lived feature branches
✗ Bad: merging without reviewing the diff
```

### Commit Messages

Format: `type(scope): description`

Types: `feat`, `fix`, `docs`, `wiki`, `refactor`, `test`, `chore`

Examples:
```
feat(api): add createTask endpoint
fix(auth): handle expired refresh tokens
docs(spec): add API contract for task sharing
wiki(iot): add MQTT broker entity
refactor(db): extract query builder into helper
test(auth): add rate limiting test
chore(deps): upgrade express to 4.18
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll squash commits later" | You won't. Commit cleanly from the start. |
| "This is just a small fix, no need for a message" | Every commit is read by someone later. A one-line message takes 10 seconds. |
| "I'll combine the refactor with the feature since they touch the same files" | Combined changes are impossible to review and dangerous to roll back. Keep them separate. |
| "I don't need to test before every commit" | A broken commit poisons bisect. Test before every commit. |

## Red Flags

- Commit messages that are empty or say "fix" / "update" / "WIP"
- Commits larger than ~200 lines changed
- Refactoring and features in the same commit
- Formatting changes mixed with logic changes
- Force pushing to shared branches
- Committing without running tests first

## Verification

- [ ] Commit does one thing
- [ ] Tests pass before commit
- [ ] Build succeeds before commit
- [ ] Commit message follows `type(scope): description` format
- [ ] No unrelated changes in the commit
- [ ] Change is independently revertable
