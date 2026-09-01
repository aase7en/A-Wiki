# WO-PORTABILITY-BASELINE-20260902 — Windows portability baseline burn-down

Status: PB0_MEASURED_PB1_CLAIM_EXPANSION_NEXT
Executor: GLM5.3-ZCode-MAX
Integrity / final reviewer: GPT-5.6-Sol
Branch: `fix/wo-portability-baseline-glm-20260902`
Worktree: `<WORKTREE>/A-Wiki-portability-glm-20260902`
Base: `8dfcbe068a00cdfa6671eef3e4e603c4552aa6d0`
Claim checkpoint: `64272cd06ae6b128fcce09217373c988390c4c07`

## Goal

Burn down current, reproducible Windows portability baseline debt using bounded root-cause families and deterministic TDD. Prioritize cp874/subprocess encoding and Git-Bash/MSYS/path behavior. Do not chase environment-only failures merely to make a count green.

Use ZCode Goal Mode + `$a-loop` for the long execution loop. Keep this Work Order as the only durable task/checkpoint file for this lane.

## Baseline authority

- M1 full Windows baseline: `58 failed / 3398 passed / 19 skipped` at `71406f8a...`.
- M8: `54 failed / 3531 passed / 19 skipped`; all 54 replayed and failed at M1, so they were PRE_EXISTING.
- Known families include Windows cp874 console/subprocess decoding, Git-Bash/MSYS path or symlink assumptions, linked-worktree assumptions, and Windows FTS runtime/tool debt.
- PR #46 is now merged at base `8dfcbe06`; it already fixed the Review Bus linked-worktree `gitdir:` family. Re-measure current baseline instead of assuming 54 remain.

## P0 — inventory before production mutation

Current claim allows mutation of only:
- `COLLAB.md`
- this Work Order

Until P0 is complete, all code/test inspection is READ-ONLY.

P0 required evidence:
1. Recover `BRAIN-ENTRY.md` -> `PROJECT-GRAPH.yaml` -> `COLLAB.md` -> this WO -> `AGENTS.md` applicable rules.
2. Verify worktree/branch/HEAD/dirty state and `python -m conductor status --json`.
3. Run native Windows `python -m pytest tests -q` with no UTF-8 environment override.
4. Record every failing nodeid and exact summary in this WO.
5. Compare failures with M1/M8 evidence in `docs/work-orders/WO-RFR-20260824.md`.
6. Classify by root-cause family: CP874/ENCODING, GIT_BASH_MSYS_PATH, WORKTREE_GIT, FTS_ENVIRONMENT, OTHER.
7. For each family, identify likely production/test files and run GitNexus impact before proposing mutation.
8. Update this WO with a failure matrix and the smallest exact file scope for the first independent family.

Before any production/test edit, expand the existing claim to that exact family scope, commit+push the claim expansion, then continue. Never claim broad `scripts/**` or `tests/**`.

## Priority order

PB-0 — fresh baseline + family matrix.
PB-1 — cp874 / subprocess decoding / console-output defects.
PB-2 — Git-Bash / MSYS / path / symlink deterministic defects.
PB-3 — remaining linked-worktree/path assumptions only if still reproducible and not already covered by PR #46.
PB-4 — full regression, audit, checkpoint, Primary handoff.

## PB-0 checkpoint — 2026-09-02 fresh baseline measured

**Environment (exact):**
- Worktree `<WORKTREE>/A-Wiki-portability-glm-20260902`, branch `fix/wo-portability-baseline-glm-20260902`, HEAD `29352ab41d90ef6396745e3aad2949ccbdc53ac2` (= pushed remote HEAD; clean tree).
- Python `3.11.15` (hermes-agent venv interpreter), pytest `9.1.1`.
- OS Windows 10.0.26200 x64, shell Git Bash; console codepage Thai `cp874`.
- Note: machine-level env carries system-wide `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8`; the baseline run explicitly removed both (`env -u PYTHONUTF8 -u PYTHONIOENCODING`), matching the M8 no-override protocol.

**Fresh baseline (no UTF-8 override): `python -m pytest tests -q` = 21 failed / 3599 passed / 19 skipped in 1324.49s.**

