# A-Flow Stage: REVIEW

> โหลดเมื่อ: `state.stage == "REVIEW"`
>
> Goal: review diff ในฐานะ outsider ก่อน ship — multi-perspective

## 1. Read diff as outsider

```bash
git diff main  # หรือ git show HEAD~N..HEAD
```

อ่านเหมือนไม่ใช่ของตัวเอง — หา:
- Dead code
- Inconsistencies
- Missing tests
- Security smells
- Performance pitfalls

## 2. Persona fan-out

เรียก personas ผ่าน `council` / `delegate-subagent`:

| Persona | มุมมอง |
|---|---|
| `code-reviewer` | architecture, idioms, debt, coupling, missing tests |
| `test-engineer` | edge cases, integration gaps, failure modes, coverage |
| `security-auditor` | auth, secrets, injection, OWASP, threat model |
| `web-performance-auditor` | Core Web Vitals, bundle, jank, animation cost (web task only) |

Personas ทำงานแบบ **persistent blackboard** (`council_persistent.py`) → ผลรวม severity

## 3. Skills

- `scrutinize` (9arm) — read code as adversary
- `code-simplification` — simplify over-engineered parts
- `audit-reference-originality` (MengTo) — ถ้า web design, เช็ค copy/plagiarism
- `optimize-web-animations` (MengTo) — ถ้ามี animation, profile perf

## 4. Decision

- **Critical** findings → block ship → advance DEBUG
- **Important** → address + re-review
- **Minor** → note + ship

## Outputs

- Persona findings → `.tmp/blackboard.jsonl`
- self_audit hook (Stop) → แจ้ง critical ก่อน ship
- Advance: ถ้า pass → `TEST`, ถ้า fail → `DEBUG`
