# A-Wiki vNext — Phase 6 Hook Engine Consolidation Work Order

**Status:** EXECUTION AUTHORIZED — Phase 6 only  
**Architect/Reviewer:** ChatGPT  
**Executor:** GLM / ZCode  
**Authoritative base `main`:** `51258fac665add6e65e6f4a239fda5d597670f0e`  
**Execution branch:** `refactor/awiki-hook-engine`

> This file is the authoritative Phase 6 execution order. Do not start Phase 7 until independent review PASS and human merge gate.

---

## 1. Entry gate

Before implementation:

```bash
git fetch origin
git switch refactor/awiki-hook-engine
git status
git rev-parse origin/main
git merge-base --is-ancestor 51258fac665add6e65e6f4a239fda5d597670f0e HEAD
```

Required:

- `origin/main` must still be `51258fac665add6e65e6f4a239fda5d597670f0e` unless a human explicitly authorizes a newer base.
- working tree clean before implementation.
- branch must descend from the reviewed Phase 5 merge SHA.
- no rebase, force-push, direct main edit, auto-merge, or deploy.
- the branch may already contain this work-order commit; that is expected.

---

## 2. Read first — mandatory

Read before editing:

- `AGENTS.md`
- `docs/architecture/A-WIKI-KERNEL.md`
- `docs/migration/awiki-vnext-plan.md`
- `docs/migration/awiki-multi-agent-orchestrator-roadmap.md`
- `config/awiki.yaml`
- `scripts/hooks_runner.py`
- all relevant files under `scripts/hooks/`
- `scripts/hooks/memory_capture.py`
- `scripts/hooks/session_start.py`
- `.claude/settings.json`
- `scripts/setup-codex-config.py`
- `scripts/setup-codex-hooks.sh`
- `scripts/codex_notify.py`
- `.github/workflows/ci-core.yml`
- existing hook/lifecycle/provider-wiring tests discovered by repository search
- Phase 4 project-adapter and Phase 5 memory files only as required for compatibility/regression checks

Search with `rg` / `git grep` for at least:

