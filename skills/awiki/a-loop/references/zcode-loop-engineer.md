# A-Loop × ZCode — Loop Engineer Mode (hooks-driven)

> ทำงานได้จริงเพราะ ZCode มี hooks ครบ + **Stop-continuation** (verified 2026-09-01,
> `zcode.z.ai/en/docs/hooks`) — loop ถูกผลักด้วยกลไก ไม่ใช่ความอดทนของ model
> WO กำเนิด: `docs/work-orders/WO-ALOOP-ZCODE-20260901.md`

## 0. ข้อเท็จจริง ZCode hooks (พิสูจน์แล้ว 2026-09-01)

- **7 events**: `SessionStart` · `UserPromptSubmit` · `PreToolUse` · `PermissionRequest` · `PostToolUse` · `PostToolUseFailure` · `Stop` (ชื่ออื่นไม่รองรับ — `PostCompact` ใน workspace config เดิมจึงเงียบตาย)
- **Stop + `{"decision":"block","reason":...}` → main model ทำต่อ** — ZCode cap 3 รอบติดแล้ว force-end (กัน infinite loop ที่ตัว runtime)
- hooks วิ่งจาก **user config** `~/.zcode/cli/config.json` (`hooks.enabled:true`) หรือ **plugin** เท่านั้น — **workspace `.zcode/config.json` โดนเมินทั้งก้อน** (นี่คือเหตุที่ wiring เดิมของ repo ไม่เคยยิงบน ZCode)
- `process`-type hook = argument vector ไม่ผ่าน shell → Windows-safe
- exit `2` = deny/block (PreToolUse) หรือ continue-one-round (Stop); stdout ถูก parse เป็น JSON (`additionalContext` / `decision` / `permissionDecision`); unknown fields ถูกเมินไม่ crash
- template `${ZCODE_PROJECT_DIR}` ขยายใน command/args + ฉีดเป็น env var

## 1. ติดตั้ง (ครั้งเดียวต่อเครื่อง)

```bash
python scripts/setup_zcode_hooks.py --dry-run   # ดูก่อน
python scripts/setup_zcode_hooks.py             # ติดตั้งจริง
```

ทำ 2 อย่าง (idempotent — รันซ้ำได้):
1. copy `scripts/hooks/zcode_hook_loader.py` → `~/.zcode/hooks/awiki_hook_loader.py`
2. merge hooks block เข้า `~/.zcode/cli/config.json` (backup `config.json.bak-*` ก่อนเสมอ, hooks/keys อื่นของ user คงเดิม)

**มีผลกับ ZCode session ใหม่เท่านั้น** (config อ่านตอน session start)

## 2. สถาปัตยกรรม — ทำไมต้องมี loader

```
~/.zcode/cli/config.json (per machine, ที่เดียวที่ ZCode รองรับ)
  └─ process hook: <python> ~/.zcode/hooks/awiki_hook_loader.py ${ZCODE_PROJECT_DIR}/<target> [args]
                        │
                        ├─ target ไม่มีใน project นี้ → exit 0 เงียบๆ (เครื่องไม่ noise)
                        └─ target มี → ส่ง stdin ต่อ, ตอบ stdout/exit 0|2 กลับ (exit อื่น normalize เป็น 0)
                              ├─ scripts/hooks/session_start.py + hooks_runner + a_loop_ssot.py   [SessionStart]
                              ├─ scripts/hooks_runner.py --provider zcode                          [UserPromptSubmit/PreToolUse/PostToolUse/Stop]
                              └─ scripts/hooks/a_loop_continue.py                                   [Stop]
```

loader จำเป็นเพราะ config อยู่ระดับเครื่องแต่สคริปต์อยู่ระดับ repo — project อื่นบนเครื่องเดียวกันต้องเงียบสนิท

## 3. วิธีสั่ง loop

