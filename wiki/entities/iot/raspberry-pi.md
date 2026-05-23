---
type: entity
category: device
tags: [raspberry-pi, linux, gateway, edge, server, mqtt, python, sbc]
sources: [raspberry-pi-iot-guide]
created: 2026-04-18
updated: 2026-04-19
---

# Raspberry Pi

**ผู้ผลิต**: Raspberry Pi Foundation (UK)
**ประเภท**: Single Board Computer (SBC) — Linux
**สถานะ**:
- ✅ **Pi 4B 4GB** — Production IoT server (Mosquitto + Node-RED + InfluxDB + Grafana)
- ✅ **Pi 5** — Bitcoin node (Umbrel OS) เปิด 24/7, RAM เหลือ → planned: Telegram AI agent

## ภาพรวม

Raspberry Pi เป็น credit-card-sized Linux computer ราคาถูก ทำงานได้ 24/7 ใช้ไฟต่ำ เหมาะมากสำหรับ self-hosted IoT server — รัน Mosquitto, Node-RED, InfluxDB, Grafana พร้อมกันบนเครื่องเดียว **ที่มีอยู่คือ Pi 4 RAM 4GB ซึ่ง overkill สำหรับ IoT stack — รัน Docker ได้สบาย**

## รุ่นที่มีและเปรียบเทียบ

| รุ่น | RAM | เหมาะกับ | สถานะ |
|------|-----|---------|-------|
| Pi Zero 2W | 512MB | Mosquitto broker เล็ก | — |
| Pi 3B+ | 1GB | MQTT + Node-RED | — |
| Pi 4 (2GB) | 2GB | MQTT + InfluxDB + Grafana | — |
| **Pi 4 (4GB)** | **4GB** | **IoT full stack** | **✅ มีแล้ว** |
| **Pi 5 (8GB)** | **8GB** | **Bitcoin node + AI agent + trading bot** | **✅ มีแล้ว** |

## บทบาทใน IoT

```
[ESP32-S3 Gateway]
        ↓ WiFi/MQTT
[Raspberry Pi]
  ├── Mosquitto broker   (port 1883)
  ├── Telegraf/Node-RED  (MQTT → DB)
  ├── InfluxDB/MySQL     (data storage)
  └── Grafana            (http://pi-ip:3000)
```

## ข้อดีสำหรับโปรเจ็คนี้

- **เปิดตลอด 24/7** ใช้ไฟแค่ 2-7W
- **IP ใน local network** — ESP32-S3 publish MQTT มาได้ตลอด
- **ยืดหยุ่น** — ลง software เพิ่มได้ง่าย (Docker รองรับ)
- **ถูกกว่า NAS** สำหรับ IoT server workload

## เปรียบเทียบ Mac (dev) vs Pi 4 (production)

| | Mac (dev) | **Pi 4 4GB (production)** |
|--|-----------|--------------------------|
| เปิดตลอด | ❌ | ✅ |
| ไฟฟ้า | 45-100W | 3-8W |
| ยืดหยุ่น | ❌ (ปิดเครื่อง) | ✅ 24/7 |
| Docker | ✅ | ✅ (ARM64) |
| RAM สำหรับ stack | เหลือเฟือ | 4GB — รัน Mosquitto+Node-RED+InfluxDB+Grafana ได้พร้อมกัน |

## Pi 4 4GB — Capacity Estimate

| Service | RAM ใช้ |
|---------|--------|
| Mosquitto | ~10MB |
| Node-RED | ~80MB |
| InfluxDB 2.x | ~200MB |
| Grafana | ~100MB |
| OS (Raspberry Pi OS Lite) | ~200MB |
| **รวม** | **~600MB จาก 4GB — เหลือ 85%** |

## Pi 5 — Bitcoin Node + Telegram AI Agent

Pi 5 รัน Umbrel OS (Docker-based) สำหรับ Bitcoin full node เปิด 24/7 และยัง **ทำ Telegram AI agent ได้พร้อมกัน** เพราะ bot ใช้แค่ HTTP call ไป API ภายนอก

### RAM Budget (Pi 5)

| Service | RAM ใช้ |
|---------|--------|
| Umbrel OS + Docker | ~200MB |
| Bitcoin Core (synced) | ~350-500MB |
| OS overhead | ~200MB |
| Telegram bot (Python + API) | ~100MB |
| Trading bot (Freqtrade) | ~300MB |
| Ollama 7B model | ~4,500MB |
| **รวม (ทุกอย่าง)** | **~5,650MB** |
| **เหลือ (จาก 8GB)** | **~2,350MB** ✅ สบาย |

