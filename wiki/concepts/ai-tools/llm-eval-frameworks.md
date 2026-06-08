---
type: concept
tags: [llm-evaluation, llm-as-judge, rouge, regression-testing, g-eval, statistical-testing, promptfoo, deepeval, braintrust, langsmith]
sources: [ai-engineering-llm]
domain: ai-tools
created: 2026-06-08
updated: 2026-06-08
last_verified: 2026-06-08
verify_tool: WebFetch
---

# LLM Evaluation Frameworks

LLM-as-judge, automated metrics, statistical rigor, regression testing — วิธีวัด LLM output อย่างเชื่อถือได้
[verified 2026-06-08] จาก `rohitg00/ai-engineering-from-scratch` Phase 11 (MIT)

---

## 1. 3 Categories ของ Evaluation

| Category | Speed | Cost | Scale | Reliability |
|---|---|---|---|---|
| **Automated** (ROUGE/BLEU/exact match) | Fast | Free | Infinite | High (deterministic) |
| **LLM-as-judge** | Fast | Low | High | 82-88% human correlation |
| **Human evaluation** | Slow | High | Low | Ground truth |

**เลือกอย่างไร**: automated สำหรับ regression CI; LLM-as-judge สำหรับ open-ended quality; human สำหรับ final sign-off + calibration

---

## 2. LLM-as-Judge

### G-Eval (Liu et al., 2023)
GPT-4 (หรือ model อื่น) rates outputs 1-5 บน criteria dimensions:
- Coherence, fluency, relevance, factual consistency
- Include **rubric + few-shot examples** ใน judge prompt
- Correlation with human judgment: **82-88%** across diverse tasks

### Bias ที่ต้องระวัง

| Bias | คำอธิบาย | Fix |
|---|---|---|
| **Self-evaluation bias** | Model rates own outputs higher | ใช้ judge model ที่ต่างจาก generator |
| **Position bias** | First option rated higher in pairwise | Average A-B ordering + B-A ordering |
| **Verbosity bias** | Longer answers rated higher | Rubric ที่ explicit เรื่อง length |
| **Sycophancy** | Judge aligns with user-provided preference | Blind evaluation (hide user preference) |

---

## 3. Automated Metrics

### ROUGE (สำหรับ summarization)
- **ROUGE-1**: unigram overlap
- **ROUGE-2**: bigram overlap
- **ROUGE-L**: longest common subsequence (แนะนำสำหรับ summaries)

```python
from rouge_score import rouge_scorer
scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
result = scorer.score(reference, hypothesis)
# result.rougeL.fmeasure = F1 score
```

### เมื่อใช้ metric ไหน
| Task | Metric |
|---|---|
| Extractive QA | Exact match |
| Abstractive summarization | ROUGE-L |
| Code generation | Pass@k (functional tests) |
| Open-ended generation | LLM-as-judge |
| Classification | Accuracy / F1 |

---

## 4. Statistical Rigor

### Confidence Intervals (บังคับสำหรับ production eval)

| Method | ใช้กับ | สูตร |
|---|---|---|
| **Wilson interval** | Binary outcomes (pass/fail) | สถิติที่ดีกว่า Wald ที่ extremes (p near 0 or 1) |
| **Bootstrap CI** | Continuous metrics (ROUGE, latency) | Resample 1000x → percentile CI |

### Sample Size
- ต้องการ **200+ cases** สำหรับ 95% CI บน 10% difference
- คำนวณ minimum detectable effect ก่อนเริ่ม eval (power analysis)
- ถ้า sample น้อยกว่า 200 → ไม่ควรรายงาน single-point estimate ที่ไม่มี CI

---

## 5. Regression Testing Protocol

```
1. Establish baseline eval set (fixed, held-out)
2. Run baseline → record metrics
3. Any change (model / prompt / retrieval) → re-run eval
4. Alert if any metric drops >2%
5. Track: accuracy, p50/p95/p99 latency, token usage, cost-per-query
6. Never deploy without passing regression suite
```

### Anti-patterns

| Anti-pattern | ปัญหา | Fix |
|---|---|---|
| Eval on training data | Inflated score (data leakage) | Held-out test set เสมอ |
| Single-metric eval | Miss important dimensions | 3+ complementary metrics |
| No confidence interval | Noise as signal | Wilson หรือ Bootstrap CI |
| Human eval ช้าเกินไป | Expensive fixes late | Human review ที่ 20% of dev cycle |
| Cherry-pick examples | Misleading | Random sample + worst-case analysis |

---

## 6. Eval Tooling (2026)

| Tool | Type | Best for |
|---|---|---|
| **promptfoo** | Open-source CLI | Test-driven prompt development, CI integration |
| **DeepEval** | Open-source framework | Custom metrics, regression suites |
| **Braintrust** | Managed cloud | Team collaboration, logging, experiments |
| **LangSmith** | Managed cloud | LangChain integration, distributed traces |

**Selection**: promptfoo สำหรับ prompt-first dev; DeepEval สำหรับ custom criteria; LangSmith ถ้าใช้ LangChain/LangGraph

---

## ความสัมพันธ์

- [[concepts/ai-tools/llm-rag-architecture]] — RAG eval: retrieval recall + answer faithfulness
- [[concepts/ai-tools/ai-myths]] — myth: "LLM self-evaluation is reliable" — self-bias พิสูจน์แล้วว่าไม่จริง

## แหล่งข้อมูล
- [[sources/ai-engineering-llm]] — Phase 11 subtopic 10 Evaluation
