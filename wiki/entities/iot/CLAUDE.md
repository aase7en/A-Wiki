> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — IoT Entities

> **โดเมน**: Internet of Things (IoT)
> **Last updated**: 2026-06-01
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน entities/iot/ เท่านั้น**

---

## Hardware ใน lab

| อุปกรณ์ | รุ่น | หมายเหตุ |
|---------|------|----------|
| MCU | ESP32 DevKit V1 (classic) | Dual-core Xtensa LX6, WiFi+BT |
| MCU | ESP32-S3 DevKit | USB OTG native, LX7, PIE SIMD |
| MCU | Arduino Uno R3 | ATmega328P, CH340 clone |
| LoRa module | DX-LR02-900T22D × 2 | ASR6601 SOC, 850-930 MHz, UART |
| USB-TTL | DX-SMART-TTL | CP2102, สำหรับ flash/debug |
| Battery | Vapcell M35 18650 × 2 | 3500mAh Li-ion |
| Battery shield | 18650 Battery Shield V3 | Boost 3.7V→5V + LDO 3.3V |

### Sensors

| Sensor | Protocol | การใช้งาน |
|--------|----------|----------|
| DHT11 | single-wire digital | อุณหภูมิ + ความชื้น (beginner) |
| DS18B20 × 3 | One-Wire | อุณหภูมิกันน้ำ, ต่อ bus เดียวกัน |
| HC-SR04 | Trigger/Echo | Ultrasonic distance, tank level |
| HC-SR501 | PIR digital | Motion detection |
| PMS5003 | UART 9600 | PM1.0/2.5/10 laser |
| PZEM-004T | UART Modbus RTU | AC power meter |
| HX711 + Load Cell | 24-bit ADC | Weight measurement |

---

## Standards & Protocols

- **LoRa**: P2P mode, 850.15 MHz, 1 MHz channel spacing, SF7-12
- **MQTT**: QoS 0 (default for sensor data), broker = Mosquitto
- **Logic level**: 3.3V (ESP32 native) — ต้อง level shift เมื่อใช้กับ 5V devices
- **WiFi**: ESP32 station mode, 2.4 GHz

---

## Rules สำหรับ entity pages

1. **frontmatter บังคับ**: `type`, `category`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **confidence markers** ทุกครั้งที่ตอบข้อมูลสำคัญ:
   - `[training]` — จาก training data (cutoff Aug 2025)
   - `[verified YYYY-MM-DD]` — ตรวจสอบผ่าน WebSearch/Gemini/WebFetch
   - `[wiki]` — จากหน้า wiki ที่มี source
3. **`last_verified`** + **`verify_tool`** ต้องมีสำหรับ entities ที่เป็น hardware (ราคา, version, สถานะ)
4. **Cross-reference**: ทุกหน้าต้องลิงก์ไปหาหน้าที่เกี่ยวข้อง
5. **ราคา/availability**: ข้อมูล time-sensitive → delegate เสมอ ห้ามเดา

---

## ความสัมพันธ์กับ domains อื่น

| Domain | ความเกี่ยวข้อง |
|--------|---------------|
| Environmental Health | IoT sensors ใช้วัดคุณภาพน้ำ/อากาศในระบบ Env |
| AI Tools | Claude Code/Agent frameworks สำหรับวิเคราะห์ IoT data |
| Pharmacy | IoT cold-chain monitoring สำหรับวัคซีน |

---

## หน้าที่มีอยู่แล้ว (35 entities)

```yaml
18650-battery-shield, arduino-ide, arduino-uno-r3, chirpstack, dht11,
ds18b20, dx-lr02-lora, dx-smart-ttl, emqx, esp-idf, esp32, esp32-s3,
grafana, hc-sr04, hc-sr501, home-assistant, hx711, influxdb, line-notify,
load-cell, mosquitto, mqtt-protocol, mysql, nb-iot, node-red, platformio,
pms5003, pzem-004t, raspberry-pi, rfm95-sx1276, telegram-bot,
the-things-network, vapcell-m35-18650
```

---

## สรุป workflow สำหรับ IoT entity

1. มี source ใหม่ → อ่าน source → ตรวจสอบ contradiction
2. สร้าง/อัปเดต entity page ตาม template ใน CLAUDE.md หลัก
3. เพิ่มใน `index-iot.md`
4. อัปเดต `wiki/context/wiki-overview.md` (รัน `python3 scripts/gen-index.py`)
5. บันทึกใน `log.md`