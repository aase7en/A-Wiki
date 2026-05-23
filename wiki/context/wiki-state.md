# Wiki State — Tier 1 Quick Load

> อ่านไฟล์นี้ก่อนเสมอ (~20 บรรทัด) ถ้าตอบได้จากที่นี่ → หยุด ไม่ต้องโหลดเพิ่ม
> ถ้าต้องการ abstracts → wiki-overview.md | relationships → knowledge-graph.md | รายละเอียด → full page

---

## Hardware Inventory

| สถานะ | อุปกรณ์ |
|-------|--------|
| ✅ มี | Pi 4B 4GB (IoT server: MQTT+Node-RED+InfluxDB+Grafana) |
| ✅ มี | Pi 5 **8GB** (Bitcoin node via Umbrel OS, 24/7) — RAM เหลือ ~7GB → Telegram AI agent + trading bot planned |
| ✅ มี | ESP32 DevKit V1, ESP32-S3-N16R8, Arduino Uno R3 |
| ✅ มี | DX-LR02 LoRa ×2, DHT11, HC-SR501, HC-SR04 |
| ✅ มี | 18650 Shield, Vapcell M35×2, DX-SMART TTL×2 |
| ❌ ขาด | PZEM-004T, Load Cell+HX711, DS18B20, PMS5003 |

---

## Domain Status

| Domain | Entities | Concepts | Sources | Synthesis | สถานะ |
|--------|----------|----------|---------|-----------|-------|
| IoT | 35 | 12 | 35+ | 10 | 🟢 Active |
| Env | 3 | 5 | 10+ | 1 | 🟡 Growing |
| AI Tools | 5 | 11 | 15+ | 7 | 🟢 Active |
| Pharmacy | 5 | 8 | 10+ | 6 | 🟢 Active |
| **รวม** | **48** | **38** | **70** | **24** | **~190 pages** |

*อัปเดต 2026-05-18 — auto-generated via `python3 scripts/gen-index.py`*

---

## Chosen Stack (ตัดสินใจแล้ว ✅)

```
Sensor → ESP32 → LoRa(DX-LR02) → ESP32-S3 → MQTT → Mosquitto(Pi4)
→ Node-RED → InfluxDB + MySQL → Grafana → Telegram Bot
```

---

## Active Projects

- **Sunday Estate Webapp** 🔥 — FastAPI + React + Supabase self-host บน Pi5. Production live at `http://umbrel.local:8090`. 4 TODOs: Cloudflare Tunnel, Pi5 redeploy ×2, SUPABASE_SECRET_KEY check → ดู [[synthesis/sunday-estate-webapp]]
- **IoT LoRa Architecture** — Phase 1: hardware test | ESP32 + DX-LR02
- **Pharmacy Web App** — FastAPI + React บน Pi5, drug validation + OCR → ดู [[synthesis/pharmacy-web-app-roadmap]]
- **Pi5 Projects** — planned: Telegram AI agent → Ollama local → Freqtrade trading bot

---

## Priority Stubs (สร้างต่อไป)

- 🔴 HIGH: `telegraf` entity
- 🟡 ENV: `wastewater-monitoring`, `indoor-air-quality`, `infectious-waste-entity`
- 🟡 PHARMACY: `sp-drugstore-entity` (entity สำหรับ supplier) + review fuzzy-match page
- 🟢 NORMAL: `esp32-deep-sleep`, `dht22`, `radiolib`, `scd41`
- 🟢 DONE: `chirpstack`, `emqx` — มีหน้าแล้ว

---

## Known Issues / Contradictions

- ⚠️ **Line Notify DEPRECATED** Mar 2025 → ใช้ Telegram แทน
- ⚠️ **DX-LR02 chip = LLCC68** ไม่ใช่ SX1276 — ต้องซื้อคู่ให้ตรง freq variant
- ⚠️ **Env sources** (2026-04-20) = web-search เท่านั้น ยังไม่ verify จาก PDF ต้นฉบับ

---

## Source Quality Legend

| สัญลักษณ์ | ความหมาย |
|----------|---------|
| ✅ verified | fetch จาก PDF / official page โดยตรง |
| ⚠️ web-search | ได้จาก search results เท่านั้น |
| 📐 design | หน้าวางแผน ยังไม่ implement |
| 🔴 stub | ยังไม่มีหน้าจริง |

---

*wiki-state v1.1 — created 2026-04-20 | updated 2026-05-18 | Tier 1 of 4-tier memory system*
