# /test — Debug failures, fix with TDD

Maps to: `debug-mantra` (A-Wiki skill) + `skills/engineering-lifecycle/build/test-driven-development/SKILL.md`

## When to use
- Tests fail after a code change
- The build breaks
- Runtime behavior doesn't match expectations

## Flow
1. Run `debug-mantra` first (reproduce → trace path → falsify → cross-reference)
2. Then run `test-driven-development` to fix with Red-Green-Refactor
3. Verify all tests pass before proceeding
