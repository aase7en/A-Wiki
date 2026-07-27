# A-Flow Stage: TEST

> โหลดเมื่อ: `state.stage == "TEST"` (stage สุดท้าย)
>
> Goal: prove ว่าทำงานได้จริง + ไม่ break อะไร

## Test pyramid

```
        ┌────────┐
        │  e2e   │  few, slow, integration
        ├────────┤
        │ integ  │  medium
        ├────────┤
        │  unit  │  many, fast
        └────────┘
```

## Skills by domain

| Domain | Skill |
|---|---|
| Python | `python-testing` (pytest + coverage) |
| React | `react-testing` (RTL + axe) |
| End-to-end | `e2e-testing` (Playwright) + `browser-qa` |
| Performance | `optimize-web-animations` + `react-performance` |
| Accessibility | `accessibility` (WCAG 2.2 AA) + `frontend-a11y` |
| C# | `csharp-testing` |
| F# | `fsharp-testing` |
| Kotlin | `kotlin-testing` |
| Rust | `rust-testing` |
| Go | `golang-testing` |

## 1. Unit tests

- ทุก public function → test case
- Edge cases (empty, null, max, min, unicode)
- Error paths (ไม่ใช่ happy path อย่างเดียว)

## 2. Integration tests

- Components ทำงานร่วมกันได้จริง
- API contract ตรง spec
- DB schema matches ORM

## 3. e2e (smoke)

- Critical user journey (login → main flow → logout)
- Browser: `browser-qa` + `browser-testing-with-devtools`
- Mobile: `windows-desktop-e2e` (PWA)

## 4. Verify-before-done (Iron Law #7)

> "Untested code = not working code"

ห้ามเรียก "เสร็จ" ถ้ายังไม่ test:
- ✅ "Tests pass — 12/12"
- ❌ "น่าจะใช้ได้" (without test)

## Outputs

- All tests green
- Coverage report (ถ้ามี)
- `verify-before-done` ผ่าน
- Close pipeline: `a_flow_state.close()` → `state.active = false`
- Summary to `memory-ledger.jsonl` (type=outcome)
