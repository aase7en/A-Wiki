---
type: entity
category: tool
tags: [vector-search, ann, quantization, simd, rust, python, embeddings]
sources: [github-turbovec]
created: 2026-05-28
updated: 2026-05-28
last_verified: 2026-05-28
verify_tool: WebFetch
---

# turbovec

**ประเภท**: High-performance vector ANN index (Rust + Python)
**สถานะ**: opt-in via `requirements-optional.txt` — A-Wiki default ยังใช้ sqlite-vec
**License**: open (Rust+Python)

## ภาพรวม

turbovec implement **TurboQuant** (Google Research) — quantize embeddings เป็น 2-bit/4-bit ผ่าน normalize + random rotation + Lloyd-Max → ได้ **16x compression** + ค้นเร็วกว่า FAISS บางเคส โดย SIMD (NEON ARM, AVX-512BW x86)

> 10M docs × float32 = 31 GB RAM → turbovec compress เหลือ **4 GB**

## คุณสมบัติหลัก

- **Compression**: 2-bit หรือ 4-bit scalar quant
- **SIMD**: NEON (Apple Silicon), AVX-512BW (Intel/AMD), AVX2 fallback
- **Stable IDs**: `IdMapIndex` รองรับ delete
- **Filtered search**: allowlist สำหรับ hybrid retrieval
- **Integrations**: LangChain, LlamaIndex, Haystack, Agno
- **Persistence**: `.write()` / `.load()`

## การใช้งานใน A-Wiki

**ตอนนี้ยังไม่ใช้ default** — A-Wiki มี 181 entries → sqlite-vec พอเหลือเฟือ

**Activate เมื่อ**:
- wiki ขยายเกิน **5,000 entries** (ingest raw/ scale ใหญ่)
- Personal AI Agent (dream) ต้อง index ทุกอย่างในชีวิต (10K+ docs)
- ต้องการ memory footprint ต่ำกว่า sqlite-vec บนเครื่อง low-RAM

## Setup (opt-in)

```bash
pip install -r requirements-optional.txt   # ติดตั้ง turbovec (ไม่อยู่ใน base requirements.txt)
python3 scripts/build-vec-index.py --backend turbovec
```

`--backend sqlite-vec` (default) ยังคงเดิม — turbovec import แบบ lazy เพื่อไม่ break เครื่องที่ไม่มี Rust toolchain

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| 16x compression — RAM ลด 87% | ต้อง Rust toolchain ตอน build (ถ้า wheel ไม่มี) |
| SIMD: 12-20% เร็วกว่า FAISS บน ARM | overhead สำหรับ corpus เล็ก (<10K vectors) |
| Framework integration เยอะ | quantization loss ที่ 2-bit (ต้อง 4-bit สำหรับ recall สูง) |
| Persistence ง่าย | ใหม่ — community ยังเล็กกว่า FAISS/HNSW |

## ความสัมพันธ์

- เปรียบเทียบกับ: [[sqlite-vec]] — current backend (CPU-friendly, simple)
- เปรียบเทียบกับ: FAISS, HNSW, ScaNN — vector search ตัวอื่น
- ใช้ร่วมกับ: [[embedding-models]] — paraphrase-multilingual-MiniLM-L12-v2 (current)
- เกี่ยวข้องกับ: [[vector-search]] concept

## แหล่งข้อมูล

- GitHub: https://github.com/RyanCodrai/turbovec
- Paper: Google Research TurboQuant algorithm
- [verified 2026-05-28] WebFetch — Rust 44% + Python 56%
