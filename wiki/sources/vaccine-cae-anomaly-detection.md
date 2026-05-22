---
type: source
title: "Real-time Temperature Anomaly Detection in Vaccine Refrigeration using Deep Learning on ESP32"
slug: vaccine-cae-anomaly-detection
date_ingested: 2026-04-18
original_file: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1429602/full
tags: [tinyml, esp32, vaccine, cold-chain, anomaly-detection, deep-learning, cae, pt100, rtos]
---

# Real-time Anomaly Detection in Vaccine Refrigeration — Frontiers AI 2024

**ประเภท**: academic paper  
**วารสาร**: Frontiers in Artificial Intelligence  
**ปีที่ตีพิมพ์**: 2024

## ประเด็นหลัก

1. **Convolutional Autoencoder (CAE)** รันบน ESP32 โดยตรง — ตรวจ anomaly โดยไม่ต้องตั้ง threshold ตายตัว
2. **Hardware**: ESP32 + PT100 (precision) + MAX31865 (ADC) + FreeRTOS (5-min sampling)
3. **Semi-supervised learning**: train บน "normal" data เท่านั้น → flagge deviation
4. **Performance**: accuracy 92%, precision 0.92, recall 0.90, 200ms/batch, 50mW
5. **Memory**: 1.2MB, ~9,500 parameters

## Model Architecture

```
Input (temperature sequence)
    ↓ Convolutional layers (encode)
    ↓ Latent representation
    ↓ Transposed Conv (decode)
Output (reconstructed sequence)
→ Reconstruction error > threshold → ANOMALY
```

## ข้อมูลที่น่าสนใจ

- ใช้ PT100 แทน DS18B20 เพราะ precision สูงกว่า (medical grade)
- FreeRTOS ช่วยแยก task sampling, inference, และ alert ออกจากกัน
- Model precision บน ESP32 (0.92) สูงกว่าบน desktop (0.86) — เพราะ quantization ช่วย generalize

## ผลลัพธ์เทียบกับ threshold-based

| วิธี | ข้อดี | ข้อเสีย |
|-----|-------|---------|
| Threshold-based | ง่าย, เร็ว | false alarm จาก noise, ตาม pattern ไม่ได้ |
| CAE (TinyML) | ตรวจ subtle pattern ได้ | ต้องมี training data, ซับซ้อนกว่า |

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มีความขัดแย้งกับ wiki ปัจจุบัน — เป็นข้อมูลใหม่

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/tinyml]] — เพิ่ม performance benchmark จากงานวิจัยจริง
- [[concepts/iot/cold-chain-monitoring]] — เพิ่ม AI approach
- [[entities/iot/ds18b20]] — กล่าวถึง PT100 เป็นทางเลือก precision สูงกว่า
