---
name: a-flow
description: "Master 7-stage dev pipeline (professional loop): ASK → DESIGN → PLAN → IMPLEMENT → REVIEW → DEBUG → TEST. Thin router that delegates each stage to canonical skills (a-think, a-plan, a-debug, scrutinize, verify-before-done). Hook-enforced (check_a_flow_discipline) — ห้ามข้าม stage. State in .tmp/a-flow.json. Trigger: '/A-Flow', 'workflow', 'dev pipeline', 'professional dev'."
version: 1.0.0
author: A-Wiki
domain: [engineering, code]
lifecycle_phase: meta
category: pipeline
agents: [all, hermes]
invocation: manual
invocation_hint: "/A-Flow"
# 2026-07-26: foundation skill ของ A-Wiki Pro Workflow System.
# ออกแบบตามแนวคิด ask > design > plan > implement > review > debug > test
# ตามมาตรฐานมืออาชีพ (reference: MengTo/Skills, fable-method, addyosmani lifecycle)
---

# A-Flow — Professional Dev Pipeline (7 stages)

> Foundation skill ของ A-Wiki Pro Workflow — ทำให้ทุก task non-trivial เดินตาม
> dev cycle มืออาชีพ: ถามให้รู้เรื่อง → ออกแบบก่อนทำ → วางแผน → ลงมือ → รีวิว → แก้บั๊ก → ทดสอบ
> Compose canonical skills ที่มีอยู่ ไม่ duplicate. Hook-enforced กันหลุด focus.

## Iron Law

> **NO IMPLEMENT WITHOUT PLAN APPROVED FIRST**
>
> ห้าม jump ไป Edit/Write ก่อนจบ stage ASK + DESIGN + PLAN — Hook
> `check_a_flow_discipline` จะ block (除非 trivial: typo, comment, whitespace)

## เมื่อไหร่ใช้

✅ ใช้:
- Task non-trivial (≥3 files, design decision, multi-step)
- User พิมพ์ `/A-Flow` หรือขอ "professional workflow"
- งานที่ stake สูง (security, money, deploy, migration)
- อยากได้ review/debug/test อย่างเป็นระบบ

❌ ข้าม (ใช้ skill เฉพาะทาง):
- Bug fix ระบุที่มาชัด → `a-debug` ตรง
- แค่ doc → `a-doc` chain
- Typo / field เดียว / lookup → ไม่ต้อง pipeline

## 7 Stages (เรียงบังคับ)

```
  ┌─────┐    ┌────────┐    ┌──────┐    ┌────────────┐
  │ ASK │───▶│ DESIGN │───▶│ PLAN │───▶│ IMPLEMENT  │
  └─────┘    └────────┘    └──────┘    └────────────┘
   restate     ≥2 approach    tasks       incremental
   ≥3 Qs       trade-off      subagent     tdd
                                                │
                                                ▼
  ┌──────┐    ┌───────┐    ┌──────┐
  │ TEST │◀───│ DEBUG │◀───│REVIEW│
  └──────┘    └───────┘    └──────┘
   e2e+unit    root-cause    scrutinize
   smoke       tdd-fix        persona
```

**อ่านรายละเอียดแต่ละ stage ใน `references/stage-<name>.md`** (progressive disclosure — โหลดเฉพาะที่ active).

## วิธีใช้

### เริ่ม pipeline
```
/A-Flow "<task description>"
```

A-Flow จะ:
1. เขียน state → `.tmp/a-flow.json` (`stage:"ASK"`, `active:true`)
2. เรียก ASK skill (a-think + grill-with-docs)
3. พอ ASK จบ → advance stage → DESIGN ...
4. Stage สุดท้าย (TEST) → mark `active:false` → ปิด hook

### ข้ามไป stage เฉพาะ (debugging mid-flow)
```
/A-Flow --stage DEBUG
```
ใช้เมื่อ implement แล้วเจอ bug — advance ไป DEBUG ตรงๆ (hook ยัง enforce ว่า stage ก่อนหน้าผ่านแล้ว)

### ปิด pipeline
```
/A-Flow --close
```
mark `active:false` → hook ไม่บังคับต่อ → ใช้เมื่อ task เสร็จหรือยกเลิก

## Handoff contract (cross-session safe)

State ทุกอย่างเขียนลง `.tmp/a-flow.json` (survives compact, resume ข้าม session):

```yaml
active: true | false
stage: ASK | DESIGN | PLAN | IMPLEMENT | REVIEW | DEBUG | TEST
category: web | design | content | marketing | game | audit | arch | research | ...
goal: "<task description from /A-Flow>"
allowed_files:
  - "src/auth.ts"           # ไฟล์ที่ PLAN stage อนุมัติให้ edit
  - "tests/auth.test.ts"
started_ts: 1784955460
completed_stages: [ASK, DESIGN]
notes:
  - "ADR-001: chose JWT over session (user confirmed)"
  - "grill Q3 answer: refresh rate = real-time"
```

**Resume**: อ่าน `.tmp/a-flow.json` → รู้ทันที stage ไหน + อนุญาตไฟล์อะไร + notes

## Skill composition per stage