`hooks_runner`, `hook_event_name`, `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, `UserPromptSubmit`, `PreCompact`, `PostCompact`, `hard`, `soft`, `registry`, `exit 2`, `memory_capture`, `codex_notify`, `setup-codex`, `settings.json`.

**Rule:** `REUSE → CONSOLIDATE → EXTEND`.

Do not create a second hook engine if the existing runner can be made canonical.

### Initial inspection note to verify, not blindly assume

At the reviewed base, `scripts/hooks_runner.py` already behaves like a central lifecycle runner and `.claude/settings.json` routes Claude lifecycle hooks through it. The runner also appears to attempt a hook-classification registry import while reviewer inspection did not resolve the expected `scripts/hooks/registry.py` path. Verify the actual repository state first: classification may live elsewhere, be generated, or be missing. Resolve the truth from code/tree/tests before changing architecture.

A missing or malformed classification authority must **never silently downgrade an intended hard gate to soft**.

---

## 3. Phase 6 objective

Roadmap scope is intentionally narrow:

> **Hook engine consolidation — lifecycle runner, unit tests for every hard gate.**

Implement the minimum safe **provider-neutral lifecycle hook engine** by consolidating existing pieces.

Required outcomes:

- one canonical lifecycle dispatch contract;
- one explicit authority for hook registration/classification;
- deterministic hook ordering;
- explicit hard-vs-soft behavior;
- tested timeout/error semantics;
- unit tests for every registered hard gate;
- thin provider wiring/adapters where provider translation is needed;
- equivalent security outcome for the same canonical action across supported provider paths;
- no hook becomes a workflow manager or orchestrator.

**Hooks are police, not manager.**

Phase 6 is lifecycle policy + dispatch + safety + parity. It is not agent orchestration and not model/provider selection.

---

## 4. Canonical lifecycle contract

First inventory the lifecycle events that actually exist in the repo and supported provider wiring. Normalize only what is real.

Current code may include events such as:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `Stop`
- `PreCompact`
- `PostCompact` if actually supported by current wiring/runner

Do not invent lifecycle events solely for symmetry.

The canonical runner must:

1. accept a normalized event payload;
2. resolve the event deterministically;
3. select only hooks registered for that lifecycle event;
4. run hooks in stable deterministic order;
5. apply explicit hard/soft policy;
6. normalize provider-facing result semantics;
7. never depend on filesystem enumeration order or filename accidents for security policy.

Provider-specific adapters may translate provider payload shapes, but canonical policy must live behind the shared lifecycle boundary.

---

## 5. Hook registration / classification authority

Create or consolidate the **smallest explicit authority** for executable hooks and their policy.

At minimum each registered hook must have enough durable information to determine:

- stable hook id/name;
- lifecycle event(s);
- executable target;
- classification: `hard` or `soft`/observe-only;
- deterministic order/priority if needed;
- timeout policy if different from canonical default;
- whether contextual stdout is allowed.

Requirements:

- no duplicate hook IDs;
- no duplicate/conflicting registration;
- unknown/unregistered scripts do not become active hard gates by filename;
- filename prefixes may be compatibility/discovery hints, but must not be the sole security authority;
- classification lookup failure is deterministic and tested;
- an intended hard gate cannot silently become soft because a registry/module failed to import;
- registry/manifest and executable hook set must have a mechanical consistency test.

Prefer consolidating an existing registry/metadata seam if one exists after inspection. Do not proliferate config formats without justification.

---

## 6. Hard vs soft semantics

Do **not** make every hook fail-closed.

### Hard hooks

Hard hooks enforce safety/policy boundaries.

Canonical behavior must define and test:

- pass → provider-facing non-blocking result;
- policy violation → block with stable reason;
- timeout / exception / malformed internal result → safe deterministic behavior appropriate for a hard gate;
- unexpected child exit codes cannot leak unpredictably to providers;
- missing classification/executable cannot silently weaken a hard gate.

For provider-facing CLI semantics, preserve the established contract where applicable:

- `0` = pass / non-blocking
- `2` = block

Do not expose arbitrary child process exit codes as policy outcomes.

### Soft / observe-only hooks

Soft hooks must never block the user's action.

- a soft hook returning `2` must be normalized to non-blocking;
- timeout/exception remains non-blocking, while diagnostics may be recorded safely;
- observer/memory hooks must not become hard accidentally;
- diagnostics must not leak secrets/private machine paths.

Classification, not arbitrary filename behavior, determines this.

---

## 7. Provider-neutrality and parity

Claude already has central lifecycle wiring. Codex has its own setup/notify/config path. Inspect all current provider wiring before editing.

Goal:

```text
provider event
    ↓
thin provider normalization
    ↓
canonical A-Wiki lifecycle runner
    ↓
registered hook policy
    ↓
