# Vector Databases for Semantic Search

> **Type:** article
> **Domain:** AI Tools
> **Ref:** https://www.pinecone.io/learn/vector-database/
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** vector-db, embedding, ANN, similarity-search, RAG

## Abstract

Vector databases store and query high-dimensional embeddings produced by neural networks, enabling semantic similarity search at scale. Core indexing algorithms include IVF (Inverted File Index), HNSW (Hierarchical Navigable Small World graphs), and PQ (Product Quantization). Leading implementations include Pinecone (managed), Chroma (open-source), Qdrant (Rust-based), Weaviate (hybrid vector+scalar), Milvus (distributed), and pgvector (PostgreSQL extension). Key metrics are recall@k, queries-per-second (QPS), and indexing time. Modern vector databases support hybrid search (vector + metadata filtering + full-text), multi-vector indexing, and disk-based ANN for billion-scale datasets.

## Key Concepts

- **HNSW** — Hierarchical Navigable Small World, state-of-the-art ANN index (high recall, moderate memory)
- **IVF** — Inverted File Index partitions space into Voronoi cells for approximate search
- **Recall@k** — Fraction of true nearest neighbors returned in top-k results
- **Hybrid Search** — Combining vector similarity with keyword (BM25) and metadata filtering
- **DiskANN** — Disk-based ANN algorithm for billion-scale datasets on commodity hardware

## Related Links

- https://www.pinecone.io/learn/vector-database/
- https://github.com/erikbern/ann-benchmarks

---
*Auto-created by `scripts/ingest-source.py` — review abstract and concepts for accuracy.*