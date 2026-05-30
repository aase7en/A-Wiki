# A-Wiki Platform Hardening Plan

> Status: Step 0 baseline audit complete.
> Owner: Primary AI agent + user.
> Scope: A-Wiki across Work PC, MacBook, mobile, Claude Code, Codex, Gemini CLI, Antigravity, Cursor, Windsurf, Cline, Copilot, Obsidian, and Google Drive external data.
> Updated: 2026-05-29

## Goal

Make A-Wiki behave like one reliable second brain no matter which device, OS, or AI agent opens it.

The target state is:

- repo state syncs through `origin/main`;
- heavy/private source data syncs through the external `A-Wiki-Data` Google Drive folder;
- every platform reads the same operating rules;
- critical guardrails work even when a platform does not support Claude-style hooks;
- every feature has a clear health check;
- every remediation step records progress here, in `wiki/context/session-memory.md`, and in `log.md`, then pushes to `origin/main`.

## Current Architecture

| Layer | Current mechanism | Source of truth |
|---|---|---|
| Git brain | `A:\GitHub\A-Wiki` on Work PC; Mac path differs | `origin/main` |
| Heavy/private data | `drive/` and `raw/` links | Google Drive `A-Wiki-Data` |
| Work PC external data path | `L:\My Drive\A-Wiki-Data` | Google Drive |
| Mac external data path | Google Drive under `~/Library/CloudStorage/.../My Drive/A-Wiki-Data` | Google Drive |
| Universal rules | `AGENTS.md` | git |
| Claude runtime | `CLAUDE.md`, `.claude/settings.json`, `.claude/hooks/*` | git + local ignored config |
| Codex runtime | `.codex/config.toml`, `.codex/hooks.json`, `.codex/hooks/*` | local ignored config |
| Gemini runtime | `GEMINI.md`, `.gemini/settings.json` | local ignored config |
| Other editors | `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md` | git |
| Wiki index/search | `scripts/gen-index.py`, FTS5, graph, canvas | git-generated files |
| External source immutability | `raw/` + hook guards | Google Drive + hooks |

## Step 0 Findings

### Critical

1. Local Codex config contains plaintext API keys.
   - File observed locally: `.codex/config.toml`.
   - Git status check shows `.codex/config.toml` is ignored and not tracked, but it is still plaintext on disk.
   - Risk: accidental copy, screenshot, sync, backup, or tool output exposure.
   - Required fix: move Codex secrets to Drive `.secrets` or environment injection, then rotate exposed keys.

2. Secret leak hook is referenced but missing.
   - `.claude/settings.json` and `.codex/hooks.json` call `python scripts/hooks_runner.py check-secret-leak`.
   - `scripts/hooks/check_secret_leak.py` does not exist.
   - Risk: the intended last line of defense against committed secrets is absent.
   - Required fix: implement hook, tests, and staged-diff scan.

### High

3. Windows junctions are misclassified by the cloud-link checker.
   - Work PC has `drive/` as Junction to `L:\My Drive\A-Wiki-Data`.
   - Work PC has `raw/` as Junction to `L:\My Drive\A-Wiki-Data\raw`.
   - `scripts/hooks/check_drive_link.py` reports both as real directories because `Path.is_symlink()` does not treat Windows Junctions as symlinks.
   - Risk: false warnings at session start; agents may try unsafe relink/migration.
   - Required fix: detect Windows reparse points/junctions and tolerate `PermissionError`.

4. `scripts/wiki/*.py` shim files are not valid Python on Windows.
   - `python scripts/wiki/gen-index.py --dry-run` fails with `SyntaxError`.
   - Tests import `scripts/wiki/gen-index.py`, so the wrapper breaks test discovery.
   - Risk: documented commands fail; agents trust broken commands.
   - Required fix: replace shim files with real Python wrappers or update all docs/tests to canonical root scripts.

5. Documentation command drift.
   - `AGENTS.md` says `python scripts/wiki/gen-index.py --dry-run`.
   - Actual root script supports `--check`, not `--dry-run`.
   - Risk: every platform inherits a broken validation command.
   - Required fix: update docs after wrapper strategy is chosen.

6. Hook parity differs by platform.
   - Claude has explicit lifecycle hooks.
   - Codex has local hooks config, but `.codex/` is ignored and may not exist on another machine.
   - Gemini has a settings file pointing to hook runner, but real lifecycle support must be verified.
   - Cursor/Windsurf/Cline/Copilot mostly rely on instruction files, not active guards.
   - Antigravity playbook exists, but it references InW-Wiki-era wording and assumes hook behavior that may not be active.
   - Risk: safety depends on which tool the user opened.
   - Required fix: create one portable health command and one portable preflight command that every platform can run manually or via hooks.

### Medium

7. Stop hook still contains branch merge behavior.
   - `stop-auto-commit.sh` can merge a feature branch into `main`.
   - Current policy is no branch, no PR, no worktree.
   - Risk: stale fallback behavior contradicts solo-main policy.
   - Required fix: change to warn/block when not on `main`.

