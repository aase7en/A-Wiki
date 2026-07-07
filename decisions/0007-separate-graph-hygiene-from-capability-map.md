---
adr: 0007
title: Separate volatile graph hygiene from the stable capability map
status: Accepted
date: 2026-07-08
tags: [gen-index, capability-map, determinism, ci-gate]
related_journal: []
supersedes: []
superseded_by: []
---

# ADR-0007: Separate volatile graph hygiene from the stable capability map

## Status
**Accepted**

## Context

`scripts/gen-index.py --check` is an integrity gate used by `scripts/agent-preflight.py`. It compares on-disk generated files against a fresh rebuild and fails if any drift. The comparison already strips volatile bits: the `Last updated: YYYY-MM-DD` date is normalized out via `_date_re` before diffing.

For a long time `wiki/context/wiki-capability-map.md` (built by `scripts/wiki/build-capability-map.py`) embedded a **"Knowledge Graph Hygiene"** section with live counters read from `.wiki-graph.json`:

```
| Nodes | 538 |      ← shifts every gen-index run
| Edges | 1713 |
| Broken links | 11 |
| Orphans | 16 |
```

These counters are **non-deterministic across consecutive runs**. Each full `gen-index` run regenerates `.wiki-graph.json`, and the new graph can include newly orphaned nodes (e.g. a freshly emitted overview file that nothing links yet). The capability map then renders those new counters, so the *next* `--check` always sees drift on the capability map even though the catalog (skills/scripts/protocols) did not change.

Observed symptom (real env, 2026-07-07):

```
$ python scripts/gen-index.py        # full rebuild
$ python scripts/gen-index.py --check
::: wiki/context/wiki-capability-map.md is out of date — run scripts/gen-index.py
exit=1
```

The counters had shifted 538→539 nodes, 11→10 broken, 16→17 orphans between the two runs — purely from graph recomputation, not from any content edit. This made the preflight FAIL permanent and the gate meaningless for that file.

## Decision

We will **separate the stable catalog from the volatile live metrics** by moving the Knowledge Graph Hygiene section out of `wiki-capability-map.md` into its own file `wiki/context/graph-hygiene.md`.

Concretely:

1. `build-capability-map.py` no longer renders the graph hygiene section into the catalog markdown. It still *collects* the data in `data["graph_hygiene"]` (so the builder remains the canonical classifier-by-domain).
2. `gen-index.py` gains `render_graph_hygiene(gh)` and `_extract_graph_hygiene()`, and writes `wiki/context/graph-hygiene.md` on every full run.
3. `graph-hygiene.md` is written **outside** the `outputs` dict that `--check` iterates — it is intentionally excluded from the gate, because its content changes every run *by design*.

## Alternatives Considered

### Option A: Strip counters in the `--check` normalizer
Extend `_date_re` to also strip graph-counter rows (`| Nodes | … |`, etc.) before comparison.
- **Pros:** Minimal change, single file.
- **Cons:** Couples the catalog's content to the gate's normalization rules. Fragile — every new volatile line needs a new strip rule. The counters would still live in a "stable" file, which is conceptually wrong.
- **Why not chosen:** Hides the real problem (mixing stable + volatile in one file) behind ever-growing normalization rules.

### Option B: Delete the hygiene section entirely
Remove graph hygiene from the capability map and emit it nowhere, relying on `.wiki-graph.json` + `wiki/context/knowledge-graph.md` (which already exist).
- **Pros:** Simplest. Maximum token reduction.
- **Cons:** Loses the human-readable "broken links by domain / orphan samples" view that the cap-map conveniently co-located with capability context. `knowledge-graph.md` has a different shape.
- **Why not chosen:** Throws away a useful surface. The data is cheap to keep rendering to a dedicated file.

### Option C (chosen): Separate file, excluded from gate
- **Pros:** Stable catalog stays stable (truly checkable). Volatile metrics still get rendered for humans, just not gated. Clean separation of concerns. No special-case normalization rules.
- **Cons:** One more generated file. Consumers that scraped the hygiene section from the capability map (none known) would need to read the new file.
- **Why chosen:** Aligns file volatility with gate semantics. Each file is either fully stable or explicitly excluded — no half-measures.

## Consequences

### Positive
- `gen-index.py --check` is now **idempotent** in the real environment (verified: `exit=0` immediately after a full run).
- `agent-preflight.py`'s `generated wiki context` check stops reporting a permanent FAIL on the capability map.
- The capability map is a true catalog (skills/scripts/protocols/lanes) — its content only changes when the catalog changes.
- Graph hygiene still has a dedicated, readable surface at `wiki/context/graph-hygiene.md`.

### Negative / Trade-offs
- One additional generated file (`graph-hygiene.md`) to regenerate and track.
- Anyone (human or agent) reading the capability map no longer sees graph stats inline; they must consult the separate file or `.wiki-graph.json`.

### Risks
- A future editor might re-embed counters into the capability map "for convenience" and reintroduce the drift. Mitigated by the test `test_capability_map_has_no_graph_section` and this ADR.

## Revisit Conditions
- If `graph-hygiene.md` becomes needed inside the `--check` gate (e.g. we want to assert orphan count never grows), revisit and add a dedicated counter-stripping rule — do NOT re-embed in the capability map.
- If the catalog itself ever needs a volatile sub-section, apply the same pattern (separate file, exclude from gate) rather than special-casing the normalizer.

## References
- Root-caused 2026-07-07 via debug-mantra 4-step (Iron Law #2).
- Tests: `tests/test_gen_index.py::TestGraphHygieneSeparation`, `tests/test_build_capability_map.py::test_graph_hygiene_section_is_separate_file`.
- Related code: `scripts/gen-index.py` (`render_graph_hygiene`, `_extract_graph_hygiene`, `main`), `scripts/wiki/build-capability-map.py` (`format_markdown`, `read_graph_hygiene`).
- Preflight gate consumer: `scripts/agent-preflight.py::check_generated_index`.