Comparison: M1 = 58F/3398P/19S; M8 = 54F/3531P/19S. Baseline debt dropped 54→21 (33 previously failing nodeids were repaired by later merges, incl. PR #46 linked-worktree `gitdir:` family). The 21 below are the current authority.

**Failure matrix (all 21 nodeids, root signal from the run log):**

| # | Nodeid | Root signal | Family |
|---|---|---|---|
| 1 | tests/test_awiki_cli.py::test_cli_status_end_to_end | child `python -m conductor status --json` rc1; `cp874.py line 19 charmap_encode` | CP874/ENCODING (child encode) |
| 2 | tests/test_check_machine_path_hook.py::test_blocks_windows_user_path | hook child rc1 (expected 2); `UnicodeEncodeError` in child | CP874/ENCODING (child encode) |
| 3 | tests/test_check_machine_path_hook.py::test_blocks_posix_user_path | same | CP874/ENCODING (child encode) |
| 4 | tests/test_check_pr_loop.py::test_cli_reads_json_payload_and_exits | `UnicodeEncodeError: 'charmap' codec can't encode '\u2705' position 0` | CP874/ENCODING (child encode) |
| 5 | tests/test_conductor.py::TestCli::test_status_json_valid | conductor child rc1, stderr ends `...EncodeError` | CP874/ENCODING (child encode) |
| 6 | tests/test_conductor.py::TestBridgeSearch::test_search_fts_returns_structured_hits | conductor child rc1, same | CP874/ENCODING (child encode) |
| 7 | tests/test_conductor.py::TestBridgeSearch::test_search_hybrid_mode_is_default | same | CP874/ENCODING (child encode) |
| 8 | tests/test_doctor_guide.py::test_doctor_runs_and_reports_sections | doctor stdout empty (crash before sections) | CP874/ENCODING (child encode) |
| 9 | tests/test_doctor_guide.py::test_guide_topics | guide child stdout empty; stderr `EncodeError`; Thai assertion | CP874/ENCODING (child encode) |
| 10 | tests/test_graph_yaml.py::test_cli_exit_zero_when_clean | child `check-graph-yaml.py` traceback at `cp874.py line 19 charmap_encode` | CP874/ENCODING (child encode) |
| 11 | tests/test_rabies_regression.py::test_regression_hns_pass | `verify_regression.py` exit1, `'\u2705' position 2` encode crash | CP874/ENCODING (child encode) |
| 12 | tests/test_versioning.py::test_doctor_prints_version | doctor stdout `''`; child EncodeError | CP874/ENCODING (child encode) |
| 13 | tests/test_versioning.py::test_doctor_version_line_is_first_class | version idx -1 (empty stdout) | CP874/ENCODING (child encode) |
| 14 | tests/test_link_agent_configs.py::test_keeps_existing_real_directory | parent reader-thread `UnicodeDecodeError: 'charmap' can't decode byte 0x9f` → `stdout=None` | CP874/ENCODING (parent decode of UTF-8 bash output) |
| 15 | tests/test_link_agent_configs.py::test_without_force_skills_real_dir_is_left_alone | same mechanism | CP874/ENCODING (parent decode) |
| 16 | tests/test_link_agent_configs.py::test_msys_ln_copy_behavior_never_leaves_silent_copy | same | CP874/ENCODING (parent decode) |
| 17 | tests/test_link_agent_configs.py::test_status_ok_after_link | same | CP874/ENCODING (parent decode) |
| 18 | tests/test_link_agent_configs.py::test_status_counts_real_link_target_not_just_symlink_bit | same | CP874/ENCODING (parent decode) |
| 19 | tests/test_link_agent_configs.py::test_clean_backups_dry_run_deletes_nothing | same | CP874/ENCODING (parent decode) |
| 20 | tests/test_link_my_skills.py::test_link_my_skills_skips_existing_real_directory | same | CP874/ENCODING (parent decode) |
| 21 | tests/test_user_journey_e2e.py::TestJourney2bMcpButtons::test_semantic_search_button_degrades_honestly | MCP `wiki_semantic_search` returns `Internal error: TypeError: the JSON object must be str, bytes or bytearray, not NoneType` instead of honest `missing dependency` degrade | OTHER (degrade-path defect, repo-owned) |

**Family classification totals:** CP874/ENCODING = 20 (13 child-encode + 7 parent-decode) · GIT_BASH_MSYS_PATH = 0 distinct remaining (all 7 link-script failures reproduce as pure cp874 decode crashes in the pytest reader thread — reproduced directly: `UnicodeDecodeError ... byte 0x9f` in `subprocess._readerthread`, after which `stdout` becomes None) · WORKTREE_GIT = 0 (PR #46 fixed that family) · FTS_ENVIRONMENT = 0 failing (the M8 FTS-debt test is now among the 19 skipped or passes; the conductor search failures above are encode crashes, not FTS) · OTHER = 1 (MCP degrade path).

**Mechanism note (single root cause for 20/21):** on native Thai Windows, Python child processes whose stdout is a pipe encode with locale `cp874`; printing `✅`/emoji/Thai crashes (`charmap_encode`), and parent tests using `text=True` without explicit encoding decode the UTF-8 bash-script output as cp874 and crash the reader thread (stdout→None). The repo already has an established inline guard idiom — `sys.stdout/stderr.reconfigure(encoding="utf-8", errors="replace")` (scripts/hooks_runner.py, scripts/a_escalate.py, scripts/check-staged-syntax.py, scripts/regen-skill-surfaces.py) — the failing entries simply lack it. All 13 encode-side test parents already pass `encoding="utf-8", errors="replace"` to subprocess, so the child entry scripts are the only encode-side gap; the 2 link-script test helpers are the only decode-side gap.

**Smallest exact file scope for PB-1 (first independent family — CP874/ENCODING):**

Production (add the existing reconfigure guard idiom at entry):
1. `conductor/__main__.py` (covers #1,5,6,7)
2. `scripts/awiki-doctor.py` (covers #8,12,13)
3. `scripts/awiki-guide.py` (covers #9)
4. `scripts/check_pr_loop.py` (covers #4)
5. `scripts/hooks/check_machine_path.py` (covers #2,3)
6. `scripts/check-graph-yaml.py` (covers #10)
7. `scripts/hospital/verify_regression.py` (covers #11)

Tests (decode-side harness portability — explicit UTF-8 decode matching the documented UTF-8 bash-script output; not assertion weakening):
8. `tests/test_link_agent_configs.py` (covers #14-19)
9. `tests/test_link_my_skills.py` (covers #20)

New deterministic Tier-1 regression (so the family stays fixed on any locale, not only cp874 machines):
10. `tests/test_console_pipe_safety.py` (NEW — spawn representative children with `PYTHONIOENCODING=cp874` forced, assert rc/decoded output)

Deferred to its own family: #21 (`scripts/mcp-wiki-server.py` degrade path) — investigate/fix after PB-1.

RED evidence = the 21 baseline failures above (per-family focused re-run commands recorded below as work proceeds).

Next safe action: GitNexus impact for the 7 production entry symbols, then claim expansion to exactly the 10 files above, commit+push, then RED/TDD per file.

## PB-1 checkpoint — CP874/ENCODING family repaired (2026-09-02)

**Claim expansion:** conductor claim row `WO-PORTABILITY-BASELINE-20260902 PB-1 cp874 pipe-safety family` (13 exact files incl. `scripts/mcp-wiki-server.py` + `tests/test_user_journey_e2e.py` for PB-1b), pushed at `79a162c6`. No overlap with GPT Primary's ZCode-runtime lane. GitNexus impact before edit: all 7 production entry `main` symbols = **LOW** (0-2 direct callers, 0 processes); `tool_wiki_semantic_search`/`tool_wiki_regen_index` = 0 direct callers (registry-dispatched).

**RED (deterministic Tier-1, new file `tests/test_console_pipe_safety.py`):**
`env -u PYTHONUTF8 -u PYTHONIOENCODING python -m pytest tests/test_console_pipe_safety.py -q` = **7 failed in 3.15s** — every child crashed with the exact baseline signature `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'`. The tests force `PYTHONIOENCODING=cp874` + `PYTHONUTF8=0` in the child, so the crash reproduces on ANY locale (UTF-8 CI included), not only Thai-Windows machines.

**Fix (commit `71246e8c`, 10 files, +170 lines):**
- 7 production entries gained the existing repo guard idiom `for _s in (sys.stdout, sys.stderr): _s.reconfigure(encoding="utf-8", errors="replace")` (same as scripts/hooks_runner.py / scripts/a_escalate.py): `conductor/__main__.py`, `scripts/awiki-doctor.py`, `scripts/awiki-guide.py`, `scripts/check_pr_loop.py`, `scripts/hooks/check_machine_path.py`, `scripts/check-graph-yaml.py`, `scripts/hospital/verify_regression.py`.
- 2 test helpers gained explicit `encoding="utf-8", errors="replace"` (bash scripts emit UTF-8; `text=True` alone decodes with the locale codec and crashes the reader thread, silently turning `stdout` into None): `tests/test_link_agent_configs.py::run_script`, `tests/test_link_my_skills.py`.
- Guard scope note: interactive Windows consoles already use UTF-16 WriteConsoleW; the guard only changes byte-pipe streams, which is exactly where the crash lived.

**GREEN:** `tests/test_console_pipe_safety.py` = **7 passed in 7.58s**. Full family sweep (all 11 affected files): **101 tests, 100 passed / 1 failed** — the 1 was `test_doctor_guide.py::test_doctor_runs_and_reports_sections` failing on the doctor **privacy section being red**, caused by the new test file's first payload (a non-placeholder Linux-home username) tripping `check-privacy.py`'s `home_path` scanner. Resolved by switching the fixture to the scanner's doc-placeholder username `you` (still denied rc 2 by the hook — that name is not on the hook allowlist). After that: privacy = "no personal data detected" (rc 0) and `tests/test_console_pipe_safety.py + tests/test_doctor_guide.py` = **10 passed**.

**Pre-commit gates for `71246e8c`:** `git diff --check` PASS · managed Python 3.8 `py_compile` on all 7 production files + 3 test files PASS · privacy PASS · GitNexus `detect-changes --scope staged` = 10 files / 18 symbols / **0 processes / risk LOW**.

## PB-1b checkpoint — MCP semantic-search decode defect repaired (2026-09-02)

**Root cause (#21):** `scripts/mcp-wiki-server.py::tool_wiki_semantic_search` ran `query-rag.py` via `subprocess.run(..., text=True)` without an explicit encoding. The child emits UTF-8 (emoji/Thai in snippets — verified 94 non-ASCII bytes per response); under a locale-pipe the parent's reader thread dies on undefined cp874 byte 0x9F (UTF-8 emoji trail byte), `stdout` silently becomes None, and `json.loads(None)` raises `TypeError` surfaced as JSON-RPC `Internal error` instead of the honest missing-dependency degrade the journey test demands. Same family as PB-1, but on the production side of the pipe. (Verified: standalone mimic with matching env succeeded, isolating the failure to the fixture's UTF-8 env + locale-decode combination.)

**RED:** `env -u PYTHONUTF8 -u PYTHONIOENCODING python -m pytest "tests/test_user_journey_e2e.py::TestJourney2bMcpButtons::test_semantic_search_button_degrades_honestly" -q` = **1 failed** (`TypeError: the JSON object must be str, bytes or bytearray, not NoneType` inside the tool).

**Fix (commit `51d3be66`):** explicit `encoding="utf-8", errors="replace"` on all three text-mode child pipes in the server — `tool_wiki_semantic_search` (query-rag) and `tool_wiki_regen_index` (gen-index + build-vec-index, same latent gap: `result.stdout.strip()` would have raised AttributeError on None).

**GREEN:** full `tests/test_user_journey_e2e.py` = **38 passed / 1 skipped in 90.52s**; related `tests/test_mcp_wiki_server.py + tests/test_awiki_adopt.py` = **64 passed**. Python 3.8 `py_compile` PASS; `git diff --check` PASS; GitNexus `detect-changes --scope staged` = 1 file / 2 symbols / **0 processes / risk LOW**.

## PB-2 / PB-3 classification — no distinct defects remain in those families

- **PB-2 (Git-Bash/MSYS/path/symlink):** the 7 link-script failures were 100% the cp874 parent-decode mechanism (reader-thread `UnicodeDecodeError byte 0x9f` → stdout None). After the helper decode fix, all 7 pass — junction/symlink/MSYS-ln logic itself (skip-existing, msys-ln guard, status counts, dry-run) behaves correctly on this machine. No production symlink defect to fix. GIT_BASH_MSYS_PATH final = 0.
- **PB-3 (linked-worktree/git):** 0 failures in the fresh baseline — PR #46's relative-gitdir fix covers this family. Nothing to repair.
- **FTS_ENVIRONMENT:** 0 failing nodeids in the fresh baseline (the M8-era FTS-debt test is skipped/passes). GitNexus FTS extension remains unavailable on this Windows runtime (OpenSSL DLL dependency) — recorded as environment/tool limitation, no machine mutation attempted, per WO rules.

**Safety gates at this checkpoint (pre-final-regression):** privacy = "no personal data detected" PASS · security `scan_repo.py --ci` = **6324 tracked / 51 baseline / 0 new** · stale-spec = `[OK] no stale specs` PASS · wiki-health = **0 hard / 352 advisory** (advisory count unchanged from M8) · `git diff --check` PASS.

**Remaining before completion:** final full native regression, final WO verdict, claim release.

## Parallel-lane boundaries

GPT Primary concurrently owns the ZCode runtime repair lane. Do NOT modify:
- `scripts/setup_zcode_hooks.py`
- `tests/test_setup_zcode_hooks.py`
- `docs/work-orders/WO-ALOOP-ZCODE-20260901.md`
- branch/worktree `fix/wo-aloop-zcode-runtime-matchers`

Avoid Review Bus surfaces unless a fresh baseline proves a remaining independent defect and Primary explicitly expands scope:
- `scripts/lib/a_loop_review.py`
- `tests/test_a_loop_review.py`
- `docs/runbooks/review-bus.md`
- `docs/work-orders/WO-REVIEW-BUS-OPS-20260901.md`

Never modify `AGENTS.md`, `CLAUDE.md`, `raw/`, secrets, the primary checkout, or A-Conductor. Do not install FTS/OpenSSL/system DLLs in this WO. Classify environment-only FTS debt rather than mutating the machine.

## Per-family Loop Engineer contract

For each claimed family:
`RECOVER -> VERIFY -> IMPACT -> RED -> ROOT CAUSE -> IMPLEMENT -> SELF REVIEW -> FOCUSED TEST -> RELATED REGRESSION -> SAFETY GATES -> detect_changes -> CHECKPOINT -> COMMIT/PUSH -> NEXT FAMILY`

Production fixes require a failing test first. Do not weaken tests or hide failures with global UTF-8 environment overrides. Fix the owning code boundary when the behavior is repo-owned.

After each coherent family, append exact evidence to this same WO: HEAD, files, RED/GREEN commands, results, defect mechanism, residual risk, and next safe action. Commit+push each resumable checkpoint.

## Verification minimum per production family

- focused RED/GREEN regression(s)
- relevant related tests
- `git diff --check`
- `python scripts/check-privacy.py`
- `python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt`
- `python scripts/check-stale-specs.py`
- `python scripts/health/wiki_health.py`
- GitNexus impact before symbol edit and `detect_changes` before commit

Tool failure is `UNVERIFIED — tool failure`, never PASS.

## Completion / handoff

Do not merge. GPT Primary owns exact-SHA independent review, remote diff audit, CI verdict, merge and post-merge verification.

The Goal is complete only when PB-0 is measured, every safely claimable high-value portability family is either fixed with deterministic evidence or explicitly classified with a reason not to mutate, the final full regression is recorded, all required gates pass, and this WO identifies any residual environment-only debt.

Stop only for `HUMAN_DECISION_REQUIRED`, `OWNERSHIP_CONFLICT`, `SAFETY_BLOCK`, or scope expansion that Primary must authorize. Do not ask the human to relay detailed results; persist them here and push the branch.
