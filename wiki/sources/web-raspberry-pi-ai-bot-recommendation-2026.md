---
tags: [iot, web, raspberry, bot, recommendation]
type: source
title: "web raspberry pi ai bot recommendation 2026"
slug: web-raspberry-pi-ai-bot-recommendation-2026
date_ingested: 2026-05-24
original_file: raw/web-raspberry-pi-ai-bot-recommendation-2026.md
---

```yaml
---
---
```

# Recommended Raspberry Pi Setup for Wiki AI Bot (2026)

> ⚠️ PENDING REVIEW — เนื้อหานี้ยังไม่ได้รับการตรวจสอบโดย Claude

## 1. Primary Recommendation: The "Power Bot" Setup
To run a local Wiki AI bot with acceptable latency on a Raspberry Pi, the following configuration is the 2026 standard:

- **Board:** Raspberry Pi 5 (16GB RAM)
- **AI Accelerator:** Raspberry Pi AI HAT+ 2 (featuring Hailo-10H NPU)
- **Storage:** NVMe SSD (via M.2 HAT) for fast vector database lookups.
- **Cooling:** Official Active Cooler or high-end passive case (e.g., Argon ONE V3).

## 2. Technical Capabilities
- **LLM Support:** Specialized for SLMs (Small Language Models) like Llama 3.2 (1B/3B), Phi-3.5, and Qwen 2.5 (1.5B).
- **Inference Speed:** Instantaneous response for 1B models; ~10-15 t/s for 3B models (using NPU).
- **Memory Management:** 
    - 8GB on Hailo-10H handles the model weights.
    - 16GB on Pi 5 handles the OS, Wiki index (Vector DB), and Telegram Bot API.

## 3. Cost Estimate (Thai Market 2026)
- Total Project Cost: ~11,000 - 13,000 THB.
- Performance/Price Ratio: Higher than a base PC, but offers the best "always-on" low-power solution for a private wiki assistant.

## ข้อสังเกตสำหรับ Claude
- Hailo-10H NPU ตัวใหม่ช่วยแก้ปัญหาความร้อนและภาระ CPU ของ Pi 5 ได้ดีมาก
- แม้จะมี NPU แต่การเลือกใช้โมเดลยังจำกัดอยู่ที่ขนาดไม่เกิน 3B-7B (Quantized) หากต้องการใช้โมเดลใหญ่กว่านี้ (เช่น 14B) ยังคงต้องขยับไป Mac Mini M4
- ข้อมูลนี้ควรนำไปอัปเดตใน `entities/iot/raspberry-pi-5.md` หรือสร้างหน้าใหม่สำหรับ AI Accelerators