| โหมด | วิธีสั่ง | พฤติกรรม |
|---|---|---|
| ปกติ | `/A-Loop "<objective>"` | ทำทีละ task ตาม Phase 2 — หยุดทุกจุดจบ turn |
| **autonomous** | `/A-Loop "<objective>"` + "loop จนจบ" | เขียน goal_id ลง `.tmp/a-loop-autonomous` → Stop hook ผลักทำต่อเองทุกครั้งที่จะหยุด จนกว่า goal จบ |
| หยุดกลางทาง | user พูด "หยุด loop" | ลบ `.tmp/a-loop-autonomous` (hook เองก็ self-clean เมื่อ goal จบ/ตาย) |

## 4. Semantics ของ continuation (กัน spin — สำคัญ)

- งบ **≤3 รอบต่อ task** (override: env `AWIKI_ALOOP_MAX_CONTINUE`) + ZCode cap 3 รอบติดซ้อนอีกชั้น
- **next_todo ขยับ** (task เดิมจบ) → งบรีเซ็ต (ความก้าวหน้า = สิทธิ์วนต่อ)
- **task เดิมค้าง 3 รอบ** → allow stop + `additionalContext` สั่ง checkpoint ลง WO/task_board แล้วจบรอบ รอ user (ห้าม burn token ไปเปล่า)
- state อยู่ใน `.tmp/a-loop-continuations.json` (goal_id + task_id + count)
- **never exits non-zero** — Stop driver พัง = Stop พังทั้ง session, จึง degrade เป็น allow เสมอ

## 5. แผนที่ Loop Engineer 30 ขั้น → กลไกบน ZCode

| ขั้น | กลไก | ชนิด |
|---|---|---|
| RECOVER SSoT / VERIFY ACTUAL STATE | `a_loop_ssot` (SessionStart) + Agent Continuity Gate (อ่าน COLLAB+WO+branch) | 🔴 hook inject + 🟡 model-follow |
| REPO + OWNERSHIP GATE | `hooks_runner --provider zcode` → `check_agent_claim` (Iron Law #11) | 🔴 hook block |
| ROUTE / CLAIM READY LANE | a-router + COLLAB lanes + WO-LANES | 🟡 model-follow |
| Grill / Brainstorm / Spec | a-plan chain + Universal Loop Contract (CI) | 🟡 + CI |
| Impact Analysis / detect_changes | GitNexus | 🟡 (AGENTS.md MUST) |
| Implement (test-first) / Review / Test / E2E | tdd + a-council + `check_test_before_code` | 🔴 hook + 🟡 |
| Defect Memory | `memory_ledger` + a-loop Phase 3 distill (`hooks_runner` Stop) | 🔴 hook (Claude) / 🟡 manual (ZCode ผ่าน runner) |
| Commit / PR / CI / Merge / Fetch | Core Rule 6+8 + `pr-loop-gate.yml` | 🔴 CI |
| STATE checkpoint | task_board + WO Checkpoint log (append ไฟล์เดิม) | 🔴 state-on-disk |
| **NEXT READY NODE ↺** | **`a_loop_continue` (Stop)** | 🔴 **hook ผลัก** |

🔴 = บังคับด้วยกลไก · 🟡 = model ทำตาม protocol

## 6. Verify

```bash
python -m pytest tests/test_a_loop_zcode_hooks.py tests/test_setup_zcode_hooks.py -q
# state จริง (manual):
echo '{"session_id":"t"}' | python scripts/hooks/a_loop_continue.py   # ไม่มี flag → เงียบ exit 0
# E2E: หลังติดตั้ง เปิด session ใหม่ใน repo ที่มี goal active → ต้องเห็น "[a-loop SSoT ...]" ใน context
```

## 7. ข้อจำกัด / ถัดไป

- 3-continue cap = ต่อ user turn — ข้าม turn/session ให้ state ใน task_board พาไปต่อ (อยู่แล้ว)
- แจกจ่ายเป็น **ZCode plugin** (hooks/hooks.json auto-enable ไม่ต้องรัน setup ต่อเครื่อง) = backlog
- pattern loader นี้ copy ไปใช้กับ Codex/Gemini hooks ของตัวเองได้
- docs ที่ตามอัปเดต: `zcode.z.ai/en/docs/hooks` + local `zcode-guide` plugin `diagnosing-hooks` skill
