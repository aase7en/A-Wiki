# WO-ALOOP-ZCODE-20260901 — a-loop Loop Engineer mode บน ZCode (hooks จริง)

Status: MERGE_READY / CLAIM_RELEASED · Created: 2026-09-01 · Owner: GLM/ZCode (lane GLM — deterministic/โค้ด)
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

- 2026-09-01 **✅ MERGED — PR #45 → main `05c0e4e5`** (user-authorized): CI 3/3 เขียวที่ rebased HEAD `b4d9cf69`
  (Core verification 6m17s · loop-contract · py38-smoke) · rebase resolve COLLAB conflict กับ main ใหม่
  (PRs #42-44 ล้างตาราง claim เก่า — เคารพ cleanup ฝั่งนั้น) · fetch-verify main SHA แล้ว ·
  ติดตั้งบนเครื่อง Win แล้ว (`~/.zcode/cli/config.json` 11 hooks/5 events + loader, backup
  `config.json.bak-20260901-233637`) · remaining: verify ใน ZCode session ใหม่ (SSoT inject + Stop
  continuation) + backlog: แพ็ก ZCode plugin
- 2026-09-01 created: facts verified (online + local + side-effect), TDD 23/23 เขียว,
  skill v1.1.0 + reference เขียนแล้ว, branch `feat/a-loop-zcode-loop-engineer`
- 2026-09-01 next: regen-check/privacy/audit → commit chunks → draft PR (Loop-Evidence) →
  ติดตั้งบนเครื่องนี้ (`python scripts/setup_zcode_hooks.py`) หลัง PR แล้ว verify ใน session ใหม่
- หมายเหตุกระบวนการ: งานเริ่มใน session เดียวกับที่ค้นพบ facts (claim row เพิ่มหลังเริ่มเขียน
  tests ~30 นาที — gap ที่ควรเริ่ม claim ก่อน; note เพื่อไม่ทำซ้ำ; ironic จุดนี้คือ claim-gate
  hook ที่ควะกันเรื่องนี้เองไม่ได้ยิงบน ZCode = ปัญหาที่ WO นี้แก้)
- Backlog: แพ็กเป็น ZCode plugin (hooks/hooks.json) แจกข้ามเครื่องไม่ต้อง setup ต่อเครื่อง

## Checkpoint - 2026-09-02 runtime matcher + cp874 repair

Post-merge live ZCode logs exposed a real runtime blocker that PR #45 tests missed: `~/.zcode/cli/config.json` was rejected with `config_file_invalid` because generated `UserPromptSubmit` and `Stop` groups used `matcher: ""`; ZCode requires a non-empty matcher and documents omission as match-all. The active desktop session therefore had no A-Wiki user-hook execution evidence.

TDD repair 1: regression `test_build_hooks_block_omits_matcher_for_match_all_events` was RED on the shipped generator. GitNexus pre-edit impact for `build_hooks_block` = MEDIUM, 9 impacted symbols, 0 execution flows. `HOOK_WIRING` now uses `None` for match-all and `build_hooks_block()` omits the matcher key instead of serializing an empty string. Target GREEN; related ZCode installer/hook suite reached 24 passed.

Live reinstall then exposed a second deterministic Windows defect: config was written correctly but installer exited 1 because its final Thai/arrow console text raised `UnicodeEncodeError` under cp874. Regression `test_installer_cli_survives_cp874_console` reproduced the failure. GitNexus impact for `main()` = LOW, 2 impacted symbols, 0 execution flows. CLI guidance is now ASCII-safe; compile PASS and related suite = **25 passed**.

Machine E2E after repair: installer exit 0, backup `config.json.bak-20260902-005621`, 11 process hooks across 5 events, `empty_matchers=[]`, and match-all matcher omitted for both UserPromptSubmit and Stop. A fresh ZCode CLI process from `%TEMP%` ran `skills list --json` with `rc=0`, `stderr=0`, loaded 473 skills, and reported no `config_file_invalid` diagnostic. Two unrelated pre-existing `skill_description_too_long` diagnostics remain outside this WO. Existing ZCode GUI sessions still use their startup snapshot; the next fresh GUI/task session is the remaining presentation-layer confirmation for SessionStart/Stop behavior.

## Checkpoint - 2026-09-02 final Primary release

Primary reconciled this branch with merged Review Bus main `8dfcbe06` using a merge commit (no force-push). PR #46 push-main Core CI run `33540896144` completed SUCCESS at that exact main SHA.

Post-reconcile evidence: Review Bus + ZCode related regression = **99 passed**; compile PASS. Installed ZCode config has five expected events, no empty matcher values, and omits matchers for UserPromptSubmit/Stop match-all groups. Fresh headless ZCode `skills list --json` returned rc=0, 473 skills, stderr empty, and zero `config_file_invalid` hits; two unrelated pre-existing overlong-skill diagnostics remain out of scope. Privacy PASS; security 6,322 tracked / 51 baseline / 0 new; stale-spec PASS; wiki-health 0 hard / 352 advisory; branch diff check clean.

Final governance release removes this runtime claim and the stale historical MERGED #45 row from the active claim table. Durable evidence remains in this WO and Git history. Next safe action: exact-SHA PR/CI review, merge, fetch/reconcile, then fresh GUI-task SessionStart/Stop presentation proof when a new ZCode task is opened.