### วิธีการทำงาน

```
[Telegram] ← user message
      ↓
[Pi 5: Python bot]
      ↓ HTTP request
[Claude API / OpenRouter / Gemini]
      ↓ response
[Telegram] → user
```

### ข้อดี/ข้อเสียแต่ละแนวทาง

| แนวทาง | RAM | ความเร็ว | ค่าใช้จ่าย | แนะนำ |
|--------|-----|---------|-----------|-------|
| **Claude/OpenAI API** | ~100MB | เร็ว (cloud) | มีค่า API | ✅ ดีสุด |
| **OpenRouter** | ~100MB | เร็ว | ยืดหยุ่น (หลาย model) | ✅ ดี |
| **Ollama 1-3B (local)** | 1-2GB | ปานกลาง (CPU) | ฟรี | ✅ พอใช้ได้ |
| **Ollama 7B (local)** | ~4.5GB | ช้า 1-3 tok/s | ฟรี | ⚠️ ช้า แต่รันได้ |

> **Pi 5 8GB**: รัน Bitcoin + Telegram bot + trading bot + Ollama 7B ได้พร้อมกัน RAM ยังเหลือ ~2GB

## Pi 5 — Storage Analysis (M.2 2TB SSD)

### ภาพรวมการใช้พื้นที่

| Service | ใช้ตอนนี้ | เติบโตต่อปี |
|---------|----------|-----------|
| **Bitcoin full node** | ~650-700GB | ~55-60GB/ปี |
| Umbrel OS + apps | ~20GB | น้อย |
| Ollama models (1-2 models) | ~5-10GB | ตามที่เพิ่ม |
| Freqtrade + historical data | ~5GB | ~1-2GB/ปี |
| OS + misc | ~20GB | น้อย |
| **Wiki (markdown files)** | **<50MB** | **<10MB/ปี** |
| **รวมตอนนี้** | **~700-755GB** | |
| **เหลือจาก 2TB** | **~1.25TB** ✅ | |

### Bitcoin คือตัวกินพื้นที่จริงๆ

```
2TB SSD
├── Bitcoin blockchain ~700GB ████████████░░░░░░░░  35%
├── อื่นๆ ทั้งหมด       ~60GB  ███░░░░░░░░░░░░░░░░░   3%
└── ว่าง               ~1.24TB ░░░░░░░░░░░░░░░░░░░  62%

อัตราเติบโต Bitcoin: ~60GB/ปี
→ 2TB จะเต็มใน: ~20 ปี (ถ้า growth rate คงที่)
```

### Wiki files — ไม่ใช่ปัญหาเลย

| ขนาด wiki | พื้นที่ใช้ |
|-----------|---------|
| 100 หน้า (ตอนนี้) | ~1MB |
| 1,000 หน้า | ~10MB |
| 10,000 หน้า | ~100MB |
| **แม้ขยาย 100x ก็ยังใช้ <100MB** | ✅ |

> Markdown text ไม่มีวันเป็นปัญหา storage — Bitcoin คือตัวจริงที่ต้องจับตา

| Framework | RAM | ความสามารถ | แนะนำ |
|-----------|-----|-----------|-------|
| **Freqtrade** | ~300MB | Strategy backtest, DCA, Telegram notify | ✅ ดีสุด |
| **Jesse** | ~200MB | Backtest เน้น, Python strategy | ✅ ดี |
| **ccxt + custom** | ~100MB | ยืดหยุ่นสูง เขียนเอง | ⚠️ ต้องเขียนเอง |
| **Hummingbot** | ~500MB | Market making, arbitrage | ⚠️ ซับซ้อน |

**Freqtrade** เหมาะสุดสำหรับ Pi 5: มี Telegram integration built-in, backtest ได้, รองรับ spot + futures, Docker image พร้อมใช้

> ⚠️ **คำเตือน**: Trading bot เกี่ยวข้องกับเงินจริง — ต้องมีกลยุทธ์ที่ backtest แล้ว, ตั้ง stop-loss, และใช้ API key ที่จำกัดสิทธิ์ (trade only, no withdrawal)

## ความสัมพันธ์

- รัน: [[entities/iot/mosquitto]], [[entities/iot/influxdb]], [[entities/iot/grafana]], [[entities/iot/node-red]]
- ต่อกับ: [[entities/iot/esp32-s3]] (ผ่าน WiFi/MQTT)
- เปรียบเทียบกับ: [[entities/iot/esp32-s3]] (Linux vs RTOS — คนละ use case)

## แหล่งข้อมูล

- [[sources/raspberry-pi-iot-guide]] — บทบาท RPi ใน IoT ecosystem
