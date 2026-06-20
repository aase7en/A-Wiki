# /ship — Ship with confidence

Maps to: `skills/engineering-lifecycle/ship/shipping-and-launch/SKILL.md` + parallel fan-out (code-reviewer, security-auditor, test-engineer)

## When to use
- Preparing to deploy to production
- Feature is complete and reviewed

## Flow
1. Run `shipping-and-launch` skill (pre-launch checklist)
2. Parallel fan-out: spawn code-reviewer, security-auditor, test-engineer concurrently
3. Merge reports → go/no-go decision
4. Document rollback plan before deploy
