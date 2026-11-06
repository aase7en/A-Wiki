---
name: grill-me
description: Two-mode, user-invoked-only skill for ANY technical endeavor (skill, MCP server, project, AI agent, plugin, script, config, hook), invoked solely via the literal slash forms `/grill-me plan` and `/grill-me check`. PLAN MODE (`/grill-me plan`) is a design-only grilling interview — it asks only about intent and desired outcome, auto-decides every technical specific by best practice, and never executes, builds, or writes anything until the user gives an explicit green light. CHECK MODE (`/grill-me check`) runs AFTER the green-lit plan has actually been executed — it deeply verifies, strictly read-only, the real result against the approved plan AND the surrounding environment, then PROPOSES repairs as diffs and applies them only after the user explicitly approves each proposal. EXPLICIT INVOCATION ONLY — never auto-trigger on paraphrases such as "grill me", "interview me about this", "check what I built", "verify my work", or "fix what broke". Stay inert until the user literally types `/grill-me plan` or `/grill-me check`. Bare `/grill-me` prints a usage hint.
disable-model-invocation: true
---

# grill-me

Two modes used in sequence. `/grill-me plan` captures intent and plans without executing
anything. After the user's explicit green light and the work's execution, `/grill-me check`
verifies the real result read-only, then proposes (never auto-applies) repairs.

## Subcommand dispatch

Parse the first whitespace-delimited token of `args`:

- `plan` → enter PLAN MODE.
- `check` → enter CHECK MODE.
- empty / any other value → emit this usage hint verbatim and stop:

  > grill-me needs a mode. Use `/grill-me plan` to plan, or `/grill-me check` to verify what was executed afterwards.

## Write-consent model (both modes)

- Before the green light: no writes of any kind (HARD RULE 0 below).
- `/grill-me check` grants consent for **read-only verification only**. Every write —
  repair, revert completion, checkpoint — requires its own explicit "yes" from the user
  on a concrete proposal. There is no auto-apply anywhere in this skill.
- **Claim discipline:** if a proposed repair would touch a file/scope owned by another
  agent's active claim, worktree, or lane, do not propose applying it here — report the
  defect and point the user to the claim owner.

---

## PLAN MODE

Design-and-understanding interview. Plans the work, waits for the explicit green light,
executes/builds/writes nothing.

### User constraint (HARD RULES — never violate)

0. **No execution without explicit green light (ABSOLUTE).** Design-only. No executing,
   building, creating, writing, modifying, running, implementing, or installing anything
   discussed during the grilling until the user gives an explicit, unambiguous green
   light for that specific work. Interview answers are never authorization. If
   everything seems clear, you may say so and ASK to proceed — then wait.
1. **General scope.** Any technical endeavor the user wants to create or change: skill,
   MCP server, project, agent, plugin, script, config, hook.
2. **Treat the user as non-technical.** Their contribution is WHAT and WHY, never HOW.
3. **Ask only about intent — never about code.** Questions cover goal, desired
   behavior/outcome, inputs/outputs in plain words, scope, success criteria, priorities,
   constraints, edge cases. Never ask about implementation, architecture, libraries,
   file layout, or configuration syntax.
4. **Auto-adopt technical recommendations.** Decide every technical matter yourself by
   best practice and proceed; you may briefly note the decision, never ask the user to
   pick.
5. **Re-express or decide, never ask technical.** Turn would-be technical questions into
   plain-language intent questions, or decide them yourself. Research answers in
   files/docs/web instead of asking.
6. **When to pause.** Only (a) truly irreversible or external actions (delete, send,
   public push, paid spend) or (b) genuinely missing non-technical intent.
7. **Language.** Conduct the conversation in the user's preferred language; this file
   stays in English.

### The grilling interview

Interview relentlessly, one question AT A TIME (wait for each answer), walking every
branch — goal, behavior, inputs/outputs, scope, success criteria, priorities,
constraints, edge cases — providing your recommended answer each time so the user can
agree, adjust, or veto. Continue until intent is fully pinned with no ambiguity,
resolving all technical specifics yourself. This skill is self-contained.

### Closing step — offer a live behavior test (never auto-run)

After the green light AND the work's execution, OFFER (do not automatically run) a live
behavior test: actually use the artifact on a representative task and watch it behave as
the approved plan intended. Structural checks (parses/loads/compiles) are the floor, not
the test. If the user accepts: run it, stopping short of anything irreversible/external
(delete, send, public push, paid spend), and report plainly. If it fails: diagnose, then
PROPOSE the fix as a diff and wait for the user's yes before applying (snapshot first,
see CHECK MODE Phase 2); bound to 2–3 proposed-fix rounds before stopping to explain in
plain language. If the only meaningful live run is itself irreversible/external, do not
run it — describe what would happen and ask whether they want it.

---

## CHECK MODE

Runs after a green-lit plan has actually been executed. `/grill-me check` = consent for
**read-only verification** end-to-end; repairs are proposals only. Order: **verify
deeply (read-only) → (if broken) propose surgical repairs → apply only on explicit yes →
confirm healthy.**

### Detect intent FIRST — verify-implementation vs confirm-revert

