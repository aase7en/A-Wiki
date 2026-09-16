---
name: a-fasttask
description: "Thin cross-harness router for substantial repository work. Use when a non-trivial repo task needs workflow/executor/lane selection, safe parallel-lane routing, cross-executor continuation/takeover, or temporary-lane closeout. Prefer a compatible repo-local A-FastTask binding when present; never invent a second claim/review/completion authority."
version: 1.0.0
author: A-Wiki
domain: [engineering, ai-ops]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: both
invocation_hint: "/A-FastTask"
a_phase: any
---

# A-FastTask — universal cross-harness entrypoint

A-FastTask is a **router/binder, not a workflow engine**. Its job is to find the
current repository's real authority and hand substantial work to the smallest
existing safe workflow. It may help fill/recycle parallel lanes, recover a
stopped executor, or close temporary worktrees, but it creates no scheduler,
claim store, lease store, reviewer, completion state machine, or cleanup daemon.

## Use / bypass

Use for non-trivial repository work when at least one routing decision exists:
workflow/risk tier, executor choice, WIP lane allocation, continuation/takeover,
or temporary-lane closeout.

Bypass for trivial Q&A, one obvious mechanical edit, or mid-lane execution where
the exact task/claim/workflow is already bound and no new routing decision is
needed.

## Binding order

1. **Recover current repository truth first.** Read the repository entry files,
   current Git/worktree/branch/HEAD/dirty state, active work item, ownership and
   task-relevant policy before mutation. Chat memory is never authority.
2. **Prefer a repo-local A-FastTask binding when one exists.** The canonical
   project-local path is `.agents/skills/a-fasttask/SKILL.md`; if that file is
   tracked/present in the current repository, read it and follow its authority
   pointers. Repo-local rules outrank this generic entrypoint.
3. **If no repo-local A-FastTask exists, use that repository's existing entry,
   claim, workflow, review and release system.** Do not import A-Sunday
   Conductor semantics into an unrelated repository and do not create a new
   authority just to make FastTask work.
4. **A-Wiki itself:** use `a-router`/`a-flow` for workflow routing and `a-claim`
   for shared-surface ownership. `skills-registry.json` remains the skill SSoT.

A missing or contradictory authority item means fail closed and report the
blocker plus the exact next safe action. Never repair authority by inventing a
side-channel task list, lease, queue or handoff database.

## Routing output

At the routing boundary record/report:
- current task/work-order and claim/owner reference, if the repo uses them;
- selected existing workflow/risk path;
- selected executor/lane and evidence destination;
- current blocker (`NONE` or the repository's typed failure code);
- exact next safe action;
- `CLEANUP_STATE=NOT_NEEDED|PENDING|BLOCKED|COMPLETE` when temporary lanes are
  involved, with exact path/reason/evidence for non-`NOT_NEEDED` states.

The routing role ends after this decision, but the user-facing session should
**continue immediately** when the current agent is still the authorized
executor/integrator and a safe next micro-step exists. Stop only for a real
blocker, approval gate, terminal state, or handoff to another execution surface.

## Parallel lane rules

Parallel work is acceleration, never extra authority.

- Respect the repository's existing WIP limit. If none is defined, do not invent
  one here; use the repository's normal workflow or ask its router/owner.
- A mutable scope has one mutable writer. Independent review stays read-only.
- New lanes require known repo/worktree/branch/HEAD, owner, allowed scope,
  non-overlap and reconciliation destination before mutation.
- Tool/model availability changes routing only. It never grants mutation,
  acceptance, merge, cleanup or claim-transfer authority.
- A failed tool blocks only dependent work; independent safe work may continue.

## Continuation and takeover

A timeout, rate limit or silent model does **not** prove the old writer stopped.
Before a different executor mutates the same bounded scope, prove from runtime
and repository evidence that the previous writer/session and child processes
are inactive, recheck exact Git/dirty state and pending commands, then serialize
transfer through the repository's existing claim/ownership mechanism. The old
executor becomes read-only after transfer until ownership is explicitly returned.

If inactivity or ownership is uncertain: checkpoint unique state and report a
blocked takeover. Never start a second writer "just in case".

## Temporary-lane cleanup

Cleanup is a terminal closeout action, not background housekeeping. Before
removing any worktree/task folder prove:
- accepted/reconciled/abandoned disposition is durable;
- required review/CI/post-main evidence is preserved outside the target;
- no live claim/lease/reviewer/writer/process references the lane;
- exact repo/worktree/branch/HEAD/dirty/untracked state is known;
- no unique unmerged commit or only-copy result/evidence would be lost;
- target is not a protected root/shared/user-data/secret directory.

Any UNKNOWN => `CLEANUP_STATE=BLOCKED`. Never use reset, clean, stash, broad
process kill or force deletion merely to make cleanup pass. For registered Git
worktrees prefer canonical `git worktree remove <exact-path>` without force;
branch deletion is a separate decision.

## Cross-harness discovery

This canonical file is registered in A-Wiki `skills-registry.json`. Generated
agent surfaces expose `skills/awiki` to Kilo/Codex/ZCode/Cline/etc.; do not make
manual copies into `~/.kilo/skills` or per-agent generated directories. If a
harness cannot see this skill, verify registry/surface generation and that
harness's configured skill paths before creating another copy.

## Completion

FastTask is successful when it reduces routing/context overhead while leaving
execution, verification, review, merge, release and cleanup authority where the
repository already defines them. Prefer **REUSE → WRAP → EXTEND**; create a new
authority only through an explicit repository design decision.
