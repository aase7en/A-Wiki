> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — Synthesis (Cross-domain)

> **โดเมน**: Cross-domain analysis  
> **Last updated**: 2026-05-09  
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน synthesis/**

---

## Synthesis ที่มีอยู่ (17 files)

| Slug | Domains ที่เชื่อม |
|------|------------------|
| `air-quality-monitoring` | IoT × Env |
| `appsheet-to-webapp-pi5` | Env × AI Tools |
| `cold-chain-vaccine` | IoT × Pharmacy |
| `digital-legacy-ai-architecture` | AI Tools |
| `dream-projects` | IoT × Env × AI Tools |
| `dual-ai-workflow` | AI Tools |
| `energy-power-monitoring` | IoT |
| `env-webapp-schema-wastewater` | Env × AI Tools |
| `fuel-tank-level` | IoT |
| `iot-lora-architecture` | IoT |
| `local-llm-pc-vs-mac-2026` | AI Tools |
| `pharmacy-order-checker` | Pharmacy × AI Tools |
| `pharmacy-project-specs` | Pharmacy |
| `pharmacy-web-app-roadmap` | Pharmacy × AI Tools |
| `pi4-lora-gateway-server` | IoT |
| `temperature-monitor-project` | IoT |
| `waste-weight-monitoring` | IoT × Env |

---

## Rules

1. **frontmatter บังคับ**: `type: synthesis`, `tags`, `sources`, `created`, `updated`
2. **ทุก synthesis ต้องมี**: คำถามที่ตอบ, สรุป, การวิเคราะห์, แหล่งข้อมูล
3. **อย่าปน entities/concepts ใน synthesis** — ใช้ cross-reference แทน
4. **Confidence markers**: `[wiki]` / `[notebooklm YYYY-MM-DD]` / `[verified YYYY-MM-DD]`

---

## Workflow

1. มีคำถาม cross-domain → ตรวจสอบ synthesis ที่มีก่อน
2. ถ้ายังไม่มี → เสนอ user ใช้ NotebookLM ก่อน (ประหยัด token)
3. ถ้า user paste คำตอบจาก NotebookLM → review → save เป็น synthesis page
4. อัปเดต `index.md` + รัน `python3 scripts/gen-index.py`
5. บันทึก `log.md`