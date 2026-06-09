---
name: openmed
description: Medical entity extraction, PII detection, and clinical text de-identification using OpenMed. Use when working with healthcare text, patient records, drug names, clinical notes, diagnoses, or any biomedical NLP task. Supports 1000+ pre-trained models across 13 biomedical domains in 12+ languages.
---

# OpenMed — Healthcare AI (Local, Privacy-First)

OpenMed processes clinical text entirely on-device. No data leaves the machine.

**Install:** `pip install "openmed[hf]"` (standard) or `pip install "openmed[mlx]"` (Apple Silicon)
**Docs:** https://openmed.life/docs/

---

## Before You Start

1. Check if OpenMed is installed: `python -c "import openmed; print(openmed.__version__)"`
2. If not installed, tell the user to run: `pip install "openmed[hf]"` (or `[mlx]` on Apple Silicon)
3. First use downloads models from Hugging Face Hub — requires internet access once, then cached locally

---

## Capability 1: Medical Entity Extraction

Use when the user wants to extract drugs, diseases, anatomy, genes, or clinical concepts from text.

```python
from openmed import analyze_text

result = analyze_text(
    text="Patient was prescribed metformin 500mg for Type 2 diabetes mellitus.",
    model="pharma_detection_superclinical"   # or disease_detection_superclinical
)
print(result)
```

**Key models:**
| Model | ใช้กับ |
|-------|--------|
| `pharma_detection_superclinical` | ยา, dosage, drug names |
| `disease_detection_superclinical` | โรค, diagnosis, ICD codes |
| `oncology_detection_superclinical` | มะเร็ง, oncology terms |

**List available models:**
```python
import openmed
models = openmed.list_models()
```

---

## Capability 2: PII Detection (HIPAA-compliant)

Use when the user wants to find personally identifiable information in clinical text. Covers all 18 HIPAA Safe Harbor identifiers + 55+ entity types.

```python
from openmed import extract_pii

result = extract_pii(
    text="John Smith, DOB 1985-03-22, MRN 12345, visited on 01/15/2024.",
    language="en"   # also: th, de, es, fr, ar, hi, ja, nl, pt, te, tr, zh
)
# Returns: list of detected PII entities with spans and types
```

---

## Capability 3: De-identification / Anonymization

Use when the user wants to remove or replace PII from clinical text before sharing or storing.

```python
from openmed import deidentify

result = deidentify(
    text="Patient Jane Doe (SSN: 123-45-6789) was treated for hypertension.",
    method="mask",        # options: mask | hash | replace | date_shift
    language="en"
)
print(result["anonymized_text"])
```

**Methods:**
| Method | ผลลัพธ์ |
|--------|---------|
| `mask` | `[PERSON]`, `[SSN]` |
| `replace` | สุ่มชื่อจริงแทน (format-preserving) |
| `hash` | deterministic hashed value |
| `date_shift` | เลื่อนวันที่แบบ consistent |

---

## Batch Processing

```python
from openmed import analyze_text

records = [
    "Patient A: prescribed atorvastatin 40mg.",
    "Patient B: diagnosed with COPD, started tiotropium."
]
results = [analyze_text(r, model="pharma_detection_superclinical") for r in records]
```

---

## REST Service (Optional)

If the user prefers an HTTP API:
```bash
python -m openmed serve --host 0.0.0.0 --port 8770
```
Endpoints: `POST /analyze`, `POST /pii/extract`, `POST /pii/deidentify`, `GET /models/loaded`

---

## A-Wiki Pharmacy Integration

When working with `wiki/entities/pharmacy/` or `wiki/concepts/pharmacy/`:
- Extract drug entities from source documents before ingesting
- De-identify any patient-related content before saving to wiki
- Use `pharma_detection_superclinical` to enhance drug entity pages

See also: `wiki/entities/ai-tools/openmed.md`
