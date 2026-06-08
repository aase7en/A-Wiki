---
type: concept
tags: [rag, retrieval-augmented-generation, embedding, vector-database, chunking, hybrid-search, hyde, raptor]
sources: [ai-engineering-llm]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# RAG Architecture

Retrieval-Augmented Generation — ระบบเชื่อมต่อ LLM กับ external knowledge base
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` Phase 11 (MIT)

---

## 1. RAG Pipeline (4 ขั้นตอน)

```
Document → [Chunk] → [Embed] → [Store] → Vector DB
                                              ↓
Query → [Embed] → [Retrieve k chunks] → [Generate] → Answer
```

| ขั้นตอน | Input | Output | Key decision |
|---|---|---|---|
| **Chunk** | Raw document | Text segments | Size + overlap strategy |
| **Embed** | Text segments | Float vectors | Embedding model choice |
| **Retrieve** | Query vector | Top-k chunks | k, similarity metric |
| **Generate** | Query + chunks | Answer | LLM + prompt template |

---

## 2. Chunking

### Sweet Spot
- **256-512 tokens** per chunk (empirically validated)
- **50 tokens** overlap between adjacent chunks (prevents context loss at boundaries)

### Strategies
| Strategy | Best for |
|---|---|
| Fixed-size | Simple documents, quick setup |
| Semantic | Coherent topics; splits at meaning boundaries |
| Recursive | Nested structure (headers → paragraphs → sentences) |
| Document-aware | Tables, code blocks = own chunks (preserve structure) |

---

## 3. Embedding Models (2026)

| Model | Dims | Context | Notes |
|---|---|---|---|
| **text-embedding-3-small** | 1536 | 8k | OpenAI; cost-effective default |
| **Gemini Embedding 2** | 768-3072 | 8k | Multimodal support |
| **voyage-4** | 1024 | 32k | High recall, long context |
| **BGE-M3** | 1024 | 8k | Open-source SOTA; free |
| **Qwen3-Embedding** | 1024-4096 | 32k | Multilingual SOTA 2025; good for Thai |

**Selection**: BGE-M3 สำหรับ self-hosted; text-embedding-3-small สำหรับ OpenAI stack; Qwen3 สำหรับ multilingual

---

## 4. Vector Databases

| DB | Type | Best for |
|---|---|---|
| **FAISS** | Library (in-memory) | Dev/research, single-machine, no server |
| **Chroma** | Embedded | Local dev, simple persistence |
| **Pinecone** | Managed cloud | Production, serverless, zero ops |
| **pgvector** | PostgreSQL extension | Existing Postgres stack, SQL+vector |
| **Qdrant** | Self-hosted / cloud | Production, rich filtering, HNSW |

**Selection rule**: pgvector ถ้ามี Postgres แล้ว; Qdrant ถ้าต้องการ filtering ซับซ้อน; Pinecone ถ้า fully managed

---

## 5. Retrieval

### Default Settings
- **k=5-10** retrieved chunks (ปรับตาม context window และ answer complexity)
- **Cosine similarity** สำหรับ normalized vectors; dot product สำหรับ unnormalized

### Hybrid Search (แนะนำสำหรับ production)
```
Dense retrieval (semantic vector search)
  + Sparse retrieval (BM25 keyword)
  → Reciprocal Rank Fusion (RRF)
  → Better recall than either alone
```

### Reranking
Cross-encoder reranker หลัง initial retrieval:
- Initial retrieval: top-50 (fast, bi-encoder)
- Rerank: cross-encoder scores each pair → top-5 (slow but precise)
- Result: higher precision with manageable latency

---

## 6. RAG vs Fine-tuning

| Aspect | RAG | Fine-tuning |
|---|---|---|
| **Knowledge update** | Real-time (update index) | Retrain required |
| **Factual accuracy** | High (grounded in source) | Can hallucinate |
| **Inference cost** | Low + retrieval overhead | Standard inference cost |
| **Training cost** | None | High (compute + data) |
| **Best for** | Factual QA, knowledge base | Style, format, domain behavior |

**Rule**: RAG ก่อนเสมอสำหรับ factual knowledge. Fine-tune สำหรับ behavior/style/format เท่านั้น.

---

## 7. Advanced RAG Patterns

| Pattern | Idea | When to use |
|---|---|---|
| **HyDE** | Embed hypothetical answer, retrieve against it | Sparse query ที่ exact match ไม่ work |
| **RAPTOR** | Recursive summarization tree | Very long documents (books, reports) |
| **Contextual Retrieval** (Anthropic) | Prepend document context to each chunk before embedding | Chunks ที่ ขาด context เมื่อแยกออกมา |
| **Multi-vector** | Embed summary + full text separately; retrieve by summary, return full | Dense docs ที่ chunk level ใหญ่เกินไป |

---

## ความสัมพันธ์

- [[concepts/ai-tools/llm-eval-frameworks]] — วัด RAG quality: retrieval recall, answer faithfulness, ROUGE
- [[concepts/ai-tools/agent-memory-systems]] — RAG = external memory pattern สำหรับ agents
- [[concepts/ai-tools/mcp-architecture]] — MCP Resources primitive = structured RAG access
- [[concepts/ai-tools/ai-myths]] — myth: "bigger context = RAG ไม่จำเป็น" — Mem0 2025 พิสูจน์แล้วว่าผิด

## แหล่งข้อมูล
- [[sources/ai-engineering-llm]] — Phase 11 subtopics 06 RAG
