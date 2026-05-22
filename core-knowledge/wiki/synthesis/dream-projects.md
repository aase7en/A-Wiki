---
type: synthesis
tags: [dream-projects, roadmap, iot, web-app, ai, home-server, hospital]
sources: []
created: 2026-04-29
updated: 2026-04-29 (AI cost strategy + Mac Mini AI server)
---

# Dream Projects — โปรเจกต์ในฝัน

> รวมทุกโปรเจกต์ที่วางแผน/กำลังทำ/อยากทำ จัดตาม category
> อัปเดตเมื่อเริ่ม/จบโปรเจกต์

**Legend**: 🔵 วางแผน | 🟡 กำลังทำ/มีข้อมูลแล้ว | ✅ เสร็จ | 💤 พัก

---

## 🏥 IoT โรงพยาบาล (งานหลัก)

| # | โปรเจกต์ | Hardware | Status | Wiki |
|---|----------|----------|--------|------|
| 1 | Monitor การใช้ไฟฟ้า | PZEM-004T + ESP32 | 🟡 มี synthesis + source | [[synthesis/energy-power-monitoring]] |
| 2 | ชั่งน้ำหนักขยะอัตโนมัติ | Load Cell + HX711 + ESP32 | 🟡 มี synthesis + source | [[synthesis/waste-weight-monitoring]] |
| 3 | Monitor การใช้น้ำ | Flow sensor + ESP32 | 🔵 ยังไม่มีข้อมูล | — |
| 4 | เช็คฝุ่น PM2.5 | PMS5003 + LoRa + ESP32 | 🟡 มี synthesis + source | [[synthesis/air-quality-monitoring]] |
| 5 | ระบบรดน้ำอัตโนมัติ | Soil sensor + relay + ESP32 | 🔵 ยังไม่มีข้อมูล | — |
| 6 | คำนวณ Carbon Footprint โรงพยาบาล | — (data integration) | 🔵 ต้องรอ data ข้ออื่นก่อน | — |
| 7 | Monitor อุณหภูมิ Vaccine/Cold chain | DS18B20 + TinyML | 🟡 มี synthesis | [[synthesis/cold-chain-vaccine]] |

**โครงสร้างระบบ**: ESP32 nodes → DX-LR02 LoRa → Raspberry Pi 4B gateway → MQTT → Grafana
ดู [[synthesis/iot-lora-architecture]] สำหรับ full architecture

---

## 💻 Software / Web App

| # | โปรเจกต์ | Stack | Status | หมายเหตุ |
|---|----------|-------|--------|---------|
| 1 | Bot เทรด Crypto/หุ้น | Freqtrade + Pi 5 | 🟡 มี source | [[sources/freqtrade-pi5]] |
| 2 | Web app บำบัดน้ำเสียประจำวัน | FastAPI + React + PostgreSQL | 🔵 อยู่ในแผน | แทน AppSheet เดิม |
| 3 | Web app สอบสวนโรค (Epidemiology) | FastAPI + React + PostgreSQL | 🔵 อยู่ในแผน | — |
| 4 | Migrate AppSheet → Web App | FastAPI + React + PostgreSQL + Pi 5 | 🔵 รอ Pi 5 setup | migrate ทั้งหมดในครั้งเดียว |

---

## 🤖 AI / Automation

| # | โปรเจกต์ | Stack | Status | Wiki |
|---|----------|-------|--------|------|
| 1 | Telegram AI Router | Python + OpenRouter + Pi 5 | 🟡 มี code skeleton | [[entities/ai-tools/telegram-ai-router]] |
| 2 | **Mac Mini — Personal AI Server** | Mac Mini + Ollama + MLX + LiteLLM | 🔵 อยู่ในแผน | [[sources/ollama-pi5]] |
| 3 | Wiki AI Bot (ถาม wiki ผ่าน Telegram) | Hermes Agent / Claude Code | 🟡 ออกแบบแล้ว | [[synthesis/dual-ai-workflow]] |
| 4 | Claude Code multi-model (OpenRouter) | LiteLLM proxy + OpenRouter | 💤 รอ Mac Mini | [[concepts/ai-tools/openrouter-claude-code]] |

> **AI Cost Strategy (decided 2026-04-29)**
> งานง่าย → Gemini CLI (ฟรี) | งานกลาง → OpenRouter free (ผ่าน tools อื่น) | งานซับซ้อน → Claude Pro subscription
> Pi 5 ไม่เหมาะทำ AI server เพราะ RAM ถูกใช้โดย Bitcoin node + webapp — ใช้ Mac Mini แทนในอนาคต

---

## 🖥️ Home Server

| # | โปรเจกต์ | Hardware | Status | Wiki |
|---|----------|----------|--------|------|
| 1 | Pi 4B เป็น LoRa Gateway + MQTT | Pi 4B 4GB + DX-LR02 | 🟡 ออกแบบแล้ว | [[synthesis/pi4-lora-gateway-server]] |
| 2 | Pi 5 — Bitcoin + Webapp Server | Pi 5 8GB + M.2 2TB (เหลือ ~340GB) | 🟡 Bitcoin รันอยู่ | [[sources/umbrel-pi5-setup]] |
| 3 | **Mac Mini — Personal AI Server** | Mac Mini (อนาคต) + Ollama + LiteLLM | 🔵 อยู่ในแผน | [[sources/ollama-pi5]] |

> **Pi 5 role (confirmed 2026-04-29)**: Bitcoin node + webapp server เท่านั้น — ไม่รัน LLM หนัก
> เหตุผล: RAM เหลือ ~6GB (Bitcoin กิน 1-2GB), storage เหลือ ~340GB ต้องเก็บสำหรับ webapp

---

## 🌱 ความสนใจระยะยาว (ยังไม่มีแผนชัด)

- [ ] Robotics / ระบบอัตโนมัติ
- [ ] EV / Solar Cell (พลังงานสะอาด)
- [ ] LoRaWAN scale-up (จาก LoRa P2P → network server เมื่อ node เยอะขึ้น)
- [ ] Mac Mini AI Server → LiteLLM proxy → approach $0 AI cost (เมื่อซื้อ Mac Mini)

---

## 📊 Summary

| Category | วางแผน 🔵 | กำลังทำ 🟡 | พัก 💤 | เสร็จ ✅ |
|----------|-----------|------------|--------|---------|
| IoT โรงพยาบาล | 3 | 4 | 0 | 0 |
| Software/Web App | 4 | 0 | 0 | 0 |
| AI/Automation | 2 | 2 | 1 | 0 |
| Home Server | 1 | 1 | 0 | 0 |
| **รวม** | **10** | **7** | **1** | **0** |

---

## ความสัมพันธ์
- [[synthesis/iot-lora-architecture]] — architecture หลักของ IoT hospital
- [[synthesis/dual-ai-workflow]] — workflow AI ที่ใช้อยู่
- [[entities/iot/raspberry-pi]] — hardware หลักของ home server
- [[profile.md]] — ข้อมูลส่วนตัว + goals
