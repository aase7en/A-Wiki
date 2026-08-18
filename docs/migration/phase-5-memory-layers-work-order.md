# A-Wiki vNext — Phase 5 Memory Layers Work Order

**Status:** EXECUTION AUTHORIZED — Phase 5 only  
**Architect/Reviewer:** ChatGPT  
**Executor:** GLM / ZCode  
**Authoritative base `main`:** `10507ceec1c286c53f62e331813692c9e2225e81`  
**Execution branch:** `refactor/awiki-memory-layers`

> This file is the authoritative Phase 5 execution order. Read it together with the kernel and migration docs. Do not start Phase 6 until independent review PASS.

---

## 1. Entry gate

Before implementation:

```bash
git fetch origin
git switch refactor/awiki-memory-layers
git status
git rev-parse origin/main
git merge-base --is-ancestor 10507ceec1c286c53f62e331813692c9e2225e81 HEAD
```

Required:

- `origin/main` must still be `10507ceec1c286c53f62e331813692c9e2225e81`, unless a human explicitly authorizes a newer base.
- working tree clean before implementation.
- branch must descend from the authoritative Phase 4 merge SHA.
- no rebase, force-push, direct main edit, auto-merge, or deploy.

The branch may already contain this work-order commit. That is expected.

---

## 2. Read first — mandatory

Read before editing:

- `AGENTS.md`
- `docs/architecture/A-WIKI-KERNEL.md`
- `docs/migration/awiki-vnext-plan.md`
- `docs/migration/awiki-project-context-architecture-deltas.md`
- `docs/migration/awiki-multi-agent-orchestrator-roadmap.md`
- `config/awiki.yaml`
- `schemas/awiki-project/v1.schema.json`
- `scripts/project/attach.py`
- `scripts/project/status.py`
- `scripts/project/validate.py`

Inspect existing memory/storage primitives before creating anything:

- `scripts/lib/memory_ledger.py`
- `scripts/lib/ports.py`
- `scripts/lib/adapters/memory/`
- `scripts/lib/neural_spine_mcp.py`
- `scripts/mcp-wiki-server.py`
- `scripts/hooks/memory_capture.py`
- `scripts/hooks/session_start.py`
- `.gitignore`
- `scripts/drive_path.py` and existing Drive/data-root helpers
- privacy/security scanners and raw-data protections

Search with `rg` / `git grep` for:

`memory`, `memory_ledger`, `memory_recall`, `memory_remember`, `session-memory`, `AWIKI_DATA_DIR`, `raw`, `drive`, `experiment`, `promote`, `promotion`, `provenance`, `privacy`, `immutable`.

**Rule:** `REUSE → CONSOLIDATE → EXTEND`.

The repo already has `MemoryPort`, `JsonlMemoryAdapter`, `InMemoryMemoryAdapter`, `MemoryLedger`, MCP `memory_recall`, `memory_semantic_recall`, `memory_remember`, local `.tmp` storage, path-sandboxing, secret redaction, SessionStart replay, and `memory_capture`. Preserve these caller contracts unless extension is demonstrably required. Do not build a parallel memory engine.

---

## 3. Phase 5 objective

Implement the minimum safe **A-Wiki Memory Plane**:

- explicit L0–L5 memory semantics;
- Phase-4 project-policy integration;
- project-memory isolation;
- experiment-memory contract;
- deterministic storage/path boundaries;
- manual-with-evidence promotion pipeline;
- privacy and provenance gates;
- read-only status/inspection where appropriate.

This phase is **memory contracts + boundaries + minimum working services**, not autonomous memory, not orchestration, and not a rewrite of search/indexing.

---

## 4. Normative memory layers

### L0 — Working Context

Examples: claims, current task state, focus, scratch, temporary handoff state.

Properties:

- runtime/local/regenerable;
- normally `.tmp` or equivalent existing runtime store;
- never global knowledge;
- never automatically committed or promoted.

### L1 — Session / Operational Memory

Use the existing Memory Ledger as the primary existing substrate unless inspection proves otherwise.

Properties:

- session/cross-session operational continuity;
- searchable/replayable;
- local/private by default;
- agent memory is not automatically evidence or publishable knowledge;
- cannot directly auto-promote to L3.

### L2 — Project Memory

Durable knowledge belonging to exactly one attached project.

Identity must come from `.awiki/project.yaml` (`awiki-project/v1`).

Logical storage may resemble:

```text
projects/<project-id>/memory/
```

Use existing Drive/data-root conventions for private durable storage. Never commit absolute machine paths or private memory contents.

Project A must not silently read/write Project B memory.

### L3 — Global Knowledge

The existing `wiki/` remains the canonical global reusable knowledge plane. Do not create another global knowledge tree.

