---
name: research-pipeline
description: "Generic 3-stage research pipeline that works for ANY domain: gather (broad evidence collection) → analyze (synthesize findings into a structured take) → critique (red-team the analysis for gaps/biases). Maps the 28 specialized subagents into a reusable gather→analyze→critique pattern. Use when the user wants a thorough, self-critiqued answer on a topic that doesn't fit a domain-specific pipeline (finance/medical)."
version: 1.0.0
domain: [productivity, data]
lifecycle_phase: meta
category: pipeline
agents: [all, zcode]
---

# research-pipeline

ไปป์ไลน์วิจัยแบบ 3 stage ที่ใช้ได้กับทุก domain — รูปแบบ gather → analyze → critique

## เมื่อไหร่ใช้

ใช้เมื่อ user ขอ **คำตอบที่ผ่านการวิจัย + วิพากษ์วิจารณ์** บนหัวข้อที่ไม่ตรงกับ finance/medical pipeline:

- "research หา best practice สำหรับ cache invalidation"
- "อยากเข้าใจ trade-offs ของ microservices vs monolith"
- "วิเคราะห์ trend ของ edge computing ใน 2026"

**ใช้ domain-specific pipeline แทน** เมื่อ: finance (ใช้ `finance-pipeline`), medical (ใช้ `medical-pipeline`)

## Pipeline flow (3 stages)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   GATHER     │ ──▶ │   ANALYZE    │ ──▶ │   CRITIQUE   │ ──▶ REPORT
│ (broad info) │     │ (synthesize) │     │ (red-team)   │
└──────────────┘     └──────────────┘     └──────────────┘
```

แต่ละ stage **เลือก subagent ตาม domain ของคำถาม** (primary agent routing decision):

| Domain | Gather | Analyze | Critique |
|---|---|---|---|
| code/engineering | `code-explorer` | `code-architect` | `security-auditor` |
| ai-ops | `cost-auditor` | `model-router-advisor` | `token-optimizer` |
| webapp | `frontend-architect` | `ui-ux-reviewer` | `db-schema-designer` |
| business | `marketing-strategist` | `business-doc-drafter` | `realestate-tax-advisor` |
| productivity | `inbox-triage` | `workflow-simplifier` | `copywriting-partner` |
| data | `data-profiler` | `finance-analyst` | `finance-debater` |
| tutor/thought-partner | `language-tutor` | `skill-coach` | `copywriting-partner` |
| (default) | `Explore` (built-in) | `general-purpose` (built-in) | `scrutinize` |

**หลักการ**: แต่ละ stage ต้องอยู่คนละ bucket (ดู `docs/protocols/subagent-model-routing.md`) เพื่อกัน rate-limit collision

## Handoff contract

### Stage 1: GATHER
**Input**: คำถาม/หัวข้อวิจัย
**Output schema**:
```json
{
  "topic": "<question>",
  "findings": [
    {"source": "<where>", "point": "<key point>", "confidence": "<high|med|low>"}
  ],
  "raw_evidence": "<summary or links>"
}
```
**Primary agent action**: เลือก gather-subagent ตาม domain table + ส่ง prompt "Gather information on <TOPIC>. Return key findings with sources + confidence."

### Stage 2: ANALYZE
**Input**: Stage 1 findings
**Output schema**:
```json
{
  "synthesis": "<integrated take>",
  "key_takeaways": ["<takeaway1>"],
  "recommendations": ["<rec1>"],
  "open_questions": ["<q1>"]
}
```
**Primary agent action**: รวม Stage 1 findings + ส่ง prompt "Synthesize these findings: <stage1_json>. Provide key takeaways, recommendations, and open questions." เข้า analyze-subagent

### Stage 3: CRITIQUE
**Input**: Stage 2 synthesis
**Output schema**:
```json
{
  "weak_points": ["<gap1>"],
  "biases": ["<bias1>"],
  "missing_evidence": ["<evidence1>"],
  "revised_confidence": "<high|med|low>",
  "verdict": "<final assessed take>"
}
```
**Primary agent action**: ส่ง prompt "Red-team this analysis: <stage2_json>. Identify weak points, biases, missing evidence. Give a revised confidence + verdict." เข้า critique-subagent

## Final report

```markdown
# Research: <TOPIC>

## Findings (Stage 1)
<stage1_findings>

## Analysis (Stage 2)
<stage2_synthesis>

## Critique (Stage 3)
Weak points: <weak>
Verdict: <verdict>

**Confidence**: <revised_confidence>
```

## Cost

- โดยเฉลี่ย deepseek-v4-flash + deepseek-v4-pro + sonnet (~3 calls)
- เลือก gather-subagent จาก tier ต่ำสุดก่อน (cost-first)

## ข้อควรระวัง

- **Bucket diversity**: ทั้ง 3 stage ต้องอยู่ bucket ต่างกัน — ตรวจด้วย `check_subagent_fanout` hook
- ถ้า stage ไหน fail → `subagent_fallback.sh` แล้ว resume
- สำหรับ domain ที่ตารางไม่ครอบคลุม → fallback `Explore` → `general-purpose` → `scrutinize`
