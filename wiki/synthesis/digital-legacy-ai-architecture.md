---
type: synthesis
tags: [digital-legacy, ai, architecture, ollama, local-llm, philosophy]
sources: []
created: 2026-04-30
updated: 2026-04-30
---

# Digital Legacy AI — Self + Persistent

> **TL;DR:** สร้าง AI ที่ "เป็นเรา" และ persist หลังเราจากไป ด้วย 5-layer open + self-hosted architecture ไม่พึ่ง vendor เดียว

---

## คำถามที่ตอบ

"จะออกแบบ AI ที่เก็บความเป็นเรา (วิธีคิด, ความรู้, การตัดสินใจ) และอยู่ต่อหลังเราจากไปได้อย่างไร?"

## สรุป

ใช้ wiki + journal + decisions เป็น "digital DNA" → embed → run ผ่าน local LLM (Ollama) → expose ผ่าน Telegram/Web

**เปรียบเทียบ:**
- Wiki = **WHAT we know** (ความรู้)
- Journal = **HOW we think** (วิธีคิดประจำวัน)
- Decisions = **WHY we chose** (เหตุผลตัดสินใจสำคัญ)

ทั้งสามรวมกัน → AI สามารถ "เลียน" เราได้ทั้ง knowledge + reasoning + judgment

---

## 5-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Data (open, version-controlled)               │
│  ✅ wiki/        — knowledge (IoT, Env, AI, Pharmacy)    │
│  ✅ profile.md   — Decision Logic, Values                │
│  ✅ log.md       — chronological reasoning               │
│  ➕ journal/     — daily thinking patterns               │
│  ➕ decisions/   — major ADRs                            │
│  raw/            — sources (PDFs ใน Drive)               │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Embeddings (regenerable)                      │
│  • bge-m3 / sentence-transformers (open-source)         │
│  • Qdrant / Chroma vector DB (self-hosted)              │
│  • Re-build จาก Layer 1 ได้เสมอ                          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Inference (local-first)                       │
│  • Ollama on Mac Mini                                   │
│  • Llama 3.3 / Qwen / Mistral (open-source)             │
│  • Optional: LoRA fine-tune จาก writing pattern         │
│  • Fallback: claude-router (cloud) ตอน Mac Mini ไม่อยู่  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Interface                                     │
│  • Telegram bot (สำหรับครอบครัว/heir)                    │
│  • Web UI (Pi5 หรือ Mac Mini)                            │
│  • Voice (อนาคต — TTS เลียนเสียง)                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Persistence                                   │
│  • Git mirrors: GitHub + GitLab + Codeberg              │
│  • Cold storage: external HDD + encrypted               │
│  • Heir trustee: คนที่มี access ตอนเราไม่อยู่             │
│  • Constitutional rules: AI ห้ามทำอะไร                    │
└─────────────────────────────────────────────────────────┘
```

---

## Roadmap

### Phase A — ตอนนี้ (Apr 2026)
- [x] Wiki ใน git ✅ (มีแล้ว 120 pages)
- [x] profile.md, log.md ✅
- [x] สร้าง journal/ + decisions/ folder + templates ✅
- [x] Setup git mirror script ([[scripts/setup-git-mirror.sh]]) ✅
- [ ] ใช้ journal ทุกวัน (หรืออย่างน้อย 3 วัน/สัปดาห์)
- [ ] เขียน decisions เมื่อ major decision (เริ่ม ADR-0001, 0002)

### Phase B — เมื่อมี Mac Mini
- [ ] Setup Ollama + open-source LLM
- [ ] Build RAG ของ wiki (Qdrant + bge-m3)
- [ ] LiteLLM proxy เชื่อม local + cloud (ดู [[wiki/concepts/ai-tools/openrouter-claude-code]])
- [ ] Test: เปรียบเทียบคำตอบกับ Claude — match กี่ %

### Phase C — Long-term (3-5 ปี)
- [ ] LoRA fine-tune ด้วย writing/voice patterns
- [ ] Constitutional AI rules (จริยธรรม + ขอบเขตหลังเสียชีวิต)
- [ ] Heir setup — ใครเข้าได้, ใครเปิด/ปิดได้, นานแค่ไหน
- [ ] Operator manual สำหรับ heir (non-technical)

### Phase D — Long-term (5-30 ปี)
- [ ] Migration เมื่อ tech stack เปลี่ยน (markdown → ?)
- [ ] Public archive (เลือก) — บางส่วนแชร์เป็น public good
- [ ] Trust foundation legal structure (?)

---

## ที่ตัดสินใจแล้ว

ดู ADRs:
- [[decisions/0001-digital-legacy-strategy]] — choose open + self-hosted over proprietary
- [[decisions/0002-git-mirror-redundancy]] — multi-host git (GitHub + GitLab + Codeberg)

---

## Decision rules (สำหรับ revisit)

| ถ้า... | ทำ |
|-------|-----|
| Open-source LLM คุณภาพยังตามไม่ทัน Claude/GPT | ใช้ hybrid (cloud now, self-host เก็บไว้ persist) |
| Vendor หนึ่งเสนอ "AI clone" service | **ไม่ใช้** — lock-in ไม่ตอบโจทย์ legacy |
| ครอบครัวไม่อยาก maintain | เปิด minimal interface (Telegram bot) ไม่ต้อง dev knowledge |
| ค่าใช้จ่าย cloud พุ่ง | เร่ง Phase B local-first |
| Mac Mini ตาย | Layer 1 (data) ยังอยู่ใน git → reconstruct Layer 2-4 ได้ |

---

## ความสัมพันธ์

- [[journal/README]] — บันทึกประจำวัน (Layer 1)
- [[decisions/README]] — ADRs (Layer 1)
- [[wiki/concepts/ai-tools/local-llm-routing]] — model routing (Layer 3)
- [[wiki/sources/local-llm-mac-mini-guide]] — Mac Mini setup
- [[wiki/concepts/ai-tools/openrouter-claude-code]] — current cloud usage
- [[wiki/entities/ai-tools/telegram-ai-router]] — interface design (Layer 4)
- [[scripts/setup-git-mirror.sh]] — Layer 5 redundancy

---

## คำเตือนสำหรับตัวเองในอนาคต

- 📝 **Journal สม่ำเสมอ ≠ ความสมบูรณ์** — เขียน 3 บรรทัดยังดีกว่าไม่เขียน
- 🚫 **อย่าหลงเสน่ห์ closed AI service** — "AI clone" services ส่วนใหญ่จะปิดใน 5 ปี
- 🔐 **Heir ต้องรู้ก่อนเราตาย** — ไม่ใช่หลังจากนั้น
- 🌱 **Open formats > fancy features** — markdown 30 ปียังอ่านได้ Notion JSON ไม่แน่
- ⚖️ **Legacy AI ไม่ใช่ตัวเรา** — เป็นเครื่องมือที่เลียนเรา ตั้งกฎให้ชัดเจน
