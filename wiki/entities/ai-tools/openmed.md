---
type: entity
category: tool
tags: [healthcare, nlp, pharmacy, pii, ner, python, on-device, hipaa, biomedical]
sources: []
created: 2026-06-09
updated: 2026-06-09
last_verified: 2026-06-09
verify_tool: WebFetch
---

# OpenMed

**ประเภท**: Python library + REST service + Swift package (healthcare AI)
**สถานะ**: external install (`pip install "openmed[hf]"`) — skill wrapper ที่ `skills/openmed/`
**License**: Apache 2.0
**เวอร์ชัน**: v1.5.5 (2026-06-08)
**Homepage**: https://openmed.life

## ภาพรวม

OpenMed คือ open-source healthcare AI framework ที่ประมวลผล clinical text ทั้งหมด **on-device** ไม่ส่งข้อมูลออกภายนอก รองรับ medical entity extraction, PII detection แบบ HIPAA-compliant, และ clinical text de-identification ใน 12+ ภาษา [verified 2026-06-09]

เหมาะกับ A-Wiki pharmacy domain โดยตรง — ช่วย extract ชื่อยา, โรค, และ anonymize ข้อมูลผู้ป่วยก่อน ingest เข้า wiki

## Capabilities

| ความสามารถ | รายละเอียด |
|-----------|-----------|
| **Medical Entity Extraction** | ยา, โรค, anatomy, gene, protein, oncology จาก 1,000+ models |
| **PII Detection** | HIPAA Safe Harbor 18 identifiers + 55+ entity types |
| **De-identification** | mask, hash, replace, date-shift — format-preserving |
| **Multilingual** | 13+ ภาษา: EN, TH, DE, ES, FR, AR, HI, JA, NL, PT, TE, TR, ZH |
| **Batch processing** | multi-document workflows |

## Models หลักที่เกี่ยวข้องกับ Pharmacy

| Model | ใช้กับ |
|-------|--------|
| `pharma_detection_superclinical` | ชื่อยา, dosage, drug interaction |
| `disease_detection_superclinical` | โรค, ICD codes, diagnosis |
| `oncology_detection_superclinical` | มะเร็ง, oncology terminology |

```python
from openmed import analyze_text
result = analyze_text("betadine 10% solution applied to wound", model="pharma_detection_superclinical")
```

## Deployment Options

```bash
# Standard (CPU/GPU)
pip install "openmed[hf]"

# Apple Silicon (MLX — เร็วกว่า)
pip install "openmed[mlx]"

# + REST API
pip install "openmed[hf,service]"
python -m openmed serve --port 8770
```

## การใช้งานใน A-Wiki

**ใน session (ผ่าน skill):**
- Claude Code ดึง `skills/openmed/SKILL.md` เมื่อพูดถึง medical/pharmacy text
- ตัวอย่าง: "ช่วย extract ชื่อยาจาก source นี้" → Claude ใช้ openmed API

**ก่อน ingest source pharmacy:**
1. Extract drug/disease entities ด้วย `pharma_detection_superclinical`
2. De-identify ข้อมูลผู้ป่วยถ้ามี (HIPAA compliance)
3. Ingest ผ่าน `ingest-source` skill ตามปกติ

**ตัวอย่าง workflow:**
```python
from openmed import analyze_text, deidentify

# 1. De-identify ก่อน
clean = deidentify(raw_text, method="mask")["anonymized_text"]

# 2. Extract pharmacy entities
entities = analyze_text(clean, model="pharma_detection_superclinical")

# 3. ใช้ entities เป็น tags/metadata ใน wiki page
```

## เปรียบกับทางเลือกอื่น

| | **OpenMed** | **spaCy scispaCy** | **Hugging Face ตรง** |
|-|------------|-------------------|---------------------|
| License | Apache 2.0 | MIT | ขึ้นกับ model |
| Models ให้เลือก | 1,000+ | ~10 biomedical | ทุก HF model |
| HIPAA PII | ✅ built-in | ❌ | ❌ |
| On-device | ✅ | ✅ | ✅ |
| Apple Silicon | ✅ MLX | ❌ | บางส่วน |
| REST API | ✅ built-in | ❌ | ❌ |

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Privacy-first — ไม่มีข้อมูลออกนอก | ต้อง download models ครั้งแรก (HF Hub) |
| HIPAA Safe Harbor compliance built-in | dependency หนัก (torch/transformers) |
| 1,000+ pre-trained biomedical models | ไม่มี MCP server สำเร็จรูป |
| Apache 2.0 — ใช้เชิงพาณิชย์ได้ | |
| Active maintenance (v1.5.5, Jun 2026) | |

## ความสัมพันธ์

- ใช้ใน domain: [[wiki/entities/pharmacy]] — drug entity extraction
- เกี่ยวข้องกับ: [[anthropic-skills]] — ใช้ร่วมกับ docx/pdf skill สำหรับ medical documents
- ทางเลือก: spaCy scispaCy (lighter), HuggingFace biomedical models (more flexible)