8. `review-check.py` produces too many failures to be actionable.
   - Latest report had thousands of failures, mostly from frontmatter/link quality rules applied to generated/context files.
   - Risk: alert fatigue; real issues hide in noise.
   - Required fix: define separate rule profiles for generated context, entity/concept pages, sources, and protocol docs.

9. External data layer is under-documented as a first-class system component.
   - The user confirmed A-Wiki depends on `L:\My Drive\A-Wiki-Data` on Work PC and a different Google Drive path on Mac.
   - Risk: future agents treat repo as the whole system and miss `drive/`, `.secrets`, `raw/`, userscript backups, OCR feedback.
   - Required fix: document External Data Layer in AGENTS/GEMINI/Codex-facing docs and add health checks.

10. `session-memory.md` still contains stale path assumptions.
    - Sticky note says main wiki path is `/Users/aase7en/Desktop/InW-Wiki`.
    - Current Work PC path is `A:\GitHub\A-Wiki`.
    - Risk: handoff confusion between old InW-Wiki and current A-Wiki.
    - Required fix: replace with platform-neutral storage statement.

11. Secrets-on-demand helper is referenced but missing from the repo.
    - `scripts/hooks/check_claudemd_lock.py` imports `scripts/lib/drive_secrets.py`.
    - `scripts/import-keys.py` comments also describe `scripts/lib/drive_secrets.py::fetch_secret()`.
    - Current Work PC repo has no `scripts/lib/` directory.
    - Risk: Drive-first secret fetching silently falls back or fails differently per machine; docs overstate the available implementation.
    - Required fix: restore/add `scripts/lib/drive_secrets.py`, ensure `.gitignore` does not accidentally exclude it, and test it without printing secret values.

## Remediation Work Plan

## Priority Handoff Plan

When switching device or agent, read `docs/runbooks/a-wiki-handoff-priority-plan.md` first.

Current priority order:

1. **P0 Secret Safety** — repo guardrails are done; user key rotation is still pending.
2. **P1 Cross-Device Verification** — Work PC passes; Mac verification is pending.
3. **P1 Codex Local Config Sync** — Work PC local `.codex` config repaired; tracked template/setup sync is pending.
4. **P2 Dependency Bootstrap Reliability** — `apsw` and GitNexus repair paths are pending.
5. **P2 Review Noise Reduction** — profiles/actionable reports are pending.
6. **P3 Sync Reliability + Platform Docs** — final playbook and doc sweep are pending.

### Step 1: Secret Safety Baseline

Purpose: stop plaintext secret exposure and make secret leak prevention real.

Tasks:

1. Implement `scripts/hooks/check_secret_leak.py`.
2. Add tests in `tests/test_hooks.py` for command text, staged diff, and allowlisted examples.
3. Replace local Codex plaintext key loading with Drive `.secrets` or user environment import flow.
4. Restore/add `scripts/lib/drive_secrets.py` and tests for secret-name listing / health checks without printing values.
5. Document that exposed keys must be rotated after migration.
6. Verify `python -m pytest tests/test_hooks.py -v`.

Acceptance criteria:

- Missing hook gap is closed.
- No tracked file contains live secrets.
- Local ignored config no longer needs plaintext long-lived API keys.
- Rotation reminder is logged for user action.

### Step 2: Cross-Platform Link Health

Purpose: make Google Drive `A-Wiki-Data` a verified first-class dependency.

Tasks:

1. Fix `scripts/hooks/check_drive_link.py` to support Windows Junction/ReparsePoint, POSIX symlink, `.drive-path`, and `PermissionError`.
2. Add tests using monkeypatched path probes.
3. Add a richer command, likely `scripts/health_external_data.py`, that reports resolved drive path, resolved raw path, expected folders, raw file count, and `.secrets` presence without printing contents.
4. Verify on Work PC and Mac.

Acceptance criteria:

- Work PC reports `drive/` and `raw/` OK when they are junctions.
- Mac reports symlink OK.
- Broken/missing Drive mount produces a clear warning without false migration advice.

### Step 3: Script Entry Point Normalization

Purpose: make documented commands work on Windows, Mac, Git Bash, WSL, and Python imports.

Tasks:

1. Replace `scripts/wiki/*.py` shim files with valid Python wrappers, or remove shim use and update all docs/tests to canonical root scripts.
2. Fix docs to use `python scripts/gen-index.py --check`, not `--dry-run`.
3. Verify `python scripts/gen-index.py --check` and `python -m pytest tests/test_gen_index.py -v`.

Acceptance criteria:

- No documented command points at invalid shim code.
- Tests can import the index module on Windows.

### Step 4: Portable Agent Preflight

Purpose: make every platform start from the same state even without lifecycle hooks.

Tasks:

1. Add `scripts/agent-preflight.py` or similar.
2. Check branch, remote reachability, working tree summary, drive/raw health, generated index freshness, hooks present, secret hook present, and instruction drift.
3. Add one-line invocation to all platform instruction files.