Only generalized, public-safe, evidence-backed knowledge may enter L3.

Forbidden in L3 includes secrets, project-private details, customer/patient/personal data, raw chats, hidden reasoning, local paths, temporary notes, and uncontrolled raw code excerpts.

### L4 — Raw Evidence

Existing `raw/` model is authoritative.

- read/reference allowed;
- mutation/delete/rewrite/normalize-in-place via memory operations forbidden;
- no direct L4 → L3 promotion;
- promotion may reference raw evidence but must first produce a safe distilled project candidate.

### L5 — Experiment Memory

Minimum logical contract:

```text
experiments/<experiment-id>/
├─ baseline.json
├─ iterations.jsonl
├─ winner.json
└─ report.md
```

Required semantics:

- validated experiment ID;
- project isolation;
- storage outside Git runtime churn;
- `baseline.json` immutable after initialization;
- `iterations.jsonl` append-only;
- `winner.json` references an existing recorded iteration/evidence;
- `report.md` is human-readable output, not replacement for structured evidence.

Do not implement A-Loop v2 here; that belongs to Phase 9.

---

## 5. Phase 4 Project Adapter is authoritative

Memory behavior must consume `.awiki/project.yaml` and enforce:

- `memory.scopes.global`
- `memory.scopes.project`
- `memory.scopes.session`
- `memory.scopes.private`
- `privacy.project_private`
- `trust.private_context`

Examples:

- `project=false` → deny project-memory operation.
- `global=false` → deny global retrieval/promotion as applicable.
- invalid adapter → fail closed.
- private-context restrictions must be honored.

Do not invent a second project-memory policy.

---

## 6. Storage and path safety

All project/private/experiment storage resolution must be containment-safe and cross-platform.

Reject mechanically:

- `../` traversal;
- absolute private-machine paths in stable/durable metadata;
- symlink escapes;
- project-ID crossover;
- unsafe malformed paths.

Never hardcode `C:\...`, `A:\...`, `/Users/...`, `/home/...` into stable config/contracts.

Use logical/env/data-root resolution already present in the repo.

---

## 7. Promotion pipeline — hard contract

Only allowed path:

```text
Project Experience
→ Distill
→ Privacy Check
→ Generalize
→ Evidence Check
→ Global Promotion
```

Default mode: **manual-with-evidence**.

No automatic L0/L1/L4 → L3. No scheduled/background promotion.

### Distill

Create a concise candidate lesson, not a raw transcript dump.

### Privacy Check

Fail closed for secrets, private project/customer/patient/personal data, hidden reasoning, raw agent chatter, absolute/private paths, private external-storage paths, and forbidden raw/source-code payloads.

Reuse existing privacy/security primitives instead of creating an unrelated scanner.

### Generalize

Remove project-specific details while preserving truth. Do not invent evidence.

### Evidence Check

Promotion requires acceptable provenance/evidence, e.g. commit SHA, tests, experiment ID, ADR, source/wiki reference, review finding/verdict, task/handoff reference.

No evidence → no promotion.

### Global Promotion

Prefer preview/dry-run by default. An explicit apply may create/update only intended reviewable L3 candidate/content. It must not push, merge, deploy, or mutate Git refs automatically.

---

## 8. Minimum contracts/interfaces

After inspecting existing repo conventions, implement the smallest coherent set. Possible pieces include:

- stable memory-layer policy/manifest;
- minimal `awiki-memory/v1` or equivalent schema if justified;
- project-aware storage/scope resolver;
- experiment-memory service/helper;
- promotion candidate/provenance validation;
- read-only memory status;
- dry-run-first promotion command/service.

Do not create schema proliferation solely to mirror this work order.

Any stable schema should be strict where appropriate (`additionalProperties: false`), vendor-neutral, and separate durable policy from runtime state.

Global wiki writes must remain behind promotion gates; do not expose L3 as an uncontrolled generic writable MemoryPort.

---

## 9. TDD / required negative tests

Write failing tests first for important invariants. At minimum prove:

1. all L0–L5 are defined with non-overlapping runtime/durable semantics;
2. L0 is not global durable knowledge;
3. L1 cannot auto-promote to L3;
4. project A cannot silently access project B memory;
5. disabled project scope blocks L2 operations;
6. disabled global scope blocks promotion/global use as applicable;
7. invalid Project Adapter fails closed;
8. private project material cannot promote without required privacy/generalization gates;
9. promotion without evidence fails;
10. secret-bearing candidate fails;
11. absolute machine paths in durable provenance fail;
12. traversal and symlink escapes fail;
13. L4 mutation through memory API fails;
14. raw cannot directly promote to L3;
15. experiment baseline cannot be overwritten;
16. experiment iterations are append-only;
17. winner must reference an existing iteration/evidence;
18. malformed experiment records fail;
19. project crossover for experiments fails;
20. dry-run promotion changes no global/durable target;
21. explicit apply changes only intended candidate/content and never Git refs/remotes;
22. existing MemoryLedger secret-redaction compatibility remains green;
23. existing MCP `memory_recall` / `memory_remember` caller contract remains green;
24. Phase 4 project-adapter tests remain green;
25. Windows/POSIX path shapes are covered without committing machine-specific paths.

