---
adr: 0001
title: Digital Legacy AI strategy — open formats + self-hosted
status: Accepted
date: 2026-04-30
tags: [digital-legacy, ai, architecture, infrastructure, philosophy]
related_journal: [journal/2026/2026-04-30]
supersedes: []
superseded_by: []
---

# ADR-0001: Digital Legacy AI strategy — open formats + self-hosted

## Status
**Accepted** (2026-04-30)

## Context

เป้าหมายระยะยาว: สร้าง AI ที่ "เป็นเรา" และ **persist หลังเราจากไป** (digital legacy)

**ข้อจำกัด:**
- เวลาจริง: 30+ ปีข้างหน้า — เทคโนโลยีจะเปลี่ยนเยอะ
- งบ: ไม่ unlimited — ต้องกระจายต้นทุน
- ความรู้: เป็น engineer ทำเองได้บ้าง แต่ไม่ใช่ ML researcher
- ครอบครัว: ต้องคนอื่นดูแลตอนเราไม่อยู่ — ต้องเรียบง่ายพอ
- กฎหมาย: บัญชี cloud หลายเจ้าจะถูกปิดถ้าไม่ active 1-2 ปี

**ผู้เกี่ยวข้อง:** เรา (ตอนนี้) → AI agent → ครอบครัว/heir (อนาคต)

---

## Decision

ใช้ **5-layer architecture** แบบ open + self-hosted ไม่ผูกกับ vendor เดียว

```
Layer 1: Data — wiki/, journal/, decisions/ (markdown ใน git)
Layer 2: Embeddings — open-source (bge, sentence-transformers)
Layer 3: Inference — Ollama + open model on Mac Mini
Layer 4: Interface — Telegram/Web bot
Layer 5: Backup — multi-host git mirror + offline + heir trustee
```

หลักการ:
1. **Open formats เท่านั้น** (markdown, JSON, plaintext)
2. **Self-hosted inference** (ไม่พึ่ง cloud API ระยะยาว)
3. **Multi-host redundancy** (GitHub + GitLab + Codeberg)
4. **Documented reasoning** (journal + decisions = HOW we think, not just WHAT)

---

## Alternatives Considered

### Option A: NotebookLM + Claude Code (proprietary stack)
จาก Boom Big Note YouTube workflow
- **Pros:**
  - Setup เร็ว (1 ชม.)
  - Gemini AI ฟรีของ Google
  - ใช้ token Claude Pro ได้คุ้ม
- **Cons:**
  - Lock-in Google + Anthropic
  - NotebookLM ปิดได้ตามใจ Google
  - Scraping fragile
  - Closed-source setup script ของ creator
- **ทำไมไม่เลือก:** ไม่ตอบโจทย์ legacy 30+ ปี — vendor risk สูงเกินไป

### Option B: Cloud-only (OpenAI/Anthropic + their hosted RAG)
- **Pros:** ดูแลน้อย, performance ดี
- **Cons:** Subscription ตลอดชีพ, account ปิดถ้าไม่ active
- **ทำไมไม่เลือก:** ไม่ persistent หลังเราจากไป

### Option C (chosen): Open + self-hosted hybrid
- **Pros:**
  - ของเราเป็นเจ้าของจริง
  - Open format = อนาคต-proof
  - Self-host = ไม่ต้องจ่ายตลอดชีพ
  - Mirror หลาย host = redundancy ฟรี
- **Cons:**
  - Setup เริ่มต้นใช้เวลา (Mac Mini, Ollama)
  - ต้องดูแลเอง (server uptime)
  - Performance อาจสู้ cloud ไม่ได้
- **ทำไมเลือก:** ตรงเป้าหมาย legacy ที่สุด

---

## Consequences

### Positive
- ข้อมูลทั้งหมดเป็นของเรา — markdown ใน git
- 50+ ปีข้างหน้ายังใช้ได้ (open format)
- ไม่พึ่ง subscription ใด
- AI สามารถถูก reconstruct ได้ตราบใดที่ open-source LLM ยังมี
- เป็นรากฐานให้ครอบครัว/heir ใช้ต่อได้

### Negative / Trade-offs
- ต้องเขียน journal + decisions เพิ่ม (effort ทุกวัน)
- Mac Mini จะมี cost ครั้งเดียว ~30K-50K
- ต้อง setup multi-host mirror manual
- AI quality เริ่มแรกจะสู้ Claude Sonnet ไม่ได้

### Risks
- ถ้าไม่เขียน journal สม่ำเสมอ — AI จะมี "เนื้อหา" แต่ไม่มี "เสียง"
- ถ้า Mac Mini ตายและไม่มี backup — Layer 3 ตาย (แต่ Layer 1 ยังอยู่)
- Heir อาจไม่เข้าใจวิธี maintain → ต้องเขียน "operator manual" ภายใน 2027

---

## Revisit Conditions

- 📅 **2027-04-30**: review หลัง 1 ปี — journal + decisions เขียนสม่ำเสมอจริงไหม?
- 🖥️ **เมื่อได้ Mac Mini**: เริ่ม Phase B (Ollama + RAG)
- 👥 **เมื่อมี heir candidate**: เพิ่ม operator manual + access plan
- 🔄 **ถ้า open-source LLM ตามไม่ทัน Claude/GPT**: revisit hybrid (cloud for now, local for legacy)

---

## References

- [[journal/2026/2026-04-30]] — วันที่ถกเรื่องนี้
- [[wiki/synthesis/digital-legacy-ai-architecture]] — รายละเอียดสถาปัตยกรรม
- [[wiki/concepts/ai-tools/openrouter-claude-code]] — context การคุยตอนแรก
- [[wiki/sources/local-llm-mac-mini-guide]] — Mac Mini setup
- [[wiki/concepts/ai-tools/local-llm-routing]] — model routing
- ADR template inspiration: https://adr.github.io/