normalized PASS / BLOCK / context result
```

Requirements:

- same canonical action must receive the same hard-gate decision regardless of supported provider adapter;
- provider adapters must not bypass canonical hard gates;
- provider-specific setup remains thin;
- generated configs remain deterministic/idempotent;
- do not build a provider registry, model selector, fallback engine, quota manager, or health scorer here — those belong to Phase 7.

If a provider cannot support a lifecycle feature equivalently, report the limitation truthfully rather than simulating parity.

---

## 8. Contextual stdout / hook output

Inventory which existing lifecycle events intentionally return context to the agent/provider.

Define a canonical output contract so that:

- only explicitly allowed event/hook combinations may emit contextual stdout;
- hard-gate block reasons are concise and deterministic;
- hook diagnostics do not become hidden prompts or uncontrolled context injection;
- secrets, credentials, private absolute paths, patient/customer/private data, or hidden reasoning are not emitted;
- unexpected stdout from non-context hooks is handled deterministically.

Do not turn hook output into agent-to-agent messaging.

---

## 9. Memory compatibility — Phase 5 boundary

Phase 5 is already merged and authoritative.

Preserve:

- `MemoryLedger` caller behavior;
- L0–L5 boundaries;
- project isolation;
- L2→L3 promotion gates;
- raw immutability;
- read-only/private-path-safe status.

`memory_capture.py` remains operational/observe-only memory behavior unless existing policy proves otherwise.

Hard rules:

- hook capture must not directly promote to L3;
- no automatic global memory ingestion;
- no hidden chain-of-thought persistence;
- hook failures must not bypass Phase 5 privacy/storage boundaries;
- do not implement A-Loop v2.

Minimal compatibility changes to existing hooks are allowed only when required by the canonical runner contract.

---

## 10. Project Adapter compatibility — Phase 4 boundary

Where a hook is project-aware, `.awiki/project.yaml` remains authoritative.

Do not create a second project policy.

- invalid adapter → fail according to the hook's explicit security classification/policy;
- project-private context must not be exposed by diagnostics/output;
- cross-project access remains forbidden;
- status/read-only paths must not gain mutation side effects.

Phase 6 must keep the Phase 4 adapter suite green.

---

## 11. TDD — required negative/invariant tests

Write failing tests first for the consolidated contract.

At minimum prove the following where applicable to actual repo hooks:

1. lifecycle event mapping is deterministic;
2. provider normalization maps equivalent provider actions to the same canonical event/action;
3. unknown lifecycle event has a deterministic non-crashing result;
4. malformed provider payload is deterministic and does not traceback uncontrolled;
5. every registered hard hook has at least one test proving a real block path;
6. hard hook PASS returns canonical non-blocking result;
7. hard hook policy violation returns canonical block (`2`) with stable reason;
8. hard hook timeout follows explicit hard-hook safety policy;
9. hard hook exception follows explicit hard-hook safety policy;
10. soft hook cannot block even if child returns `2`;
11. soft hook timeout is non-blocking;
12. soft hook exception is non-blocking;
13. unexpected child exit codes are normalized;
14. only `0` / `2` policy outcomes reach provider-facing hook surfaces where that exit contract applies;
15. registration/classification authority matches executable hooks;
16. missing/malformed classification authority cannot silently downgrade an intended hard gate;
17. duplicate hook registration/classification fails validation;
18. hook order is stable independent of filesystem enumeration order;
19. arbitrary new filename does not silently become a security gate;
20. contextual stdout occurs only for explicitly allowed events/hooks;
21. unexpected stdout is handled deterministically;
22. emitted context/block diagnostics contain no secret/private absolute path;
23. equivalent canonical action gets the same hard-gate outcome across supported provider paths;
24. no provider-specific bypass path around hard gates;
25. runner cannot push, merge, deploy, or mutate Git refs/remotes;
26. `memory_capture` remains non-blocking if classified observe-only;
27. memory hook behavior remains L1/operational and cannot directly write/promote L3;
28. SessionStart/read-only behavior does not unexpectedly create unsafe/private storage;
29. project-aware hard gates consume Phase 4 adapter authority where applicable;
30. Phase 5 memory regression tests remain green;
31. Windows/POSIX invocation/path shapes are covered without hardcoded private paths;
32. missing executable/interpreter has stable hard-vs-soft behavior;
33. CI hook smoke exercises the canonical lifecycle runner rather than a provider-specific bypass.

Do not force tests for nonexistent lifecycle features. If an item is not applicable, document why with repository evidence.

Use temp fixtures/synthetic payloads only; never real private Drive/business/hospital data.

---

## 12. CI / configuration consolidation

Inspect existing CI and provider setup before modifying.

Desired end state:

- canonical runner has focused unit tests;
- every hard gate is mechanically covered;
- existing CI hard-gate smoke remains truthful or is updated to the canonical surface;
- provider config generators use the shared lifecycle contract where supported;
- generated config remains deterministic;
- no new CI workflow unless existing workflow cannot safely host the checks.

Do not weaken a security check to make CI green.

---

## 13. Hard out of scope

Do **not** implement:

- Phase 7 model/provider control plane;
- provider/model selection, fallback, quota, benchmark, health scoring, or routing;
- Phase 8 automated reviewer/eval promotion runtime;
- Phase 9 A-Loop v2;
- Phase 10 Graft / World Intel runtime;
- Phase 12+ Agent Registry / Assignment Engine / Orchestrator service;
- autonomous agent-to-agent messaging;
- background scheduler/daemon/task queue;
- workflow ownership inside hooks;
- automatic Git push/merge/deploy;
- memory rewrite or automatic L3 promotion;
- new vector database/search architecture;
- UI/dashboard;
- broad repository reorganization;
- new hosted/cloud dependency.

Record later-phase discoveries instead of implementing them.

---

## 14. Validation gates

Run focused Phase 6 hook tests first during development.

At completion run relevant canonical gates, including:

```bash
python scripts/check-privacy.py
python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt
python scripts/health/wiki_health.py --json --baseline scripts/health/wiki-health-baseline.txt
python -m pytest tests/ -q --tb=line
```

Also run:

- hook runner focused tests;
- every hard-gate test;
- current CI hook smoke equivalent locally where practical;
- provider config-generation/idempotency tests affected by the change;
- Phase 4 project-adapter regression suite;
- Phase 5 memory regression suite;
- MCP/memory compatibility tests where hook changes touch those seams.

Do not hide unrelated failures or alter baselines merely to make the branch green.

---

## 15. Commit discipline

Use small coherent reversible commits.

Suggested logical slices — adapt after inspecting actual repo architecture:

1. lifecycle + registration/classification contract and red tests;
2. canonical runner consolidation;
3. hard/soft timeout/error/output semantics + tests;
4. thin provider wiring/config parity + tests;
5. CI hard-gate coverage + migration documentation.

Push normally to:

`refactor/awiki-hook-engine`

**DO NOT MERGE.**

---

## 16. Definition of done

Phase 6 is complete only when:

- one canonical lifecycle runner is authoritative;
- no parallel lifecycle policy remains without explicit justification;
- registration/classification is explicit and mechanically validated;
- every hard gate has a real blocking unit test;
- hard/soft timeout/error semantics are explicit and tested;
- soft hooks cannot block;
- hard gates cannot silently downgrade to soft;
- deterministic order/output/result contracts are tested;
- provider adapters are thin and cannot bypass canonical hard gates;
- supported provider paths produce equivalent hard-gate decisions for equivalent canonical actions;
- contextual output is explicitly controlled and privacy-safe;
- Phase 4 project policy remains authoritative;
- Phase 5 memory boundaries remain intact;
- hooks do not push/merge/deploy or become orchestrators;
- privacy/security/wiki-health/full tests are green or failures are truthfully reported;
- no Phase 7+ implementation slipped in.

---

## 17. STOP / report

When implementation and validation are complete:

1. push the Phase 6 branch;
2. do not merge;
3. do not start Phase 7;
4. stop at `REVIEW_REQUESTED`.

Report:

```text
PHASE COMPLETE
Phase: 6
Base main SHA: 51258fac665add6e65e6f4a239fda5d597670f0e
Branch:
Implementation HEAD:
Commits:

Files added:
Files modified:
Files deleted:

Existing hook components reused:
Canonical lifecycle entrypoint:
Lifecycle events/mapping:
Registry/classification authority:
Hard-gate behavior:
Soft/observe behavior:
Timeout/error semantics:
Provider parity:
Context/output behavior:
Memory-hook compatibility:
Phase 4 compatibility:
Phase 5 compatibility:

Tests run:
Passed:
Failed:
Warnings:

Architecture deviations:
Known risks:
Deferred to Phase 7+:

Recommended next step:
REVIEW_REQUESTED
```

**STOP. Do not begin Phase 7 until independent reviewer PASS.**
