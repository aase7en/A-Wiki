---
type: source
title: "LLM Engineering — rohitg00/ai-engineering-from-scratch Phase 11 (subtopics 06 RAG, 10 Evaluation)"
slug: ai-engineering-llm
date_ingested: 2026-06-08
original_file: raw/ai-engineering-llm.md
tags: [rag, retrieval-augmented-generation, embedding, vector-database, llm-evaluation, llm-as-judge, rouge, regression-testing]
domain: ai-tools
---

# LLM Engineering — Phase 11

**ประเภท**: curriculum / theory  
**วันที่**: 2026  
**ผู้เขียน**: Rohit Ghumare (MIT License)

## ประเด็นหลัก

1. **RAG Pipeline (4 ขั้นตอน)**: Chunk → Embed → Retrieve → Generate; sweet spot 256-512 tokens, overlap 50 tokens
2. **Embedding Models 2026**: text-embedding-3-small, Gemini Embedding 2, voyage-4, BGE-M3, Qwen3-Embedding
3. **Vector Databases**: FAISS (dev), Chroma (local), Pinecone (cloud), pgvector (Postgres), Qdrant (self-hosted)
4. **RAG vs Fine-tuning**: RAG ดีกว่าสำหรับ factual knowledge; fine-tune ดีกว่าสำหรับ behavior/style/format
5. **Advanced RAG**: HyDE, RAPTOR, Contextual Retrieval (Anthropic), Multi-vector patterns
6. **LLM-as-Judge**: 82-88% correlation กับ human judgment; G-Eval; หลีกเลี่ยง self-evaluation bias
7. **Statistical Rigor**: Wilson interval (binary), Bootstrap CI (continuous), ต้องการ 200+ samples สำหรับ 95% CI
8. **Regression Testing**: baseline → alert >2% drop; track accuracy/latency/tokens/cost

## ข้อมูลที่น่าสนใจ

- Chunking sweet spot: 256-512 tokens + 50 overlap คือ empirically validated เป็น starting point ที่ดีที่สุด
- LLM-as-judge (G-Eval): 82-88% human correlation — reliable แต่ต้องระวัง position bias (average A-B + B-A)
- RAG vs fine-tuning: RAG beats fine-tuning สำหรับ factual QA เพราะ grounded in source (ไม่ hallucinate)
- k=5-10 retrieved chunks เป็น practical default; ปรับตาม context budget
- Qwen3-Embedding: multilingual SOTA 2025, context 32k — ดีมากสำหรับ Thai content ใน A-Wiki

## หน้า Wiki ที่ได้รับการอัปเดต / สร้างใหม่

- [[concepts/ai-tools/llm-rag-architecture]] — สร้างใหม่ (chunk P4)
- [[concepts/ai-tools/llm-eval-frameworks]] — สร้างใหม่ (chunk P4)
