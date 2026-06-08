---
type: concept
tags: [glossary, llm, embeddings, rag, agents, transformers, fine-tuning, mcp, swarm]
sources: [ai-engineering-glossary]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# AI Engineering Glossary

คำศัพท์ AI Engineering ที่แม่นยำ — แยก "สิ่งที่คนพูด" ออกจาก "ความหมายจริง"
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` (MIT)

---

## Core Architecture Terms

| Term | ความหมายจริง |
|------|------------|
| **Transformer** | Neural net ที่ใช้ self-attention แทน recurrence — ทุก position attend to ทุก position ได้พร้อมกัน |
| **Self-Attention** | Q×K→weights → weighted sum of V. แต่ละ token เห็นทุก token อื่น |
| **Encoder** | Bidirectional attention (BERT) — ดีสำหรับ understanding tasks |
| **Decoder** | Causal/masked attention (GPT) — ดีสำหรับ generation |
| **Autoregressive** | Predict next token → feed back as input → repeat. GPT, LLaMA, Claude ทั้งหมดเป็น autoregressive |
| **KV Cache** | Cache key/value matrices จาก previous tokens → ไม่ต้อง recompute. Memory ↑ แต่ speed ↑ |

---

## Training Terms

| Term | ความหมายจริง |
|------|------------|
| **Parameter** | Learnable number ใน model. 7B params × 4 bytes = 28GB RAM |
| **Loss Function** | วัด gap ระหว่าง prediction กับ actual. Training = minimize this |
| **Gradient Descent** | ขยับ parameters ไปในทิศที่ลด loss มากที่สุด |
| **Backpropagation** | Chain rule ย้อนกลับผ่าน network — คำนวณ gradient ของแต่ละ weight |
| **Epoch** | 1 รอบผ่าน training data ทั้งหมด |
| **Learning Rate** | Step size ใน gradient descent — hyperparameter สำคัญที่สุด |
| **Overfitting** | เรียน noise ไม่ใช่ signal — ดีใน train, แย่ใน test |
| **Dropout** | Random zero out activations ระหว่าง training. Turned off at inference |
| **Adam / AdamW** | Default optimizer. AdamW = decoupled weight decay = better regularization |
| **Cross-Entropy** | Loss สำหรับ LMs: -log(P(correct token)). Perplexity = exp(cross-entropy) |

---

## LLM-Specific Terms

| Term | ความหมายจริง |
|------|------------|
| **LLM** | Transformer-based network, billions of params, trained on internet-scale text, predicts next token |
| **Token** | Subword unit (~3-4 chars). "unbelievable" ≈ 3 tokens |
| **Context Window** | Max tokens (input + output) ต่อ 1 API call. Buffer ที่ reset ทุก call — ไม่ใช่ memory |
| **Temperature** | Scales logits before softmax. Higher = more random. Lower = more deterministic. ≠ creativity |
| **Hallucination** | Pattern-completing ข้อมูลที่ไม่มีใน training data หรือ context. ไม่ใช่ "โกหก" |
| **System Prompt** | Message แรกของ conversation — set behavior/persona โดย developer. User มักไม่เห็น |
| **Streaming** | ส่ง tokens ทีละตัวขณะ generate แทนที่จะรอให้ครบ. ใช้ SSE หรือ WebSocket |

---

## Fine-tuning & Adaptation

| Term | ความหมายจริง |
|------|------------|
| **Fine-tuning** | ต่อ training จาก pretrained model บน smaller task-specific dataset. ปรับ behavior ไม่ใช่เพิ่ม knowledge |
| **SFT** | Supervised Fine-Tuning บน (instruction, response) pairs → เปลี่ยน base model เป็น chat model |
| **RLHF** | (1) เก็บ human preferences (2) train reward model (3) PPO optimize LLM ให้ reward สูง |
| **DPO** | Direct Preference Optimization — skip reward model, optimize LM โดยตรงบน preference pairs |
| **LoRA** | Low-Rank Adaptation — insert small matrices alongside frozen weights. Train only those. 10-100x memory reduction |
| **QLoRA** | LoRA + base model in 4-bit (NF4). 7B model ใน 4-6GB |
| **Quantization** | ลด precision: float32→int8→int4. GPTQ, AWQ, GGUF เป็น formats ที่ใช้บ่อย |

---

## RAG & Retrieval

| Term | ความหมายจริง |
|------|------------|
| **Embedding** | Learned mapping discrete → dense vector. Similar items = nearby vectors |
| **Semantic Search** | ค้นหาด้วย meaning (embedding similarity) ไม่ใช่ keyword matching |
| **Chunking** | แบ่งข้อความเป็น segments ก่อน embed. Typical: 256-512 tokens, 10-20% overlap |
| **Cosine Similarity** | dot(a,b)/(‖a‖×‖b‖). Range: -1 to 1. Standard metric สำหรับ embedding similarity |
| **Vector Database** | Database สำหรับ store float vectors + fast approximate nearest-neighbor search |
| **RAG** | Retrieve docs (embedding similarity) → เพิ่มใน prompt → LLM ตอบจาก context |
| **Latent Space** | Compressed representation space — similar inputs = nearby points |

---

## Agents & Tools

| Term | ความหมายจริง |
|------|------------|
| **Agent** | while loop: LLM ตัดสินใจ tool ที่จะ call → execute → observe result → repeat |
| **Function Calling** | LLM request execution ของ external function ผ่าน JSON Schema. Mechanism ไม่ใช่ agent |
| **Swarm** | Multiple agents share state + coordinate via message passing → emergent behavior จาก simple rules |
| **MCP** | Model Context Protocol: JSON-RPC (stdio/HTTP) — standardizes AI↔tools/resources connection |
| **Guardrails** | Input/output validation layers รอบ LLM. Rule-based หรือ model-based |
| **Prompt Injection** | Attack ที่ malicious text override system prompt. LLM equivalent ของ SQL injection |

---

## Optimization & Training Tricks

| Term | ความหมายจริง |
|------|------------|
| **MoE (Mixture of Experts)** | หลาย "expert" subnetworks — routing ส่ง input ไปแค่บางส่วน. Full model ใหญ่ แต่ each pass เบา |
| **Mixed Precision** | float16 forward pass + float32 weight updates. ~2x speedup, negligible accuracy loss |
| **Weight Decay** | Penalty บน weight magnitude = L2 regularization. ป้องกัน weights โตเกินไป |
| **Softmax** | exp(x_i)/Σexp(x_j). Turns arbitrary numbers → probability distribution |
| **Chain of Thought** | ให้ model แสดง reasoning steps → ดีขึ้นบน multi-step problems |
| **Few-Shot** | 3-5 examples ใน prompt ก่อน task. ต่างจาก zero-shot (0 examples) และ fine-tuning |

---

## ความสัมพันธ์

- ดู [[concepts/ai-tools/ai-myths]] — myths จาก same source, เสริมกัน
- ดู [[concepts/ai-tools/multi-agent-theory]] — expand จาก Swarm + Agent entries (P2a)
- ดู [[concepts/ai-tools/llm-rag-architecture]] — expand จาก RAG entry (P4)
- ดู [[entities/ai-tools/openrouter-api]] — LLM routing ใน A-Wiki
- ดู [[agent-skills/swarm-intelligence/agile-swarm]] — Swarm implementation ใน A-Wiki

## แหล่งข้อมูล
- [[sources/ai-engineering-glossary]] — Original source summary
