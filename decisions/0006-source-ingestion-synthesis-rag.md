---
adr: 0006
title: Source Ingestion, Cross-Domain Synthesis, and GraphRAG Pipeline
status: Accepted
date: 2026-05-25
tags: [pipeline, ingestion, synthesis, RAG, graph, FAISS]
related_journal: []
supersedes: []
superseded_by: []
---

# ADR-0006: Source Ingestion, Cross-Domain Synthesis, and GraphRAG Pipeline

## Status

**Accepted**

## Context

A-Wiki needs a structured pipeline for:

1. **Source ingestion** — Adding new knowledge entries (articles, docs, research) in a consistent format with provenance metadata (domain, type, quality, tags).
2. **Cross-domain synthesis** — Connecting related concepts across domains (e.g., IoT + Environmental Health, AI Tools + Pharmacy) to generate higher-level insights.
3. **Semantic search (GraphRAG)** — Enabling natural-language queries over both raw sources and synthesized knowledge, with filters by domain, tags, and quality.

Previously, knowledge was collected ad-hoc with no standard frontmatter, no automated synthesis, and no query capability.

## Decision

We implement a three-stage pipeline, each as a standalone Python script under `scripts/wiki/`:

| Stage | Script | Purpose |
|-------|--------|---------|
| Ingest | `ingest-source.py` | Parse and commit source entries from URLs or local files into `wiki/sources/{domain}/` |
| Synthesize | `synthesize.py` | Read `wiki/sources/`, generate domain-level syntheses + cross-domain bridges into `wiki/synthesis/` |
| Query | `query-rag.py` | Build a FAISS index (sentence-transformers embeddings), support semantic + filter search |
| Auto-pipeline | `auto-synthesize.py` | Watch mode: detect new/changed sources, auto-trigger synthesis + index rebuild |

### Key Design Decisions

1. **Flat Markdown frontmatter** — Sources use `> **Key:** Value` syntax in blockquotes (not YAML frontmatter) to remain readable in raw Markdown and compatible with Obsidian/Notion exports.
2. **Explicit domain directories** — `wiki/sources/{domain}/` for domain isolation; cross-domain bridges are defined declaratively in `CROSS_DOMAIN_BRIDGES`.
3. **Concept extraction** — `**Concept** — description` patterns are parsed automatically for concept co-occurrence analysis and synthesis pairing.
4. **FAISS + sentence-transformers** — `all-MiniLM-L6-v2` (384-dim) for fast local embeddings; FAISS `IndexFlatIP` for cosine similarity search.
5. **Stateful auto-pipeline** — `.auto-synthesize-state.json` tracks file hashes, synthesis timestamps, and change detection to avoid redundant regeneration.

## Alternatives Considered

### Option A: Single monolithic script
- **Pros:** Simpler to maintain.
- **Cons:** Harder to debug, test, and run stages independently. Violates Unix philosophy.
- **Why not chosen:** Separation of concerns allows each stage to be used independently (e.g., query without rebuilding).

### Option B: Vector database (Pinecone, Weaviate)
- **Pros:** Managed scaling, hybrid search, metadata filtering built-in.
- **Cons:** Requires network, API keys, ongoing cost. FAISS is free, local, and sufficient for <100K documents.
- **Why not chosen:** Local-first aligns with A-Wiki's self-contained, offline-capable architecture.

### Option C: Cross-domain synthesis via LLM API
- **Pros:** Higher quality narrative synthesis.
- **Cons:** Cost, latency, non-deterministic, requires API key. Current rule-based approach is deterministic and auditable.
- **Why not chosen (yet):** Future enhancement — `synthesize.py` structure allows plugging in an LLM generator.

## Consequences

### Positive
- Standardized source format with provenance (quality, source URL, ingest date).
- Automated cross-domain insight generation — 14 syntheses from 10 sources across 5 domains.
- Semantic search works offline with zero external dependencies.
- Change detection prevents redundant work; `--watch` mode enables continuous pipeline.

### Negative / Trade-offs
- Rule-based synthesis lacks narrative depth vs. LLM-generated text.
- FAISS index is local-only — not shareable across machines without manual rebuild.
- Concept extraction is regex-based and may miss non-standard formatting.

### Risks
- `sentence-transformers` and `faiss-cpu` are optional runtime deps — must be documented for users who want RAG search.
- Large source volumes (>10K) may require migrating from `IndexFlatIP` to `IndexIVFFlat` for performance.

## Revisit Conditions

- If source volume exceeds 10,000 entries → revisit FAISS index strategy (IVF or HNSW).
- If LLM API cost decreases significantly → reconsider LLM-based synthesis generation.
- If Obsidian or Notion support changes Markdown frontmatter → update parser in all three scripts.

## References

- `scripts/wiki/ingest-source.py`
- `scripts/wiki/synthesize.py`
- `scripts/wiki/query-rag.py`
- `scripts/wiki/auto-synthesize.py`
- `wiki/sources/{domain}/*.md` — source entries
- `wiki/synthesis/*.md` — generated syntheses
- ADR-0004: Autosynthesis Pipeline Design (superseded by this ADR)