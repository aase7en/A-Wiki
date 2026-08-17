# A-Wiki × NanoNets Graft — Integration Plan

> Status: architecture/pilot plan only. No implementation authorization.
> Classification: **MODULE + PATTERN**
> Target roadmap: Phase 10 external modules, with interfaces prepared in Phases 3–4 and consumption by Phases 12–16.
> Upstream: `NanoNets/Graft` (`@nanonets/graft`, MIT, Node >=20).

## 1. Executive decision

Do **not** merge or vendor Graft into the A-Wiki kernel.

Use Graft as an optional **Project Code Context Plane** behind an A-Wiki adapter/gateway. The Graft graph remains a project-local, regenerable, gitignored cache. A-Wiki remains the canonical control tower for memory, governance, routing, review state, privacy, skills, and reusable knowledge.

Canonical separation:

```text
                    A-WIKI TEAM OS
                          |
        +-----------------+------------------+
        |                 |                  |
   MEMORY PLANE      CONTROL PLANE      PROJECT CONTEXT
   wiki/global       task/review/       live code context
   project memory    claims/router          |
                                            v
                                   Context Provider Gateway
                                     /             \
                                  Graft          GitNexus
                                  MODULE         optional
                                     |
                                     v
                              implementation repo
                          tree-sitter / symbols / calls
                          local gitignored cache
```

The important boundary is:

```text
A-Wiki Knowledge Graph != Project Code Graph
```

The former stores durable reusable knowledge. The latter is an ephemeral/rebuildable view of the current working tree.

## 2. What Graft materially adds

Graft provides a deterministic structural context layer that A-Wiki does not currently own at the same fidelity:

- symbol-level code graph;
- call/reference/import/implements/extends traversal;
- transitive blast-radius queries;
- signatures-only file API;
- repo map/hub orientation;
- graph-aware grep ranked by coupling;
- exact file:line/source excerpts;
- pre-query freshness against the current working tree;
- worktree seeding and refresh logic;
- multi-repo/workspace federation;
- optional LLM enrichment while keeping the structural path offline/$0;
- host wiring for multiple coding-agent ecosystems;
- MCP tools exposing the context graph.

These capabilities reduce repeated repository rediscovery by agents without requiring A-Wiki to ingest source code into global memory.

## 3. Upstream properties relevant to A-Wiki

As inspected from the current upstream:

- package: `@nanonets/graft`;
- license: MIT;
- runtime: Node.js >=20;
- deterministic structural graph uses tree-sitter and can operate without a model/key;
- full-fidelity extractors cover TypeScript/JavaScript, Python, Go, Java, with broader tree-sitter language support and optional LSP-resolved edges;
- MCP surface includes `graft_find_code`, `graft_file_api`, `graft_check_freshness`, `graft_trace_calls`, `graft_find_all`, and `graft_repo_map`;
- every normal retrieval tool invokes a freshness gate before answering;
- refresh is structural only, lock-protected, fail-soft, and designed not to call an LLM;
- the `graft/` directory is explicitly a local regenerable cache and is gitignored;
- host registry/wiring supports AGENTS-style hosts, Cursor, Gemini CLI, Antigravity, Copilot, Kiro, Windsurf, AdaL, plus Claude-specific integration;
- current CI gates both Ubuntu and Windows and upstream also carries CodeQL/Scorecard workflows.

A-Wiki must treat upstream benchmark claims as upstream evidence, not as proof that the same gains will occur on A-Wiki projects. Promotion requires A-Wiki-owned evaluation.

## 4. Why this must not become A-Wiki core

### Dependency footprint

Graft adds a substantial Node/tree-sitter dependency surface and multiple language grammars. The A-Wiki kernel should remain usable without Node 20 or Graft installed.

### Domain boundary

Graft solves **live repository code understanding**. A-Wiki solves **persistent cross-project memory, policy, orchestration, knowledge, and governance**. Combining their storage/state would make cache lifecycle and knowledge lifecycle indistinguishable.

### Existing overlap

A-Wiki already has:

- wiki FTS5 + semantic search;
- wiki knowledge graph;
- project adapters planned;
- MCP server;
- optional GitNexus/Graphify/GBrain integrations;
- task claims and cross-agent workflow primitives.

Therefore Graft must enter through an interface and compete against existing context providers rather than bypass them.

### Replaceability

If Graft later becomes unmaintained or another provider wins A-Wiki's benchmark, A-Wiki should replace the adapter, not redesign its kernel.

## 5. New capability: Project Code Context Plane

Introduce a vendor-neutral abstraction:

```text
ProjectCodeContextProvider
```

Conceptual operations:

```text
code_context.status(project)
code_context.orient(project, budget)
code_context.find(project, query, scope?)
code_context.file_api(project, file)
code_context.trace(project, symbol, direction, depth)
code_context.search(project, pattern, scope?)
code_context.freshness(project)
```

Provider mapping for Graft:

```text
orient     -> graft_repo_map
find       -> graft_find_code
file_api   -> graft_file_api
trace      -> graft_trace_calls
search     -> graft_find_all
freshness  -> graft_check_freshness
```

A-Wiki skills/protocols should call the A-Wiki abstraction. Vendor-native tool names may remain available for expert/debug use, but must not become the durable workflow contract.

## 6. Project adapter extension

Future `.awiki/project.yaml` may declare code-context policy without hardcoding workflow logic to Graft:

```yaml
schema: awiki-project/v1
id: example-project

code_context:
  enabled: true
  mode: auto
  preferred:
    - graft
    - gitnexus
  required_capabilities:
    - symbol-search
    - call-graph
    - blast-radius
  cache_policy: local-regenerable
  global_memory_promotion: false
```

`AUTO` chooses the smallest healthy provider set for the task.

A project may also disable code-context providers entirely.

## 7. Storage contract

Hard rules:

```text
Graft cache/project code graph
  -> project-local
  -> gitignored
  -> regenerable
  -> runtime evidence only

A-Wiki project memory
  -> durable project decisions/outcomes

A-Wiki global wiki
  -> generalized reusable knowledge only
```

Never automatically copy:

- `graft/.graph/*`;
- generated symbol cards;
- source excerpts;
- raw project implementation details;
- private source code;

into A-Wiki global/public knowledge.

A reusable lesson discovered via a code graph must pass the normal promotion pipeline:

```text
Project evidence
 -> distill
 -> privacy check
 -> generalize
 -> evidence check
 -> global promotion
```

## 8. Privacy and trust boundary

Before enabling Graft for a project, the project adapter must know whether source code is public, private, restricted, or contains regulated data.

Default policy:

- structural/offline graph is permitted when local project access is already permitted;
- LLM enrichment is **off by default**;
- `--deep`/provider-backed enrichment requires explicit project policy and approved provider trust level;
- no project source excerpts go into GitHub review state unless already safe for that repository;
- secrets/private files remain governed by A-Wiki privacy gates and project ignore rules;
- external provider keys remain outside Git.

## 9. Freshness pattern worth absorbing

Even if Graft is not selected as the provider, A-Wiki should absorb this architectural pattern:

```text
QUERY
  -> cheap freshness probe
  -> if clean: answer
  -> if drift: refresh only required structural state
  -> answer
```

Key properties to preserve:

- freshness is checked on the query path;
- no hidden paid/network operation in automatic refresh;
- lock to prevent refresh stampedes;
- re-check after waiting for another refresh;
- fail-soft degradation;
- worktree-aware cache seeding;
- cache invalidation after refresh;
- refresh only what the query consumes.

This pattern is valuable for A-Wiki's own indexes, model/intel caches, and future project-context providers.

## 10. Host-wiring pattern worth absorbing

Graft's host registry demonstrates a clean pattern:

```text
canonical capability/instructions
   -> host registry
   -> detect host
   -> plan writes
   -> dry-run
   -> idempotent owned/section update
```

A-Wiki should reuse this concept for generated cross-agent surfaces rather than independently hand-maintaining Claude/Codex/Gemini/ZCode/Kilo/Cursor/Windsurf configuration.

Required A-Wiki differences:

- A-Wiki's canonical source remains its own AGENTS/registries/protocols;
- vendor-specific files are generated/validated surfaces;
- all global/machine-wide writes are explicit and previewable;
- no external module may silently own A-Wiki's canonical instruction files;
- A-Wiki's hook/security policy remains authoritative.

## 11. Integration with Multi-Agent Orchestrator

The orchestrator can use project code context during planning, assignment, and review.

### Before assignment

```text
repo_map
 -> detect subsystem boundaries
 -> decompose task into non-overlapping claims/worktrees
```

### Before refactor

```text
trace_calls(depth=all)
 -> blast radius
 -> required files/tests
 -> claim scope
```

### Reviewer

```text
changed symbol
 -> incoming/outgoing dependencies
 -> verify siblings/callers were considered
```

### Agent handoff

Instead of carrying a large transcript:

```yaml
handoff:
  changed_symbols:
    - ProviderClient.call
  context_queries:
    - trace incoming depth=2
    - file_api scripts/lib/providers/client.py
```

The receiving agent reconstructs fresh code context from the project rather than trusting stale copied prose.

## 12. Relationship to GitNexus and other code-graph tools

Do not activate Graft and GitNexus indiscriminately for every task.

Create a context-provider capability matrix and benchmark both against the same A-Wiki task corpus.

Example dimensions:

| Capability | Graft | GitNexus/other |
|---|---:|---:|
| local structural graph | evaluate | evaluate |
| working-tree freshness | evaluate | evaluate |
| exact symbol spans | evaluate | evaluate |
| transitive blast radius | evaluate | evaluate |
| repo orientation | evaluate | evaluate |
| worktree behavior | evaluate | evaluate |
| Windows parity | evaluate | evaluate |
| language coverage | evaluate | evaluate |
| token/tool reduction | benchmark | benchmark |
| latency | benchmark | benchmark |
| install/dependency burden | benchmark | benchmark |
| privacy/offline mode | verify | verify |

Routing rule:

```text
no provider needed -> use native file/grep tools
one provider clearly sufficient -> enable one
provider degraded/missing capability -> fallback/alternate
never load all providers just because they exist
```

## 13. Pilot phases

### G0 — Contract only

During Phases 3–4:

- define `ProjectCodeContextProvider` capability vocabulary;
- reserve project-adapter fields;
- no Graft dependency;
- no Graft MCP in default config.

### G1 — Controlled local pilot

After Project Adapter and hard safety are stable:

- select 2–3 representative code repos;
- install Graft locally, not in A-Wiki kernel dependencies;
- run structural mode only first;
- verify generated cache stays gitignored;
- test Windows + Linux/worktree behavior;
- record install/runtime overhead;
- no automatic wiring to every agent.

### G2 — A-Wiki adapter

Implement thin adapter exposing the vendor-neutral code-context operations.

Requirements:

- health/freshness reporting;
- graceful `provider unavailable` response;
- no direct global-memory writes;
- no automatic LLM/deep enrichment;
- explicit local cache ownership;
- compatibility with isolated worktrees.

### G3 — Comparative benchmark

Benchmark native tools vs Graft vs GitNexus/other provider using repeatable tasks:

- unfamiliar repo orientation;
- find implementation of behavior;
- multi-file refactor blast radius;
- reviewer dependency check;
- edited-working-tree freshness;
- worktree switch;
- Windows path handling.

Measure:

- task correctness;
- missed affected files;
- tool calls;
- tokens/context size;
- wall-clock latency;
- CPU/build overhead;
- installation burden;
- failure/degraded behavior.

### G4 — Promotion decision

Possible outcomes:

```text
PROMOTE_DEFAULT_MODULE
KEEP_OPTIONAL
PATTERN_ONLY
REJECT
```

Promotion is policy/config only after evidence. Do not fork/vendor upstream by default.

## 14. Proposed future integration registry entry

When `config/integrations.yaml` is introduced, Graft could be represented as:

```yaml
integrations:
  graft:
    classification: module
    domain: project-code-context
    default: false
    lazy: true
    runtime: local
    requires:
      - node>=20
    provides:
      - symbol-search
      - call-graph
      - blast-radius
      - repo-map
      - code-search
      - freshness
    storage:
      type: local-regenerable-cache
      commit: false
    network:
      structural: false
      enrichment: optional
    trust:
      deep_enrichment: project-policy
```

## 15. Anti-goals

Do not:

- copy Graft source wholesale into A-Wiki;
- commit Graft's graph/cache into A-Wiki or project Git history;
- merge project code graph with the A-Wiki global knowledge graph;
- enable paid/deep enrichment automatically;
- preload Graft MCP for non-code tasks;
- make A-Wiki require Node 20 solely because Graft does;
- replace A-Wiki's own MCP with Graft MCP;
- let Graft's init overwrite canonical A-Wiki agent instructions/hooks without review;
- claim upstream benchmark improvements as A-Wiki results;
- select Graft over GitNexus without comparative evidence.

## 16. Acceptance criteria

The integration is successful when:

1. An agent opening an attached implementation repo can obtain a fresh, low-cost structural map without polluting A-Wiki global memory.
2. Multi-file refactors can mechanically obtain blast-radius evidence before edits.
3. Two different agents can reconstruct the same project context from the same working tree without copying a long chat transcript.
4. Graft can be absent/uninstalled and A-Wiki still functions normally.
5. Runtime graph/cache never churns Git.
6. Private project code does not cross its trust boundary.
7. The context provider can be swapped for GitNexus/future providers without changing task/review/handoff protocols.
8. A-Wiki-owned benchmarks demonstrate measurable value before Graft becomes default for any project class.

## 17. Classification result

```text
CORE       -> NO
MODULE     -> YES
PATTERN    -> YES
REFERENCE  -> YES (upstream implementation/benchmark evidence)
REJECT     -> NO
```

Recommended disposition:

> **Adopt Graft first as an optional Project Code Context module, absorb its freshness and host-registry patterns into A-Wiki architecture, and require an A-Wiki benchmark before any default promotion.**