Use temporary fixture repos/storage; never real private Drive data.

---

## 10. Existing subsystem boundaries

### Hooks

Do not perform Phase 6 hook-engine consolidation. Existing memory hooks may receive only minimal compatibility changes required by Phase 5.

### Code Context / Graft

Project Code Context Plane is separate from Memory Plane. Do not install, initialize, depend on, or implement Graft runtime/adapter/MCP. Graft/code-context caches never promote to global memory.

### Search/indexing

Do not rearchitect FTS/vector search or add a new vector database in Phase 5.

---

## 11. Hard out of scope

Do **not** implement:

- Phase 6 hook consolidation;
- Phase 7 model/provider control plane;
- Phase 8 automated reviewer/eval promotion runtime;
- Phase 9 A-Loop v2;
- Phase 10 Graft / World Intel runtime;
- Agent Registry / Assignment Engine / Orchestrator daemon;
- autonomous agent-to-agent messaging;
- new hosted/cloud memory backend;
- automatic global-memory ingestion;
- background promotion;
- broad repository reorganization;
- mass legacy wiki migration.

Record useful later-phase discoveries in `docs/migration/awiki-vnext-discoveries.md` instead of implementing them.

---

## 12. Validation gates

During implementation run focused Phase 5 tests first.

At completion run relevant canonical gates, including:

```bash
python scripts/check-privacy.py
python scripts/security/scan_repo.py --ci --baseline scripts/security/baseline.txt
python scripts/health/wiki_health.py --json --baseline scripts/health/wiki-health-baseline.txt
python -m pytest tests/ -q --tb=line
```

Also run project-adapter regression tests and MCP/memory compatibility tests.

Do not hide unrelated failures or weaken security tests just to get green.

If generated context becomes stale, regenerate only through the canonical repo mechanism and inspect the diff.

---

## 13. Commit discipline

Use small coherent reversible commits.

Suggested logical slices, adapt to the existing architecture:

1. memory-layer contracts + tests;
2. scope/storage resolver + project isolation;
3. experiment memory + tests;
4. promotion/privacy/evidence gates + tests;
5. thin CLI/MCP integration only if appropriate;
6. normative docs/migration log.

Push normally to `refactor/awiki-memory-layers`.

**DO NOT MERGE.**

---

## 14. Definition of done

Phase 5 is complete only when:

- L0–L5 semantics are explicit and mechanically testable;
- existing MemoryPort/MemoryLedger is reused rather than duplicated;
- Phase 4 identity/policy controls memory scopes;
- project isolation is enforced;
- runtime/private/global boundaries are enforced;
- L4 is immutable from memory write paths;
- L5 baseline/iterations/winner semantics work;
- promotion follows the exact five-gate pipeline;
- promotion is manual-with-evidence and dry-run-first;
- no private data can reach L3 through tested paths;
- no evidence means no promotion;
- provenance contains no private-machine path;
- no push/merge/deploy automation exists;
- existing MCP memory caller contracts remain compatible;
- Phase 4/privacy/security/wiki-health/full tests are green or failures are truthfully reported;
- no Phase 6+ implementation slipped in.

---

## 15. STOP / report

When implementation and validation are complete:

1. push the Phase 5 branch;
2. do not merge;
3. do not start Phase 6;
4. stop at `REVIEW_REQUESTED`.

Report:

```text
PHASE COMPLETE
Phase: 5
Base main SHA: 10507ceec1c286c53f62e331813692c9e2225e81
Branch:
Implementation HEAD:
Commits:

Files added:
Files modified:
Files deleted:

Existing memory components reused:
L0 implementation/mapping:
L1 implementation/mapping:
L2 implementation/mapping:
L3 implementation/mapping:
L4 implementation/mapping:
L5 implementation/mapping:

Project isolation:
Experiment-memory behavior:
Promotion pipeline:
Privacy gate:
Evidence gate:
Raw immutability:
Dry-run behavior:
Phase 4 compatibility:

Tests run:
Passed:
Failed:
Warnings:

Architecture deviations:
Known risks:
Deferred to Phase 6+:

Recommended next step:
REVIEW_REQUESTED
```

**STOP. Do not begin Phase 6 until independent reviewer PASS.**