Read the conversation and judge by MEANING (any language), never phrase-matching:
- **Verify-implementation (default)** → Phases 0–3 below.
- **Confirm-revert** — the user wants something undone: full (everything the discarded
  plan made) or partial (a named subset, keeping the rest). Goal: CONFIRM in-scope
  changes are gone and kept ones intact. If unclear which job or scope, ask ONE short
  plain-language question and wait.

#### Confirm-revert flow

1. Reconstruct the concrete changes (files/artifacts/configs created/edited/deleted,
   absolute paths) from the whole conversation. No journal is kept.
2. Fix scope (full vs the named subset); confirm the split in one plain-language line
   if any doubt.
3. Verify each in-scope change is undone via concrete read-only checks (absent /
   restored-to-prior via snapshot comparison / returned). One check = one falsifiable
   command.
4. If anything in scope is NOT undone: PROPOSE the exact remaining revert (diff or
   action list) and WAIT for an explicit yes — then snapshot first, apply smallest-diff,
   route created files to a trash/backup folder (never hard-delete), re-check. Files on
   the agent-config surface (settings*.json, hooks, MCP configs, permission files) are
   never written without the user's yes, and hook-file edits additionally deserve an
   explicit warning that hooks auto-execute on future tool calls.
5. Partial reverts: re-confirm kept changes are still correctly in place.
6. Confirm whole-environment health (Axis 2, read-only).
7. Report ONE plain-language verdict: what was confirmed undone, what (if anything) you
   proposed to finish and whether it was applied. If something cannot be safely undone,
   say so plainly.

If — verify-implementation mode only — no executed/approved plan is visible, halt
verbatim and never invent a target:

> I cannot find an executed plan in this conversation that I could verify. If the work ran elsewhere or the history was truncated, briefly describe what was planned and approved and where the result is — then I will check it.

### Phase 0 — Anchor

Lock exactly ONE anchor: the **approved plan as amended** (original green-lit plan PLUS
every later addition/refinement/correction folded in, reconstructed by reading the whole
conversation in order), the **result** (artifact paths), and a one-sentence **Prime
Objective**. If several candidates or uncertainty: ask ONE plain-language numbered
question and wait. If compaction lost the plan: ask the user to restate it in one or two
sentences rather than guessing.

### Phase 1 — Deep check (strictly READ-ONLY, two axes)

Depth scales with blast radius. One check = one falsifiable claim tied to one concrete
command. Apply the test *"if this failed, would it mean the work failed or caused
damage?"* — include only checks that pass it.

- **Axis 1 — Plan (as amended) fulfilled.** Every item of the cumulative intent gets its
  own check (ls, grep -c, wc, cat, bash -n, py_compile, JSON-validate, cmp), explicitly
  including later additions.
- **Axis 2 — Integration & environment health.** Affirmatively confirm the surrounding
  environment still works: config loads, settings/hooks/permissions still valid, the
  artifact AND siblings discoverable/usable (skill registered, MCP answers a read-only
  call, script passes syntax check), no collisions or dangling references, nothing
  external damaged. If a part cannot be positively confirmed, mark WARN and say why.

Structured report: check plan, PASS/FAIL per check with Evidence, one-sentence plan
restatement, conspicuous verdict `OVERALL: PASS` or `OVERALL: FAIL — <reason>`.
**Anti-greenwashing:** unverifiable = WARN; overall PASS only if every in-scope check
passed. PASS → Phase 3. FAIL → Phase 2.

### Phase 2 — Propose surgical repairs (only on FAIL)

1. For each defect: read the flagged file in full, then PRESENT a concrete proposal —
   the exact diff (or action), why it is the smallest safe fix, and what it touches.
2. WAIT for the user's explicit yes per proposal. No auto-apply, no batching a yes
   across proposals unless the user says so.
3. On yes: snapshot first into `.grill-me-checkpoints/.pre-fix-<YYYY-MM-DD-HHMMSS>/`
   INSIDE the project directory (never the user's home), apply the smallest diff, re-run
   the FULL Phase 1 check.
4. Bound to 2 fix-and-recheck rounds; then stop and explain in plain language.
5. Rollback is a last resort, proposed explicitly and performed only after yes.
6. Never silently discard the user's artifact; never broaden scope; prefer deletion over
   addition when both achieve the goal.

### Phase 3 — Healthy outcome

- Report what was checked, what was proposed/applied (if anything), snapshot paths.
- Offer (never force) an additive checkpoint at
  `.grill-me-checkpoints/<YYYY-MM-DD-HHMMSS>-grill-me-check/` in the project directory,
  and optionally an off-machine backup. Additive only; pruning routes to trash/backup,
  never hard-deletes.

## Safety invariants

- PLAN MODE writes nothing before the green light; the post-execution live test is
  offered, not auto-run, and its fixes are propose-first.
- CHECK MODE's verification is strictly read-only; every write (repair, revert
  completion, checkpoint) follows a concrete proposal + explicit user yes + snapshot.
- Smallest diffs only; never touch unflagged files; never hard-delete; claim-owned
  scopes are reported to their owners, not repaired here.
- Snapshots/checkpoints live in the project directory, never the home directory.

## Communication protocol

- Plain language with the user; every file/artifact in English. End each turn with a
  one-line `Summary:`.
- Every question is a simple preference/intent decision — never code, never a diff
  judgment the user must make technically.
- If a turn leaves user-only actions, list them in a brief numbered "Manual steps"
  section just above the `Summary:` line; omit when none.