Acceptance criteria:

- Any agent can run one command and know if A-Wiki is safe to work on.
- Mobile/human workflows have a short manual checklist when scripts cannot run.

### Step 5: Hook Parity and Policy Cleanup

Purpose: reduce behavior drift between Claude, Codex, Gemini, and other tools.

Tasks:

1. Generate or sync hook config from one source of truth.
2. Update `stop-auto-commit.sh` to refuse non-main instead of merging branches.
3. Add a config audit that detects hook commands pointing to missing files.
4. Verify all hook commands resolve on Windows and Mac.

Acceptance criteria:

- Claude and Codex hook lists match where possible.
- Missing hook references fail health checks.
- Branch policy is consistent everywhere.

### Step 6: Review Noise Reduction

Purpose: make wiki health reports useful.

Tasks:

1. Add review profiles for content, generated files, protocol docs, and full scan.
2. Exclude or downgrade generated context files from strict frontmatter/TL;DR checks.
3. Add summary focused on top actionable issues.

Acceptance criteria:

- `review-check.py --strict --profile content` has a realistic failure count.
- Generated files no longer drown out real content defects.

### Step 7: Cross-Device Sync Reliability

Purpose: make Mac, Work PC, mobile, and future machines continue cleanly.

Tasks:

1. Update setup-new-machine runbook for current A-Wiki paths and Google Drive model.
2. Add "close old session before opening new session" warning to preflight.
3. Verify `sync.py --now` and `sync.py --daemon` on Mac and Work PC.
4. Document mobile/Obsidian workflow separately from AI-agent workflow.

Acceptance criteria:

- New device setup takes one path through `scripts/setup-local.sh`.
- Device-specific paths are not hardcoded in universal docs except examples.

### Step 8: Platform Instruction Refresh

Purpose: keep every software surface aligned.

Tasks:

1. Refresh AGENTS, Gemini, Copilot, Cursor, Windsurf, Cline, and Antigravity instructions.
2. Add External Data Layer section everywhere short enough to follow.
3. Add command matrix by platform.

Acceptance criteria:

- No platform doc points at stale InW-Wiki paths.
- Every platform has a clear "first 3 commands" section.

## Progress Ledger

| Step | Status | Date | Notes |
|---|---|---|---|
| 0. Baseline audit + plan | Done | 2026-05-29 | Found secret config risk, missing secret hook, missing `scripts/lib/drive_secrets.py`, Windows junction false warnings, invalid script shim, doc command drift, hook parity gaps, review noise, external data under-documentation. |
| 1. Secret Safety Baseline | Code complete; user rotation pending | 2026-05-29 | Added `check_secret_leak.py`, restored `scripts/lib/drive_secrets.py`, added tests, sanitized local ignored `.codex/config.toml`; user still needs to rotate keys that were previously exposed in local plaintext config. |
| 2. Cross-Platform Link Health | Done on Work PC; Mac verification pending | 2026-05-29 | `check_drive_link.py` and `drive_path.py` now support Windows Junction/ReparsePoint; added `scripts/health_external_data.py`; Work PC resolves `L:\My Drive\A-Wiki-Data`, reports 54 raw files, and does not print secrets. |
| 3. Script Entry Point Normalization | Done | 2026-05-29 | Replaced Python shims under `scripts/wiki/` with real compatibility wrappers, fixed Windows console encoding for search/review/gen-index chain output, excluded generated context from review-check self-input, and updated stale gen-index docs from `--dry-run` to `--check`. |
| 4. Portable Agent Preflight | Done on Work PC; Mac verification pending | 2026-05-29 | Added `scripts/agent-preflight.py`, tests, and one-line invocation across platform instruction files; checks branch, origin/main reachability, working tree, Drive data, generated context freshness, core hooks, and instruction drift. |
| 5. Hook Parity and Policy Cleanup | Core policy done on Work PC; Mac verification pending | 2026-05-29 | `stop-auto-commit.sh` now refuses non-main instead of merging branches; `.codex/hooks.json` uses portable relative hook paths; preflight audits hook command paths. |
| 6. Review Noise Reduction | Done | 2026-05-30 | Added `review-check.py --profile {content,generated,protocol,full}`, top actionable summary, generated-report self-scan exclusion, improved link resolver for `wiki/` and repo paths, and switched `gen-index.py` chain to `--profile content`; generated profile strict passes, content strict now reports a realistic 44 link failures plus downgraded metadata warnings. |
| 7. Cross-Device Sync Reliability | Pending | - | Covers Mac/PC/mobile usage. |
| 8. Platform Instruction Refresh | Pending | - | Final doc sweep after behavior is fixed. |

## Rule for Future Steps

After each step:

1. update this progress ledger;
2. update `wiki/context/session-memory.md` with what changed and what remains;
3. add a short entry to `log.md`;
4. run the relevant verification command for that step;
5. commit directly to `main`;
6. push to `origin/main`.
