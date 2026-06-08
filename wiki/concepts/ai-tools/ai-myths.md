---
type: concept
tags: [myths, misconceptions, llm, agents, fine-tuning, rag, scaling, ai-engineering]
sources: [ai-engineering-myths, ai-engineering-glossary]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# AI Myths — ความเชื่อผิดๆ ที่พบบ่อย

ความเชื่อผิดๆ 20 ข้อเกี่ยวกับ AI/ML — แต่ละข้ออธิบาย reality + design implication
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` (MIT)

---

## 1. LLM & Language

### ❌ "AI understands language"
**Reality:** LLMs predict the next token from statistical patterns. No understanding, no world model (provably). Pattern matching across billions of examples.
**Design implication:** ออกแบบ systems รอบข้อจำกัดนี้ อย่าออกแบบราวกับมี reasoning จริง

### ❌ "Transformers understand order because of positional encoding"
**Reality:** Self-attention treats input as a SET not a sequence. Positional encoding เป็น workaround (hack) ไม่ใช่ built-in sequential understanding. ยังเป็น active research (RoPE, ALiBi, Sinusoidal)

### ❌ "Neural networks are black boxes"
**Reality:** Tools มีจริง: attention visualization, probing classifiers, mechanistic interpretability (induction heads, feature detectors). ไม่ใช่ full transparency แต่ไม่ใช่ black box ด้วย

---

## 2. Model Size & Compute

### ❌ "More parameters = smarter model"
**Reality (Chinchilla, 2022):** Most models were over-parameterized and under-trained. Data quality สำคัญเท่ากับ parameter count. Phi-2 (2.7B) beat models 10x its size on benchmarks.
**Design implication:** อย่าเลือก biggest model โดย default. Match size กับ task และ budget

### ❌ "Scaling laws mean bigger is always better"
**Reality:** Diminishing returns. Improvements มาจาก better architecture, training techniques, data quality ไม่ใช่แค่ scale

### ❌ "You need massive compute to train useful models"
**Reality:** Foundation model pre-training ต้องการ massive compute. แต่ fine-tuning, LoRA, transfer learning = single GPU. หลาย apps ไม่ต้องการ training เลย — แค่ prompting + RAG

---

## 3. Fine-tuning vs RAG

### ❌ "Fine-tuning teaches the model new knowledge"
**Reality:** Fine-tuning ปรับ HOW the model uses existing knowledge ไม่ใช่ WHAT it knows. Information ที่ไม่ได้อยู่ใน pre-training data จะไม่ถูก add อย่างน่าเชื่อถือ
**Decision rule:**
- New knowledge/facts/documents → **RAG**
- New format/style/behavior/tone → **Fine-tuning**

---

## 4. Context & Memory

### ❌ "Bigger context window = better"
**Reality:** "Lost in the middle" problem — models ให้ attention กับ beginning และ end มากกว่า middle. 200K context ≠ equal attention ตลอด 200K tokens. ยิ่งยาวยิ่ง cost สูงและช้า
**Design implication:** อย่า dump ทุกอย่างใน context. Selective retrieval > stuffing full document

---

## 5. Agents & Autonomy

### ❌ "AI agents are autonomous"
**Reality:** Agents = think → act → observe → repeat. ทำตาม pattern ที่ harness กำหนด. ไม่มี goals, plans, self-awareness. "Autonomy" มาจาก loop ไม่ใช่ LLM.
**Design implication:** เมื่อ build agents → build the loop, tools, guardrails. LLM = decision-making component เท่านั้น

---

## 6. Training & Alignment

### ❌ "RLHF aligns AI with human values"
**Reality:** RLHF align กับ preferences ของ specific humans ที่ให้ feedback. คนเหล่านี้ไม่เห็นด้วยกัน, มี biases, ครอบคลุมไม่ได้ทุก situation. RLHF = training technique ไม่ใช่ solution ของ alignment

### ❌ "Pre-training is just reading the internet"
**Reality:** Data curation, filtering, deduplication มีผลสูงมาก. Garbage in, garbage out.

---

## 7. Representations

### ❌ "Embeddings capture meaning"
**Reality:** Embeddings capture statistical co-occurrence patterns. "King - Man + Woman = Queen" = distributional patterns ไม่ใช่ semantic understanding.
**Use:** ดีสำหรับ similarity search, clustering, retrieval. อย่า over-interpret "similarity"

---

## 8. Tools & Techniques

### ❌ "Temperature makes the AI more creative"
**Reality:** Temperature = randomness knob (scales logits before softmax). Higher = flatter distribution = more random selection.
**Use:** Too repetitive → raise. Too chaotic → lower.

### ❌ "Prompt engineering is not real engineering"
**Reality:** Prompt engineering = system design — interface between human intent and model behavior. ต้องเข้าใจ tokenization, attention patterns, context limits, output parsing. ใกล้เคียง API design มากกว่า "พูดดีๆ กับ AI"

### ❌ "GPT stands for General Purpose Technology"
**Reality:** GPT = Generative Pre-trained Transformer.

---

## 9. Open Source

### ❌ "Open source AI = open weights"
**Reality:** "Open source" ส่วนใหญ่ = open weights เท่านั้น (ไม่รวม training data, training code). True open source (OLMo) release everything. Open weights ≠ open source.

---

## 10. Architecture

### ❌ "CNNs are outdated, everything is transformers now"
**Reality:** Vision Transformers (ViT) beat CNNs on many benchmarks แต่ CNNs ยังใช้ widely: faster inference, mobile/edge, needs less data. Best architectures often combine both. Learn both.

---

## ความสัมพันธ์

- ดู [[concepts/ai-tools/ai-glossary]] — คำอธิบายที่แม่นยำของ terms เหล่านี้
- ดู [[concepts/ai-tools/multi-agent-theory]] — expand จาก "agents are autonomous" myth (P2a)
- ดู [[concepts/ai-tools/llm-rag-architecture]] — expand จาก fine-tuning vs RAG myth (P4)
- ดู [[agent-skills/swarm-intelligence/agile-swarm]] — A-Wiki swarm design ที่ aware เรื่อง myths เหล่านี้

## แหล่งข้อมูล
- [[sources/ai-engineering-myths]] — Original source summary
- [[sources/ai-engineering-glossary]] — Companion glossary
