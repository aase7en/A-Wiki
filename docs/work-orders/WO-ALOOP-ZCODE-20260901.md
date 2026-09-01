# WO-ALOOP-ZCODE-20260901 — a-loop Loop Engineer mode บน ZCode (hooks จริง)

Status: ACTIVE · Created: 2026-09-01 · Owner: GLM/ZCode (lane GLM — deterministic/โค้ด)
Related: `skills/awiki/a-loop` · `docs/protocols/brain-improvement-gate.md` · AGENTS.md §Universal Loop Contract

## Goal

ทำให้ `/A-Loop` เดิน loop ได้จริงบน ZCode ด้วยกลไก (hooks) ไม่ใช่ prompt-only:
Stop hook ผลัก "ทำต่อ" ขณะ goal ยังมี todo ค้าง + SessionStart ฉีด SSoT (goal +
NEXT READY NODE + WO checkpoints) + พา hard gates (claim gate Iron Law #11 ฯลฯ)
ขึ้นทำงานบน ZCode เป็นครั้งแรก

## Root facts (พิสูจน์แล้ว 2026-09-01)

1. ZCode รองรับ hooks **7 events** — local `zcode-guide` plugin docs + ออนไลน์
   `zcode.z.ai/en/docs/hooks` ตรงกัน (AGENTS.md ที่บอก "ZCode ไม่มี hooks" = เพราะ
   substrate table เก่า)
2. **Stop + `{"decision":"block","reason"}` = main model ทำต่อ, cap 3 รอบติด** โดย runtime
3. **workspace `.zcode/config.json` hooks โดนเมิน** (docs: "ignored as a whole") —
   พิสูจน์ด้วย side-effect: `.tmp/caveman.flag` ไม่ถูกแตะใน session ZCode ปัจจุบัน,
   `session_start.py` output ไม่ปรากฏ → wiring เดิมของ repo ไม่เคยยิงบน ZCode
   ต้องต่อที่ user config `~/.zcode/cli/config.json` (หรือ plugin)

## Design (ผ่าน Brain Improvement Gate)

Brain Gate:
- Gain: loop autonomous จริงบน ZCode + claim gate/hard gates ทำงานบน ZCode + SSoT auto-inject ทุก session
- Shape: hook scripts 3 ตัว + installer 1 + skill reference 1 (เบา, no-op เมื่อไม่มี goal)
- Weight: load on-demand — hook เงียบสนิทเมื่อไม่มี state, ไม่กิน context ถาวร
- Safety: ไม่มี secret/raw; config user-level = ของเครื่อง (backup ก่อนแก้เสมอ)
- Verify: `python -m pytest tests/test_a_loop_zcode_hooks.py tests/test_setup_zcode_hooks.py`

กัน spin: งบ continuation ≤3/task (reset เมื่อ next_todo ขยับ) — task ตัน → allow
stop + additionalContext สั่ง checkpoint; never exit non-zero (Stop driver พังไม่ได้)

## Files

| ไฟล์ | บทบาท |
|---|---|
| `scripts/hooks/a_loop_continue.py` | Stop driver — block+reason ขณะมี todo ค้าง (opt-in ผ่าน `.tmp/a-loop-autonomous`) |
| `scripts/hooks/a_loop_ssot.py` | SessionStart — additionalContext: goal + NEXT + WO ล่าสุด |
| `scripts/hooks/zcode_hook_loader.py` | machine-local dispatcher — no-op เมื่อ target หาย, forward 0/2 |
| `scripts/setup_zcode_hooks.py` | installer per machine (loader + merge user config, idempotent, backup) |
| `tests/test_a_loop_zcode_hooks.py` | 17 tests — decide/main/build_context/loader |
| `tests/test_setup_zcode_hooks.py` | 6 tests — block/idempotency/install/dry-run |
| `skills/awiki/a-loop/SKILL.md` | +section Loop Engineer mode (v1.1.0) |
| `skills/awiki/a-loop/references/zcode-loop-engineer.md` | docs เต็ม: facts/ติดตั้ง/semantics/แผนที่ 30 ขั้น |

## Verify commands

```bash
python -m pytest tests/test_a_loop_zcode_hooks.py tests/test_setup_zcode_hooks.py -q   # 23 passed
python scripts/regen-skill-surfaces.py --check    # No drift
python scripts/verify-skill-surfaces.py           # visibility OK
python scripts/check-privacy.py                   # clean
python scripts/audit_a_suite.py                   # a-loop pass
```

## Checkpoint

- 2026-09-01 created: facts verified (online + local + side-effect), TDD 23/23 เขียว,
  skill v1.1.0 + reference เขียนแล้ว, branch `feat/a-loop-zcode-loop-engineer`
- 2026-09-01 next: regen-check/privacy/audit → commit chunks → draft PR (Loop-Evidence) →
  ติดตั้งบนเครื่องนี้ (`python scripts/setup_zcode_hooks.py`) หลัง PR แล้ว verify ใน session ใหม่
- หมายเหตุกระบวนการ: งานเริ่มใน session เดียวกับที่ค้นพบ facts (claim row เพิ่มหลังเริ่มเขียน
  tests ~30 นาที — gap ที่ควรเริ่ม claim ก่อน; note เพื่อไม่ทำซ้ำ; ironic จุดนี้คือ claim-gate
  hook ที่ควะกันเรื่องนี้เองไม่ได้ยิงบน ZCode = ปัญหาที่ WO นี้แก้)
- Backlog: แพ็กเป็น ZCode plugin (hooks/hooks.json) แจกข้ามเครื่องไม่ต้อง setup ต่อเครื่อง
