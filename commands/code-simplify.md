# /code-simplify — Reduce complexity, preserve behavior

Maps to: `skills/engineering-lifecycle/review/code-simplification/SKILL.md`

## When to use
- Code works but is harder to read or maintain than it should be
- You want to reduce technical debt in a specific module

## Flow
1. Run `code-simplification` skill
2. Apply Chesterton's Fence (understand before removing)
3. Apply Rule of 500 (extract modules at 500-line threshold)
4. Verify existing tests still pass after each simplification
