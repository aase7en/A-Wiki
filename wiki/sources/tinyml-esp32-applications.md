---
type: source
title: "6 Popular ESP32 AI Applications Using TinyML (DFRobot + TeachMeMicro)"
slug: tinyml-esp32-applications
date_ingested: 2026-04-18
original_file: https://www.dfrobot.com/blog-13902.html
tags: [tinyml, esp32, edge-ai, edge-impulse, tensorflow-lite, anomaly-detection, gesture]
---

# TinyML on ESP32 — Applications & Tutorial

**ประเภท**: blog article + tutorial  
**แหล่ง**: DFRobot Blog + TeachMeMicro

## ประเด็นหลัก

1. **TinyML คืออะไร**: ML บน microcontroller ทำให้ inference เกิดบนอุปกรณ์ ลด latency, ประหยัดพลังงาน, รักษา privacy
2. **6 Use Cases บน ESP32**: electronic nose, wildfire detection, gesture recognition, gesture classification, predictive maintenance, voice control
3. **Workflow**: Edge Impulse → train → export Arduino library → flash ESP32
4. **Framework**: TensorFlow Lite Micro + Edge Impulse (แนะนำสำหรับผู้เริ่มต้น)
5. **Deployment**: model แปลงเป็น `.tflite` → embed เป็น C array → รันผ่าน `MicroInterpreter`

## TinyML Workflow ทีละขั้น

```
1. เก็บ sensor data (บน ESP32 หรือ upload file)
2. อัปโหลดขึ้น Edge Impulse
3. ออกแบบ DSP pipeline (normalization, windowing)
4. Train Neural Network / Anomaly Detection model
5. Test accuracy บน browser
6. Export: "Arduino library" (.zip)
7. ติดตั้งใน Arduino IDE → flash ESP32
```

## Hardware ขั้นต่ำ

- **ESP32 classic**: รัน model เล็กๆ ได้ (< 200KB)
- **ESP32-S3** (แนะนำ): PSRAM 8MB รองรับ model ใหญ่กว่า + vector instructions เร็วกว่า

## Constraints ที่ต้องรู้

- RAM ใน ESP32 classic: ~320KB SRAM → model ต้องพอดี tensor arena
- ต้อง quantize เป็น int8 (ลด size ~4x, ลด accuracy เล็กน้อย)
- Training ยังต้องใช้ cloud/PC เสมอ

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/tinyml]] — สร้างใหม่
