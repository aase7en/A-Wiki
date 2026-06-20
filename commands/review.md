# /review — Review quality, simplify, harden

Maps to: `scrutinize` + `skills/engineering-lifecycle/review/code-simplification/SKILL.md` + `skills/engineering-lifecycle/review/security-and-hardening/SKILL.md`

## When to use
- Before merging any code change
- Code is ready for quality review

## Flow
1. Run `scrutinize` for end-to-end outsider-perspective review
2. Run `code-simplification` (Chesterton's Fence, Rule of 500)
3. Run `security-and-hardening` for OWASP checks
4. Compile findings by severity: Critical → Important → Suggestion
