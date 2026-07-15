---
name: medical-pipeline
description: "End-to-end clinical question pipeline that chains three specialized subagents: medical-lit-reviewer (evidence retrieval + citations) → clinical-reasoner (differential diagnosis / treatment reasoning) → medical-safety-checker (drug interaction / contraindication critique). The primary agent orchestrates the handoff. One command produces an evidence-based, safety-checked clinical summary. NOT a substitute for a clinician — decision-support only."
version: 1.0.0
domain: [medical]
lifecycle_phase: meta
category: pipeline
agents: [all, zcode]
---

# medical-pipeline

ไปป์ไลน์คำถามทางคลินิกแบบครบวงจร — 3 stage ตามหลักฐานเชิงประจักษ์ (evidence-based) พร้อมตรวจสอบความปลอดภัย

## เมื่อไหร์ใช้

ใช้เมื่อ user ถาม **คำถามทางการแพทย์ที่ต้องการ evidence + safety check**:

- "อยากรู้ evidence เรื่อง metformin ในเบาหวาน type 2"
- "patient มี fever + rash หลังเที่ยว — differential diagnosis?"
- "check drug interaction ระหว่าง warfarin กับ amoxicillin"

**ไม่ใช้** เมื่อ user ขอแค่ข้อมูล drug fact เดียว (ใช้ `medical-lit-reviewer` ตรงๆ) หรือ emergency (ส่งโรงพยาบาล)

⚠️ **ข้อจำกัด**: decision-support เท่านั้น ไม่ใช่การวินิจฉัย/รักษา ผู้ใช้ต้องปรึกษาแพทย์เสมอ

## Pipeline flow (3 stages)

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ medical-lit-reviewer │ ──▶ │  clinical-reasoner   │ ──▶ │ medical-safety-checker│ ──▶ REPORT
│ (evidence + citations│     │ (differential dx /   │     │ (drug interaction /  │
│  from PubMed)        │     │  treatment reasoning)│     │  contraindication)   │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
   WebSearch, WebFetch          Read, WebSearch              Read, WebSearch
   deepseek-v4-flash            deepseek-v4-pro              sonnet
```

## Handoff contract

### Stage 1: `medical-lit-reviewer`
**Input**: คำถาม/โจทย์ทางการแพทย์
**Output schema** (must include all):
```json
{
  "query": "<original question>",
  "evidence": [
    {"source": "<guideline/pubmed>", "finding": "<summary>", "citation": "<ref>"}
  ],
  "summary": "<synthesis of evidence>"
}
```
**Primary agent action**: ส่ง prompt "Summarize the evidence on <QUESTION>. Provide citations." เข้า `medical-lit-reviewer`

### Stage 2: `clinical-reasoner`
**Input**: Stage 1 evidence + อาการ/บริบทผู้ป่วย
**Output schema** (must include all):
```json
{
  "differential": ["<dx1>", "<dx2>", "<dx3>"],
  "reasoning": "<why each is considered>",
  "recommended_workup": ["<test1>", "<test2>"],
  "treatment_considerations": "<text>"
}
```
**Primary agent action**: รวม Stage 1 evidence + ส่ง prompt "Given this evidence: <stage1_json>, and patient presentation: <SYMPTOMS>, provide differential diagnosis, reasoning, workup, and treatment considerations" เข้า `clinical-reasoner`

### Stage 3: `medical-safety-checker`
**Input**: Stage 2 treatment considerations + ยาที่เกี่ยวข้อง
**Output schema** (must include all):
```json
{
  "drug_interactions": ["<interaction1>"],
  "contraindications": ["<contra1>"],
  "safety_warnings": ["<warning1>"],
  "safe_to_proceed": true|false
}
```
**Primary agent action**: ส่ง prompt "Check drug interactions and contraindications for: <stage2_treatment_considerations> in context of <PATIENT_MEDS>" เข้า `medical-safety-checker`

## Final report

```markdown
# Clinical Summary: <QUESTION>

## Evidence (Stage 1)
<stage1_summary>
**Citations**: <refs>

## Reasoning (Stage 2)
Differentials: <differential>
Recommended workup: <workup>

## Safety Check (Stage 3)
Drug interactions: <interactions>
Contraindications: <contras>

⚠️ **Decision-support only — consult a clinician before acting.**
```

## Cost

- Stage 1: deepseek-v4-flash (free)
- Stage 2: deepseek-v4-pro (cheap)
- Stage 3: sonnet (primary tier) — safety ต้องการ reasoning ลึก
- รวม ~3 subagent calls, sequential

## ข้อควรระวัง

- **Iron Law (safety)**: ผลลัพธ์เป็น decision-support เท่านั้น — ไม่ใช่การวินิจฉัย/สั่งยา
- **PDPA/PHI**: ห้ามใส่ข้อมูลผู้ป่วยจริงใน prompt — ใช้ synthetic/de-identified เท่านั้น
- **Rate-limit diversity**: 3 stages ใช้ 3 buckets ต่างกัน — ไม่ชน bucket
- ถ้า stage ไหน fail → `subagent_fallback.sh` แล้ว resume จาก stage นั้น