| Stage | Canonical skills เรียก |
|---|---|
| ASK | `a-think` (step 1-2: restate + done) + `grill-with-docs` (≥3 Qs mandatory) |
| DESIGN | `a-think` (step 4-6: approaches + pre-mortem + right-size) + design tool ตาม domain |
| PLAN | `a-plan` chain (grill → spec → design tool → plan-orchestrate) |
| IMPLEMENT | `incremental-implementation` + `test-driven-development` (Iron Law #1) |
| REVIEW | `scrutinize` + persona fan-out (`code-reviewer`, `test-engineer`, `security-auditor`, `web-performance-auditor`) |
| DEBUG | `a-debug` chain (a-think → debug-mantra → root-cause-first → tdd → fix → verify → scrutinize) |
| TEST | `verify-before-done` + domain test skill (`react-testing`/`python-testing`/`e2e-testing`/`browser-qa`) |

## Hook enforcement (`check_a_flow_discipline`)

PreToolUse Edit/Write — block ถ้า:
- อยู่ใน ASK/DESIGN stage (ห้าม Edit ก่อน PLAN)
- ไฟล์ไม่อยู่ใน `allowed_files` list

Allow (auto-skip):
- Tools: Bash, Read, Glob, Grep, TodoWrite, WebFetch, WebSearch
- Trivial edit: typo, comment-only, whitespace-only, < 5 chars
- ไฟล์ `.tmp/*` (state advance)
- `HOOK_SKIP=check_a_flow_discipline` opt-out

## Context discipline (กันหลุด/ลืม)

- **SKILL.md นี้ ~120 บรรทัด** — โหลดเบา
- **references/** แยก — โหลดเฉพาะ stage active
- **State ใน disk** — compact แล้ว resume จาก `.tmp/a-flow.json`
- **invocation: manual** — ไม่ auto-load ทุก session (เหมือน a-loop, a-plan)

## สิ่งที่ reuse (ไม่ duplicate)

| สิ่งที่มี | ใช้ตรงไหน |
|---|---|
| `a-think` | ASK + DESIGN (7-step reasoning) |
| `a-plan` chain | PLAN stage |
| `a-debug` chain | DEBUG stage |
| `grill-with-docs` | ASK stage (≥3 Qs) |
| `scrutinize` + personas | REVIEW stage |
| `verify-before-done` | TEST stage |
| `incremental-implementation` + `tdd` | IMPLEMENT stage |
| `.tmp/task-board.json` (NS C5) | sub-task tracking |
| Hook infrastructure | `check_a_flow_discipline` |

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | This thin router (~120 lines) |
| `references/stage-ask.md` | ASK detail |
| `references/stage-design.md` | DESIGN detail |
| `references/stage-plan.md` | PLAN detail |
| `references/stage-implement.md` | IMPLEMENT detail |
| `references/stage-review.md` | REVIEW detail |
| `references/stage-debug.md` | DEBUG detail |
| `references/stage-test.md` | TEST detail |
| `scripts/hooks/check_a_flow_discipline.py` | Hard enforcement hook |
| `scripts/lib/a_flow_state.py` | State manager (read/write .tmp/a-flow.json) |

## Cross-agent parity

- `agents: [all, hermes]` — Hermes exclude `[all]` ต้อง explicit
- `invocation_hint: "/A-Flow"` + `aliases: ["/a-flow", "aflow"]` — LLM pattern-match cross-agent
- symlink farm (`link-agent-configs.sh`) — auto-pickup `skills/awiki/a-flow/`
- hook ทำงานเฉพาะ Claude Code + agents ที่รู้ PreToolUse (Codex/Cline/ZCode) — text-only agents (Cursor/Windsurf/Copilot) อ่าน SKILL.md เอง

## Model tier policy (cost-first)

อ้างอิง Cost-First Pyramid (AGENTS.md). แต่ละ stage เลือก tier ตาม stakes:

| Stage | Tier | เหตุผล |
|---|---|---|
| ASK | Primary (4c) | decisions สำคัญ — คุ้มที่สุด |
| DESIGN | Primary (4c) | architecture = one-way door |
| PLAN | Cheap-capable (2) | mechanical task breakdown |
| IMPLEMENT | Cheap-capable (2) | tdd verify อยู่แล้ว |
| REVIEW | Primary (4c) | quality gate |
| DEBUG | Free/cheap (1) | debug-mantra + tdd |
| TEST | Free (1) | deterministic |

Override: `A_FLOW_TIER_STAGE_<NAME>=<tier>`

## Examples

**Bad (skip A-Flow)**:
```
user: ทำ auth module ใหม่
agent: [implement ทันที] → พลาด requirement 3 ข้อ, รื้อทำใหม่
```

**Good (A-Flow)**:
```
/A-Flow "ทำ auth module ใหม่"
  ASK:    restate + grill (Q1: JWT/session? Q2: refresh? Q3: 2FA?)
  DESIGN: 2 approaches (JWT vs session) → ADR-001 = JWT
  PLAN:   T1 schema, T2 /login, T3 /refresh, T4 tests
  IMPLEMENT: tdd per task (small verified steps)
  REVIEW:   code-reviewer (architecture) + security-auditor (OWASP)
  TEST:     unit (auth.test.ts) + e2e (login flow) + smoke
  → close: active:false, summary to ledger
```
