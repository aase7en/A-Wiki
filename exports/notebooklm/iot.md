# Wiki Snapshot — iot domain

**Snapshot**: 2026-05-18T12:05:05Z
**Repo**: aase7en/aase7en-inw-wiki
**Commit**: 583ebc8
**Generator**: scripts/export-to-notebooklm.sh

> ใช้กับ NotebookLM Pro: upload ไฟล์นี้เป็น single source ใน notebook ของ domain iot
> สำหรับคำถามเชิงโครงสร้าง/อ้างอิง — ไม่ใช่ source-of-truth (ของจริงอยู่ใน wiki/ ของ repo)

---

## Domain Index

### `index-iot.md`

# IoT Domain Index

> ดัชนีเฉพาะ domain: Internet of Things — hardware, protocols, platforms, tools

## Entities (35)

### Hardware — Microcontrollers & SBCs
- [[entities/iot/esp32]] — ESP32 DevKit V1, WiFi+BT, ใช้งานหลัก
- [[entities/iot/esp32-s3]] — ESP32-S3 N16R8, gateway node
- [[entities/iot/esp32-c6]] — ESP32-C6, WiFi 6 + BLE 5 + Thread/Zigbee, Edge AI gateway
- [[entities/iot/arduino-uno-r3]] — Arduino Uno R3, AVR-based board
- [[entities/iot/raspberry-pi]] — Raspberry Pi 4B 4GB, MQTT broker + gateway server

### Hardware — Sensors
- [[entities/iot/dht11]] — Temperature & Humidity sensor
- [[entities/iot/ds18b20]] — DS18B20 Waterproof temperature sensor
- [[entities/iot/hc-sr04]] — Ultrasonic distance sensor
- [[entities/iot/hc-sr501]] — PIR motion sensor
- [[entities/iot/pms5003]] — PM2.5 air quality sensor
- [[entities/iot/pzem-004t]] — AC power meter (Modbus RTU)
- [[entities/iot/load-cell]] — Weight measurement
- [[entities/iot/hx711]] — Load cell amplifier

### Hardware — Radio & Communication
- [[entities/iot/dx-lr02-lora]] — LoRa UART module (LLCC68)
- [[entities/iot/dx-smart-ttl]] — USB-TTL converter
- [[entities/iot/rfm95-sx1276]] — LoRa SX1276 module
- [[entities/iot/nb-iot]] — NB-IoT module

### Hardware — Power
- [[entities/iot/18650-battery-shield]] — 18650 battery shield
- [[entities/iot/vapcell-m35-18650]] — Vapcell M35 18650 cells

### Software — Brokers & Databases
- [[entities/iot/mqtt-protocol]] — MQTT protocol: OASIS standard, publish-subscribe, broker roles, QoS levels
- [[entities/iot/mosquitto]] — Eclipse Mosquitto MQTT broker
- [[entities/iot/emqx]] — EMQX enterprise MQTT broker
- [[entities/iot/influxdb]] — InfluxDB time-series database
- [[entities/iot/mysql]] — MySQL relational database

### Software — Tools & Platforms
- [[entities/iot/node-red]] — Flow-based programming / automation
- [[entities/iot/grafana]] — Dashboard visualization
- [[entities/iot/home-assistant]] — Home automation platform
- [[entities/iot/telegram-bot]] — Telegram Bot API for alerts
- [[entities/iot/the-things-network]] — LoRaWAN network server (cloud)
- [[entities/iot/chirpstack]] — ChirpStack self-hosted LoRaWAN server
- [[entities/iot/line-notify]] — ⚠️ DEPRECATED Mar 2025 → ใช้ Telegram แทน

### Software — Dev Tools
- [[entities/iot/arduino-ide]] — Arduino IDE
- [[entities/iot/esp-idf]] — ESP-IDF framework
- [[entities/iot/platformio]] — PlatformIO IDE/build system

## Concepts (11)

### Protocols
- [[concepts/iot/publish-subscribe]] — Pub/Sub messaging pattern
- [[concepts/iot/mqtt-qos]] — MQTT Quality of Service levels
- [[concepts/iot/lora]] — LoRa modulation technology
- [[concepts/iot/lora-p2p]] — LoRa Point-to-Point (UART/AT command)
- [[concepts/iot/lorawan]] — LoRaWAN network protocol
- [[concepts/iot/modbus]] — Modbus RTU/TCP industrial protocol

### Data & Architecture
- [[concepts/iot/data-logger]] — Data logging patterns
- [[concepts/iot/dashboard-design]] — Dashboard design principles
- [[concepts/iot/tinyml]] — TinyML on-device machine learning

### Domain-Specific
- [[concepts/iot/air-quality-index]] — AQI standards and calculation
- [[concepts/iot/cold-chain-monitoring]] — Cold chain logistics monitoring


---

## Entities (iot)

### `wiki/entities/iot/18650-battery-shield.md`

---
type: entity
category: device
tags: [power, 18650, battery, boost-converter, portable]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# 18650 Battery Shield V3

**รุ่น**: 18650 Battery Shield V3 (V1045)  
**สถานะใน Lab**: ✅ มีอยู่ × 2  
**ใช้คู่กับ**: [[entities/iot/vapcell-m35-18650]]

## ภาพรวม

Battery shield สำหรับ 18650 cell 1 ก้อน แปลง 3.7V เป็น 5V (boost) และ 3.3V (LDO) พร้อม USB-A output สำหรับชาร์จ device อื่น มี Micro-USB สำหรับชาร์จ battery

## Specs หลัก

| Output | Voltage | Current | ใช้สำหรับ |
|--------|---------|---------|----------|
| 5V rail | 5V | **4A max** | ESP32 VIN, อุปกรณ์ USB |
| 3V rail | 3.3V | 1A max | MCU 3.3V โดยตรง |
| USB-A | 5V | 4A | ชาร์จ/power อุปกรณ์ภายนอก |

**Input**: Micro-USB (ชาร์จ 18650)

## การคำนวณ Battery Life

กับ [[entities/iot/vapcell-m35-18650]] (3500mAh):
- ESP32 WiFi active: ~150mA avg → ประมาณ **~20 ชั่วโมง** (3500/150 × efficiency 85%)
- ESP32 deep sleep: ~10µA → ถ้า duty cycle 1% active → ประมาณ **หลายร้อยชั่วโมง**
- ESP32 + DHT11 polling ทุก 30s: avg ~5mA → ประมาณ **~500 ชั่วโมง**

## ข้อควรระวัง

- 18650 slot เดียว — ถ้าต้องการ runtime นาน ต้องหา shield 2-slot แทน
- มี on/off switch — สำคัญสำหรับ deployment จริง
- "Becareful + and -" ที่ silkscreen เตือน orientation ของ battery

## ความสัมพันธ์

- ใช้คู่กับ: Vapcell INR18650 M35 (ยังไม่มีหน้า)
- Power ให้: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]]


---

### `wiki/entities/iot/CLAUDE.md`

> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — IoT Entities

> **โดเมน**: Internet of Things (IoT)  
> **Last updated**: 2026-05-09  
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

## หน้าที่มีอยู่แล้ว (32 entities)

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

---

### `wiki/entities/iot/arduino-ide.md`

---
type: entity
category: platform
tags: [arduino-ide, development-tool, esp32, programming, beginner]
sources: [arduino-ide-esp32-setup, esp32-complete-guide-thai, platformio-esp32-guide]
created: 2026-04-18
updated: 2026-04-18
---

# Arduino IDE

**ผู้พัฒนา**: Arduino LLC / Arduino AG
**License**: Open source
**เวอร์ชันแนะนำ**: 2.x (ใหม่กว่า, เร็วกว่า, autocomplete ดีกว่า)
**บทบาทในโปรเจ็ค**: IDE หลักสำหรับ flash firmware บน ESP32/ESP32-S3

## ภาพรวม

Arduino IDE เป็น IDE ที่ง่ายที่สุดสำหรับเขียนโปรแกรม MCU — รองรับ Arduino, ESP32, ESP8266 และอื่นๆ อีกมาก ผ่าน Board Manager ไม่ต้องตั้งค่าซับซ้อน ดาวน์โหลดแล้วใช้ได้เลย

## คุณสมบัติหลัก

- **Code Editor**: syntax highlighting, autocomplete (IDE 2.x)
- **Verify / Upload**: compile และ flash ผ่านปุ่มเดียว
- **Serial Monitor**: debug ผ่าน Serial.print() real-time
- **Serial Plotter**: graph sensor data ได้ทันที — ดี debug DHT11
- **Board Manager**: เพิ่ม ESP32, ESP8266 support
- **Library Manager**: ติดตั้ง library ง่าย (PubSubClient, DHT, LoRa ฯลฯ)

## เพิ่ม ESP32 Board Support

```
File → Preferences → Additional Boards Manager URLs:
https://espressif.github.io/arduino-esp32/package_esp32_index.json

Tools → Board → Boards Manager → ค้นหา "esp32" → Install "esp32 by Espressif Systems"
Tools → Board → ESP32 Arduino → ESP32 Dev Module  (สำหรับ ESP32 DevKit V1)
Tools → Board → ESP32 Arduino → ESP32S3 Dev Module (สำหรับ ESP32-S3)
```

## Arduino IDE vs PlatformIO

| หัวข้อ | Arduino IDE 2 | [[entities/iot/platformio]] |
|--------|--------------|---------|
| ง่ายสำหรับ beginner | ✅ มาก | ⬜ ต้องตั้งค่า |
| IntelliSense | ⬜ จำกัด | ✅ เต็มที่ |
| Dependency management | ⬜ manual | ✅ platformio.ini |
| เหมาะกับ | เรียนรู้, prototype | production, team |

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]], [[entities/iot/arduino-uno-r3]]
- ทางเลือก: [[entities/iot/platformio]], [[entities/iot/esp-idf]]

## แหล่งข้อมูล

- [[sources/arduino-ide-esp32-setup]] — ขั้นตอนติดตั้ง + ESP32 Board Manager
- [[sources/esp32-complete-guide-thai]] — Arduino IDE URL


---

### `wiki/entities/iot/arduino-uno-r3.md`

---
type: entity
category: device
tags: [arduino, microcontroller, avr, atmega328p, beginner]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# Arduino Uno R3 (CH340)

**ผู้ผลิต**: Arduino / Compatible (CH340 = Chinese clone)  
**รุ่นที่มีในแล็บ**: R3 CH340 (clone พร้อม Starter Kit)  
**สถานะใน Lab**: ✅ มีอยู่ × 1 (มาใน Starter Kit)

## ภาพรวม

Arduino Uno R3 เป็น development board คลาสสิกที่ใช้ ATmega328P (AVR 8-bit 16MHz) มาพร้อม ecosystem ขนาดใหญ่มาก รุ่น CH340 เป็น clone ที่ใช้ USB-to-Serial chip จีน (CH340G) แทน ATmega16U2 ของ official Arduino

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | ATmega328P 8-bit 16MHz |
| Flash | 32KB |
| SRAM | **2KB** |
| EEPROM | 1KB |
| GPIO | 14 digital, 6 analog |
| PWM | 6 pins |
| USB | CH340G (ต้องลง driver บาง OS) |
| Logic | **5V** |
| Power | 5V USB หรือ 7-12V VIN |

## ข้อจำกัดสำคัญ

- **2KB RAM เท่านั้น** — ไม่พอสำหรับ WiFi, JSON parsing, หรือ String operations ซับซ้อน
- ไม่มี WiFi/Bluetooth built-in — ต้องต่อ module แยก (ESP-01, nRF24L01)
- 5V logic — ต้องระวังถ้าต่อกับ 3.3V module (เช่น ESP32) ต้องใช้ level shifter
- ช้ากว่า ESP32 มาก (~16MHz vs 240MHz)

## บทบาทใน Lab นี้

Arduino Uno เหมาะสำหรับ:
- เรียนรู้ basics (มาพร้อม starter kit tutorial)
- ทดสอบ sensor ง่ายๆ ที่ไม่ต้องการ WiFi
- ควบคุม actuator แบบ standalone (relay, servo, stepper)

**ไม่เหมาะสำหรับ** โปรเจ็ค IoT ที่ต้องการ WiFi/MQTT — ใช้ [[entities/iot/esp32]] แทน

## ความสัมพันธ์

- แข่งขันกับ: [[entities/iot/esp32]] (แรงกว่ามาก, มี WiFi), [[entities/iot/esp32-s3]]
- Sensor ใน Kit: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มาพร้อม Arduino Starter Kit


---

### `wiki/entities/iot/chirpstack.md`

---
type: entity
category: project
tags: [lorawan, network-server, open-source, self-hosted, rak3172]
sources: [lorawan-fuota-rak3172, lorawan-network-beginner]
created: 2026-04-18
updated: 2026-04-18
---

# ChirpStack

**ประเภท**: LoRaWAN Network Server (Open Source)  
**ผู้พัฒนา**: Orne Brocaar / ChirpStack project  
**License**: MIT  
**เวอร์ชัน**: v4 (ปัจจุบัน)

## ภาพรวม

ChirpStack เป็น open-source LoRaWAN Network Server ที่ self-host ได้เอง เป็นทางเลือกแทน The Things Network (TTN) สำหรับผู้ที่ต้องการ control เต็มที่และไม่ต้องพึ่ง cloud ภายนอก รัน stack เต็มรูปแบบบน Raspberry Pi ได้

## Components

```
[LoRa Gateway] ──UDP──> [ChirpStack Gateway Bridge]
                                  ↓
                        [ChirpStack Network Server]
                                  ↓
                        [ChirpStack Application Server]
                                  ↓
                        [Dashboard / API / Webhook]
```

| Component | หน้าที่ |
|-----------|--------|
| Gateway Bridge | แปลง Semtech UDP protocol → MQTT |
| Network Server | จัดการ MAC layer, device activation, ADR |
| Application Server | decrypt payload, forward ไปยัง application |

## เปรียบเทียบกับ TTN

| หัวข้อ | ChirpStack | The Things Network |
|--------|-----------|-------------------|
| Hosting | Self-hosted | Cloud (TTN manages) |
| Privacy | เต็มที่ (data อยู่ที่เรา) | ข้อมูลผ่าน TTN server |
| Fair Use Policy | ไม่มี limit | 30 downlinks/day |
| Setup | ซับซ้อนกว่า | ง่ายกว่า |
| Cost | ฟรี (self-host) | ฟรี (community tier) |
| Suitable for | production, privacy-sensitive | prototype, learning |

## FUOTA Support

ChirpStack v4 รองรับ FUOTA (Firmware Update OTA) ผ่าน LoRaWAN Class C multicast ดู [[sources/lorawan-fuota-rak3172]] สำหรับ demo บน RAK3172

## ความสัมพันธ์

- ทำหน้าที่เป็น: Network Server ในสถาปัตยกรรม [[concepts/iot/lorawan]]
- แข่งขันกับ: [[entities/iot/the-things-network]] (cloud managed)
- ใช้ร่วมกับ: [[entities/iot/rfm95-sx1276]] (LoRa radio), [[entities/iot/raspberry-pi]] (host)

## แหล่งข้อมูล

- [[sources/lorawan-fuota-rak3172]] — FUOTA demo บน ChirpStack v4
- [[sources/lorawan-network-beginner]] — กล่าวถึง ChirpStack เป็น self-hosted option


---

### `wiki/entities/iot/dht11.md`

---
type: entity
category: device
tags: [sensor, temperature, humidity, dht11, digital, beginner]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# DHT11 Temperature & Humidity Sensor

**ผู้ผลิต**: Aosong (generic)  
**สถานะใน Lab**: ✅ มีอยู่ × 1 (ใน Starter Kit)

## ภาพรวม

DHT11 เป็น sensor วัดอุณหภูมิและความชื้นแบบ digital output ใช้ protocol เดียว (single-wire) ราคาถูกมาก เป็นตัวเลือกแรกสำหรับ beginner IoT project รวมถึงโปรเจ็ค temperature monitor ที่วางแผนไว้

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| Temperature range | 0–50°C |
| Temperature accuracy | **±2°C** |
| Humidity range | 20–90% RH |
| Humidity accuracy | **±5% RH** |
| Sampling rate | **1 ครั้ง/วินาที** (ช้ามาก) |
| Interface | Single-wire digital |
| Voltage | 3.3V–5.5V |
| Current | 0.3mA measuring, 60µA standby |

## ข้อจำกัด (สำคัญ)

- **±2°C accuracy** — ถ้าต้องการความแม่นยำสูงกว่านี้ ใช้ DHT22 (±0.5°C) หรือ SHT30 (±0.2°C)
- **อ่านได้แค่ทุก 1-2 วินาที** — ถ้า poll เร็วกว่านี้ sensor อาจ hang
- **ไม่รองรับ I2C/SPI** — ใช้ protocol เฉพาะของตัวเอง ต้องใช้ library

## Library สำหรับ ESP32

```cpp
#include <DHT.h>
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

float t = dht.readTemperature();
float h = dht.readHumidity();
```

## เปรียบเทียบกับรุ่นอื่น

| Sensor | Temp accuracy | RH accuracy | ราคา |
|--------|-------------|------------|------|
| **DHT11** | ±2°C | ±5% | ถูกสุด |
| DHT22 | ±0.5°C | ±2-5% | กลาง |
| SHT30 | ±0.2°C | ±2% | แพงกว่า |
| BME280 | ±1°C | ±3% | กลาง (มี pressure ด้วย) |

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]], [[entities/iot/arduino-uno-r3]]
- เหมาะสำหรับโปรเจ็ค: Temperature Monitor (เป้าหมายของ lab นี้)
- อัปเกรดได้เป็น: DHT22, SHT30, BME280 (ยังไม่มีหน้า)

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]]


---

### `wiki/entities/iot/ds18b20.md`

---
type: entity
category: device
tags: [sensor, temperature, one-wire, waterproof, ds18b20, cold-chain]
sources: [ds18b20-esp32-randomnerd, vaccine-temp-monitoring-iot, vaccine-cae-anomaly-detection]
created: 2026-04-18
updated: 2026-04-18
---

# DS18B20

**ผู้ผลิต**: Maxim Integrated (ปัจจุบัน: Analog Devices)  
**ประเภท**: Digital Temperature Sensor (1-Wire)  
**สถานะใน Lab**: ❌ ยังไม่มี (ต้องซื้อ)  
**ราคาประมาณ**: ~$1-3 (AliExpress), ~$5-8 รุ่น waterproof

## ภาพรวม

DS18B20 เป็น digital temperature sensor ที่ใช้ One-Wire protocol สื่อสารผ่านสายเพียงเส้นเดียว จุดเด่นคือ sensor หลายตัวสามารถต่อพ่วง bus เดียวกันได้โดยใช้ GPIO เพียง 1 ขา แต่ละตัวมี 64-bit unique ID ทำให้ระบุตัวได้ เหมาะมากสำหรับงาน cold chain และ multi-point temperature monitoring

## Specs หลัก

| คุณสมบัติ | ค่า |
|----------|-----|
| ช่วงอุณหภูมิ | -55°C ถึง +125°C |
| ความแม่นยำ | ±0.5°C (ที่ -10°C ถึง +85°C) |
| Resolution | 9–12 bit (configurable) |
| Protocol | 1-Wire (single data pin) |
| Supply | 3.0V–5.5V |
| Package | TO-92, SO8, หรือ waterproof probe |

## Wiring กับ ESP32

```
DS18B20 DATA  ──┬── GPIO 4 (หรือ GPIO 2)
                │
              4.7kΩ (pull-up)
                │
DS18B20 VCC  ──── 3.3V
DS18B20 GND  ──── GND
```

> **⚠️ ต้องมี 4.7kΩ pull-up resistor** ระหว่าง DATA และ VCC เสมอ ไม่งั้นอ่านค่าไม่ได้

## Multiple Sensors บน Bus เดียว

```
ESP32 GPIO4 ──┬── DS18B20 #1 (addr: 28:FF:AA...)
              ├── DS18B20 #2 (addr: 28:FF:BB...)
              └── DS18B20 #3 (addr: 28:FF:CC...)
                    (ทุกตัวแชร์ DATA line เดียวกัน)
```

## Libraries (Arduino IDE)

```
Sketch → Include Library → Manage Libraries
→ ติดตั้ง "OneWire" by Paul Stoffregen
→ ติดตั้ง "DallasTemperature" by Miles Burton
```

## Code ขั้นต่ำ

```cpp
#include <OneWire.h>
#include <DallasTemperature.h>

OneWire oneWire(4);           // GPIO 4
DallasTemperature sensors(&oneWire);

void setup() { sensors.begin(); }

void loop() {
  sensors.requestTemperatures();
  float temp = sensors.getTempCByIndex(0);
  // publish via MQTT...
}
```

## Use Case: ตู้แช่วัคซีน

WHO กำหนดอุณหภูมิวัคซีนที่ **+2°C ถึง +8°C** (cold chain standard)
- DS18B20 วัด range นี้ได้แม่นยำ ±0.5°C
- Multi-sensor: ติดหลายจุดในตู้ (บน/กลาง/ล่าง)
- Alert เมื่อออกนอก range → Telegram / SMS via GSM module
- บันทึก log ลง InfluxDB ทุก 5 นาที → Grafana

## AI Anomaly Detection (Advanced)

งานวิจัย Frontiers AI 2024 รัน **Convolutional Autoencoder (CAE)** บน ESP32 โดยตรง:
- ตรวจ pattern ผิดปกติได้โดยไม่ต้องตั้ง threshold
- Accuracy 92%, 50mW, 200ms per inference
- ใช้ PT100 + MAX31865 แทน DS18B20 สำหรับ precision สูงกว่า

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]] — อ่านผ่าน GPIO
- Concept: [[concepts/iot/cold-chain-monitoring]]
- Alert: [[entities/iot/telegram-bot]] — แจ้งเตือนอุณหภูมิ
- Storage: [[entities/iot/influxdb]], [[entities/iot/grafana]]
- เปรียบเทียบกับ: [[entities/iot/dht11]] — DS18B20 แม่นกว่าและ waterproof ได้

## แหล่งข้อมูล

- [[sources/ds18b20-esp32-randomnerd]] — wiring, libraries, multi-sensor
- [[sources/vaccine-temp-monitoring-iot]] — complete cold chain system
- [[sources/vaccine-cae-anomaly-detection]] — AI anomaly detection research


---

### `wiki/entities/iot/dx-lr02-lora.md`

---
type: entity
category: device
tags: [lora, 900mhz, uart, wireless, long-range, dx-smart, asr6601]
sources: [hardware-inventory-2026-04-18, dx-lr02-datasheet, dx-lr02-official-arduino-library, dx-lr02-module-spec-official, dx-lr02-serial-guide-v2]
created: 2026-04-18
updated: 2026-04-19
---

# DX-LR02-900T22D LoRa Module

**ผู้ผลิต**: DX-SMART (Shenzhen Daxia Longque Technology Co., Ltd.)
**รุ่น**: DX-LR02-900T22D (900MHz, 22dBm)
**Chip ภายใน**: **ASR6601** SOC (Arm China STAR-MC1) — ยืนยันจาก official spec
**สถานะใน Lab**: ✅ มีอยู่ × **2** พร้อมเสาอากาศ SMA

> ⚠️ **แก้ไขข้อมูลเดิม**: source บทความ third-party ระบุ LLCC68 แต่ official PDF ยืนยันชัดว่าเป็น **ASR6601** — ดู [[sources/dx-lr02-module-spec-official]]

> ⚠️ **Safety**: ต้องต่อเสาอากาศก่อนจ่ายไฟเสมอ — ถ้าไม่มีเสา RF power ไม่ระบาย → วงจรภายในพัง

## ภาพรวม

DX-LR02 เป็น UART LoRa transceiver module ใช้ ASR6601 SOC (Sub-1GHz LoRa + Arm China STAR-MC1 processor) สื่อสารกับ MCU ผ่าน LPUART/UART TTL มาพร้อม antenna SMA connector ทำงานที่ 900MHz band ระยะไกลสูงสุด 8km (LOS)

## Specs หลัก (Official)

| Parameter | Value |
|-----------|-------|
| Chip | **ASR6601** (Arm China STAR-MC1, 48MHz) |
| Module size | 19.0 × 16.5 × 2.4 mm |
| Frequency | **850–930 MHz** (รุ่นในแล็บ) |
| TX power | 0–**+22 dBm** |
| Sensitivity | **-138 dBm** |
| Operating voltage | **3.3V–5.5V** |
| Range (LOS) | **~8 km** |
| Range (Urban) | **~3.8 km** |
| Op. temperature | -40 to +85 °C |
| Interfaces | LPUART, UART, I2C, SSP, ADC |

## Power Consumption

| Mode | State | Current |
|------|-------|---------|
| Sleep | Standby | **59.15 µA** |
| Air Wake-Up | Standby | 4.63 mA |
| Air Wake-Up | Receive | 6.7 mA |
| High Efficiency | Standby | 9.71 mA |
| High Efficiency | **Transmit** | **53.5 mA** |
| High Efficiency | Receive | 9.53 mA |

## ⚠️ ซื้อให้ถูกรุ่น

DX-LR02 มี **2 frequency versions** — ต้องซื้อคู่ที่ตรงกัน:
- **850-930 MHz** (รุ่นที่มีในแล็บ ✅)
- **430-475 MHz**

## Pin Definition

| Pin | Name | Function |
|-----|------|---------|
| 1 | M0 | Mode select / Customizable IO |
| 2 | M1 | Mode select / Customizable IO |
| 3 | UART_RX | Serial data input |
| 4 | UART_TX | Serial data output |
| 5 | AUX | RF status indicator |
| 6 | VCC | Power (3.3–5.5V) |
| 7 | GND | Ground |

## AUX Pin

- **HIGH** = กำลัง TX/RX หรือ switching mode → รอ
- **LOW** = พร้อมรับส่ง (idle/done)
- AUX จะ HIGH **ล่วงหน้า 2-3ms** ก่อนส่งข้อมูลให้ MCU — ใช้ interrupt ได้

```cpp
// ตัวอย่าง: รอ AUX = LOW ก่อนส่ง
while (digitalRead(AUX_PIN) == HIGH) delay(1);
Serial2.write(data, len);
```

## Default Settings

| Parameter | Default |
|-----------|---------|
| Baud rate | **9600 bps** |
| Air rate | **LEVEL2** = 2148 bps |
| Frequency | **Channel 41** = 915.15 MHz |
| TX power | 22 dBm |
| Mode | Transparent (MODE0) |
| Address | ff,ff |
| Encryption key | **12345** (ON by default) |

## AT Commands (สำคัญ)

```
+++              เข้า AT mode (ออกด้วย +++ อีกครั้ง)
AT               Test
AT+RESET         Restart (จำเป็นหลังเปลี่ยน config)
AT+DEFAULT       Factory reset
AT+HELP          Query all settings

AT+BAUD3         Set 9600 bps (default)
AT+LEVEL2        Set air rate LEVEL2 (default, 2148 bps)
AT+MODE0         Transparent mode
AT+CHANNEL41     Channel 41 = 915.15 MHz (default)
AT+SLEEP2        High Efficiency mode (default)
AT+POWE22        Max TX power 22 dBm
```

## LEVEL (Air Rate) เลือกตามระยะ

| LEVEL | Air Rate | Range LOS |
|-------|----------|-----------|
| 0 | 336 bps | **8.0 km** (max range) |
| **2** | **2148 bps** | — (default) |
| 5 | 18229 bps | 2.4 km |
| 7 | 62500 bps | — (max speed) |

## การต่อสาย (ESP32)

```
ESP32          DX-LR02
──────────────────────────
GPIO (any) --> M0
GPIO (any) --> M1
TX2 (GPIO17) --> RXD
RX2 (GPIO16) --> TXD
GPIO (any) <-- AUX
3.3V/5V     --> VCC
GND         --> GND
```

## Official Arduino Library

```cpp
LoRaModule lora(rxPin, txPin); // baud=9600 default
lora.setExpect(pong, sizeof(pong));
lora.onTxDone(cb);
lora.onRxDone(cb);
lora.onRxTimeout(cb);
lora.send(buf, len);
lora.poll(); // ต้องเรียกใน loop()
```

> บน ESP32 ให้แทน `SoftwareSerial` ด้วย `HardwareSerial Serial2`

## ความสัมพันธ์

- ใช้งาน concept: [[concepts/iot/lora]], [[concepts/iot/lora-p2p]]
- ต่อกับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]
- เปรียบเทียบ chip: [[entities/iot/rfm95-sx1276]] (SX1276 = Semtech, ใช้ SPI)

## แหล่งข้อมูล

- [[sources/dx-lr02-module-spec-official]] — Official spec v1.1 (2024-06-19), ยืนยัน ASR6601, range, power
- [[sources/dx-lr02-serial-guide-v2]] — Official AT guide v2.0 (2025-11-17), command ครบชุด, LEVEL table
- [[sources/dx-lr02-official-arduino-library]] — Official Arduino library + PingPong example
- [[sources/dx-lr02-datasheet]] — ⚠️ third-party article, ระบุ LLCC68 ซึ่งไม่ถูกต้อง
- [[sources/hardware-inventory-2026-04-18]] — รูป 2 ตัวต่อกับ ESP32 กำลัง test


---

### `wiki/entities/iot/dx-smart-ttl.md`

---
type: entity
category: device
tags: [usb, ttl, serial, uart, flash-tool, ch340, type-c]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# DX-SMART USB-C to TTL (DX-PJ15-V1.1)

**ผู้ผลิต**: DX-SMART  
**รุ่น**: DX-PJ15-V1.1  
**สถานะใน Lab**: ✅ มีอยู่ × 2  
**Connector**: USB Type-C (host) → TTL header pins

## ภาพรวม

USB-to-TTL serial converter สำหรับ flash firmware และ debug serial กับ microcontroller ใช้งานง่าย เสียบ USB-C กับคอมพิวเตอร์ ฝั่ง TTL ต่อกับ TX/RX ของ MCU

## Pinout

| Pin | หน้าที่ |
|-----|--------|
| TX | ส่งจาก converter → RX ของ MCU |
| RX | รับจาก TX ของ MCU |
| NC | No connect |
| GND | Ground |
| 5V | จ่ายไฟ 5V ให้ MCU (ถ้าต้องการ) |
| 3V3 | จ่ายไฟ 3.3V ให้ MCU (ถ้าต้องการ) |
| GND | Ground (เพิ่ม) |

## การใช้งานใน IoT

ใช้หลักในสองกรณี:
1. **Flash firmware** — สำหรับ MCU ที่ไม่มี USB native เช่น ESP32 DevKit V1 (ต้องการ CH340 หรือ CP2102 บน board)
2. **Serial debug** — monitor Serial output จาก MCU ขณะ runtime

> **หมายเหตุ**: [[entities/iot/esp32-s3]] ไม่ต้องใช้ converter นี้ เพราะมี USB OTG native — flash ผ่าน USB-C ได้ตรงเลย

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]] — flash ผ่าน UART
- ไม่จำเป็นสำหรับ: [[entities/iot/esp32-s3]] — มี USB native

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 2, ใช้สำหรับ flash/debug serial


---

### `wiki/entities/iot/emqx.md`

---
type: entity
category: project
tags: [mqtt, broker, enterprise, open-source, high-scale]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# EMQX

**ประเภท**: MQTT Broker (Open Source / Enterprise)  
**ผู้พัฒนา**: EMQ Technologies  
**License**: Apache 2.0 (Community), Commercial (Enterprise)  
**เวอร์ชัน MQTT**: 3.1, 3.1.1, 5.0

## ภาพรวม

EMQX เป็น MQTT broker ที่ออกแบบมาสำหรับ scale ขนาดใหญ่ อ้างว่ารองรับ **100 ล้าน concurrent connections** บน cluster เดียว เหมาะสำหรับ production IoT platform ที่มี device จำนวนมาก ต่างจาก Mosquitto ที่เน้น lightweight สำหรับ edge

## คุณสมบัติหลัก

- Clustered deployment — horizontal scale ได้
- Built-in dashboard และ REST API สำหรับ management
- Rule Engine — route messages ไปยัง database/webhook ได้โดยตรง
- รองรับ MQTT over WebSocket, TLS, QUIC (enterprise)
- Authentication: username/password, JWT, X.509 certificates, LDAP

## การใช้งานใน IoT

เหมาะสำหรับ:
- Production platform ที่มี > 10,000 concurrent devices
- ระบบที่ต้องการ built-in monitoring และ management UI
- Integration กับ databases (MySQL, InfluxDB, Kafka) ผ่าน Rule Engine

ไม่จำเป็นสำหรับ:
- Home lab หรือโปรเจ็คส่วนตัวที่มีอุปกรณ์ไม่กี่ตัว — ใช้ Mosquitto แทน

## ความสัมพันธ์

- แข่งขันกับ: [[entities/iot/mosquitto]] (lightweight, edge), HiveMQ (enterprise)
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- ใช้ร่วมกับ: [[entities/iot/node-red]], [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/mqtt-introduction]] — กล่าวถึง EMQX ในฐานะ high-scale broker (100M connections claim)


---

### `wiki/entities/iot/esp-idf.md`

---
type: entity
category: platform
tags: [esp-idf, espressif, cmake, freertos, c-programming, advanced, native]
sources: [esp-idf-docs]
created: 2026-04-18
updated: 2026-04-18
---

# ESP-IDF (Espressif IoT Development Framework)

**ผู้พัฒนา**: Espressif Systems
**License**: Apache 2.0
**เวอร์ชันปัจจุบัน**: v6.0 (stable) — v4.4 เป็น EOL แล้ว
**บทบาทในโปรเจ็ค**: Advanced option (ไม่จำเป็นสำหรับโปรเจ็คปัจจุบัน)

## ภาพรวม

ESP-IDF คือ official framework ของ Espressif สำหรับพัฒนา firmware บน ESP32 ทุกรุ่น ใช้ CMake build system และเปิดเผย FreeRTOS API โดยตรง ให้ control ระดับต่ำกว่า Arduino framework มาก

## เมื่อไหร่ควรเปลี่ยนจาก Arduino → ESP-IDF

Arduino framework เพียงพอสำหรับโปรเจ็คส่วนใหญ่ แต่ ESP-IDF จำเป็นเมื่อ:
- ต้องการ FreeRTOS tasks หลายตัว (เช่น LoRa receive task + MQTT publish task ต่างหาก)
- Deep sleep ละเอียด (ULP coprocessor, custom wake stub)
- OTA firmware update ผ่าน partition table ที่กำหนดเอง
- Production code ที่ต้องการ stability สูงสุด
- Ethernet, USB HID/CDC custom profiles

## ESP-IDF vs Arduino

| หัวข้อ | Arduino | ESP-IDF |
|--------|---------|---------|
| Language | C++ (simplified) | C/C++ |
| Build | Arduino IDE / PlatformIO | CMake + idf.py |
| FreeRTOS | ซ่อน | เปิดเผย API |
| Abstraction | สูง (ง่าย) | ต่ำ (control) |
| เหมาะกับ | Maker, prototype | Production, advanced |

## SoC Compatibility

รองรับ: ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-C6, ESP32-H2
ไม่รองรับ: ESP8266 (ใช้ ESP8266 RTOS SDK แยก)

## ความสัมพันธ์

- ทางเลือก (ง่ายกว่า): [[entities/iot/arduino-ide]], [[entities/iot/platformio]]
- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/esp-idf-docs]] — official docs + GitHub repo


---

### `wiki/entities/iot/esp32-c6.md`

---
type: entity
category: device
tags: [esp32-c6, microcontroller, wifi6, ble5, thread, zigbee, espressif, edge-ai, iot-core]
sources: [iot-edge-ai-esp32-c6-2026]
created: 2026-05-13
updated: 2026-05-13
last_verified: 2026-05-13
verify_tool: training
---

# ESP32-C6

**ผู้ผลิต**: Espressif Systems  
**สถานะใน Lab**: ❌ ยังไม่มีในแล็บ (reference only)

## ภาพรวม

ESP32-C6 เป็น MCU จาก Espressif ที่ออกแบบมาเพื่อการเชื่อมต่อไร้สายสมัยใหม่ เป็นรุ่นแรกในตระกูล ESP32 ที่รองรับ **WiFi 6 (802.11ax)**, **BLE 5.0**, และ **Thread/Zigbee (IEEE 802.15.4)** ในชิปเดียว ใช้ CPU RISC-V single-core แทน Xtensa [training]

## Specs หลัก [training]

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | RISC-V single-core 160MHz |
| RAM | 512KB SRAM |
| Flash | 4MB (มาตรฐาน) |
| WiFi | **802.11ax (WiFi 6)** 2.4GHz |
| Bluetooth | **BLE 5.0** |
| Sub-GHz | **Thread / Zigbee** (IEEE 802.15.4) |
| GPIO | 30 pins |
| ADC | 7ch 12-bit |
| Logic level | 3.3V |
| Deep sleep current | ~5µA |

## จุดเด่นเทียบกับ ESP32 classic

| ด้าน | ESP32 classic | ESP32-C6 |
|------|--------------|----------|
| WiFi standard | 802.11 b/g/n | **802.11ax (WiFi 6)** |
| Bluetooth | BT 4.2 + BLE | **BLE 5.0 เท่านั้น** |
| Thread/Zigbee | ❌ | ✅ IEEE 802.15.4 |
| CPU | Xtensa LX6 dual-core | RISC-V single-core |
| ML workload | ปานกลาง | ปานกลาง (ไม่มี PSRAM) |
| ราคา | ถูก | ใกล้เคียงกัน |

## การใช้งานใน IoT

- **Smart Home gateway**: รองรับ Matter/Thread ทำให้ควบคุมอุปกรณ์ Matter-compatible ได้โดยตรง
- **Edge AI gateway**: รับข้อมูลจาก LoRa sensor nodes → วิเคราะห์ด้วย TinyML on-device → สั่ง actuator
- **Smart Farm**: เป็น gateway กลาง รับ soil moisture ผ่าน LoRa → Edge AI ตัดสินใจ → เปิด Relay วาล์วน้ำ → แจ้งเตือนผ่าน WiFi 6
- **WiFi 6 environment**: เหมาะกับสภาพแวดล้อมที่มี congestion (กล้องวงจรปิด, อุปกรณ์หลายชิ้น) เพราะ OFDMA ลด interference

## TinyML บน ESP32-C6

แม้จะไม่มี PSRAM เหมือน ESP32-S3 แต่ ESP32-C6 รัน TinyML สำหรับงานเบาได้:
- Anomaly detection บนข้อมูล sensor (vibration, temperature pattern)
- Keyword spotting แบบเบา
- Classification จากค่า sensor ไม่กี่ channel

สำหรับ model ขนาดใหญ่กว่า → แนะนำ [[entities/iot/esp32-s3]] (8MB PSRAM)

## ความสัมพันธ์

- รุ่นพี่น้อง: [[entities/iot/esp32]] (classic), [[entities/iot/esp32-s3]] (ML workload สูง)
- Thread/Zigbee ecosystem: Matter standard (cross-platform IoT)
- ใช้ร่วมกับ: [[entities/iot/dx-lr02-lora]] (LoRa gateway), [[entities/iot/mqtt-protocol]]
- ML on-device: [[concepts/iot/tinyml]]
- Use case: Smart Farm ด้วย LoRa + Edge AI

## แหล่งข้อมูล

- [[sources/iot-edge-ai-esp32-c6-2026]] — overview architecture + Smart Farm example
- [Espressif official](https://www.espressif.com/en/products/socs/esp32-c6) — product page


---

### `wiki/entities/iot/esp32-s3.md`

---
type: entity
category: device
tags: [esp32-s3, microcontroller, wifi, bluetooth, espressif, usb-native, ai]
sources: [hardware-inventory-2026-04-18, esp32-s3-intro-thai]
created: 2026-04-18
updated: 2026-04-18
---

# ESP32-S3-N16R8

**ผู้ผลิต**: Espressif Systems  
**รุ่นที่มีในแล็บ**: ESP32-S3-N16R8 WROOM + Terminal Breakout (green PCB, 25.50mm width)  
**สถานะใน Lab**: ✅ มีอยู่ × 1

## ภาพรวม

ESP32-S3 เป็น MCU ที่แรงที่สุดใน lab นี้ มี USB OTG native (ไม่ต้องใช้ CH340/CP2102) และ vector instruction สำหรับ AI/ML inference บน edge รุ่น N16R8 หมายถึง 16MB Flash + 8MB PSRAM ซึ่งมากพอสำหรับงาน TinyML หรือ image processing เบาๆ

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | Xtensa LX7 dual-core 240MHz |
| RAM | 512KB SRAM + **8MB PSRAM (SPIRAM)** |
| Flash | **16MB** |
| WiFi | 802.11 b/g/n 2.4GHz |
| Bluetooth | BLE 5.0 (ไม่มี Classic BT) |
| USB | **Native USB OTG** (ไม่ต้องใช้ USB-to-Serial chip) |
| GPIO | 45 pins |
| AI acceleration | vector instructions สำหรับ neural net |

## ข้อดีเหนือ ESP32 Classic

| | ESP32 | ESP32-S3 |
|-|-------|---------|
| CPU | LX6 240MHz | LX7 240MHz (เร็วกว่า ~40%) |
| PSRAM | ไม่มี (บางรุ่นมี 4MB) | **8MB** |
| Flash | 4MB | **16MB** |
| USB | ต้องใช้ CH340 | **Native USB** |
| BLE | 4.2 | **5.0** |
| AI | ไม่มี | vector instructions |

## การใช้งานใน IoT

- งานที่ต้องการ RAM มาก: web server, JSON parsing, image buffer
- TinyML: รันโมเดล เช่น keyword detection, anomaly detection
- USB device: appear as HID, CDC, MSC โดยไม่ต้องใช้ chip แปลง
- Firmware flash: ใช้ USB native โดยตรง (ไม่ต้องใช้ [[entities/iot/dx-smart-ttl]])

## ข้อควรระวัง

- USB native ใช้ GPIO19/20 — ห้ามใช้ GPIO นี้เป็น IO ปกติถ้า flash ผ่าน USB
- BLE 5.0 แต่ **ไม่มี Classic Bluetooth** — ถ้าต้องการ audio หรือ SPP ต้องใช้ ESP32 classic
- PSRAM ใช้ SPI bus ร่วม — อาจกระทบ throughput ถ้าใช้ SPI peripheral พร้อมกัน

## ความสัมพันธ์

- รุ่นเก่ากว่า: [[entities/iot/esp32]]
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- Sensor ที่ใช้ร่วมได้: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]

## Chip Variants (ชื่อ decode)

N16R8 = **N**OR Flash 16MB + **R**AM (PSRAM) 8MB

| Part | Flash | PSRAM |
|------|-------|-------|
| ESP32-S3 | external | — |
| ESP32-S3R8 | external | 8MB |
| ESP32-S3FN8 | 8MB built-in | — |
| **ESP32-S3-N16R8** (ใน lab) | **16MB** | **8MB** |

## Development Environment

เหมือนกับ ESP32 classic — ใช้ Arduino IDE ผ่าน Board Manager เดียวกัน
Board: `ESP32S3 Dev Module`
ตั้งค่าเพิ่ม: Flash Size = 16MB, PSRAM = OPI PSRAM

## ความสัมพันธ์

- รุ่นเก่ากว่า: [[entities/iot/esp32]]
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- Sensor ที่ใช้ร่วมได้: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]
- IDE: [[entities/iot/arduino-ide]], [[entities/iot/platformio]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 1 พร้อม terminal breakout สีเขียว
- [[sources/esp32-s3-intro-thai]] — specs ละเอียด, LX7, PIE, chip variants


---

### `wiki/entities/iot/esp32.md`

---
type: entity
category: device
tags: [esp32, microcontroller, wifi, bluetooth, espressif, iot-core]
sources: [hardware-inventory-2026-04-18, mqtt-introduction, esp32-complete-guide-thai, arduino-ide-esp32-setup]
created: 2026-04-18
updated: 2026-04-18
---

# ESP32 DevKit V1

**ผู้ผลิต**: Espressif Systems  
**รุ่นที่มีในแล็บ**: ESP32 DevKit V1 + Terminal Breakout Board  
**สถานะใน Lab**: ✅ มีอยู่ × 1

## ภาพรวม

ESP32 เป็น dual-core 32-bit MCU ที่ได้รับความนิยมสูงสุดใน IoT โลก มี WiFi 802.11 b/g/n และ Bluetooth 4.2/BLE built-in ในราคาถูก Espressif ออกแบบมาเพื่อ replace ESP8266 โดยเพิ่ม CPU cores, GPIO, และ peripheral

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | Xtensa LX6 dual-core 240MHz |
| RAM | 520KB SRAM |
| Flash | 4MB (DevKit V1 ทั่วไป) |
| WiFi | 802.11 b/g/n 2.4GHz |
| Bluetooth | Classic BT 4.2 + BLE |
| GPIO | 34 pins |
| ADC | 18ch 12-bit |
| DAC | 2ch 8-bit |
| UART/SPI/I2C | 3/4/2 ตามลำดับ |
| Power | 3.3V (VIN 5V ผ่าน AMS1117) |
| Deep sleep current | ~10µA |

## Terminal Breakout Board

ESP32 ในแล็บนี้มาพร้อม breakout board ที่มี screw terminal ทุก pin — ทำให้ต่อสายได้โดยไม่ต้องบัดกรี เหมาะมากสำหรับ prototyping ระยะยาว

## การใช้งานใน IoT

- **WiFi node**: ส่งข้อมูล sensor ผ่าน MQTT หรือ HTTP REST
- **BLE beacon**: advertising ข้อมูลแบบ passive
- **LoRa gateway**: จับคู่กับ [[entities/iot/dx-lr02-lora]] ผ่าน UART
- **MQTT client**: ใช้ library `PubSubClient` หรือ `AsyncMqttClient`

## ข้อจำกัด

- ADC บน ESP32 classic มี non-linearity ที่ voltage สูง (>3V) — ใช้ ADC1 ดีกว่า ADC2 เมื่อใช้ WiFi
- GPIO 34-39 เป็น input-only
- ใช้ 3.3V logic ทุก pin (ห้ามต่อ 5V signal โดยตรง)

## โปรเจ็คที่วางแผน

- Temperature monitor ด้วย [[entities/iot/dht11]] → MQTT → Dashboard
- LoRa node ด้วย [[entities/iot/dx-lr02-lora]]

## Development Environment

| IDE/Framework | เหมาะกับ | Board Manager URL |
|--------------|---------|-----------------|
| [[entities/iot/arduino-ide]] | เริ่มต้น, prototype | `https://espressif.github.io/arduino-esp32/package_esp32_index.json` |
| [[entities/iot/platformio]] | professional, team | auto-detect จาก platformio.ini |
| [[entities/iot/esp-idf]] | production, advanced | idf.py install |

**แนะนำ: Arduino IDE 2.x** สำหรับโปรเจ็คนี้ (Phase 1-4 ทั้งหมด)

## ความสัมพันธ์

- รุ่นพี่/น้อง: [[entities/iot/esp32-s3]] (แรงกว่า, ML), [[entities/iot/esp32-c6]] (WiFi 6 + Thread/Zigbee), ESP8266 (รุ่นเก่า)
- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- Sensor ที่ใช้ร่วม: [[entities/iot/dht11]], [[entities/iot/hc-sr501]]
- ใช้ร่วมกับ: [[entities/iot/dx-lr02-lora]], [[entities/iot/mosquitto]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 1 พร้อม terminal breakout
- [[sources/mqtt-introduction]] — กล่าวถึง ESP32 เป็น MQTT client platform
- [[sources/esp32-complete-guide-thai]] — specs ครบ, features overview
- [[sources/arduino-ide-esp32-setup]] — Board Manager URL, setup guide


---

### `wiki/entities/iot/grafana.md`

---
type: entity
category: platform
tags: [grafana, dashboard, visualization, time-series, open-source]
sources: [iot-lora-gateway-architecture, iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# Grafana

**ผู้พัฒนา**: Grafana Labs  
**License**: AGPL v3 (self-hosted ฟรี)  
**บทบาทในโปรเจ็ค**: Dashboard กราฟอุณหภูมิย้อนหลัง  
**สถานะ**: 🔲 ยังไม่ได้ติดตั้ง

## ภาพรวม

Grafana เป็น visualization platform ที่ดีที่สุดสำหรับ time-series data ใช้คู่กับ [[entities/iot/influxdb]] เป็น data source มาตรฐาน IoT: Grafana query InfluxDB แสดงกราฟ real-time และย้อนหลัง

## Architecture ในโปรเจ็คนี้

```
MQTT Broker (Mosquitto)
       ↓
  Telegraf (bridge)   ← subscribe MQTT topics
       ↓
  InfluxDB            ← เก็บ time-series data
       ↓
  Grafana             ← query และแสดงกราฟ
```

หรือ alternative (ไม่ใช้ Telegraf):
```
Python script → subscribe MQTT → write to InfluxDB → Grafana
```

## การติดตั้ง (Docker Compose แนะนำ)

```yaml
version: '3'
services:
  influxdb:
    image: influxdb:2.7
    ports: ["8086:8086"]
    volumes: ["influxdb-data:/var/lib/influxdb2"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    depends_on: [influxdb]

volumes:
  influxdb-data:
```

## Dashboard สำหรับ Temperature Monitor

Panel ที่แนะนำสร้าง:
1. **Gauge** — อุณหภูมิปัจจุบัน (real-time)
2. **Time series graph** — ย้อนหลัง 24 ชั่วโมง
3. **Alert rule** — trigger เมื่ออุณหภูมิ > threshold → ส่ง Telegram

## Data Sources ที่รองรับ

Grafana รองรับ data source หลายแบบ — เลือกตาม stack ที่ใช้:

| Data Source | Stack | เหมาะกับ |
|-------------|-------|---------|
| InfluxDB | Telegraf → InfluxDB → Grafana | time-series sensor, production |
| MySQL | Node-RED → MySQL → Grafana | Data Logger ทั่วไป, lab |
| PostgreSQL | - | relational + time-series |

## ความสัมพันธ์

- Data source (time-series): [[entities/iot/influxdb]]
- Data source (relational): [[entities/iot/mysql]]
- Data pipeline A: [[entities/iot/mosquitto]] → Telegraf → [[entities/iot/influxdb]] → Grafana
- Data pipeline B: [[entities/iot/mosquitto]] → [[entities/iot/node-red]] → [[entities/iot/mysql]] → Grafana
- Alert ไปยัง: [[entities/iot/telegram-bot]]

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]] — ระบุใน architecture diagram
- [[sources/iot-nodered-mqtt-sql-course]] — Grafana + MySQL datasource


---

### `wiki/entities/iot/hc-sr04.md`

---
type: entity
category: device
tags: [sensor, ultrasonic, distance, level, hc-sr04]
sources: [hardware-inventory-2026-04-18, esp32-tank-level-mqtt]
created: 2026-04-18
updated: 2026-04-18
---

# HC-SR04

**ผู้ผลิต**: หลายยี่ห้อ (generic)  
**ประเภท**: Ultrasonic Distance Sensor  
**สถานะใน Lab**: ✅ มีอยู่ × 1 (ในชุด Arduino Starter Kit)  
**ราคาประมาณ**: ~$1-2

## ภาพรวม

HC-SR04 ใช้คลื่นเสียง ultrasonic วัดระยะห่างจากวัตถุ 2–400cm ใช้งานง่ายผ่าน Trigger/Echo pins นอกจาก distance measurement แล้วยังใช้ทำ **tank level monitoring** (น้ำ, น้ำมัน, เชื้อเพลิง) ได้โดยติดตั้งด้านบนถัง แล้วคำนวณระดับจากระยะที่วัดได้

## Specs หลัก

| คุณสมบัติ | ค่า |
|----------|-----|
| Range | 2–400cm |
| Accuracy | ±0.3cm |
| Angle | <15° |
| Supply | 5V |
| Trigger | 10µs pulse |
| Interface | Digital (Trigger + Echo) |

## Wiring กับ ESP32

| HC-SR04 | ESP32 |
|---------|-------|
| VCC | 5V (Vin) |
| GND | GND |
| TRIG | GPIO 4 |
| ECHO | GPIO 18 (ต้องใช้ voltage divider: 5V→3.3V) |

> **⚠️ Echo pin ส่งสัญญาณ 5V** — ต้องใช้ voltage divider (1kΩ + 2kΩ) หรือ level shifter ก่อนต่อกับ ESP32

## Tank Level Monitoring

```
[HC-SR04 ติดบนฝาถัง]
         ↓ วัดระยะ d (cm)
[ESP32 คำนวณ level]
   level% = (H_empty - d) / (H_empty - H_full) × 100
         ↓ MQTT publish
   topic: tank/level   payload: {"level": 73.5}
   topic: tank/status  payload: "normal"
```

**Captive Portal config** (จาก Voelk-IT project):
- ครั้งแรก ESP32 ทำตัวเป็น AP
- ผู้ใช้ connect และตั้งค่า WiFi, MQTT broker, ค่า empty/full distance ผ่าน web form
- ค่า config เก็บใน flash memory

## MQTT Topics

| Topic | Payload | คำอธิบาย |
|-------|---------|---------|
| `tank/level` | `73.5` | % เต็ม |
| `tank/status` | `"normal"` | สถานะ |
| `tank/lastupdate` | timestamp | อัปเดตล่าสุด |
| `tank/wificonnect` | timestamp | WiFi connect time |

## Use Cases ใน IoT

- **ถังน้ำมันเชื้อเพลิง** — วัดระดับน้ำมัน แจ้งเตือนเมื่อใกล้หมด
- **ถังน้ำ** — monitor ถังเก็บน้ำ, pump automation
- **ถังขยะ** — ทางเลือกแทน load cell เมื่อ geometry สม่ำเสมอ

## ข้อจำกัด

- ไม่เหมาะกับของเหลวที่มีฟอง, ไอ, หรือผิวไม่สม่ำเสมอ
- ของแข็ง (เช่น ขยะ) อาจสะท้อนสัญญาณผิดพลาด → load cell แม่นกว่า
- ต้องติดตั้งให้ตั้งฉากกับผิวของเหลว

## ความสัมพันธ์

- MCU: [[entities/iot/esp32]]
- Protocol: [[entities/iot/mqtt-protocol]]
- ทางเลือก (น้ำหนัก): [[entities/iot/load-cell]] + [[entities/iot/hx711]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีในชุด Arduino Starter Kit × 1
- [[sources/esp32-tank-level-mqtt]] — tank level sensor project (MQTT + captive portal)


---

### `wiki/entities/iot/hc-sr501.md`

---
type: entity
category: device
tags: [sensor, pir, motion, hc-sr501, digital]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# HC-SR501 PIR Motion Sensor

**สถานะใน Lab**: ✅ มีอยู่ × 1 (ใน Starter Kit)

## ภาพรวม

HC-SR501 เป็น Passive Infrared (PIR) sensor วัด motion ของสิ่งมีชีวิต (คน/สัตว์) จาก body heat ราคาถูกมาก output เป็น digital HIGH/LOW มี potentiometer ปรับ sensitivity และ delay

## Specs หลัก

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| Voltage | 5V–20V |
| Output | Digital HIGH (3.3V) เมื่อ detect |
| Range | สูงสุด 7m |
| Angle | 120° cone |
| Delay time | ปรับได้ 3s–5min |
| Sensitivity | ปรับได้ |
| Warm-up time | **~30 วินาที** หลัง power on |

## การใช้งานใน IoT

- Security alert: ส่ง notification เมื่อมีคนเข้า
- Smart lighting: เปิดไฟอัตโนมัติ
- Power saving: wake MCU เมื่อมีคน (ใช้กับ interrupt)

## ข้อควรระวัง

- ต้องรอ warm-up ~30 วินาทีหลัง power on — อย่า check output ทันที
- อ่าน output ผ่าน interrupt ดีกว่า polling
- แสงแดดหรือแหล่งความร้อนอื่นอาจ trigger false positive

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/arduino-uno-r3]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]]


---

### `wiki/entities/iot/home-assistant.md`

---
type: entity
category: platform
tags: [home-automation, open-source, mqtt, integration]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# Home Assistant

**ประเภท**: Home Automation Platform (Open Source)  
**ผู้พัฒนา**: Nabu Casa / Community  
**License**: Apache 2.0  
**ภาษา**: Python

## ภาพรวม

Home Assistant เป็น open-source home automation platform ที่ได้รับความนิยมสูงสุดในโลก รองรับการ integrate กับอุปกรณ์กว่า 3,000 ประเภท ใช้ MQTT เป็นโปรโตคอลหลักสำหรับการสื่อสารกับอุปกรณ์ custom

## การใช้งาน MQTT

Home Assistant มี MQTT integration built-in รองรับ:
- Auto-discovery ผ่าน MQTT topics พิเศษ
- การ subscribe/publish ผ่าน UI หรือ automation
- รองรับ Mosquitto เป็น broker หลัก (มี add-on อย่างเป็นทางการ)

## ความสัมพันธ์

- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- ใช้ร่วมกับ: [[entities/iot/mosquitto]]
- รันบน: Raspberry Pi (ยังไม่มีหน้า), Home Assistant OS

## หมายเหตุ

*(หน้านี้ยังมีข้อมูลน้อย จะอัปเดตเมื่อ ingest source ที่เกี่ยวกับ Home Assistant โดยตรง)*

## แหล่งข้อมูล

- [[sources/mqtt-introduction]] — กล่าวถึง Home Assistant เป็น use case หลักของ MQTT


---

### `wiki/entities/iot/hx711.md`

---
type: entity
category: device
tags: [hx711, adc, amplifier, load-cell, weight, spi-like, esp32]
sources: [esp32-hx711-randomnerd, esp32-hx711-mqtt-github]
created: 2026-04-18
updated: 2026-04-18
---

# HX711

**ผู้ผลิต**: Avia Semiconductor  
**ประเภท**: 24-bit ADC + Amplifier สำหรับ Load Cell  
**สถานะใน Lab**: ❌ ยังไม่มี (ต้องซื้อพร้อม load cell)  
**ราคาประมาณ**: ~$1-3 (AliExpress, มักขายคู่กับ load cell)

## ภาพรวม

HX711 เป็น IC ที่ทำหน้าที่ขยายสัญญาณจาก load cell (strain gauge) ซึ่งเป็นสัญญาณแรงดันเพียง mV และแปลงเป็นค่าดิจิตัล 24-bit ที่ microcontroller อ่านได้ผ่าน 2 สาย (Clock + Data) เป็นองค์ประกอบจำเป็นสำหรับ IoT scale ทุกชนิด

## Specs หลัก

| คุณสมบัติ | ค่า |
|----------|-----|
| Resolution | 24-bit ADC |
| Input channels | 2 differential inputs (Channel A, B) |
| Gain | 128x หรือ 64x (Ch A), 32x (Ch B) |
| Supply | 2.6–5.5V (ใช้ 3.3V กับ ESP32 ได้) |
| Interface | Custom 2-wire (Clock + Data) |
| Sample rate | 10 SPS หรือ 80 SPS |

## Wiring กับ ESP32

| HX711 Pin | Load Cell | ESP32 |
|-----------|----------|-------|
| E+ | Red wire | — |
| E- | Black wire | — |
| A+ | Green wire | — |
| A- | White wire | — |
| DT | — | GPIO 16 |
| SCK | — | GPIO 4 |
| VCC | — | 3.3V |
| GND | — | GND |

## Calibration (บังคับทุกครั้ง)

```
1. Upload calibration sketch
2. tare() — ตั้งศูนย์ (ไม่มีน้ำหนัก)
3. วางของน้ำหนักรู้ค่า (เช่น 300g)
4. บันทึก raw reading
5. calibration_factor = raw_reading / known_weight
6. ใส่ค่าใน set_scale(calibration_factor)
```

> ห้ามใช้ calibration factor ของคนอื่น — แต่ละ load cell มีค่าต่างกัน

## Libraries (Arduino IDE)

- **HX711** by Bogdan Necula — แนะนำ (รองรับ ESP32 240MHz)
- PubSubClient — สำหรับส่ง MQTT

## ข้อควรระวัง

- ESP32 CPU บางรุ่นต้องลดเป็น 80MHz ถ้าใช้ library เก่า
- Deep sleep + WiFi reconnect อาจมีปัญหา — ดู [[entities/iot/esp32]] workaround
- บัดกรีสายจาก load cell ให้แน่นก่อน twist สายเพื่อป้องกันสายขาด

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/load-cell]] — sensor ที่ HX711 อ่านค่า
- MCU: [[entities/iot/esp32]] — อ่านผ่าน 2 GPIO
- ส่งข้อมูลผ่าน: [[entities/iot/mqtt-protocol]] → [[entities/iot/node-red]] → [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/esp32-hx711-randomnerd]] — wiring, calibration, code ครบถ้วน
- [[sources/esp32-hx711-mqtt-github]] — MQTT integration + Node-RED architecture


---

### `wiki/entities/iot/influxdb.md`

---
type: entity
category: platform
tags: [influxdb, time-series, database, iot-core, open-source]
sources: [iot-lora-gateway-architecture]
created: 2026-04-18
updated: 2026-04-18
---

# InfluxDB

**ผู้พัฒนา**: InfluxData  
**เวอร์ชัน**: 2.x (OSS, ฟรี self-hosted)  
**บทบาทในโปรเจ็ค**: เก็บ time-series sensor data สำหรับ Grafana  
**สถานะ**: 🔲 ยังไม่ได้ติดตั้ง

## ภาพรวม

InfluxDB เป็น time-series database ออกแบบมาเพื่อ IoT และ metrics โดยเฉพาะ เก็บข้อมูลที่มี timestamp ได้อย่างมีประสิทธิภาพมาก auto-compress data เก่า (retention policy)

## ทำไมใช้ InfluxDB แทน MySQL/SQLite

| | InfluxDB | MySQL |
|-|---------|-------|
| เหมาะกับ | Time-series (sensor) | General-purpose |
| Storage efficiency | สูงมาก (compression) | ปานกลาง |
| Query for time range | ง่ายมาก (Flux/InfluxQL) | ต้อง index |
| Retention auto-delete | ✅ built-in | ❌ ต้อง custom |
| Grafana integration | ✅ native | ต้องเพิ่ม plugin |

## การเขียนข้อมูล (Python)

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(url="http://localhost:8086", token="MY_TOKEN", org="my-org")
write_api = client.write_api(write_options=SYNCHRONOUS)

point = Point("environment") \
    .tag("location", "living_room") \
    .field("temperature", 28.5) \
    .field("humidity", 65.0)

write_api.write(bucket="iot-data", record=point)
```

## Retention Policy แนะนำ

- **Raw data**: เก็บ 30 วัน (ทุก 30 วินาที)
- **Downsampled**: เก็บ 1 ปี (hourly average)

## ความสัมพันธ์

- ถูก query โดย: [[entities/iot/grafana]]
- รับข้อมูลจาก: [[entities/iot/mosquitto]] (ผ่าน Telegraf หรือ Python script)

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]]


---

### `wiki/entities/iot/line-notify.md`

---
type: entity
category: platform
tags: [line, notification, thailand, deprecated, messaging]
sources: [iot-lora-gateway-architecture]
created: 2026-04-18
updated: 2026-04-18
---

# Line Notify

**ผู้ให้บริการ**: LINE Corporation  
**สถานะ**: ⚠️ **DEPRECATED — หยุดให้บริการ 31 มีนาคม 2025**  
**ทางเลือก**: Line Messaging API (ซับซ้อนกว่า) หรือ [[entities/iot/telegram-bot]]

## ภาพรวม

Line Notify เป็น service ที่ให้ส่งข้อความเข้า Line chat ผ่าน HTTP POST ง่ายมาก แต่ **ปิดให้บริการแล้วตั้งแต่ 31 มีนาคม 2025** ไม่สามารถใช้งานได้อีกแล้ว

## ⚠️ ข้อขัดแย้งกับ Architecture Diagram

Architecture diagram ที่ ingest เข้ามาระบุ "Line Notify" เป็น service ปลายทาง แต่ **Line Notify deprecated แล้ว** ต้องเปลี่ยนเป็น Line Messaging API หรือย้ายไปใช้ Telegram แทน

## ทางเลือกแทน Line Notify

### 1. Line Messaging API (Messaging API)
- สมัครที่ LINE Developers Console
- สร้าง Channel → ได้ `Channel Access Token`
- ซับซ้อนกว่า Line Notify แต่ยังรองรับอยู่

### 2. Telegram Bot (แนะนำสำหรับ IoT)
- ดูรายละเอียดที่ [[entities/iot/telegram-bot]]
- API ง่ายกว่า, ฟรี, ไม่มี deprecation risk

## ความสัมพันธ์

- แทนที่ด้วย: [[entities/iot/telegram-bot]] (แนะนำ)
- Subscribe จาก: [[entities/iot/mosquitto]]

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]] — ระบุใน diagram แต่ deprecated แล้ว


---

### `wiki/entities/iot/load-cell.md`

---
type: entity
category: device
tags: [sensor, load-cell, strain-gauge, weight, hx711]
sources: [esp32-hx711-randomnerd]
created: 2026-04-18
updated: 2026-04-18
---

# Load Cell (Strain Gauge)

**ประเภท**: Weight Sensor (Analog)  
**สถานะใน Lab**: ❌ ยังไม่มี  
**ราคาประมาณ**: ~$2-10 ขึ้นกับ capacity (1kg / 5kg / 50kg)  
**ใช้คู่กับ**: [[entities/iot/hx711]] (ADC amplifier บังคับ)

## ภาพรวม

Load cell คือ transducer แปลงแรงกด/น้ำหนักเป็นสัญญาณไฟฟ้า โดยใช้ strain gauge (ตัวต้านทานที่เปลี่ยนค่าตามแรงที่กระทำ) สัญญาณออกมาเป็น mV ต้องต่อผ่าน [[entities/iot/hx711]] ก่อนเชื่อมต่อ microcontroller

## ประเภทที่นิยมใน IoT

| ประเภท | Capacity | ใช้สำหรับ |
|--------|---------|---------|
| Single point (bar) | 1kg, 5kg, 10kg | ตาชั่งในครัว, กล่องเล็ก |
| S-type | 50kg, 100kg | ถังขยะ, ถังน้ำ, ถังเชื้อเพลิง |
| Platform / Beam | 50-500kg | ถังอุตสาหกรรม |

## Wiring (4 สาย)

| สี | Pin HX711 | ความหมาย |
|----|----------|---------|
| Red | E+ | Excitation + |
| Black | E- | Excitation – |
| Green | A+ | Signal + |
| White | A- | Signal – |

> บางผู้ผลิตใช้สีต่าง — ตรวจสอบ datasheet ก่อนต่อสายทุกครั้ง

## การใช้งานใน IoT (Use Cases)

**น้ำหนักขยะ**:
- Load cell 50kg ใต้ถังขยะ
- ESP32 + HX711 วัดน้ำหนักทุก X นาที
- MQTT publish → Node-RED → แจ้งเตือนเมื่อถังเต็ม (เช่น > 80% capacity)

**ถังน้ำมัน/น้ำ**:
- ทางเลือกแทน ultrasonic เมื่อถัง geometry ไม่สม่ำเสมอ
- ชั่งน้ำหนักถังรวม แล้วลบน้ำหนักถังเปล่า

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| วัดได้แม่นยำ (±0.1%) | ต้องติดตั้งให้น้ำหนักกระจายสม่ำเสมอ |
| ทนทาน, ไม่มีชิ้นส่วนเคลื่อนไหว | ต้อง calibrate ทุกครั้ง |
| ราคาถูก | สัญญาณ mV ต้องการ HX711 เสมอ |
| ไม่กระทบจาก shape ของถัง | อุณหภูมิกระทบความแม่นยำ |

## ความสัมพันธ์

- ต้องใช้คู่กับ: [[entities/iot/hx711]] — ADC amplifier
- MCU: [[entities/iot/esp32]]
- Protocol: [[entities/iot/mqtt-protocol]]

## แหล่งข้อมูล

- [[sources/esp32-hx711-randomnerd]] — wiring, calibration guide ครบถ้วน


---

### `wiki/entities/iot/mosquitto.md`

---
type: entity
category: project
tags: [mqtt, broker, open-source, eclipse, edge]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# Eclipse Mosquitto

**ประเภท**: MQTT Broker (Open Source)  
**ผู้พัฒนา**: Eclipse Foundation  
**License**: EPL/EDL  
**เวอร์ชัน MQTT**: 3.1, 3.1.1, 5.0

## ภาพรวม

Mosquitto เป็น MQTT broker ที่ได้รับความนิยมสูงสุดในโลก open source มีน้ำหนักเบามาก เหมาะสำหรับ deployment บน Raspberry Pi หรืออุปกรณ์ edge ที่มีทรัพยากรจำกัด

## คุณสมบัติหลัก

- ใช้ RAM น้อยมาก — รันบน Raspberry Pi Zero ได้สบาย
- รองรับ MQTT 3.1, 3.1.1, และ 5.0
- TLS/SSL และ WebSocket support
- Plugin API สำหรับ authentication/authorization

## การใช้งานใน IoT

เหมาะมากสำหรับ home lab, self-hosted home automation, และ edge gateway ขนาดเล็ก ไม่แนะนำสำหรับ production ที่ต้องการ > 10,000 concurrent connections (ใช้ EMQX หรือ HiveMQ แทน)

## ความสัมพันธ์

- ใช้งานโปรโตคอล: [[entities/iot/mqtt-protocol]]
- ใช้ร่วมกับ: [[entities/iot/home-assistant]]
- แข่งขันกับ: [[entities/iot/emqx]] (ยังไม่มีหน้า), HiveMQ (ยังไม่มีหน้า)

## แหล่งข้อมูล

- [[sources/mqtt-introduction]]


---

### `wiki/entities/iot/mqtt-protocol.md`

---
type: entity
category: protocol
tags: [mqtt, messaging, publish-subscribe, iot-core, oasis-standard]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# MQTT Protocol

**ประเภท**: Messaging Protocol (OASIS Standard)  
**เวอร์ชันปัจจุบัน**: 5.0 (2019), 3.1.1 ยังใช้งานแพร่หลาย  
**พอร์ต**: 1883 (plain), 8883 (TLS)

## ภาพรวม

MQTT (Message Queuing Telemetry Transport) เป็น lightweight publish-subscribe protocol ออกแบบโดย Andy Stanford-Clark (IBM) และ Arlen Nipper ในปี 1999 เพื่อ monitoring pipeline น้ำมันผ่านดาวเทียม ปัจจุบันเป็น OASIS standard และเป็นโปรโตคอลหลักของ IoT ecosystem

## คุณสมบัติหลัก

- **Fixed header เพียง 2 bytes** — overhead ต่ำที่สุดในบรรดา IoT protocols
- **Broker-based** — อุปกรณ์ไม่คุยกันตรงๆ ผ่าน broker กลาง
- **Topic-based routing** — hierarchical string เช่น `home/room/sensor`
- **Wildcards**: `+` (single level), `#` (multi-level)
- **QoS 0/1/2** — ปรับ reliability vs performance ได้
- **Persistent sessions** — TCP connection ไม่ต้องเปิด-ปิดทุกครั้ง
- **Last Will & Testament** — แจ้งเตือนอัตโนมัติเมื่ออุปกรณ์หลุด

## การใช้งานใน IoT

เหมาะกับ:
- อุปกรณ์ที่มี RAM/CPU น้อย (ESP32, ESP8266, Arduino + Ethernet)
- เครือข่ายที่ไม่เสถียร (cellular, satellite)
- ระบบที่ต้องการ real-time updates (sensor data, alerts)
- Home automation (Home Assistant ใช้ MQTT เป็นหลัก)

ไม่เหมาะกับ:
- การส่งไฟล์ขนาดใหญ่
- Request-response แบบ synchronous (แม้ MQTT 5.0 จะรองรับแล้ว)

## เปรียบเทียบกับ HTTP

| | MQTT | HTTP |
|-|------|------|
| Header overhead | 2 bytes | ~500 bytes |
| Connection | Persistent TCP | Open/close ต่อ request |
| Battery usage | ต่ำกว่า ~2x | สูงกว่า |
| Pattern | Pub/Sub | Request/Response |
| Firewall friendly | ต้องเปิด port 1883 | 80/443 |

## MQTT 5.0 Features เพิ่มเติม

- Reason codes บน ACK ทุกตัว (debugging ง่ายขึ้น)
- User properties (custom key-value headers)
- Message expiry interval
- Shared subscriptions (load balancing ระหว่าง consumers)
- Topic aliases (ลด bandwidth)

## Security

- **TLS/SSL** บนพอร์ต 8883
- **Username/Password** authentication
- **Client certificates** (mTLS)
- Authorization: ขึ้นอยู่กับ broker (topic-level ACLs)

## Client Libraries

| Platform | Library |
|----------|---------|
| Python | `paho-mqtt` |
| JavaScript | `mqtt.js`, `MQTTX` |
| ESP32/Arduino | `PubSubClient`, `AsyncMqttClient` |
| Go | `paho.mqtt.golang` |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/mosquitto]], [[entities/iot/home-assistant]], [[entities/iot/emqx]]
- แนวคิดพื้นฐาน: [[concepts/iot/publish-subscribe]], [[concepts/iot/mqtt-qos]]
- แข่งขันกับ: CoAP (ยังไม่มีหน้า), AMQP (ยังไม่มีหน้า)
- รองรับโดย: [[entities/iot/esp32]] (ยังไม่มีหน้า)

## แหล่งข้อมูล

- [[sources/mqtt-introduction]] — บทความแนะนำ MQTT พร้อมเปรียบเทียบ HTTP และ QoS


---

### `wiki/entities/iot/mysql.md`

---
type: entity
category: platform
tags: [mysql, database, sql, relational, data-logger, open-source]
sources: [iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# MySQL

**ผู้พัฒนา**: Oracle (open source community edition)
**License**: GPL v2
**ประเภท**: Relational Database (SQL)
**บทบาทในโปรเจ็ค**: Data Logger สำหรับ sensor data (ทางเลือกแทน InfluxDB)

## ภาพรวม

MySQL เป็น relational database ที่ได้รับความนิยมสูงสุดในโลก ใช้ SQL standard ข้อดีคือ query ยืดหยุ่น มีเอกสารมาก และ Grafana รองรับเป็น data source โดยตรง ต่างจาก InfluxDB ตรงที่ไม่ได้ออกแบบมาสำหรับ time-series โดยเฉพาะ

## การใช้งานใน IoT (Data Logger Pattern)

```sql
-- ตาราง sensor log
CREATE TABLE sensor_data (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  device_id VARCHAR(50),
  topic     VARCHAR(100),
  value     FLOAT,
  unit      VARCHAR(20)
);

-- INSERT จาก Node-RED
INSERT INTO sensor_data (device_id, topic, value, unit)
VALUES ('esp32-s3-gw', 'home/room/temperature', 28.5, 'C');

-- Query ใน Grafana (macro $__timeFilter)
SELECT timestamp, value
FROM sensor_data
WHERE topic = 'home/room/temperature'
  AND $__timeFilter(timestamp)
ORDER BY timestamp ASC;
```

## MySQL vs InfluxDB สำหรับ IoT

| หัวข้อ | MySQL | InfluxDB |
|--------|-------|----------|
| ประเภท DB | Relational (SQL) | Time-series |
| Query | SQL มาตรฐาน | Flux / InfluxQL |
| Compression | ปกติ | สูง (time-series optimize) |
| Retention policy | ต้องจัดการเอง | built-in |
| Grafana datasource | ✅ | ✅ |
| เหมาะกับ | Data Logger ทั่วไป, รายงาน | sensor monitoring, alert |
| Node-RED node | ✅ node-red-node-mysql | ✅ node-red-contrib-influxdb |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/node-red]] — Data Logger via MQTT
- ใช้ร่วมกับ: [[entities/iot/grafana]] — MySQL datasource สำหรับ dashboard
- แข่งขันกับ: [[entities/iot/influxdb]] — สำหรับ IoT data storage

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — Data Logger workshop ด้วย MySQL


---

### `wiki/entities/iot/nb-iot.md`

---
type: entity
category: protocol
tags: [nb-iot, lpwan, cellular, 3gpp, narrowband, licensed]
sources: [lora-vs-nbiot]
created: 2026-04-18
updated: 2026-04-18
---

# NB-IoT (Narrowband IoT)

**ผู้พัฒนา**: 3GPP (cellular standard)
**ความถี่**: Licensed cellular band (ต้องผ่าน operator)
**ประเภท**: LPWAN cellular technology

## ภาพรวม

NB-IoT (Narrowband Internet of Things) เป็น LPWAN technology บนโครงสร้างพื้นฐาน cellular — ใช้ tower ของ AIS/DTAC/True โดยตรง ไม่ต้องติดตั้ง gateway เอง แต่มีค่าบริการรายเดือน

## เปรียบเทียบกับ LoRa

| หัวข้อ | LoRa (โปรเจ็คนี้) | NB-IoT |
|--------|------|--------|
| Frequency | unlicensed (433/900 MHz) | licensed cellular |
| Infrastructure | gateway ของตัวเอง | tower operator |
| ค่าใช้จ่าย | hardware only | monthly fee (operator) |
| Coverage | เฉพาะ gateway range | ทั่วประเทศ |
| Power | ต่ำมาก (µA) | ต่ำ (mA) |
| Data rate | 300 bps–50 kbps | 20–250 kbps |
| QoS | ไม่มี guarantee | มี |
| Latency | วินาที | วินาที |
| เหมาะกับ | private network, lab | nationwide IoT, utility meter |

## Use Cases ใน IoT ไทย

- **เครื่องวัดน้ำอัจฉริยะ** (smart water meter): ติดตั้งทั่วเมือง → ใช้ NB-IoT รายงาน consumption
- **smart parking**: sensor ใต้ถนน → NB-IoT → central management
- **precision farming**: sensor กระจายทั่วไร่ → ต้องการ coverage กว้าง

## ทำไมโปรเจ็คนี้เลือก LoRa ไม่ใช่ NB-IoT

- ต้นทุนต่ำกว่า (ไม่มีค่า operator)
- ไม่ต้องการ nationwide coverage
- Hardware มีอยู่แล้ว (DX-LR02)
- เหมาะ lab และ prototype

## ความสัมพันธ์

- แข่งขันกับ: [[concepts/iot/lora]]
- อยู่ใน category เดียวกัน: LPWAN (Low Power Wide Area Network)
- เปรียบเทียบ: [[concepts/iot/lorawan]] — LoRaWAN คล้าย NB-IoT แต่ใช้ unlicensed spectrum

## แหล่งข้อมูล

- [[sources/lora-vs-nbiot]] — บทความเปรียบเทียบ (smart meter context)


---

### `wiki/entities/iot/node-red.md`

---
type: entity
category: platform
tags: [node-red, low-code, flow-programming, mqtt, dashboard, node-js, iot-platform]
sources: [iot-nodered-mqtt-sql-course, nodered-dashboard-ui]
created: 2026-04-18
updated: 2026-04-18
---

# Node-RED

**ผู้พัฒนา**: IBM (open source), ดูแลโดย OpenJS Foundation
**License**: Apache 2.0
**Runtime**: Node.js
**บทบาทในโปรเจ็ค**: ตัวเลือก middleware แทน/เสริม Telegraf — รับ MQTT → บันทึก DB → แสดง Dashboard

## ภาพรวม

Node-RED เป็น flow-based programming tool แบบ low-code สำหรับ IoT และ Automation เขียน Logic ด้วยการ "ลาก-วาง Node" และเชื่อมต่อกัน ทำงานบน Node.js รองรับตั้งแต่ Raspberry Pi จนถึง industrial server

## คุณสมบัติหลัก

- **Flow-based**: ลาก Node มาเชื่อมกัน แทนการเขียนโค้ด
- **MQTT native**: มี MQTT in/out node ในตัว ไม่ต้องติดตั้งเพิ่ม
- **Dashboard UI**: ติดตั้ง `node-red-dashboard` ได้ Gauge, Chart, Button, Switch ทันที
- **Database**: มี node สำหรับ MySQL, MongoDB, InfluxDB, SQLite
- **Protocol**: รองรับ Modbus RTU/TCP, OPC UA, HTTP, WebSocket, TCP/UDP
- **Function node**: เขียน JavaScript ใน node ได้ถ้าต้องการ logic ซับซ้อน

## Architecture ในโปรเจ็คปัจจุบัน (ทางเลือก)

Stack ปัจจุบัน (Telegraf):
```
MQTT → Telegraf → InfluxDB → Grafana
```

Stack ทางเลือก (Node-RED):
```
MQTT → Node-RED → MySQL → Grafana
              ↓
         Node-RED Dashboard (web UI + control)
```

Stack รวม (ใช้ทั้งคู่):
```
MQTT → Node-RED → MySQL (Data Logger + Dashboard)
              ↓
           InfluxDB → Grafana (time-series analytics)
```

## การติดตั้ง

```bash
# ติดตั้ง global
npm install -g --unsafe-perm node-red

# รัน
node-red

# เข้า web editor
# http://localhost:1880

# ติดตั้ง Dashboard package
# Manage Palette → Install → node-red-dashboard
```

## Dashboard UI Nodes

| Node | ประเภท | ใช้กับ |
|------|--------|--------|
| ui_gauge | Display | อุณหภูมิ/ความชื้น real-time |
| ui_chart | Display | trend กราฟย้อนหลัง |
| ui_text | Display | ค่า sensor ปัจจุบัน |
| ui_button | Input | trigger / test command |
| ui_switch | Input | เปิด/ปิดอุปกรณ์ |
| ui_slider | Input | ปรับ threshold/setpoint |

Dashboard เข้าถึงที่: `http://localhost:1880/ui`

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| ไม่ต้องเขียนโค้ด (low-code) | Flow ซับซ้อนขึ้นเมื่อ logic เยอะ |
| Dashboard + Broker bridge ในเครื่องเดียว | ไม่ใช่ time-series DB โดยตรง |
| รองรับ Modbus, PLC, OPC UA | Node.js single-threaded — throughput จำกัด |
| Community node มาก (3000+ nodes) | Dashboard ไม่สวยเท่า Grafana |
| ทำงานบน Raspberry Pi ได้ดี | ต้องการ restart เมื่อแก้ flow บางกรณี |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/mosquitto]] — subscribe/publish MQTT
- ใช้ร่วมกับ: [[entities/iot/mysql]] — Data Logger
- ใช้ร่วมกับ: [[entities/iot/influxdb]] — time-series storage
- แข่งขันกับ: Telegraf (สำหรับ MQTT-to-DB bridge)
- เสริมกับ: [[entities/iot/grafana]] — ใช้คู่กัน (Node-RED ส่งข้อมูล, Grafana แสดงกราฟ)
- โปรโตคอล: [[concepts/iot/modbus]]

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — คอร์สครบวงจร MQTT + SQL + Grafana
- [[sources/nodered-dashboard-ui]] — การสร้าง Dashboard UI แบบ low-code


---

### `wiki/entities/iot/platformio.md`

---
type: entity
category: platform
tags: [platformio, vscode, ide, cmake, esp32, professional, dependency-management]
sources: [platformio-esp32-guide]
created: 2026-04-18
updated: 2026-04-18
---

# PlatformIO

**ผู้พัฒนา**: PlatformIO Labs
**License**: Open source (Community) / Commercial (Pro)
**รูปแบบ**: Plugin สำหรับ VS Code (ไม่ใช่ standalone IDE)

## ภาพรวม

PlatformIO เป็น ecosystem สำหรับ embedded development ที่ทรงพลังกว่า Arduino IDE มีระบบ dependency management, multi-environment, และ IntelliSense เต็มรูปแบบ เหมาะสำหรับโปรเจ็คขนาดใหญ่หรือ team development

## คุณสมบัติหลัก

- **platformio.ini**: config file กำหนด board, framework, library ทั้งหมด
- **Library management**: ล็อค version library ได้ เหมาะ reproducible build
- **Multi-environment**: build สำหรับ ESP32 classic + ESP32-S3 ในไฟล์เดียว
- **Hardware debugger**: รองรับ JTAG debug ผ่าน VS Code
- **CI/CD**: integrate กับ GitHub Actions ได้ตรง

## ตัวอย่าง platformio.ini

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
    adafruit/DHT sensor library@^1.4.6
    knolleary/PubSubClient@^2.8
    sandeepmistry/LoRa@^0.8.0

[env:esp32-s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
```

## ความสัมพันธ์

- ทางเลือก: [[entities/iot/arduino-ide]] (ง่ายกว่า), [[entities/iot/esp-idf]] (native)
- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/platformio-esp32-guide]] — beginner guide + DHT project


---

### `wiki/entities/iot/pms5003.md`

---
type: entity
category: device
tags: [sensor, air-quality, pm2.5, pm10, dust, uart, plantower]
sources: [air-quality-iot-lora-network, air-quality-sensors-dronebot]
created: 2026-04-18
updated: 2026-04-18
---

# PMS5003

**ผู้ผลิต**: Plantower  
**ประเภท**: Laser Particulate Matter Sensor  
**สถานะใน Lab**: ❌ ยังไม่มี  
**ราคาประมาณ**: ~$15-25 (AliExpress)

## ภาพรวม

PMS5003 ใช้ laser scattering วัดขนาดและความเข้มข้นของอนุภาคฝุ่นในอากาศ ครอบคลุม PM1.0, PM2.5 และ PM10 สื่อสาร UART 9600 baud ใช้กับ ESP32 ได้โดยตรง เหมาะสำหรับ outdoor node และ indoor AQI monitoring

## Specs หลัก

| คุณสมบัติ | ค่า |
|----------|-----|
| วัดได้ | PM1.0, PM2.5, PM10 |
| Range | 0–500 µg/m³ (effective), 1000 µg/m³ (max) |
| Accuracy | ±10% @ 100–500 µg/m³ |
| Interface | UART, 9600 baud |
| Supply | 4.5V–5.5V |
| Current | ~100mA active |
| Particle size | ≥0.3 µm ตรวจจับได้ |

## Wiring กับ ESP32

| PMS5003 | ESP32 |
|---------|-------|
| VCC (5V) | 5V (ผ่าน Vin หรือ USB) |
| GND | GND |
| TX | GPIO RX (เช่น GPIO 16) |
| RX | GPIO TX (เช่น GPIO 17) |

> **⚠️ ต้องการ 5V** — ไม่ทำงานที่ 3.3V

## Data Format (UART)

Sensor ส่ง packet 32 bytes ทุก 200–800ms:
```
[0x42, 0x4D, ...] → parse เป็น PM1.0, PM2.5, PM10 (µg/m³)
```

**Known issue**: Adafruit PMS5003 library อาจค้างหลังใช้งานหลายชั่วโมง → ใช้ discrete UART code แทน

## LoRa Integration (Air Quality Network)

```
[ESP32 + PMS5003 + BME688 + SCD41]
         ↓ LoRa 915MHz (SF7, 125kHz BW)
[ESP32 Gateway + OLED]
         ↓ USB Serial
[Raspberry Pi]
         ↓ Kafka / MQTT
[InfluxDB → Grafana]
```

Range LoRa: ~2km ใน outdoor → เหมาะ deploy sensor node ห่างไกล

## AQI Standard (Thai)

| PM2.5 (µg/m³) | ระดับ AQI | ความหมาย |
|----------------|----------|---------|
| 0–25 | ดี | ปลอดภัย |
| 26–37 | ปานกลาง | กลุ่มเสี่ยงควรระวัง |
| 38–50 | มีผลต่อสุขภาพ | ลด outdoor activity |
| 51–90 | มีผลต่อสุขภาพมาก | หลีกเลี่ยง outdoor |
| >91 | อันตราย | อยู่ในบ้าน |

(มาตรฐาน กรมควบคุมมลพิษ ประเทศไทย)

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]
- ส่งข้อมูลผ่าน: [[concepts/iot/lora-p2p]] หรือ [[entities/iot/mqtt-protocol]]
- Concept: [[concepts/iot/air-quality-index]]
- Sensor เพิ่มเติม: BME688 (temp/humidity/VOC), SCD41 (CO2)
- Gateway: [[entities/iot/raspberry-pi]] → [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/air-quality-iot-lora-network]] — LoRa network architecture พร้อม PMS5003
- [[sources/air-quality-sensors-dronebot]] — เปรียบเทียบ sensor ทุกประเภท


---

### `wiki/entities/iot/pzem-004t.md`

---
type: entity
category: device
tags: [sensor, power-meter, energy, modbus, uart, ac, pzem]
sources: [espem-energy-monitor]
created: 2026-04-18
updated: 2026-04-18
---

# PZEM-004T

**ผู้ผลิต**: PeaceFair  
**รุ่น**: v3.0 (ปัจจุบัน)  
**สถานะใน Lab**: ❌ ยังไม่มี (future expansion)  
**ราคาประมาณ**: ~$10-15 (AliExpress)

## ภาพรวม

PZEM-004T คือ AC power meter module วัดพารามิเตอร์ไฟฟ้าได้หลายค่าพร้อมกัน — Voltage, Current, Power, Energy, Power Factor, Frequency — และสื่อสารผ่าน UART TTL (Modbus RTU protocol) เหมาะสำหรับ energy monitoring ในบ้านหรือโรงงานเล็กๆ

## Specs หลัก

| พารามิเตอร์ | ย่าน | ความละเอียด |
|------------|------|------------|
| Voltage | 80–260V AC | 0.1V |
| Current | 0–100A | 0.001A |
| Power | 0–23kW | 0.1W |
| Energy | 0–9999kWh | 1Wh |
| Power Factor | 0.00–1.00 | 0.01 |
| Frequency | 45–65Hz | 0.1Hz |

**Interface**: UART TTL (Modbus RTU, 9600 baud)  
**Supply**: 5V DC

## การใช้งานใน IoT

```
[สายไฟ AC] ──CT clamp──> [PZEM-004T] ──UART──> [ESP32]
                                                    ↓
                                             [MQTT publish]
                                                    ↓
                                          [Broker → Grafana]
```

ใช้คู่กับ [[entities/iot/esp32]] หรือ [[entities/iot/raspberry-pi]] เพื่อ publish พลังงานไฟฟ้าแบบ real-time ไปยัง MQTT broker

## MQTT JSON Format (จาก espem project)

```json
[{"U":2180,"I":503,"P":778,"W":560,"Pf":71,"freq":505}]
```
(หน่วย: decivolts, mA, deciwatts, Wh, %, dHz)

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/esp32]] — MCU อ่านค่าผ่าน UART
- Protocol: [[concepts/iot/modbus]] — Modbus RTU บน UART
- Pattern: [[concepts/iot/data-logger]] — บันทึก energy data ย้อนหลัง
- Source project: [[sources/espem-energy-monitor]]

## แหล่งข้อมูล

- [[sources/espem-energy-monitor]] — ESP32 + PZEM-004T energy monitor project พร้อม MQTT + WebUI


---

### `wiki/entities/iot/raspberry-pi.md`

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


---

### `wiki/entities/iot/rfm95-sx1276.md`

---
type: entity
category: device
tags: [lora, sx1276, rfm95, spi, semtech, transceiver, chip]
sources: [esp32-lora-arduino-ide, esp32-lora-sensor-webserver, lora-getting-started-dronebot, esp32-lora-gateway-sparkfun]
created: 2026-04-18
updated: 2026-04-18
---

# RFM95W / SX1276

**ผู้ผลิต**: Semtech (SX1276 chip) / HopeRF (RFM95W module)
**Interface**: SPI
**ประเภท**: LoRa transceiver chip/module

## ภาพรวม

SX1276 คือ LoRa transceiver chip จาก Semtech — ผู้คิดค้น LoRa technology RFM95W คือ module ที่ HopeRF บรรจุ SX1276 พร้อม oscillator และ RF circuit มาให้พร้อมใช้ เป็น chip มาตรฐานที่บอร์ด LoRa ส่วนใหญ่ใช้ เช่น TTGO LoRa32, Heltec ESP32 LoRa, SparkFun LoRa Gateway

## Specs หลัก (SX1276)

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| Frequency | 137–1020 MHz (ครอบคลุมทุก band) |
| Modulation | LoRa (CSS) และ FSK |
| Sensitivity | ถึง -148dBm |
| Output power | ถึง +20dBm |
| Interface | SPI |
| Supply voltage | 1.8–3.7V |
| Bandwidth | 300 bps – 50 kbps |

## ต่างจาก DX-LR02 อย่างไร

| | RFM95 / SX1276 | DX-LR02 |
|--|---------------|---------|
| Interface | SPI | UART |
| Library | sandeepmistry/arduino-LoRa | ไม่ต้องการ library (AT commands) |
| ความยืดหยุ่น | สูง (control ทุก parameter) | ต่ำกว่า (transparent mode) |
| Frequency | 137-1020 MHz | 900 MHz fixed |
| ราคา | ถูกกว่า | แพงกว่า |
| เหมาะกับ | custom PCB, maker project | plug-and-play UART device |

## บอร์ดที่ใช้ SX1276/RFM95

- **TTGO LoRa32 SX1276**: ESP32 + SX1276 + OLED รวมบอร์ดเดียว
- **Heltec WiFi LoRa 32**: ESP32 + SX1276 + OLED
- **SparkFun ESP32 LoRa 1-CH Gateway**: ESP32 + RFM95W
- **Arduino MKR WAN 1310**: SAMD + SX1276

## Library

```bash
# Arduino IDE — Manage Libraries
arduino-LoRa by Sandeep Mistry
```

```cpp
#include <SPI.h>
#include <LoRa.h>
// Pin definitions
#define LORA_SS   18
#define LORA_RST  14
#define LORA_DIO0 26

LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
LoRa.begin(915E6);  // 915MHz
```

## ความสัมพันธ์

- ใช้งาน concept: [[concepts/iot/lora]], [[concepts/iot/lora-p2p]]
- เปรียบเทียบกับ: [[entities/iot/dx-lr02-lora]] (UART vs SPI)
- ใช้กับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]
- ผู้พัฒนา LoRa: Semtech

## แหล่งข้อมูล

- [[sources/esp32-lora-arduino-ide]] — code P2P ด้วย RFM95
- [[sources/esp32-lora-sensor-webserver]] — TTGO LoRa32 project
- [[sources/lora-getting-started-dronebot]] — SX1276 specs


---

### `wiki/entities/iot/telegram-bot.md`

---
type: entity
category: platform
tags: [telegram, bot, notification, alert, messaging, python]
sources: [iot-lora-gateway-architecture, hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# Telegram Bot

**ผู้ให้บริการ**: Telegram  
**บทบาทในโปรเจ็ค**: รับข้อมูลจาก MQTT Broker → ส่ง alert อุณหภูมิผิดปกติไปยังมือถือ  
**สถานะ**: 🔲 ยังไม่ได้ตั้งค่า

## ภาพรวม

Telegram Bot API ฟรี ไม่มี rate limit ที่น่ากังวลสำหรับ IoT scale เล็กน้อย สร้างผ่าน @BotFather ใน Telegram รับ `BOT_TOKEN` แล้วใช้ HTTP API ส่งข้อความ

## วิธีสร้าง Bot (ขั้นตอน)

1. เปิด Telegram → ค้นหา `@BotFather`
2. ส่ง `/newbot` → ตั้งชื่อ → รับ **BOT_TOKEN**
3. ส่งข้อความหา bot ก่อน 1 ครั้ง เพื่อสร้าง chat session
4. เรียก `https://api.telegram.org/bot<TOKEN>/getUpdates` → ได้ **chat_id**

## วิธีส่งข้อความ (Python)

```python
import requests

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID   = "YOUR_CHAT_ID"

def send_alert(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})
```

## รูปแบบ Integration กับ MQTT

```python
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    temp = float(msg.payload)
    if temp > 35:  # threshold
        send_alert(f"⚠️ อุณหภูมิสูง: {temp}°C")

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe("home/room/temperature")
client.loop_forever()
```

## ข้อดี/ข้อเสียเทียบ Line

| | Telegram | Line Notify |
|-|---------|------------|
| ฟรี | ✅ ตลอดไป | ✅ (แต่ deprecated 2025) |
| API ง่าย | ✅ มาก | ✅ |
| BOT ตอบโต้ได้ | ✅ (รับคำสั่งได้) | ❌ (แค่ push) |
| ใช้งานง่ายบนมือถือ | ✅ | ✅ (คนไทยใช้เยอะกว่า) |

## ความสัมพันธ์

- Subscribe จาก: [[entities/iot/mqtt-protocol]] ผ่าน [[entities/iot/mosquitto]]
- ใช้ร่วมกับ: [[entities/iot/line-notify]] (สำรอง), [[entities/iot/grafana]] (dashboard)
- ข้อมูลมาจาก: [[entities/iot/dht11]] → [[entities/iot/esp32]] → LoRa → [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]] — ระบุใน architecture diagram
- [[sources/hardware-inventory-2026-04-18]] — ระบุเป็น target platform


---

### `wiki/entities/iot/the-things-network.md`

---
type: entity
category: platform
tags: [lorawan, ttn, network-server, cloud, community, free]
sources: [esp32-lora-gateway-sparkfun, lorawan-network-beginner]
created: 2026-04-18
updated: 2026-04-18
---

# The Things Network (TTN)

**ผู้พัฒนา**: The Things Industries (Netherlands)
**License**: Community tier ฟรี
**ประเภท**: Cloud LoRaWAN Network Server (LNS)

## ภาพรวม

TTN เป็น cloud platform ที่ให้บริการ LoRaWAN Network Server ฟรีสำหรับ community และ maker เป็น platform ที่ใหญ่ที่สุดสำหรับ LoRaWAN — มี community gateway ทั่วโลก, device registry, data routing, และ API สำหรับ application

## หน้าที่ใน LoRaWAN Stack

```
[LoRa Device]
    ~~LoRa~~
[Gateway]  ──packet forwarding──>  [TTN Network Server]
                                         ↓
                                   [TTN Application]
                                         ↓
                               [Webhook / MQTT / HTTP]
                                         ↓
                               [User Application / Dashboard]
```

## คุณสมบัติ

- **Device Registry**: จัดการ DevEUI, AppKey ของทุก device
- **Data routing**: route ข้อมูลจาก gateway ไปยัง application
- **Payload decoder**: decode payload ของ device ได้ใน JavaScript
- **Integrations**: Webhook, MQTT, AWS IoT, Azure IoT Hub

## เปรียบเทียบกับ ChirpStack

| | TTN | ChirpStack |
|--|-----|------------|
| Hosting | Cloud (managed) | Self-hosted |
| ค่าใช้จ่าย | ฟรี (community) | ฟรี + server cost |
| Setup | ง่าย | ซับซ้อนกว่า |
| Control | จำกัด | เต็มที่ |
| Privacy | ข้อมูลผ่าน cloud TTN | เก็บ local ได้ |
| เหมาะกับ | hobbyist, community | enterprise, private |

## เกี่ยวข้องกับโปรเจ็คนี้

โปรเจ็คปัจจุบันใช้ **LoRa P2P** ไม่ผ่าน TTN — TTN เป็น reference สำหรับ **อนาคต** ถ้าต้องการขยายเป็น LoRaWAN network จริง

## ความสัมพันธ์

- ใช้โปรโตคอล: [[concepts/iot/lorawan]]
- ทางเลือก (self-hosted): ChirpStack (ยังไม่มีหน้า)
- Hardware ที่เข้ากัน: [[entities/iot/rfm95-sx1276]]

## แหล่งข้อมูล

- [[sources/esp32-lora-gateway-sparkfun]] — tutorial ESP32 → TTN
- [[sources/lorawan-network-beginner]] — TTN ใน LoRaWAN architecture


---

### `wiki/entities/iot/vapcell-m35-18650.md`

---
type: entity
category: device
tags: [power, 18650, battery, li-ion, portable]
sources: [hardware-inventory-2026-04-18]
created: 2026-04-18
updated: 2026-04-18
---

# Vapcell INR18650 M35

**ผู้ผลิต**: Vapcell  
**รุ่น**: INR18650 M35  
**สถานะใน Lab**: ✅ มีอยู่ × 2  
**ใช้คู่กับ**: [[entities/iot/18650-battery-shield]]

## ภาพรวม

แบตเตอรี่ลิเธียมไอออน ขนาด 18650 ความจุสูง 3500mAh เหมาะสำหรับ IoT project ที่ต้องการพลังงานต่อเนื่องนาน ใช้คู่กับ 18650 Battery Shield V3 เพื่อจ่ายไฟให้ ESP32 และอุปกรณ์ต่างๆ

## Specs หลัก

| คุณสมบัติ | ค่า |
|----------|-----|
| ความจุ | 3500mAh |
| แรงดันนอมินัล | 3.7V |
| Discharge สูงสุด (continuous) | 10A |
| Discharge สูงสุด (pulse) | 25A / 5 วินาที |
| ขนาด | 18mm × 65mm |

## การคำนวณ Runtime (กับ Battery Shield V3)

| การใช้งาน | กระแสเฉลี่ย | Runtime ประมาณ |
|----------|------------|--------------|
| ESP32 WiFi active | ~150mA | ~20 ชั่วโมง |
| ESP32 + DHT11 ทุก 30s | ~5mA | ~500 ชั่วโมง |
| ESP32 deep sleep | ~10µA | หลายร้อยวัน |

(Runtime = ความจุ × efficiency 85% ÷ กระแสเฉลี่ย)

## ข้อควรระวัง

- ใส่ orientation ถูกทิศเสมอ — ใส่กลับทำ battery shield เสียได้
- ถ้าใช้ 2 ก้อนพร้อมกัน ต้องใช้ capacity และ charge cycle ใกล้เคียงกัน
- เก็บที่ charge ~50% ถ้าไม่ได้ใช้นาน

## ความสัมพันธ์

- ใช้กับ: [[entities/iot/18650-battery-shield]] — shield V3 รองรับ 1 ก้อน
- Power ให้: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มีใน lab × 2


---

## Concepts (iot)

### `wiki/concepts/iot/CLAUDE.md`

> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — IoT Concepts

> **โดเมน**: Internet of Things (IoT) — Concepts  
> **Last updated**: 2026-05-09  
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน concepts/iot/ เท่านั้น**

---

## Concepts ที่มีอยู่ (8 concepts)

| Slug | Abstract |
|------|----------|
| `air-quality-index` | AQI — มาตรฐานสากลแปลงค่ามลพิษเป็นสเกลเดียว |
| `cold-chain-monitoring` | IoT วัดอุณหภูมิสินค้าตลอดห่วงโซ่อุปทาน |
| `dashboard-design` | Dashboard design principles สำหรับ IoT |
| `data-logger` | บันทึก sensor data ต่อเนื่องลง database |
| `lora` | LoRa modulation — CSS, long-range, low-power |
| `lora-p2p` | LoRa point-to-point โดยไม่ผ่าน LoRaWAN server |
| `lorawan` | LoRaWAN network protocol — star topology, device classes |
| `modbus` | Industrial serial protocol (1979) — RTU/ASCII/TCP |
| `mqtt-qos` | QoS 0/1/2 tradeoffs |
| `publish-subscribe` | Pub/sub messaging pattern |
| `tinyml` | ML บน microcontroller (RAM < 1MB) |

---

## Rules สำหรับ concept pages

1. **frontmatter บังคับ**: `type`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **ทุก concept ต้องมี**: นิยาม, ทำไมถึงสำคัญใน IoT, วิธีการทำงาน, ตัวอย่างการใช้งาน, ข้อดี/ข้อเสีย
3. **Cross-reference**: ลิงก์ไป entities และ synthesis ที่เกี่ยวข้อง
4. **Confidence markers**: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]`

---

## ความสัมพันธ์กับ entities

| Concept | Entity ที่เกี่ยวข้อง |
|---------|---------------------|
| lora, lora-p2p, lorawan | dx-lr02-lora, rfm95-sx1276, chirpstack, the-things-network |
| mqtt-qos, publish-subscribe | mosquitto, emqx, mqtt-protocol |
| tinyml | esp32, esp32-s3 |
| cold-chain-monitoring | ds18b20, esp32 |
| air-quality-index | pms5003, esp32 |
| dashboard-design, data-logger | grafana, influxdb, node-red, mysql |

---

## Workflow สำหรับสร้าง concept ใหม่

1. ตรวจสอบว่าไม่มี concept นี้แล้ว — ค้นหาจาก `wiki-overview.md` หรือ grep
2. ใช้ template จาก CLAUDE.md หลัก (section Concept Page Template)
3. เชื่อมโยงไปยัง entities ที่เกี่ยวข้อง
4. อัปเดต cross-domain ถ้าต้อง synthesis
5. อัปเดต `index-iot.md` + รัน `python3 scripts/gen-index.py`
6. บันทึกใน `log.md`

---

### `wiki/concepts/iot/air-quality-index.md`

---
type: concept
tags: [aqi, air-quality, pm2.5, pm10, iot, environment]
sources: [air-quality-sensors-dronebot, air-quality-iot-lora-network]
created: 2026-04-18
updated: 2026-04-18
---

# Air Quality Index (AQI)

## นิยาม

AQI (Air Quality Index) คือตัวเลขมาตรฐานที่แปลงค่าความเข้มข้นของมลพิษในอากาศ (PM2.5, PM10, CO, O₃ ฯลฯ) ให้เป็นสเกลเดียวที่เข้าใจง่าย แต่ละประเทศมี standard ต่างกันเล็กน้อย

## Sensor ที่ใช้วัด

| Sensor | วัดอะไร | Interface | ราคา |
|--------|--------|---------|------|
| [[entities/iot/pms5003]] | PM1.0, PM2.5, PM10 | UART 9600 | ~$20 |
| SGP30/SGP40 | CO2, VOC (tVOC) | I2C | ~$15 |
| BME688 | Temp, Humidity, Pressure, Gas | I2C | ~$20 |
| SCD41 | CO2, Temp, Humidity | I2C | ~$45 |
| MQ-series | CO, LPG, NH3 ฯลฯ (specific gas) | Analog | ~$2-5 |

## มาตรฐาน PM2.5 ประเทศไทย (กรมควบคุมมลพิษ)

| PM2.5 (µg/m³) | AQI | สี | ความหมาย |
|----------------|-----|-----|---------|
| 0–25 | 0–50 | 🟢 | ดี (Good) |
| 26–37 | 51–100 | 🟡 | ปานกลาง |
| 38–50 | 101–150 | 🟠 | มีผลต่อสุขภาพ |
| 51–90 | 151–200 | 🔴 | มีผลต่อสุขภาพมาก |
| >91 | >200 | 🟣 | อันตราย |

## Architecture IoT สำหรับ AQI Network

```
[ESP32 Node + PMS5003 + BME688]
         ↓ LoRa 915MHz (2km range)
[ESP32 Gateway + Raspberry Pi]
         ↓
[InfluxDB → Grafana Dashboard]
         ↓
[Alert เมื่อ PM2.5 > 50 µg/m³]
```

## ข้อควรระวังในการ Implement

- **PMS5003 UART library**: Adafruit library มี bug ค้างหลังหลายชั่วโมง → ใช้ discrete UART parsing แทน
- **SGP30**: ต้องการ 24-hour warmup ครั้งแรก ใช้ EEPROM เก็บ baseline
- **MQ series**: ใช้ 5V, heating element กินไฟ ~100mA → ไม่เหมาะ battery node
- **Temperature compensation**: ค่า gas sensor บางตัวขึ้นกับอุณหภูมิ ต้องชดเชย

## ความสัมพันธ์

- Sensor หลัก: [[entities/iot/pms5003]]
- LoRa network: [[concepts/iot/lora-p2p]], [[concepts/iot/lorawan]]
- Storage + Visualization: [[entities/iot/influxdb]], [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/air-quality-sensors-dronebot]] — เปรียบเทียบ sensor ทุกประเภทละเอียด
- [[sources/air-quality-iot-lora-network]] — distributed LoRa AQI network


---

### `wiki/concepts/iot/cold-chain-monitoring.md`

---
type: concept
tags: [cold-chain, vaccine, temperature, monitoring, iot, alert]
sources: [vaccine-temp-monitoring-iot, vaccine-cae-anomaly-detection, ds18b20-esp32-randomnerd]
created: 2026-04-18
updated: 2026-04-18
---

# Cold Chain Monitoring (การติดตาม Cold Chain)

## นิยาม

Cold chain monitoring คือระบบ IoT ที่ติดตามและบันทึกอุณหภูมิของสินค้าที่ต้องควบคุมอุณหภูมิตลอดห่วงโซ่อุปทาน ตั้งแต่การผลิต การขนส่ง จนถึงจุดใช้งาน โดยเฉพาะวัคซีน ยา และอาหาร

## ทำไมถึงสำคัญ

วัคซีนเสื่อมสภาพถาวรเมื่อออกนอก cold chain — ไม่สามารถมองเห็นความเสียหายด้วยตาเปล่า:
- WHO กำหนด: วัคซีนต้องเก็บที่ **+2°C ถึง +8°C**
- อุณหภูมิสูงเกิน → protein denaturation → วัคซีนไม่มีประสิทธิภาพ
- อุณหภูมิต่ำเกิน (freeze) → วัคซีนบางชนิดเสียหายถาวร

## Architecture IoT สำหรับ Cold Chain

```
[DS18B20 sensors × หลายจุด]
         ↓ One-Wire
[ESP32 + GSM module]
    ↓              ↓
[MQTT publish]  [SMS/Call alert]  ← ทันที เมื่ออุณหภูมิออกนอก range
    ↓
[MQTT Broker → Node-RED]
    ↓
[InfluxDB]  ← log ทุก 5 นาที
    ↓
[Grafana]   ← dashboard + alert rule
```

## Alert Levels

| ระดับ | เงื่อนไข | การแจ้งเตือน |
|-------|---------|------------|
| Warning | >8°C หรือ <2°C ครั้งแรก | Telegram push |
| Critical | ออกนอก range > 15 นาที | SMS + Phone call (GSM) |
| Emergency | >25°C หรือ <0°C | SMS + Call + Log incident |

## Advanced: AI Anomaly Detection

แทนที่จะตั้ง threshold ตายตัว ใช้ **Convolutional Autoencoder (CAE)** รันบน ESP32 โดยตรง:
- Model เรียนรู้ pattern "ปกติ" ของอุณหภูมิในตู้แช่
- ตรวจจับ pattern ผิดปกติก่อนที่จะถึง threshold
- Accuracy 92%, ใช้ไฟเพียง 50mW

ดู [[concepts/iot/tinyml]] สำหรับ workflow การ train และ deploy

## Hardware Stack แนะนำ (งบประหยัด)

| Component | รายการ | ราคาประมาณ |
|-----------|--------|-----------|
| MCU | [[entities/iot/esp32]] | ~$3 |
| Temp sensor | [[entities/iot/ds18b20]] × 3 | ~$6 |
| Pull-up resistor | 4.7kΩ | <$0.1 |
| Alert | [[entities/iot/telegram-bot]] (ฟรี) | ฟรี |
| Storage | [[entities/iot/influxdb]] บน [[entities/iot/raspberry-pi]] | ~$30 RPi |
| Dashboard | [[entities/iot/grafana]] (ฟรี) | ฟรี |

## ความสัมพันธ์

- Sensor: [[entities/iot/ds18b20]]
- Alert: [[entities/iot/telegram-bot]]
- AI layer: [[concepts/iot/tinyml]]
- Storage: [[entities/iot/influxdb]], [[concepts/iot/data-logger]]
- Visualization: [[entities/iot/grafana]]

## แหล่งข้อมูล

- [[sources/vaccine-temp-monitoring-iot]] — complete cold chain IoT system
- [[sources/vaccine-cae-anomaly-detection]] — AI anomaly detection research 2024
- [[sources/ds18b20-esp32-randomnerd]] — sensor implementation


---

### `wiki/concepts/iot/dashboard-design.md`

---
type: concept
tags: [dashboard, ux, visualization, iot, design, grafana, node-red]
sources: [iot-visualization-guide, dashboard-design-best-practices]
created: 2026-04-18
updated: 2026-04-18
---

# Dashboard Design (IoT)

## นิยาม

Dashboard คือหน้าจอที่แสดงข้อมูลสำคัญ "at a glance" สำหรับ IoT — แปลง raw sensor data ให้เป็น visual insight ที่ operator ใช้ตัดสินใจได้ทันที

## ทำไมถึงสำคัญใน IoT

IoT สร้าง data stream ต่อเนื่อง ถ้าไม่มี dashboard ที่ดี ข้อมูลที่เก็บมาก็ไม่มีประโยชน์ Dashboard ที่ดีทำให้ detect anomaly ได้เร็ว, ช่วย troubleshoot, และแสดง trend ที่มองไม่เห็นจาก raw numbers

## Widget Selection Guide

| Widget | ใช้กับ | อย่าใช้กับ |
|--------|--------|-----------|
| **Gauge** | ค่าปัจจุบัน (temp, %, rpm) | trend ย้อนหลัง |
| **Line Chart** | time-series trend | ค่าเดียว snapshot |
| **Stat / Number** | ค่า key metric ปัจจุบัน | หลายค่าพร้อมกัน |
| **Alert Indicator** | threshold status | ข้อมูลต่อเนื่อง |
| **Bar Chart** | เปรียบเทียบ period | real-time stream |
| **Table** | log ล่าสุด, multi-sensor | ค่าเดียว |

## Design Principles

1. **แสดงเฉพาะ relevant data** — ถ้าข้อมูลไม่ช่วยตัดสินใจ → ไม่แสดง
2. **Information hierarchy** — สำคัญ = ใหญ่/บน, รายละเอียด = เล็ก/ล่าง
3. **Consistent color coding** — เขียว=ปกติ, เหลือง=เตือน, แดง=วิกฤต ทั้ง dashboard
4. **Timestamp visible** — ทุก panel ต้องเห็น "last updated"
5. **Mobile-readable** — ขนาดตัวอักษรและ widget ต้องอ่านได้บนมือถือ
6. **Progressive disclosure** — overview ก่อน drill-down ทีหลัง

## Dashboard สำหรับโปรเจ็คนี้ (Grafana)

```
┌──────────────┬──────────────┬──────────────┐
│  Temp Gauge  │   Hum Gauge  │ Alert Status │
│   28.5°C     │    65%       │   ✅ Normal  │
├──────────────┴──────────────┴──────────────┤
│         Temperature / Humidity (24h)        │
│  ~~~~~~~~~~~~~~~~~~~~/~~~~~~~~~~~~~~~~~~~~  │
├─────────────────────────────────────────────┤
│   Last reading: 2026-04-18 14:32:05 UTC     │
└─────────────────────────────────────────────┘
```

## Platform สำหรับ IoT Dashboard

| Platform | เหมาะกับ | ข้อดี |
|---------|---------|-------|
| [[entities/iot/grafana]] | time-series analytics | สวย, query ทรงพลัง |
| [[entities/iot/node-red]] Dashboard | control panel + monitor | low-code, bidirectional |
| Custom HTML/JS | lightweight, embedded | ยืดหยุ่นสุด |

## ความสัมพันธ์

- สร้างด้วย: [[entities/iot/grafana]], [[entities/iot/node-red]]
- Data source: [[entities/iot/influxdb]], [[entities/iot/mysql]]
- Concept: [[concepts/iot/data-logger]] — เก็บข้อมูลก่อน แสดงทีหลัง

## แหล่งข้อมูล

- [[sources/iot-visualization-guide]] — widget selection, IoT-specific patterns
- [[sources/dashboard-design-best-practices]] — general UX principles


---

### `wiki/concepts/iot/data-logger.md`

---
type: concept
tags: [data-logger, storage, time-series, industrial-iot, database]
sources: [iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# Data Logger

## นิยาม

Data Logger คือระบบที่บันทึกข้อมูลจาก sensor หรืออุปกรณ์ลงใน database อย่างต่อเนื่องตามเวลา เพื่อให้สามารถ query ย้อนหลัง วิเคราะห์ trend และสร้างรายงานได้

## ทำไมถึงสำคัญใน IoT

- **Historical analysis**: ดูแนวโน้มอุณหภูมิ, การใช้พลังงาน, ความผิดปกติ
- **Compliance**: โรงงานอุตสาหกรรมต้องบันทึก log การผลิตตามมาตรฐาน
- **Debugging**: วิเคราะห์ event ย้อนหลังเมื่อระบบมีปัญหา
- **Alerting**: ตรวจจับค่าผิดปกติจาก historical baseline

## วิธีการทำงาน (ในโปรเจ็คนี้)

```
[Sensor] → [MQTT publish] → [Broker]
                                ↓
                          [Node-RED subscribe]
                                ↓
                          [MySQL INSERT]        ← บันทึกทุก reading
                                ↓
                          [Grafana query]       ← แสดง timeline
```

## ตัวอย่างการใช้งาน

**Smart Home Temperature Logger**:
- ESP32 + DHT11 publish temp/humidity ทุก 30 วินาที
- Node-RED subscribe → INSERT ลง MySQL
- Grafana แสดง chart 24 ชั่วโมง + Gauge ปัจจุบัน

**Industrial Power Meter Logger**:
- PZEM-004T วัด current/voltage/power
- ESP32 publish ทุก 1 นาที
- Data Logger บันทึก → คำนวณ energy usage รายวัน/รายเดือน

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| มี historical data สำหรับ analysis | ต้องการ storage เพิ่มขึ้นตามเวลา |
| debugging ง่ายขึ้นมาก | ต้องตั้ง retention policy ไม่งั้น DB โตไม่หยุด |
| สร้าง report และ graph ได้ | latency เพิ่มขึ้น (write → read) |

## เลือก Database ไหน

- **MySQL**: query ยืดหยุ่น, มี JOIN, คุ้นเคย, เหมาะ lab
- **InfluxDB**: compressed time-series, built-in retention, เหมาะ production sensor farm
- **SQLite**: ไม่ต้องการ server, เหมาะ edge device logging

## ความสัมพันธ์

- [[entities/iot/node-red]] — middleware บันทึก data ลง DB
- [[entities/iot/mysql]] — relational data store
- [[entities/iot/influxdb]] — time-series data store
- [[entities/iot/grafana]] — visualization layer

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — Data Logger workshop


---

### `wiki/concepts/iot/lora-p2p.md`

---
type: concept
tags: [lora, p2p, point-to-point, uart, arduino-lora, sensor-node, gateway]
sources: [esp32-lora-arduino-ide, esp32-lora-sensor-webserver, easyloranode-tracker, lora-thai-intro]
created: 2026-04-18
updated: 2026-04-18
---

# LoRa Point-to-Point (P2P)

## นิยาม

LoRa P2P คือการสื่อสาร LoRa โดยตรงระหว่าง 2 อุปกรณ์ โดยไม่ผ่าน LoRaWAN Network Server เหมาะสำหรับ lab, prototype, หรือระบบที่มี node จำนวนน้อย

## ทำไมถึงสำคัญใน IoT

LoRa P2P เป็นวิธีที่ง่ายและเร็วที่สุดในการเริ่มต้นใช้งาน LoRa ไม่ต้องการ cloud service, gateway hardware พิเศษ, หรือ network server — เพียง LoRa module 2 ตัวก็ทำ long-range link ได้ทันที

## วิธีการทำงาน

**Pattern หลักในโปรเจ็คนี้:**
```
[Sensor Node]                    [Gateway Node]
ESP32 + DHT11                    ESP32-S3
    ↓ UART                           ↓ UART
[DX-LR02 TX]  ~~LoRa 900MHz~~  [DX-LR02 RX]
                                     ↓ WiFi + MQTT
                               [Mosquitto Broker]
                                     ↓
                               [Dashboard / Alert]
```

## 2 วิธี Interface กับ LoRa Module

| วิธี | Module ตัวอย่าง | ใช้กับ library | ข้อดี |
|------|--------------|--------------|-------|
| **UART (AT commands)** | DX-LR02, E32, E220 | ไม่ต้องการ library พิเศษ | ง่าย, transparent mode |
| **SPI (register-level)** | RFM95, SX1276, TTGO LoRa32 | `sandeepmistry/arduino-LoRa` | control ได้มากกว่า |

**โปรเจ็คนี้ใช้ UART (DX-LR02)** — ส่ง serial data ผ่าน UART, module จัดการ LoRa เอง

### DX-LR02 UART Mode (Transparent)
```cpp
// โหมด Normal (M0=0, M1=0): ส่ง UART → ออก LoRa อัตโนมัติ
Serial2.begin(9600);        // baud rate ของ DX-LR02
Serial2.println("28.5");    // ส่ง LoRa ทันที (transparent mode)

// ฝั่ง receiver:
if (Serial2.available()) {
    String data = Serial2.readString();  // รับ LoRa data
}
```

### RFM95/SX1276 SPI Mode (arduino-LoRa library)
```cpp
#include <LoRa.h>
LoRa.begin(915E6);           // ตั้ง frequency
LoRa.beginPacket();
LoRa.print("28.5");
LoRa.endPacket();            // ส่ง LoRa packet
```

## Packet Format แนะนำสำหรับโปรเจ็คนี้

```
// ส่งเป็น JSON string ผ่าน UART → LoRa
{"device":"node01","temp":28.5,"hum":65.2,"rssi":-87}
```

หรือ CSV แบบเบา:
```
node01,28.5,65.2
```

## Power Optimization Tips

- **Deep sleep ระหว่าง reading**: ตั้ง ESP32 deep sleep, ตื่นทุก 30 วินาที → อ่าน sensor → ส่ง LoRa → กลับ sleep
- **ปิด LoRa module**: DX-LR02 ใส่ M1=1 → deep sleep mode ใช้ไฟน้อยลง
- Target: <15µA ขณะ deep sleep (เหมือน EasyLoRaNode Tracker)

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| ง่าย ไม่ต้องการ cloud | scale ได้ยาก (หลาย node) |
| ไม่มีค่าบริการรายเดือน | ไม่มี encryption built-in |
| เริ่มต้นได้ทันที | ไม่มี network management |
| hardware ราคาถูก | ต้อง handle collision เอง (ถ้าหลาย node) |

## ความสัมพันธ์

- Hardware: [[entities/iot/dx-lr02-lora]] (UART), [[entities/iot/rfm95-sx1276]] (SPI)
- เปรียบเทียบกับ: [[concepts/iot/lorawan]] — LoRaWAN เหมาะ scale ขึ้น
- Physical layer: [[concepts/iot/lora]]
- ใช้ร่วมกับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/esp32-lora-arduino-ide]] — P2P code + library (SPI method)
- [[sources/esp32-lora-sensor-webserver]] — project pattern sender/receiver
- [[sources/easyloranode-tracker]] — deep sleep + power optimization
- [[sources/lora-thai-intro]] — Thailand frequency legal reference


---

### `wiki/concepts/iot/lora.md`

---
type: concept
tags: [lora, lpwan, wireless, long-range, chirp, iot-core]
sources: [hardware-inventory-2026-04-18, esp32-lora-arduino-ide, lora-thai-intro, lora-getting-started-dronebot, lora-vs-nbiot]
created: 2026-04-18
updated: 2026-04-18
---

# LoRa (Long Range Radio)

## นิยาม

LoRa เป็น wireless modulation technology ที่ใช้ Chirp Spread Spectrum (CSS) ออกแบบมาเพื่อการสื่อสารระยะไกลที่ใช้พลังงานต่ำมาก พัฒนาโดย Semtech และ Cycleo (ซื้อโดย Semtech ในปี 2012)

## ทำไมถึงสำคัญใน IoT

WiFi และ BLE มี range จำกัด (~100m) LoRa แก้ปัญหานี้สำหรับอุปกรณ์ที่:
- อยู่ห่างกัน หรืออยู่ในพื้นที่ไม่มี WiFi
- ต้องการ battery life นาน (ปีหรือมากกว่า)
- ส่งข้อมูลน้อย (sensor readings, alerts)

## วิธีการทำงาน

LoRa ใช้ **Chirp Spread Spectrum (CSS)**: ส่งสัญญาณเป็น "chirp" (frequency sweep จาก low→high หรือ high→low) แทน carrier คงที่ ทำให้:
- ทนทานต่อ interference — noise ไม่ใช่ chirp จึง decode ไม่ได้
- รับสัญญาณได้แม้ signal อ่อนมาก (Sensitivity ถึง -148dBm บน SX1276)
- ระยะไกลกว่า WiFi มาก แต่ bandwidth ต่ำมาก (เทียบเท่า dial-up 300–50,000 bps)

## LoRa vs LoRaWAN

| | LoRa | LoRaWAN |
|-|------|---------|
| คือ | Physical layer modulation | Network protocol บน LoRa |
| ต้องการ gateway | ไม่ (P2P ได้) | ใช่ (LoRaWAN gateway) |
| ความซับซ้อน | ต่ำ | สูงกว่า |
| ใน lab นี้ | ✅ **ใช้ LoRa P2P** | ต้องซื้อ gateway เพิ่ม |

## Specs ทั่วไป

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| Modulation | Chirp Spread Spectrum (CSS) |
| Frequency | 433/868/915/920-925 MHz (แล้วแต่ประเทศ) |
| Thailand frequency | **920-925 MHz** ✅ กสทช. อนุญาต กำลังส่งสูงสุด 4W |
| Range (โล่ง) | 2–15km |
| Range (เมือง) | 1–3km |
| Data rate | 0.3–50 kbps |
| Sensitivity | ถึง -148dBm (SX1276) |
| Power consumption | ต่ำมาก (µA ขณะ standby) |

## Chips / Modules ที่ใช้

| Module | Interface | หมายเหตุ |
|--------|-----------|---------|
| SX1276 / RFM95W | SPI | chip มาตรฐาน, ใช้ arduino-LoRa library |
| DX-LR02 | UART | transparent mode, AT commands |
| SX1278 (433MHz) | SPI | เหมือน SX1276 แต่ 433MHz |

> **โปรเจ็คนี้ใช้ DX-LR02 (UART)** → ไม่ต้องใช้ arduino-LoRa library — ดู [[concepts/iot/lora-p2p]] สำหรับ code

## LoRa ใน Lab นี้

มี [[entities/iot/dx-lr02-lora]] × 2 ตัว → สามารถทำ **P2P LoRa link** ได้ทันที:
- ตัวที่ 1: Node (ห้องอื่น / ชั้นอื่น / ลานจอดรถ) ส่งข้อมูล sensor
- ตัวที่ 2: Gateway (ในห้อง, ต่อ WiFi, ส่งต่อไป MQTT broker)

## เปรียบเทียบกับ wireless อื่น

| Technology | Range | Power | Bandwidth | Use case |
|-----------|-------|-------|-----------|---------|
| WiFi | ~100m | สูง | สูง (Mbps) | Video, web |
| BLE | ~50m | ต่ำ | กลาง (1Mbps) | Wearables, beacons |
| Zigbee | ~100m | ต่ำ | ต่ำ | Home automation mesh |
| **LoRa** | **km** | **ต่ำมาก** | ต่ำมาก (kbps) | **Sensor networks** |
| NB-IoT | nationwide | ต่ำ | ต่ำ | เหมือน LoRa แต่ใช้ cellular |

## ความสัมพันธ์

- ใช้งานโดย: [[entities/iot/dx-lr02-lora]] (UART), [[entities/iot/rfm95-sx1276]] (SPI)
- ต่อกับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]
- Protocol บน LoRa: [[concepts/iot/lorawan]] (network) หรือ [[concepts/iot/lora-p2p]] (direct)
- เปรียบเทียบกับ: [[entities/iot/nb-iot]] (cellular LPWAN)
- เปรียบเทียบกับ: [[entities/iot/mqtt-protocol]] (LoRa เป็น transport, MQTT เป็น application protocol)

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — มี DX-LR02 × 2 ใน lab
- [[sources/esp32-lora-arduino-ide]] — P2P code basics
- [[sources/lora-thai-intro]] — Thailand frequency + กสทช.
- [[sources/lora-getting-started-dronebot]] — CSS technical detail
- [[sources/lora-vs-nbiot]] — LPWAN comparison


---

### `wiki/concepts/iot/lorawan.md`

---
type: concept
tags: [lorawan, lora, network-protocol, lpwan, ttn, chirpstack, iot-network]
sources: [lorawan-network-beginner, esp32-lora-gateway-sparkfun, lorawan-fuota-rak3172]
created: 2026-04-18
updated: 2026-04-18
---

# LoRaWAN

## นิยาม

LoRaWAN (Long Range Wide Area Network) คือ **network protocol** ที่ทำงานบน LoRa radio กำหนด rules สำหรับการ routing, security, และ device management ในเครือข่าย IoT ขนาดใหญ่ พัฒนาและดูแลโดย LoRa Alliance

> **LoRa ≠ LoRaWAN** — LoRa คือ radio technology (physical layer), LoRaWAN คือ network protocol (MAC layer ขึ้นไป)

## ทำไมถึงสำคัญใน IoT

LoRaWAN ทำให้ scale ระบบ IoT ได้จาก 1 node เป็นหลายพัน node บน gateway เดียวกัน พร้อม security (AES-128), device management, และ OTA update (FUOTA)

## วิธีการทำงาน

**Architecture (Star topology):**
```
[End-device A]──┐
[End-device B]──┤ ~~LoRa~~ [Gateway] ──IP──> [Network Server (LNS)]
[End-device C]──┘                                      ↓
                                             [Application Server]
                                                       ↓
                                               [Dashboard / App]
```

**3 Layers:**
| Layer | ส่วนประกอบ | หน้าที่ |
|-------|-----------|--------|
| Perception | End-device (sensor + LoRa module) | เก็บและส่งข้อมูล |
| Transport | Gateway | รับ LoRa signal, ส่งต่อทาง IP |
| Application | Network Server + Application Server | route, decrypt, ส่ง app |

## Device Classes

| Class | รับ downlink | Power | เหมาะกับ |
|-------|------------|-------|---------|
| A | หลัง uplink เท่านั้น (2 windows) | ต่ำที่สุด | sensor node, battery |
| B | beacon-synchronized slots | กลาง | actuator ที่ต้องรับ command |
| C | ตลอดเวลา (always-on) | สูง | mains-powered device |

## Security

- **OTAA** (Over-the-Air Activation): device join network ผ่าน DevEUI/AppKey — session keys สร้างใหม่ทุกครั้ง (แนะนำ)
- **ABP** (Activation by Personalization): hardcode session keys — ง่ายกว่าแต่ไม่ปลอดภัยเท่า
- Encryption: AES-128 ทั้ง network layer และ application layer

## Network Server Options

| Network Server | ประเภท | ข้อดี |
|----------------|--------|-------|
| The Things Network (TTN) | cloud, free tier | ง่าย, community ใหญ่ |
| ChirpStack | self-hosted, open-source | control เต็มที่, ไม่ขึ้น cloud |
| AWS IoT Core for LoRaWAN | managed cloud | integrate AWS ได้ |

## LoRaWAN vs LoRa P2P (โปรเจ็คนี้)

| หัวข้อ | LoRa P2P (โปรเจ็คนี้) | LoRaWAN |
|--------|----------------------|---------|
| Scale | 1-2 nodes | หลายพัน nodes |
| Gateway | ESP32-S3 custom | LoRaWAN-compliant HW |
| Network Server | ไม่มี | TTN/ChirpStack |
| Security | ไม่มี encryption | AES-128 |
| Setup | ง่าย | ซับซ้อน |
| ใช้เมื่อ | lab, prototype | production, scale-up |

## FUOTA (Firmware Update OTA)

LoRaWAN รองรับ Firmware Update Over-the-Air โดยส่ง firmware fragments ผ่าน multicast (Class C) — ดู [[sources/lorawan-fuota-rak3172]] สำหรับ demo

## ความสัมพันธ์

- Physical layer: [[concepts/iot/lora]]
- Protocol เปรียบเทียบ: [[concepts/iot/lora-p2p]]
- Network Server: [[entities/iot/the-things-network]]
- Hardware ที่เข้ากัน: [[entities/iot/rfm95-sx1276]]

## แหล่งข้อมูล

- [[sources/lorawan-network-beginner]] — architecture และ concept
- [[sources/esp32-lora-gateway-sparkfun]] — single-channel gateway + TTN
- [[sources/lorawan-fuota-rak3172]] — FUOTA demo


---

### `wiki/concepts/iot/modbus.md`

---
type: concept
tags: [modbus, protocol, industrial, rs485, serial, plc]
sources: [iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# Modbus

## นิยาม

Modbus เป็น serial communication protocol ที่เก่าแก่ที่สุดในอุตสาหกรรม (1979) ออกแบบมาสำหรับเชื่อมต่อ PLC กับ HMI ปัจจุบันยังใช้งานแพร่หลายมากในอุปกรณ์อุตสาหกรรม เช่น temperature controller, power meter, VFD, sensor transmitter

## ทำไมถึงสำคัญใน IoT

อุปกรณ์อุตสาหกรรมส่วนใหญ่ยังพูด Modbus เป็นภาษาหลัก ถ้าต้องการ integrate IoT กับเครื่องจักรในโรงงาน ต้องรู้ Modbus

## วิธีการทำงาน

**Modbus RTU** (serial RS-485):
```
[Master (Node-RED)]  ──RS485──  [Slave Device (e.g. Omron E5CC)]
     ↑ poll request                ↓ response (register value)
```

**Modbus TCP** (ethernet):
```
[Master] ──TCP/IP──  [Slave/Gateway]
```

**Register Types**:
| ประเภท | Address | ข้อมูล |
|--------|---------|--------|
| Coil | 0x | Digital output (R/W) |
| Discrete Input | 1x | Digital input (R) |
| Holding Register | 4x | Analog/config (R/W) |
| Input Register | 3x | Analog input (R) |

## ตัวอย่างการใช้งาน (Node-RED)

```
[Modbus Read node] ← ตั้งค่า: server, FC (function code), address, quantity
        ↓
[msg.payload = [28.5, 65.2]]   ← array ของ register values
        ↓
[Function node]               ← แปลง raw value เป็น temp/humidity
        ↓
[MQTT out node]               ← publish ต่อไปยัง Broker
```

## อุปกรณ์ที่รองรับ Modbus (ที่พบบ่อย)

- **Temp Controller**: Omron E5CC, Autonics TC
- **Power Meter**: PZEM-004T, Eastron SDM120
- **VFD (Inverter)**: Delta, Mitsubishi, Siemens
- **PLC**: Mitsubishi FX5U (Modbus TCP), Siemens (ผ่าน gateway)
- **Sensor Transmitter**: 4-20mA → Modbus converter

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| standard เก่า รองรับทุก device | ช้า (baud rate 9600-115200) |
| node-red-contrib-modbus ฟรี | poll-based ไม่ใช่ event-driven |
| debug ง่าย | max 247 slaves ต่อ bus |
| ไม่ต้องการ internet | ไม่มี encryption/auth |

## ความสัมพันธ์

- [[entities/iot/node-red]] — มี Modbus node สำหรับ read/write registers
- [[concepts/iot/publish-subscribe]] — ต่างจาก Modbus ตรงที่ Modbus เป็น request/response

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — Modbus TCP/RTU กับ Node-RED


---

### `wiki/concepts/iot/mqtt-qos.md`

---
type: concept
tags: [mqtt, qos, reliability, messaging]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# MQTT Quality of Service (QoS)

## นิยาม

QoS ใน MQTT กำหนดระดับความมั่นใจในการส่งข้อความ มี 3 ระดับ แต่ละระดับแลก tradeoff ระหว่าง reliability กับ performance

## ทำไมถึงสำคัญใน IoT

อุปกรณ์ IoT อยู่ในสภาวะเครือข่ายไม่เสถียร การเลือก QoS ผิดทำให้:
- QoS 0 บน sensor critical → ข้อมูลหายโดยไม่รู้ตัว
- QoS 2 บน sensor ที่อ่านทุกวินาที → battery และ bandwidth สิ้นเปลือง

## วิธีการทำงาน

| QoS | ชื่อ | Handshake | ผลลัพธ์ |
|-----|------|-----------|---------|
| 0 | At most once | ไม่มี | ส่งครั้งเดียว อาจหาย |
| 1 | At least once | PUBACK | รับแน่นอน อาจซ้ำ |
| 2 | Exactly once | PUBREC→PUBREL→PUBCOMP | รับแน่นอน ไม่ซ้ำ |

## ตัวอย่างการใช้งาน

- **QoS 0**: อุณหภูมิที่อ่านทุก 5 วินาที — หายไปครั้งนึงไม่เป็นไร
- **QoS 1**: การแจ้งเตือน door sensor เปิด — ต้องได้รับ ซ้ำได้รับมือได้
- **QoS 2**: คำสั่ง actuator (เปิด/ปิดวาล์ว) — ต้องทำครั้งเดียวเท่านั้น

## ข้อควรระวัง

- QoS เป็น end-to-end ระหว่าง publisher กับ broker และ broker กับ subscriber แยกกัน
- Broker อาจ downgrade QoS ถ้า subscriber ขอ QoS ต่ำกว่า
- QoS 2 ช้าที่สุด ใช้เฉพาะเมื่อ duplicate action มีผลเสีย

## ความสัมพันธ์

- ส่วนหนึ่งของ: [[entities/iot/mqtt-protocol]]
- แนวคิดพื้นฐาน: [[concepts/iot/publish-subscribe]]

## แหล่งข้อมูล

- [[sources/mqtt-introduction]]


---

### `wiki/concepts/iot/publish-subscribe.md`

---
type: concept
tags: [architecture, messaging, pattern, decoupling, iot-core]
sources: [mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# Publish-Subscribe Pattern

## นิยาม

Publish-Subscribe (pub/sub) เป็น messaging pattern ที่ผู้ส่งข้อความ (publisher) ไม่ส่งตรงถึงผู้รับ (subscriber) แต่ส่งผ่าน **broker** กลาง ผู้รับแจ้งความสนใจผ่าน **topics** และรับเฉพาะข้อความที่ตรงกัน

## ทำไมถึงสำคัญใน IoT

IoT มีอุปกรณ์จำนวนมากที่ต้องการแลกเปลี่ยนข้อมูลโดยไม่รู้จักกันล่วงหน้า Pub/sub แก้ปัญหานี้:
- อุปกรณ์ใหม่ subscribe เข้ามาได้โดยไม่กระทบระบบเดิม
- Publisher ไม่ต้องรู้ว่ามีใคร subscribe อยู่
- Broker ทำหน้าที่ buffer เมื่ออุปกรณ์ offline

## วิธีการทำงาน

```
[Sensor] --publish("home/temp", 25)--> [Broker] --forward--> [Dashboard]
                                                  --forward--> [AC Controller]
                                                  --forward--> [Logger]
```

## ตัวอย่างการใช้งาน

- MQTT topic: `factory/line-1/machine-3/temperature`
- Subscriber ของ `factory/#` ได้รับข้อมูลทุก machine ทุก line
- Subscriber ของ `factory/line-1/+/temperature` ได้เฉพาะอุณหภูมิ line-1

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| Decoupling สูง — publisher/subscriber ไม่รู้จักกัน | Broker เป็น single point of failure |
| Scale ได้ง่าย — เพิ่ม subscriber โดยไม่ต้องแก้ publisher | Debugging ยากกว่า request-response |
| Async — publisher ไม่ต้องรอ response | ไม่รู้ว่ามีคนรับข้อความหรือเปล่า (QoS 0) |
| Fan-out ง่าย — 1 message ถึงหลาย subscriber | Latency ขึ้นอยู่กับ broker |

## ความสัมพันธ์

- ใช้งานโดย: [[entities/iot/mqtt-protocol]]
- แนวคิดเกี่ยวข้อง: [[concepts/iot/mqtt-qos]]
- เปรียบเทียบกับ: Request-Response (HTTP pattern)

## แหล่งข้อมูล

- [[sources/mqtt-introduction]]


---

### `wiki/concepts/iot/tinyml.md`

---
type: concept
tags: [tinyml, edge-ai, machine-learning, esp32, tensorflow-lite, anomaly-detection]
sources: [tinyml-esp32-applications, tinyml-esp32-tutorial, vaccine-cae-anomaly-detection]
created: 2026-04-18
updated: 2026-04-18
---

# TinyML (Edge AI)

## นิยาม

TinyML คือการรัน Machine Learning model บน microcontroller หรืออุปกรณ์ขนาดเล็ก (RAM < 1MB, power < 1mW) ทำให้อุปกรณ์ IoT ตัดสินใจได้เอง โดยไม่ต้องส่งข้อมูลไปประมวลผลที่ cloud

## ทำไมถึงสำคัญใน IoT

- **Latency ต่ำ**: ตัดสินใจ ms แทนที่จะรอ round-trip ไป cloud
- **Privacy**: ข้อมูล sensor ไม่ออกนอกอุปกรณ์
- **Offline**: ทำงานได้แม้ไม่มี internet
- **ประหยัดพลังงาน**: ไม่ต้องส่ง raw data ตลอดเวลา

## วิธีการทำงาน

```
[Training บน PC/Cloud]              [Inference บน ESP32]
TensorFlow → Train model            model.tflite → C array
           → Quantize (int8)    →   TFLite Micro → MicroInterpreter
           → Export .tflite         sensor data  → predict()
```

**Workflow ด้วย Edge Impulse:**
1. เก็บ sensor data → อัปโหลดขึ้น Edge Impulse
2. ออกแบบ signal processing pipeline
3. Train model (Neural Network / Anomaly Detection)
4. Export เป็น Arduino library
5. Flash ลง ESP32

## ตัวอย่าง Use Cases

| Use Case | Input Sensor | Model Type |
|----------|-------------|-----------|
| Anomaly detection ตู้แช่วัคซีน | DS18B20 / PT100 | Convolutional Autoencoder |
| ตรวจจับท่าทาง (gesture) | Accelerometer | Dense Neural Network |
| Electronic nose | MQ gas sensors | Classification |
| ตรวจจับไฟป่า | Temp + smoke + optical | Multi-input NN |
| Predictive maintenance | Vibration + temp | Anomaly detection |
| Voice control | Microphone | Keyword spotting |

## Performance บน ESP32

จากงานวิจัย vaccine cold chain (Frontiers AI 2024):
- Model: Convolutional Autoencoder, ~9,500 parameters
- Memory: 1.2 MB
- Inference time: 200ms ± 15ms
- Power: 50mW ± 5mW
- Accuracy: 92%

## Tools & Frameworks

| Tool | หน้าที่ |
|------|--------|
| **Edge Impulse** | end-to-end platform (เก็บ data → train → deploy) |
| **TensorFlow Lite Micro** | inference framework บน MCU |
| **Arduino TensorFlowLite.h** | library สำหรับ Arduino/ESP32 |
| **PlatformIO** | IDE ที่แนะนำสำหรับ TinyML project |

## ข้อจำกัด

- RAM จำกัด: ต้อง quantize model เป็น int8 (ลด accuracy เล็กน้อย)
- Training ยังต้องใช้ PC/Cloud — แค่ inference เท่านั้นที่ on-device
- Model ซับซ้อนมากไม่ได้ — ESP32 S3 (8MB PSRAM) รับได้มากกว่า ESP32 classic
- ต้องมี training data เพียงพอ

## ความสัมพันธ์

- Hardware ML workload สูง: [[entities/iot/esp32-s3]] (16MB Flash + 8MB PSRAM)
- Hardware gateway + Edge AI เบา: [[entities/iot/esp32-c6]] (WiFi 6 + Thread/Zigbee)
- IDE: [[entities/iot/platformio]]
- Use case: [[concepts/iot/cold-chain-monitoring]], Smart Farm (soil + LoRa + C6)

## แหล่งข้อมูล

- [[sources/tinyml-esp32-applications]] — 6 use cases บน ESP32
- [[sources/tinyml-esp32-tutorial]] — step-by-step workflow
- [[sources/vaccine-cae-anomaly-detection]] — real research deployment


---

## Sources tagged with `iot`

### `wiki/sources/vaccine-temp-monitoring-iot.md`

---
type: source
title: "Vaccine Temperature Monitoring System using IoT (ESP32 + GSM)"
slug: vaccine-temp-monitoring-iot
date_ingested: 2026-04-18
original_file: https://github.com/MananDesai28/Vaccine-Temperature-Monitoring-System-using-IoT
tags: [esp32, vaccine, cold-chain, temperature, gsm, alert, cloud, iot]
---

# Vaccine Temperature Monitoring System using IoT

**ประเภท**: GitHub project (Hackathon — DU_HACKS)  
**ผู้เขียน**: MananDesai28

## ประเด็นหลัก

1. **Real-time monitoring**: ESP32 + temperature sensor วัดและส่งข้อมูลต่อเนื่อง
2. **GSM alert**: เมื่ออุณหภูมิเบี่ยงออกนอก range → SMS + phone call อัตโนมัติ
3. **Location tracking**: GPS location จาก driver's mobile device (สำหรับ vaccine transport)
4. **Cloud logging**: บันทึกข้อมูลขึ้น cloud platform (ไม่ระบุชัด — อาจเป็น Firebase)
5. **Cold chain compliance**: ออกแบบตาม WHO cold chain standard

## Hardware (จากที่ระบุ)

- ESP32 microcontroller
- Temperature sensor (ไม่ระบุรุ่น — น่าจะเป็น DS18B20 หรือ DHT22)
- GSM module (SIM800L หรือ SIM900)
- GPS module (สำหรับ location tracking)

## Alert Mechanism

```
อุณหภูมิ deviation → ESP32 detect → GSM module
                                        ↓
                                   SMS to phone
                                   + Voice call
```

## ประโยชน์สำหรับ wiki นี้

- Blueprint สำหรับ cold chain monitoring ในไทย
- GSM alert ไม่ต้องพึ่ง internet — เหมาะพื้นที่ห่างไกล
- สามารถแทนที่ GSM ด้วย Telegram bot หากมี internet

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/ds18b20]] — cold chain use case
- [[concepts/iot/cold-chain-monitoring]] — สร้างใหม่


---

### `wiki/sources/easyloranode-tracker.md`

---
type: source
title: "EasyLoRaNode_Tracker: Wearable LoRa Node with Battery"
slug: easyloranode-tracker
date_ingested: 2026-04-18
original_file: raw/IoTThinksEasyLoRaNode_Tracker A wearable LoRa node with battery for long range wearable projects.md
tags: [lora, esp32, wearable, deep-sleep, battery, github, tracker]
---

# EasyLoRaNode_Tracker: Wearable LoRa Node with Battery

**ประเภท**: GitHub project
**วันที่**: unknown
**ผู้เขียน**: IoTThinks (GitHub)

## ประเด็นหลัก

1. **Deep sleep < 15µA**: design เน้น ultra-low power — วัด battery voltage ด้วย BAT_METER pin
2. **ESP32-Pico-D4**: SoC รุ่นเล็ก (embedded flash) เหมาะ wearable ขนาดเล็ก
3. **LoRa SPI pins**: LORA_SS/SCK/MOSI/MISO/DIO0/DIO1/DIO2/RESET — ใช้ sandeepmistry/arduino-LoRa
4. **LORA_POWER pin**: สามารถปิด power LoRa module ได้เพื่อประหยัดพลังงาน

## Pin Mapping ที่น่าสนใจ

```cpp
#define LORA_POWER 21  // LOW=off, HIGH=on
#define LORA_SS    25
#define LORA_SCK   18
#define LORA_MOSI  23
#define LORA_MISO  19
#define LORA_DIO0  26
#define BAT_METER  36  // อ่าน battery voltage
```

## ข้อมูลที่น่าสนใจ

- Pattern `LORA_POWER` pin ให้ปิดโมดูล LoRa ทั้งหมดได้เมื่อไม่ใช้ — ประหยัดพลังงานมาก
- GPIO 16 ใช้โดย internal flash ของ Pico — ห้ามใช้

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

**Deep sleep + battery optimization** เป็นแนวคิดที่ apply ได้กับ ESP32 Sensor Node ในโปรเจ็คปัจจุบัน (Phase 5 ของ implementation plan)

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lora-p2p]] — เพิ่ม power optimization tip


---

### `wiki/sources/air-quality-iot-lora-network.md`

---
type: source
title: "AIR-QUALITY-IOT-NETWORK — Distributed LoRa + Kafka + Grafana"
slug: air-quality-iot-lora-network
date_ingested: 2026-04-18
original_file: https://github.com/Thweatt12/AIR-QUALITY-IOT-NETWORK
tags: [esp32, lora, pms5003, bme688, scd41, kafka, influxdb, grafana, raspberry-pi, air-quality]
---

# AIR-QUALITY-IOT-NETWORK

**ประเภท**: GitHub project (open source)  
**ผู้เขียน**: Thweatt12  
**Stack**: ESP32 + LoRa 915MHz + Raspberry Pi + Kafka + InfluxDB + Grafana

## ประเด็นหลัก

1. **Distributed network**: Sensor nodes → LoRa → Gateway → RPi → Kafka → InfluxDB → Grafana
2. **Sensors ต่อ node**: PMS5003 (PM1/2.5/10) + BME688 (Temp/Humidity/Pressure/VOC) + SCD41 (CO2)
3. **LoRa settings**: 915MHz, SF7, 125kHz BW, 14dBm TX, range ~2km
4. **Kafka แทน MQTT**: ใช้ Kafka สำหรับ message streaming (ไม่ใช่ MQTT ปกติ)
5. **Grafana dashboards**: PM2.5/PM10 trends, CO2, rolling averages, rate-of-change

## Full Architecture

```
[ESP32 Node + PMS5003 + BME688 + SCD41]
         ↓ LoRa 915MHz (SF7, 125kHz, 14dBm)
[ESP32 Gateway + OLED]
         ↓ USB Serial
[Raspberry Pi]  ← เพิ่ม RSSI/SNR metadata
         ↓ Kafka (topic: air_quality, 3 partitions, 7-day retention)
[Main PC — Docker Stack]
         ↓
[InfluxDB (bucket: sensor_data, 90-day retention)]
         ↓
[Grafana :3000]
```

## LoRa Packet Format

แต่ละ packet ประกอบด้วย:
- Node ID
- PM1.0, PM2.5, PM10
- Temperature, Humidity, Pressure, VOC
- CO2
- Packet count (สำหรับ detect packet loss)

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

**ตรงมาก** — architecture แบบเดียวกับที่เราใช้ (ESP32 + LoRa + RPi + Grafana) แต่ใช้ Kafka แทน MQTT และ sensors ครบกว่ามาก เหมาะเป็น reference สำหรับ scale up

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/pms5003]] — สร้างใหม่
- [[concepts/iot/air-quality-index]] — สร้างใหม่


---

### `wiki/sources/iot-visualization-guide.md`

---
type: source
title: "IoT Visualization Guide: Designing Effective Dashboards & Monitoring UIs"
slug: iot-visualization-guide
date_ingested: 2026-04-18
original_file: raw/IoT Visualization Guide Designing Effective Dashboards & Monitoring UIs.md
tags: [dashboard, visualization, iot, ux, real-time, gauge, chart, alert]
---

# IoT Visualization Guide: Dashboards & Monitoring UIs

**ประเภท**: video (YouTube — CodeLucky)
**วันที่**: 2025-12-31
**ผู้เขียน**: CodeLucky

## ประเด็นหลัก

1. **Sensor to Screen pipeline**: Raw sensor data → Transmit → Cloud/broker → Dashboard UI
2. **Widget selection**: Gauge เหมาะค่า current (ปัจจุบัน), Graph เหมาะ trend ย้อนหลัง
3. **Real-time data handling**: ต้องรองรับ high-frequency update โดยไม่ freeze UI
4. **Alert system**: threshold-based alert ต้องชัดเจน สีแดง/เขียว/เหลือง
5. **Layout hierarchy**: ข้อมูลสำคัญ = ใหญ่/บนซ้าย; รายละเอียด = เล็กกว่า/ด้านล่าง

## Dashboard Components ที่ดี

| Widget | ใช้กับ | อย่าใช้กับ |
|--------|--------|-----------|
| Gauge / Donut | ค่าปัจจุบัน, threshold | trend ย้อนหลัง |
| Line Chart | trend, เปรียบเทียบเวลา | ค่าเดียว |
| Bar Chart | เปรียบเทียบ category | time series ต่อเนื่อง |
| Number / Text | ค่าล่าสุด, count | ซับซ้อน |
| Alert indicator | status, threshold breach | ข้อมูลปกติ |

## Best Practices

- **Avoid clutter**: แสดงเฉพาะข้อมูลที่ operator ต้องการตัดสินใจ
- **Consistent color**: สี = ความหมาย (เขียว=ปกติ, เหลือง=เตือน, แดง=วิกฤต) ทั้ง dashboard
- **Timestamp visible**: ทุก panel ต้องเห็น "last updated" เสมอ
- **Mobile-ready**: dashboard ต้องอ่านได้บนมือถือ

## Apply กับโปรเจ็คปัจจุบัน

| Data | Widget แนะนำ | Platform |
|------|------------|---------|
| อุณหภูมิปัจจุบัน | Gauge (0-50°C) | Grafana |
| ความชื้นปัจจุบัน | Gauge (0-100%) | Grafana |
| อุณหภูมิ 24h | Line Chart | Grafana |
| Alert status | Alert indicator | Telegram Bot |

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/dashboard-design]] — สร้างใหม่


---

### `wiki/sources/iot-nodered-mqtt-sql-course.md`

---
type: source
title: "IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม"
slug: iot-nodered-mqtt-sql-course
date_ingested: 2026-04-18
original_file: raw/"IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม".md
tags: [node-red, mqtt, mysql, grafana, modbus, industrial-iot, dashboard, data-logger]
---

# IoT Node-RED + MQTT + SQL – ทำ Data Logger & Dashboard แบบอุตสาหกรรม

**ประเภท**: course (รายละเอียดหลักสูตร)
**วันที่**: unknown
**ผู้เผยแพร่**: plcsnook.com

## ประเด็นหลัก

1. **Node-RED เป็น middleware หลัก** — รับข้อมูลจาก MQTT → ประมวลผล → บันทึก MySQL → แสดงผล Grafana ได้ในระบบเดียว
2. **Stack อุตสาหกรรม**: MQTT (Mosquitto) + Node-RED + MySQL + Grafana ใช้งานได้จริงใน industrial setting
3. **รองรับ PLC** — เชื่อม PLC Siemens S7-1200 และ Mitsubishi QCPU/FX5U ผ่าน Node-RED โดยตรง
4. **Modbus RTU/TCP** — Node-RED มี Modbus node รองรับอุปกรณ์ RS485 (Temp Controller, Power Meter, VFD)
5. **MySQL เป็น data store** — ต่างจาก InfluxDB ตรงที่ใช้ SQL relational DB เหมาะสำหรับ Data Logger ที่ต้องการ query ยืดหยุ่น

## Stack ที่สอนในหลักสูตร

```
Sensor / PLC
     ↓
   MQTT (Mosquitto)
     ↓
  Node-RED          ← รับข้อมูล, ประมวลผล Flow
     ↓
  MySQL             ← Data Logger (บันทึก historical)
     ↓
  Grafana           ← Dashboard (connect MySQL datasource)
```

## 7 Parts ของหลักสูตร

| Part | หัวข้อ | เกี่ยวข้องกับโปรเจ็ค |
|------|--------|---------------------|
| 1 | Node-RED Basic + Dashboard UI | ✅ สูง |
| 2 | MQTT System (Mosquitto) | ✅ สูง |
| 3 | MySQL + Data Logger | ✅ สูง |
| 4 | PLC Siemens S7-1200 | ⬜ ไม่เกี่ยว |
| 5 | Modbus TCP/RTU | ⬜ อนาคต |
| 6 | Grafana Advanced | ✅ สูง |
| 7 | Mobile Access (Remote-RED) | ⬜ optional |

## ข้อมูลที่น่าสนใจ

- Node-RED สามารถเชื่อม MySQL โดยตรงโดยไม่ต้องใช้ Telegraf
- Grafana รองรับ MySQL เป็น data source ได้ (ไม่ต้องใช้ InfluxDB เสมอไป)
- Remote-RED App ให้ access Dashboard จากมือถือนอก network

## ข้อโต้แย้งหรือความขัดแย้ง

**Architecture ทางเลือก**: Source นี้เสนอ stack **MQTT → Node-RED → MySQL → Grafana** ซึ่งแตกต่างจาก architecture ปัจจุบันในโปรเจ็คที่ใช้ **Telegraf → InfluxDB → Grafana**
- MySQL: SQL query ยืดหยุ่น, เข้าใจง่าย แต่ไม่ใช่ time-series DB โดยตรง
- InfluxDB: optimized สำหรับ time-series, query ทรงพลังกว่าสำหรับ sensor data

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/node-red]] — สร้างใหม่
- [[entities/iot/mysql]] — สร้างใหม่
- [[concepts/iot/data-logger]] — สร้างใหม่
- [[concepts/iot/modbus]] — สร้างใหม่
- [[entities/iot/grafana]] — เพิ่ม MySQL datasource alternative


---

### `wiki/sources/esp32-complete-guide-thai.md`

---
type: source
title: "ESP32 คู่มือฉบับสมบูรณ์ พร้อมสอนติดตั้งและใช้งาน"
slug: esp32-complete-guide-thai
date_ingested: 2026-04-18
original_file: raw/ESP32 คู่มือฉบับสมบูรณ์ พร้อมสอนติดตั้งและใช้งาน.md
tags: [esp32, thai, overview, specs, deep-sleep, iot, smart-farm]
---

# ESP32 คู่มือฉบับสมบูรณ์ (Thai)

**ประเภท**: article (ภาษาไทย)
**วันที่**: 2025-12-08
**ผู้เผยแพร่**: Global Byte Shop (globalbyteshop.com)

## ประเด็นหลัก

1. **ESP32 = SoC** — รวม Dual-core CPU + WiFi + Bluetooth + peripherals ในชิปเดียว (ไม่ใช่แค่ MCU)
2. **Dual-core Xtensa LX6 240MHz** — สามารถรัน 2 tasks พร้อมกันได้ (เช่น LoRa receive + WiFi publish)
3. **Touch Pins** — ESP32 classic มี capacitive touch sensor 10 pins (T0-T9)
4. **Deep Sleep ~10µA** — ประหยัดพลังงานสูง เหมาะ battery-powered sensor node
5. **Arduino IDE compatible** — เพิ่ม ESP32 Board Manager ผ่าน JSON URL

## Key Specs

| คุณสมบัติ | รายละเอียด |
|----------|-----------|
| CPU | Xtensa LX6 dual-core 240MHz |
| RAM | 512KB SRAM |
| Flash | ขึ้นอยู่กับรุ่น (4MB–16MB external) |
| WiFi | 802.11 b/g/n 2.4GHz |
| Bluetooth | Classic 4.2 + BLE |
| Touch pins | 10 pins capacitive |
| Deep sleep | ~10µA |
| ADC | 18 channels 12-bit |
| UART/SPI/I2C | 3/4/2 |

## Arduino Board Manager URL

```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

## ข้อมูลที่น่าสนใจ

- ESP32 แรงกว่า Arduino UNO มาก — แต่ยังใช้ Arduino IDE ได้
- เหมาะ Smart Home, Smart Farm ที่ต้องการ WiFi + sensor พร้อมกัน
- ESP32-S3 คือรุ่นใหม่ที่แรงกว่า (Xtensa LX7, USB native, BLE 5.0)

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp32]] — ยืนยัน specs, เพิ่ม touch pin, deep sleep note
- [[entities/iot/arduino-ide]] — สร้างใหม่ (Board Manager URL)


---

### `wiki/sources/lora-thai-intro.md`

---
type: source
title: "#1 LoRa Arduino ESP8266 ESP32 IoT อะไรคือ LoRa ใช้งาน LoRa อย่างไร"
slug: lora-thai-intro
date_ingested: 2026-04-18
original_file: raw/1 LoRa Arduino ESP8266 ESP32 IoT อะไรคือ LoRa ใช้งาน LoRa อย่างไร.md
tags: [lora, thailand, frequency, arduino, intro, thai]
---

# #1 LoRa Arduino ESP8266 ESP32 IoT อะไรคือ LoRa ใช้งาน LoRa อย่างไร

**ประเภท**: article (ภาษาไทย)
**วันที่**: unknown
**ผู้เผยแพร่**: allnewstep.com

## ประเด็นหลัก

1. **LoRa ในไทย**: ใช้ได้ที่ 433MHz และ 920-925MHz — กสทช. อนุญาตแล้ว กำลังส่งสูงสุด 4W
2. **LoRa ย่อมาจาก Long Range** — ไม่ใช่ชื่อโปรโตคอล แต่คือชื่อเรียก technology ที่ใช้ Semtech chip
3. **เหมาะกับ**: sensor node ใช้แบตเตอรี่ก้อนเล็ก, สมาร์ทฟาร์ม, M2M
4. **ไม่เหมาะกับ**: ส่งข้อมูลมาก, ส่งบ่อย, เครือข่ายใหญ่

## ข้อมูลสำคัญเฉพาะไทย

- **433MHz**: ใช้ได้ในไทย (เอเชีย band)
- **920-925MHz**: กสทช. อนุญาตเพิ่มเติม — **DX-LR02 ของโปรเจ็คใช้ 900MHz band** ซึ่งตรงกับ range นี้ ✅
- เอกสาร กสทช.: ราชกิจจานุเบกษา 2560

## ข้อโต้แย้งหรือความขัดแย้ง

ยืนยันว่า DX-LR02 (900MHz) ใช้ในไทยได้ถูกกฎหมาย

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lora]] — เพิ่ม Thailand frequency detail
- [[entities/iot/dx-lr02-lora]] — ยืนยัน legal status ในไทย


---

### `wiki/sources/mqtt-introduction.md`

---
type: source
title: "MQTT: The Standard Messaging Protocol for IoT"
slug: mqtt-introduction
date_ingested: 2026-04-18
original_file: raw/mqtt-introduction.md
tags: [mqtt, protocol, messaging, broker, iot-core]
---

# MQTT: The Standard Messaging Protocol for IoT

**ประเภท**: article (example — wiki initialization)  
**วันที่**: 2026-04-18  
**ผู้เขียน**: ตัวอย่างสำหรับการเริ่มต้น wiki

## ประเด็นหลัก

1. MQTT เป็น publish-subscribe protocol ที่ออกแบบมาเพื่อ IoT โดยเฉพาะ มี overhead ต่ำมาก (fixed header 2 bytes)
2. ใช้ Broker เป็นศูนย์กลาง ทำให้อุปกรณ์ไม่ต้องคุยกันตรงๆ — scalable และ decoupled
3. มี 3 ระดับ QoS: fire-and-forget / at-least-once / exactly-once
4. MQTT 5.0 เพิ่ม features สำคัญ เช่น shared subscriptions, message expiry, user properties
5. รองรับ TLS บนพอร์ต 8883 และ client certificate authentication

## ข้อมูลที่น่าสนใจ

- MQTT เก่าแก่มาก ถูกออกแบบในปี 1999 สำหรับ monitoring pipeline น้ำมันผ่านดาวเทียม
- ใช้ battery น้อยกว่า HTTP ถึง ~2 เท่า สำหรับ payload ขนาดเล็ก
- Home Assistant ใช้ MQTT เป็นโปรโตคอลหลัก
- EMQX อ้างว่ารองรับ 100 ล้าน concurrent connections

## ข้อโต้แย้ง / ความขัดแย้ง

*(wiki ยังใหม่ ยังไม่มีข้อมูลเดิมให้เปรียบเทียบ)*

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/mqtt-protocol]] — สร้างใหม่
- [[entities/iot/mosquitto]] — สร้างใหม่
- [[entities/iot/home-assistant]] — สร้างใหม่
- [[concepts/iot/publish-subscribe]] — สร้างใหม่
- [[concepts/iot/mqtt-qos]] — สร้างใหม่


---

### `wiki/sources/ai-iot-server-build-v3.md`

---
type: source
title: "Personal AI & IoT Server Build List (v3)"
slug: ai-iot-server-build-v3
date_ingested: 2026-05-05
original_file: raw/ai-iot-server-build-v3-final.md
source_type: ai-generated-build-spec
url: null
tags: [local-llm, pc-build, ai-server, iot-server, ryzen, rtx-4070-ti-super, ddr5, 24-7]
---

# Personal AI & IoT Server Build List (v3)

**ประเภท**: AI-generated build spec (PDF)
**วันที่อ้างอิง**: พฤษภาคม 2026
**ผู้เขียน**: AI Assistant (ไม่ระบุตัว)

## ประเด็นหลัก

1. **PC build ราคา ~98,500฿** — เน้นใช้งาน 24/7 สำหรับ Local LLM (70B+), IoT Monitor, AI Agent, Web Server
2. **CPU เน้นประหยัดไฟ** — Ryzen 7 9700X เปิด Eco Mode 65W TDP (จาก 105W default) เหมาะ 24/7
3. **RAM 128GB DDR5** — 4 แถว 32GB เพื่อรองรับ context ใหญ่ + multi-app
4. **GPU 16GB VRAM** — RTX 4070 Ti Super (16GB) เป็น sweet spot ราคา-ประสิทธิภาพ ปี 2026
5. **Storage แยก SSD/HDD** — 2TB NVMe สำหรับ OS+model, 8TB HDD NAS-grade สำหรับ IoT data
6. **เคสเล็ก SFX form factor** — Jonsbo TK-1 v2 + Noctua NH-L9x65 (low-profile cooler) เน้นเงียบ + วางในห้องนั่งเล่น

## สเปก (สรุป)

| Component | Model | ราคา (฿) |
|---|---|---|
| CPU | Ryzen 7 9700X (Eco 65W) | 12,000 |
| Mainboard | ASRock B860M Pro RS ⚠️ | 5,500 |
| RAM | 128GB DDR5-5600 (Kingston FURY Beast) | 20,000 |
| GPU | RTX 4070 Ti Super 16GB | 34,000 |
| SSD | Samsung 990 Pro 2TB NVMe Gen4 | 5,000 |
| HDD | 8TB WD Red Plus / Seagate IronWolf | 8,500 |
| Case | Jonsbo TK-1 v2 (กระจก 270°) | 5,000 |
| PSU | Cooler Master V750 SFX Gold | 5,000 |
| Cooler | Noctua NH-L9x65 (low-profile) | 3,500 |
| **รวม** | | **98,500** |

## ⚠️ ข้อโต้แย้งหรือความขัดแย้ง

### 1. Mainboard ระบุ chipset ผิด (Critical Error)

**ปัญหา**: PDF ระบุ **"ASRock B860M Pro RS"** — แต่ chipset **B860 เป็นของ Intel** (LGA1851 socket, ใช้กับ Core Ultra 200 series) ไม่ใช่ของ AMD

AMD Ryzen 7 9700X ใช้ **socket AM5** ซึ่งต้องคู่กับ chipset ตระกูล:
- A620 / B650 / B650E (รุ่นแรก ปี 2022)
- B850 / B850E / X870 / X870E (รุ่นใหม่ ปี 2024-2025)

**คาดว่าตั้งใจจะหมายถึง**: **ASRock B850M Pro RS** (AM5 chipset ชื่อใกล้เคียง) — น่าจะเป็น typo หรือ AI hallucination ของผู้สร้าง PDF

**ก่อนซื้อต้องตรวจสอบ**: ขอ verify ชื่อ board ที่ถูกต้องกับร้านอีกครั้ง — board ที่เลือกต้อง socket AM5 และมี 4 RAM slots รองรับ DDR5-5600+ (เช่น B850M Pro RS, B850 Tomahawk, X870 ในงบสูงขึ้น)

### 2. 16GB VRAM กับ Local LLM 70B+

PDF อ้าง use case "Local LLM 70B+" แต่:
- 70B model Q4 quantized ต้องใช้ VRAM ~40GB (เกิน 16GB VRAM ของ 4070 Ti Super มาก)
- 16GB VRAM เหมาะกับ 7B-14B Q4 (รันใน VRAM เต็ม), หรือ 32B แบบ partial offload
- รัน 70B จะต้อง **offload ไป system RAM (128GB)** ซึ่งทำได้แต่ช้ากว่ารันใน VRAM ล้วนๆ มาก (~2-5 tok/s แทนที่จะ 10+ tok/s)
- เทียบ Mac Studio M4 Max 64GB unified memory จะรัน 70B ได้ดีกว่าด้วย bandwidth สูง (ดู [[sources/local-llm-mac-mini-guide]])

**สรุป**: spec นี้เหมาะรัน 7B-32B ลื่นๆ + 70B แบบช้า — ถ้าต้องการ 70B เร็วๆ ควรพิจารณา GPU ที่มี VRAM สูงขึ้น (RTX 5090 32GB หรือ 2x GPU)

### 3. RAM 128GB อาจมากเกินจำเป็น

128GB DDR5 4 แถวที่ 5600MHz มักรันที่ความเร็วลดลง (DDR5 มี signal integrity issue กับ 4 DIMM) — Ryzen 9000 series มัก stable ที่ 5200-5600 ด้วย 4 แถว แต่บางเครื่อง drop ไป 4800

**ทางเลือก**: 64GB (32GB x 2) ลดราคา ~10,000฿ และได้ความเร็วเต็ม 5600+ — ถ้าใช้ 70B ผ่าน CPU offload จริงๆ ค่อย upgrade เพิ่ม

## Technician Checklist (สำคัญ)

1. **Memtest86 อย่างน้อย 4 ชั่วโมง** ใส่ครบ 4 แถว — สำคัญมากสำหรับ 24/7
2. **BIOS update + AMD Eco Mode 65W + XMP/EXPO 5200-5600MHz**
3. **GPU ความยาวไม่เกิน 270-280mm** — TK-1 v2 พื้นที่จำกัด, แนะนำรุ่น 2 พัดลม
4. **HDD ต้องเป็น NAS-grade (WD Red Plus, IronWolf)** — ออกแบบมาสำหรับ 24/7 workload
5. **Cable management** — เคสกระจกใส โชว์รอบด้าน
6. **Fan curve เงียบ** — รัน 24/7 ในห้องนั่งเล่น

## Cross-references

- เปรียบเทียบกับแนวทาง Mac → [[synthesis/local-llm-pc-vs-mac-2026]]
- พื้นฐาน Local LLM bandwidth/RAM rules → [[sources/local-llm-mac-mini-guide]]
- Routing pattern (local + cloud) → [[concepts/ai-tools/local-llm-routing]]
- ทางเลือกเริ่มต้นบน Pi5 → [[sources/ollama-pi5]], [[sources/rpi-ai-hat-plus-2-official]]

## หน้า Wiki ที่ได้รับการอัปเดต

- [[synthesis/local-llm-pc-vs-mac-2026]] — สร้างใหม่ (synthesis เปรียบเทียบ PC vs Mac)
- [[index-ai]] — เพิ่ม source + synthesis ใหม่


---

### `wiki/sources/iot-lora-gateway-architecture.md`

---
type: source
title: "IoT Architecture Diagram: ESP32 + LoRa + MQTT + Services"
slug: iot-lora-gateway-architecture
date_ingested: 2026-04-18
original_file: raw/iot-lora-gateway-architecture.md
tags: [architecture, lora, esp32, esp32-s3, mqtt, telegram, grafana, line-notify, project-plan]
---

# IoT Architecture Diagram: ESP32 + LoRa + MQTT + Services

**ประเภท**: Architecture decision diagram (SVG)  
**วันที่**: 2026-04-18

## ประเด็นหลัก

1. **Architecture ถูกตัดสินใจแล้ว** — เลือก Approach C (LoRa P2P) ไม่ใช่ WiFi direct
2. **Role ของ hardware ชัดเจน**: ESP32 DevKit = Sensor Node, ESP32-S3 = Gateway
3. **Services ที่ต้องการ**: Telegram Bot + Line Notify + Grafana (3 services พร้อมกัน)
4. MQTT Broker = Mosquitto (ยืนยัน choice จาก wiki เดิม)

## สิ่งที่ยังต้องตัดสินใจ

- Mosquitto จะรันที่ไหน? (RPi / VPS / Mac local)
- InfluxDB: local หรือ cloud? (Grafana ต้องการ data source)
- Line Notify vs Line Messaging API (Line Notify deprecate แล้วปี 2025)

## ความขัดแย้งกับ wiki เดิม

- synthesis/temperature-monitor-project เสนอ 3 แนวทาง — ตอนนี้ **ยืนยัน Approach C (LoRa)** แล้ว → ต้องอัปเดตหน้านั้น

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/telegram-bot]] — สร้างใหม่
- [[entities/iot/line-notify]] — สร้างใหม่
- [[entities/iot/grafana]] — สร้างใหม่
- [[entities/iot/influxdb]] — สร้างใหม่
- [[synthesis/temperature-monitor-project]] — อัปเดต: ยืนยัน approach C
- [[synthesis/iot-lora-architecture]] — สร้างใหม่ (architecture เต็ม)


---

### `wiki/sources/raspberry-pi-iot-guide.md`

---
type: source
title: "Raspberry Pi and IoT: the guide to understanding their role in the Internet of Things"
slug: raspberry-pi-iot-guide
date_ingested: 2026-04-18
original_file: raw/Raspberry Pi and IoT the guide to understanding their role in the Internet of Things.md
tags: [raspberry-pi, iot, gateway, edge-computing, home-assistant, mosquitto, python]
---

# Raspberry Pi and IoT: The Complete Guide

**ประเภท**: article / guide
**วันที่**: unknown
**ผู้เผยแพร่**: monraspberry.com

## ประเด็นหลัก

1. **RPi เป็น "intelligent gateway"** — เก็บข้อมูลจาก sensor, ประมวลผล, ส่งต่อ cloud หรือ local server
2. **3 บทบาทหลัก**: IoT Gateway, Edge Computing node, Home Automation Server
3. **Protocol รองรับ**: WiFi, Bluetooth, Ethernet, GPIO, Zigbee, Z-Wave, LoRa, LTE dongle
4. **ราคา**: Pi Zero ~€5 ถึง Pi 5 ~€100 — ยังถูกสำหรับ production deployment
5. **Software stack**: Home Assistant, Node-RED, Mosquitto รันบน RPi ได้ดี

## บทบาทใน IoT

| บทบาท | รายละเอียด | เหมาะกับโปรเจ็คนี้ |
|-------|-----------|-------------------|
| **IoT Gateway** | รับ sensor data → ส่งต่อ cloud/local | ✅ รัน Mosquitto broker |
| **Edge Computing** | วิเคราะห์ data ก่อนส่ง cloud | ⬜ อนาคต |
| **Home Automation** | รัน Home Assistant, Node-RED | ⬜ optional |

## เหมาะกับโปรเจ็คนี้อย่างไร

RPi เป็นตัวเลือกที่ดีสำหรับ **production deployment ของ Mosquitto broker**:
- ใช้ไฟน้อย (เปิดตลอด 24 ชั่วโมงได้)
- รัน Mosquitto + Telegraf + InfluxDB + Grafana ได้พร้อมกัน
- ราคาถูก (Pi 4 ~$35–75)
- Linux OS ทำให้ต่อยอดได้ไม่จำกัด

ปัจจุบันโปรเจ็คใช้ Mac local สำหรับ dev — RPi เป็น upgrade path สำหรับ production

## ข้อมูลที่น่าสนใจ

- RPi 5 มี PCIe connector — รองรับ NVMe SSD ได้
- RPi Zero W (~€15) เพียงพอสำหรับ Mosquitto broker ขนาดเล็ก

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/raspberry-pi]] — สร้างใหม่


---

### `wiki/sources/lora-vs-nbiot.md`

---
type: source
title: "เครื่องวัดน้ำ LoRa-NB-IoT: การวิเคราะห์เปรียบเทียบ LoRa และ NB-IoT"
slug: lora-vs-nbiot
date_ingested: 2026-04-18
original_file: raw/เครื่องวัดน้ำ LoRa-nb iot เครื่องวัดน้ำ-เครื่องวัดน้ำอัจฉริยะ.md
tags: [lora, nb-iot, lpwan, comparison, smart-meter]
---

# เครื่องวัดน้ำ LoRa-NB-IoT: เปรียบเทียบ LoRa และ NB-IoT

**ประเภท**: article (ภาษาไทย)
**วันที่**: 2022-04-06
**ผู้เขียน**: เหอเป่ย ซ่างหง เมตร เทคโนโลยี บจก.

## ประเด็นหลัก

1. **LPWAN 2 ค่าย**: LoRa (unlicensed, private network) vs NB-IoT (licensed cellular, operator network)
2. **LoRa ข้อดี**: ไม่มีค่าบริการรายเดือน, ตั้ง private network เองได้, ราคา node ถูก
3. **NB-IoT ข้อดี**: coverage ทั่วประเทศ (ใช้ cell tower), ไม่ต้องติดตั้ง gateway, QoS ดีกว่า
4. **LoRa ใช้ frequency ไม่มีใบอนุญาต** < 1GHz — ไม่มีค่าใช้จ่าย spectrum
5. **NB-IoT ใช้ licensed band** — ต้องจ่าย operator (AIS/DTAC/True ไทย)

## ตารางเปรียบเทียบ

| หัวข้อ | LoRa | NB-IoT |
|--------|------|--------|
| Frequency | unlicensed (433/868/915 MHz) | licensed cellular |
| Infrastructure | ต้องติดตั้ง gateway เอง | ใช้ tower cellular |
| ค่าใช้จ่าย | ถูก (hardware only) | มีค่าบริการ monthly |
| Coverage | เฉพาะ gateway range | nationwide |
| Power | ต่ำมาก | ต่ำ |
| QoS | ไม่มี guarantee | มี |
| เหมาะกับ | private IoT, lab, farm, factory | nationwide deployment |

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — ยืนยัน lora.md ที่มี NB-IoT ในตาราง

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/nb-iot]] — สร้างใหม่
- [[concepts/iot/lora]] — เพิ่ม LPWAN comparison context


---

### `wiki/sources/esp32-s3-intro-thai.md`

---
type: source
title: "การเริ่มต้นใช้งานชิป Espressif ESP32-S3 - IoT Engineering Education"
slug: esp32-s3-intro-thai
date_ingested: 2026-04-18
original_file: raw/การเริ่มต้นใช้งานชิป Espressif ESP32-S3 - IoT Engineering Education.md
tags: [esp32-s3, espressif, xtensa-lx7, usb-otg, ble5, pie, specs, thai]
---

# การเริ่มต้นใช้งานชิป Espressif ESP32-S3

**ประเภท**: article (ภาษาไทย)
**วันที่**: unknown
**ผู้เขียน**: RSP (iot-kmutnb.github.io — KMUTNB IoT Engineering)

## ประเด็นหลัก

1. **Xtensa LX7 dual-core 240MHz** — เร็วกว่า LX6 ของ ESP32 classic ประมาณ 40%
2. **PIE (Processor Instruction Extensions)** — 128-bit SIMD operations สำหรับ DSP/ML inference
3. **USB-OTG built-in** — USB host + device, ไม่ต้อง CH340/CP2102
4. **Bluetooth LE 5.0** — ไม่มี Classic BT (ต่างจาก ESP32 classic)
5. **Released December 2020** — ใช้ TSMC 40nm ultra-low-power process

## Chip Variants ของ ESP32-S3

| Variant | Flash | PSRAM |
|---------|-------|-------|
| ESP32-S3 | external only | ไม่มี |
| ESP32-S3R2 | external | 2MB |
| ESP32-S3R8 | external | 8MB |
| ESP32-S3R8V | external | 8MB (1.8V) |
| ESP32-S3FN8 | 8MB built-in | ไม่มี |
| ESP32-S3FH4R2 | 4MB built-in | 2MB |

**ใน Lab**: ESP32-S3-N16R8 = 16MB Flash external + 8MB PSRAM = รุ่น top ใน lab นี้

## เปรียบเทียบ ESP32-S2 vs ESP32-S3

| Feature | ESP32-S2 | ESP32-S3 (ใน lab) |
|---------|---------|-------------|
| CPU | LX7 single-core | LX7 dual-core |
| Bluetooth | ❌ | ✅ BLE 5.0 |
| SRAM | 320 KB | 512 KB |
| AI (PIE) | ✅ | ✅ |
| USB OTG | ✅ | ✅ |

## ข้อมูลที่น่าสนใจ

- PIE extension เหมาะมาก TinyML: keyword spotting, anomaly detection ใน sensor data
- N16R8 = ชื่อรุ่น: **N**16 (16MB flash, **N**OR flash) + **R**8 (8MB psRAM)

## ข้อโต้แย้งหรือความขัดแย้ง

ไม่มี — ยืนยัน specs ที่มีใน esp32-s3.md

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp32-s3]] — เพิ่ม PIE, chip variants table, LX7 details


---

### `wiki/sources/iot-edge-ai-esp32-c6-2026.md`

---
type: source
title: "สรุปสาระสำคัญ: สถาปัตยกรรม IoT, Edge AI และศักยภาพของ ESP32-C6 (อัปเดตปี 2026)"
slug: iot-edge-ai-esp32-c6-2026
date_ingested: 2026-05-13
original_file: paste-text
tags: [esp32-c6, edge-ai, tinyml, iot-architecture, smart-farm, lora, espressif]
---

# สรุปสาระสำคัญ: สถาปัตยกรรม IoT, Edge AI และ ESP32-C6 (2026)

**ประเภท**: synthesized article (paste text)  
**วันที่**: 2026  
**ผู้เขียน**: ไม่ระบุ (บทสรุปวิชาวิศวกรรม IoT ระบบอัตโนมัติ และ AI)  
**URL อ้างอิง**: https://www.espressif.com/en/products/socs/esp32-c6

## ประเด็นหลัก

1. **IoT + Edge AI ในปี 2026** — ระบบ IoT เปลี่ยนจาก cloud-centric → Edge AI (ประมวลผลที่ปลายทาง) ช่วยลด latency และรักษา privacy
2. **ESP32-C6 คือตัวเลือกหลักของ Smart Home** — รองรับ WiFi 6, BLE 5, Thread/Zigbee ในชิปเดียว
3. **TinyML กระบวนการ 2 ขั้น** — Training บน PC/Cloud → Inference (compressed model) บน MCU
4. **Smart Farm 2026** — ESP32-C6 เป็น gateway รับข้อมูลจาก LoRa sensor nodes + Edge AI ตัดสินใจเปิดวาล์วน้ำ + แจ้งเตือนผ่าน WiFi 6
5. **ESP32 variant comparison** — source กล่าวถึงการเปรียบเทียบ ESP32 หลายรุ่น (ไม่ได้ detail ครบ)

## ข้อมูลที่น่าสนใจ

- Edge AI ลด latency จาก cloud round-trip → ms on-device
- ESP32-C6 ใช้ WiFi 6 (802.11ax) — ไม่ถูกรบกวนจาก camera streams ในฟาร์ม
- TinyML anomaly detection: เซ็นเซอร์สั่นสะเทือนบนเครื่องจักร → ตรวจพบความผิดปกติได้ทันทีแม้ไม่มี internet
- LoRa สำหรับ Smart Farm: ส่งได้ไกลระดับ km แต่ bandwidth ต่ำ (เหมาะ soil moisture, ไม่เหมาะ video)

## ข้อโต้แย้งหรือความขัดแย้ง

- Source ระบุ ESP32-C6 เป็น "Smart Home hero" แต่ wiki เดิมระบุ ESP32-S3 เป็น hardware แนะนำสำหรับ TinyML (เพราะ PSRAM มาก) — ไม่ขัดแย้ง: C6 เด่นด้านการเชื่อมต่อ / S3 เด่นด้าน ML workload

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp32-c6]] — สร้างใหม่
- [[entities/iot/esp32]] — เพิ่ม C6 ใน relations
- [[concepts/iot/tinyml]] — เพิ่ม ESP32-C6 mention + Smart Farm use case


---

### `wiki/sources/esp-idf-docs.md`

---
type: source
title: "ESP-IDF: Espressif IoT Development Framework (Official)"
slug: esp-idf-docs
date_ingested: 2026-04-18
original_file: raw/espressifesp-idf Espressif IoT Development Framework. Official development framework for Espressif SoCs..md
tags: [esp-idf, espressif, framework, cmake, c-programming, advanced]
---

# ESP-IDF: Espressif IoT Development Framework

**ประเภท**: GitHub repo + official documentation
**ผู้พัฒนา**: Espressif Systems

## ประเด็นหลัก

1. **ESP-IDF คือ native framework** ของ Espressif — ต่างจาก Arduino framework ตรงที่ใช้ C/C++ ล้วน + CMake
2. **Version ปัจจุบัน**: v6.0 (stable) — v4.4 ที่บันทึกไว้เป็น EOL แล้ว
3. **รองรับทุก Espressif SoC**: ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-H2 ฯลฯ
4. **อดีต ESP8266**: ใช้ ESP8266 RTOS SDK แยก (ไม่ใช่ ESP-IDF)

## ESP-IDF vs Arduino Framework

| หัวข้อ | Arduino Framework | ESP-IDF |
|--------|------------------|---------|
| Language | C++ (simplified) | C/C++ |
| Build system | Arduino IDE / PlatformIO | CMake + idf.py |
| Abstraction | สูง (ง่าย) | ต่ำ (control เต็มที่) |
| RTOS | ซ่อน FreeRTOS | เปิดเผย FreeRTOS API |
| Community | ใหญ่กว่า | เล็กกว่า (แต่ professional) |
| เหมาะกับ | Maker, prototype | Production, advanced |

## เหมาะสำหรับโปรเจ็คนี้ไหม

**Arduino framework เพียงพอ** สำหรับโปรเจ็คปัจจุบัน (DHT11 + LoRa + MQTT)
ESP-IDF จำเป็นถ้าต้องการ:
- FreeRTOS task แยก (concurrent LoRa receive + MQTT publish)
- Deep sleep control ละเอียด (wake stub, ULP coprocessor)
- Custom partition table สำหรับ OTA update

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/esp-idf]] — สร้างใหม่


---

## Synthesis touching `iot`

### `wiki/synthesis/energy-power-monitoring.md`

---
type: synthesis
tags: [energy, pzem-004t, modbus, mqtt, esp32, grafana, power-monitoring]
sources: [pzem-004t-guide-2025, espem-energy-monitor, iot-lora-gateway-architecture]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Energy/Power Monitoring (PZEM-004T + ESP32 + MQTT)

> **คำถามที่ตอบ**: จะออกแบบระบบมอนิเตอร์ไฟฟ้า (V/A/W/Wh) อย่างไร?

## สรุป

ใช้ [[entities/iot/pzem-004t]] ต่อกับ [[entities/iot/esp32]] ผ่าน UART (Modbus RTU) แล้ว publish ไปยัง [[entities/iot/mosquitto]] → [[entities/iot/influxdb]] → [[entities/iot/grafana]] dashboard เหมาะสำหรับมอนิเตอร์ปลั๊กไฟ ตู้แช่ หรืออุปกรณ์ไฟฟ้า AC

## Data Flow

```
[AC Load] → [PZEM-004T] ← UART Modbus RTU → [ESP32]
                                                  ↓ WiFi MQTT JSON
                                          [Mosquitto Broker]
                                                  ↓
                                          [Node-RED / Telegraf]
                                                  ↓
                                          [InfluxDB] → [Grafana]
                                                  ↓ alert
                                          [Telegram Bot]
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/pzem-004t]] | ❌ ยังไม่มี | ต้องซื้อ — UART 5V, Modbus RTU |
| [[entities/iot/esp32]] | ✅ มีแล้ว | Serial2 (GPIO16/17) ต่อ PZEM |
| [[entities/iot/mosquitto]] | software | ต้องติดตั้ง |
| [[entities/iot/influxdb]] | software | ต้องติดตั้ง |
| [[entities/iot/grafana]] | software | ต้องติดตั้ง |
| [[entities/iot/telegram-bot]] | software | alert ค่า W เกิน threshold |

## MQTT JSON Format (จาก ESPEM project)

```json
{
  "voltage": 220.5,
  "current": 1.23,
  "power": 271.2,
  "energy": 1.456,
  "frequency": 50.0,
  "pf": 0.98
}
```

**Topic แนะนำ**: `home/power/<room>/data`

## Grafana Dashboard Panels

| Panel | Metric | Unit |
|-------|--------|------|
| Gauge | Voltage | V |
| Gauge | Current | A |
| Stat | Active Power | W |
| Time-series | Power history | W/time |
| Stat | Energy (Wh) | kWh |
| Gauge | Power Factor | % |

## ⚠️ ข้อควรระวัง

1. PZEM-004T ต้องการ **CT clamp บน live wire** — ระวังไฟฟ้า 220V
2. PZEM มี 2 รุ่น: v3.0 (UART ตรง) และ รุ่นเก่า (ต้องแก้ address)
3. ใช้ `EspSoftwareSerial` ถ้าไม่มี hardware Serial ว่าง
4. ต้องต่อ **isolator optocoupler** ถ้า ground loop เป็นปัญหา

## ความสัมพันธ์

- ใช้ร่วมกับ: [[concepts/iot/modbus]], [[concepts/iot/data-logger]]
- เกี่ยวข้องกับ: [[entities/iot/node-red]] (flow-based processing)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/pzem-004t-guide-2025]] — UART wiring, MQTT JSON, ESPHome integration
- [[sources/espem-energy-monitor]] — ESPEM project reference implementation


---

### `wiki/synthesis/fuel-tank-level.md`

---
type: synthesis
tags: [tank-level, hc-sr04, ultrasonic, mqtt, esp32, captive-portal]
sources: [esp32-tank-level-mqtt]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Fuel/Water Tank Level Monitoring (HC-SR04 + ESP32 + MQTT)

> **คำถามที่ตอบ**: จะออกแบบระบบวัดระดับน้ำ/เชื้อเพลิงในถัง และแจ้งเตือนเมื่อน้อยเกินไปอย่างไร?

## สรุป

ใช้ [[entities/iot/hc-sr04]] (ultrasonic distance) ติดตั้งบนปากถัง วัดระยะห่างจาก sensor ถึงผิวน้ำ → คำนวณเป็น % level → publish MQTT → แจ้งเตือน Telegram เมื่อ level ต่ำกว่า threshold

## Data Flow

```
[HC-SR04 Ultrasonic] (ติดที่ปากถัง)
      ↓ trigger + echo
[ESP32] ← WiFi config ผ่าน Captive Portal
      ↓ MQTT publish (distance_cm + level_pct)
[Mosquitto Broker]
      ↓
[Node-RED / Telegraf]
      ↓
[InfluxDB] → [Grafana]
      ↓ alert (level < 20%)
[Telegram Bot]
```

## การคำนวณ Level

```cpp
float tank_height_cm = 100.0;  // ความสูงถัง
float distance_cm = measureUltrasonic();
float level_pct = ((tank_height_cm - distance_cm) / tank_height_cm) * 100.0;
// distance น้อย = น้ำเยอะ = level สูง
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/hc-sr04]] | ✅ มีแล้ว | 5V trigger+echo, range 2-400cm |
| [[entities/iot/esp32]] | ✅ มีแล้ว | GPIO digital out/in |
| [[entities/iot/mosquitto]] | software | MQTT broker |
| [[entities/iot/telegram-bot]] | software | แจ้งเตือน level ต่ำ |

**ข้อสรุป: Hardware ครบแล้ว ไม่ต้องซื้อเพิ่ม**

## Captive Portal Config (จาก source)

ESP32 เปิด WiFi AP "TankConfig" → ผู้ใช้เชื่อมต่อ → กรอก:
- WiFi SSID + Password
- MQTT Broker IP
- Tank height (cm)
- Alert threshold (%)

บันทึกลง SPIFFS → reboot → เชื่อม WiFi จริง

## MQTT JSON Format

```json
{
  "sensor": "tank_01",
  "distance_cm": 45.2,
  "level_pct": 54.8,
  "alert": false
}
```

**Topic**: `home/tank/<name>/level`

## Grafana Dashboard

| Panel | Metric | Display |
|-------|--------|---------|
| Gauge | Level % | 0-100% สีแดง<20% |
| Stat | Distance cm | raw distance |
| Time-series | Level history | 24h trend |
| Alert | Level < threshold | Telegram |

## ⚠️ ข้อควรระวัง

1. HC-SR04 ต้องการ **5V** แต่ ESP32 logic 3.3V → ใช้ voltage divider บน echo pin
2. foam/น้ำมัน → เสียงสะท้อนผิดปกติ → กรอง outlier ด้วย median filter
3. ถ้าอุณหภูมิเปลี่ยน → speed of sound เปลี่ยน → calibrate ตามฤดูกาล
4. ความชื้นสูงในถัง → condensation บน sensor

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/hc-sr04]], [[concepts/iot/data-logger]]
- เกี่ยวข้องกับ: [[entities/iot/node-red]] (flow processing)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/esp32-tank-level-mqtt]] — HC-SR04 + MQTT + Captive Portal implementation


---

### `wiki/synthesis/digital-legacy-ai-architecture.md`

---
type: synthesis
tags: [digital-legacy, ai, architecture, ollama, local-llm, philosophy]
sources: []
created: 2026-04-30
updated: 2026-04-30
---

# Digital Legacy AI — Self + Persistent

> **TL;DR:** สร้าง AI ที่ "เป็นเรา" และ persist หลังเราจากไป ด้วย 5-layer open + self-hosted architecture ไม่พึ่ง vendor เดียว

---

## คำถามที่ตอบ

"จะออกแบบ AI ที่เก็บความเป็นเรา (วิธีคิด, ความรู้, การตัดสินใจ) และอยู่ต่อหลังเราจากไปได้อย่างไร?"

## สรุป

ใช้ wiki + journal + decisions เป็น "digital DNA" → embed → run ผ่าน local LLM (Ollama) → expose ผ่าน Telegram/Web

**เปรียบเทียบ:**
- Wiki = **WHAT we know** (ความรู้)
- Journal = **HOW we think** (วิธีคิดประจำวัน)
- Decisions = **WHY we chose** (เหตุผลตัดสินใจสำคัญ)

ทั้งสามรวมกัน → AI สามารถ "เลียน" เราได้ทั้ง knowledge + reasoning + judgment

---

## 5-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Data (open, version-controlled)               │
│  ✅ wiki/        — knowledge (IoT, Env, AI, Pharmacy)    │
│  ✅ profile.md   — Decision Logic, Values                │
│  ✅ log.md       — chronological reasoning               │
│  ➕ journal/     — daily thinking patterns               │
│  ➕ decisions/   — major ADRs                            │
│  raw/            — sources (PDFs ใน Drive)               │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Embeddings (regenerable)                      │
│  • bge-m3 / sentence-transformers (open-source)         │
│  • Qdrant / Chroma vector DB (self-hosted)              │
│  • Re-build จาก Layer 1 ได้เสมอ                          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Inference (local-first)                       │
│  • Ollama on Mac Mini                                   │
│  • Llama 3.3 / Qwen / Mistral (open-source)             │
│  • Optional: LoRA fine-tune จาก writing pattern         │
│  • Fallback: claude-router (cloud) ตอน Mac Mini ไม่อยู่  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Interface                                     │
│  • Telegram bot (สำหรับครอบครัว/heir)                    │
│  • Web UI (Pi5 หรือ Mac Mini)                            │
│  • Voice (อนาคต — TTS เลียนเสียง)                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Persistence                                   │
│  • Git mirrors: GitHub + GitLab + Codeberg              │
│  • Cold storage: external HDD + encrypted               │
│  • Heir trustee: คนที่มี access ตอนเราไม่อยู่             │
│  • Constitutional rules: AI ห้ามทำอะไร                    │
└─────────────────────────────────────────────────────────┘
```

---

## Roadmap

### Phase A — ตอนนี้ (Apr 2026)
- [x] Wiki ใน git ✅ (มีแล้ว 120 pages)
- [x] profile.md, log.md ✅
- [x] สร้าง journal/ + decisions/ folder + templates ✅
- [x] Setup git mirror script ([[scripts/setup-git-mirror.sh]]) ✅
- [ ] ใช้ journal ทุกวัน (หรืออย่างน้อย 3 วัน/สัปดาห์)
- [ ] เขียน decisions เมื่อ major decision (เริ่ม ADR-0001, 0002)

### Phase B — เมื่อมี Mac Mini
- [ ] Setup Ollama + open-source LLM
- [ ] Build RAG ของ wiki (Qdrant + bge-m3)
- [ ] LiteLLM proxy เชื่อม local + cloud (ดู [[wiki/concepts/ai-tools/openrouter-claude-code]])
- [ ] Test: เปรียบเทียบคำตอบกับ Claude — match กี่ %

### Phase C — Long-term (3-5 ปี)
- [ ] LoRA fine-tune ด้วย writing/voice patterns
- [ ] Constitutional AI rules (จริยธรรม + ขอบเขตหลังเสียชีวิต)
- [ ] Heir setup — ใครเข้าได้, ใครเปิด/ปิดได้, นานแค่ไหน
- [ ] Operator manual สำหรับ heir (non-technical)

### Phase D — Long-term (5-30 ปี)
- [ ] Migration เมื่อ tech stack เปลี่ยน (markdown → ?)
- [ ] Public archive (เลือก) — บางส่วนแชร์เป็น public good
- [ ] Trust foundation legal structure (?)

---

## ที่ตัดสินใจแล้ว

ดู ADRs:
- [[decisions/0001-digital-legacy-strategy]] — choose open + self-hosted over proprietary
- [[decisions/0002-git-mirror-redundancy]] — multi-host git (GitHub + GitLab + Codeberg)

---

## Decision rules (สำหรับ revisit)

| ถ้า... | ทำ |
|-------|-----|
| Open-source LLM คุณภาพยังตามไม่ทัน Claude/GPT | ใช้ hybrid (cloud now, self-host เก็บไว้ persist) |
| Vendor หนึ่งเสนอ "AI clone" service | **ไม่ใช้** — lock-in ไม่ตอบโจทย์ legacy |
| ครอบครัวไม่อยาก maintain | เปิด minimal interface (Telegram bot) ไม่ต้อง dev knowledge |
| ค่าใช้จ่าย cloud พุ่ง | เร่ง Phase B local-first |
| Mac Mini ตาย | Layer 1 (data) ยังอยู่ใน git → reconstruct Layer 2-4 ได้ |

---

## ความสัมพันธ์

- [[journal/README]] — บันทึกประจำวัน (Layer 1)
- [[decisions/README]] — ADRs (Layer 1)
- [[wiki/concepts/ai-tools/local-llm-routing]] — model routing (Layer 3)
- [[wiki/sources/local-llm-mac-mini-guide]] — Mac Mini setup
- [[wiki/concepts/ai-tools/openrouter-claude-code]] — current cloud usage
- [[wiki/entities/ai-tools/telegram-ai-router]] — interface design (Layer 4)
- [[scripts/setup-git-mirror.sh]] — Layer 5 redundancy

---

## คำเตือนสำหรับตัวเองในอนาคต

- 📝 **Journal สม่ำเสมอ ≠ ความสมบูรณ์** — เขียน 3 บรรทัดยังดีกว่าไม่เขียน
- 🚫 **อย่าหลงเสน่ห์ closed AI service** — "AI clone" services ส่วนใหญ่จะปิดใน 5 ปี
- 🔐 **Heir ต้องรู้ก่อนเราตาย** — ไม่ใช่หลังจากนั้น
- 🌱 **Open formats > fancy features** — markdown 30 ปียังอ่านได้ Notion JSON ไม่แน่
- ⚖️ **Legacy AI ไม่ใช่ตัวเรา** — เป็นเครื่องมือที่เลียนเรา ตั้งกฎให้ชัดเจน


---

### `wiki/synthesis/appsheet-to-webapp-pi5.md`

---
type: synthesis
tags: [web-app, raspberry-pi, self-hosted, appsheet-migration, env, iot, fullstack]
sources: [appsheet-activated-sludge-app, appsheet-epidem-app, appsheet-env-datadict]
created: 2026-04-22
updated: 2026-05-04
progress: Phase 1 RESET — containers wiped by Umbrel update, must redeploy via Portainer
---

# แผน: ย้าย AppSheet → Self-hosted Web App บน Raspberry Pi 5

## คำถามที่ตอบ

"จะสร้าง web application ทดแทน AppSheet (ActivatedSludge + Epidem) บน Pi5 ที่บ้าน ได้อย่างไร?"

## สรุป

AppSheet ช้าเกินไปสำหรับการใช้งานรายวัน + ไม่สามารถ integrate กับ IoT sensors ได้ตรงๆ  
การสร้าง self-hosted web app บน Pi5 ให้: ความเร็ว, IoT integration, ควบคุมข้อมูลเอง, ขยายได้ในอนาคต

---

## ข้อมูล AppSheet ที่มีอยู่

### App 1: ActivatedSludge-29279640 (งาน ENV)
| โมดูล | ตาราง | จำนวนข้อมูล |
|-------|-------|-------------|
| คุณภาพน้ำรายวัน | ข้อมูลบ่อบำบัดประจำวัน | 80+ ฟิลด์ |
| น้ำประปา | tap water, coliform | หลายตาราง |
| ถังดับเพลิง | fire_extinguisher | พร้อม PDF report |
| ไฟฉุกเฉิน | ข้อมูลตรวจไฟฉุกเฉิน | พร้อม PDF report |
| บุคลากร | ข้อมูลผู้ปฏิบัติงาน | รูปถ่าย + ข้อมูล |
| เครื่องมือ | tool_maintainance | - |

### App 2: Epidem-29279640 (งานควบคุมโรค)
| โมดูล | ตาราง | จำนวนข้อมูล |
|-------|-------|-------------|
| ผู้ถูกสัตว์กัด (Rabies PEP) | patient information | 80+ ฟิลด์ |
| SQL backup | sql_export1-4 | สำรองข้อมูล |

### ข้อมูลร่วม (Shared)
- ระบบน้ำประปา, ถังดับเพลิง, บุคลากร — มีอยู่ในทั้งสองแอป

---

## สถาปัตยกรรม Web App ที่แนะนำ

```
┌─────────────────────────────────────────────────────────┐
│                   Raspberry Pi 5 (8/16GB)                │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────┐   │
│  │  Nginx   │   │ FastAPI  │   │   PostgreSQL       │   │
│  │ (reverse │──▶│ Backend  │──▶│   (main database)  │   │
│  │  proxy)  │   │ :8000    │   │   :5432            │   │
│  └──────────┘   └──────────┘   └───────────────────┘   │
│       │                │                                  │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────┐   │
│  │  React/  │   │Mosquitto │   │   InfluxDB         │   │
│  │  Vite    │   │  MQTT    │   │   (time-series)    │   │
│  │ Frontend │   │ :1883    │   │   IoT sensor data  │   │
│  └──────────┘   └──────────┘   └───────────────────┘   │
│                       │                                   │
└───────────────────────│───────────────────────────────── ┘
                        │ MQTT
              ┌─────────┴─────────┐
              │   ESP32 Sensors   │
              │   (future IoT)    │
              │  DO, pH, TDS,     │
              │  Temp, Chlorine   │
              └───────────────────┘
```

### Tech Stack

| Layer | เทคโนโลยี | เหตุผล |
|-------|-----------|--------|
| **Frontend** | React 18 + Vite + Tailwind CSS | เร็ว, component-based, mobile-friendly |
| **Backend** | FastAPI (Python) | Python ecosystem รองรับ IoT ดี, async |
| **Database** | PostgreSQL | เชื่อถือได้, relational ✔ ทุก module |
| **Time-series** | InfluxDB | เมื่อเพิ่ม IoT sensors จริง |
| **MQTT** | Mosquitto | ส่งข้อมูล sensor → server (ใช้ wiki รู้อยู่แล้ว) |
| **Reverse Proxy** | Nginx | SSL termination, static files |
| **Container** | Docker Compose | จัดการทุก service ง่าย |
| **PDF** | WeasyPrint | สร้าง ทส.1/ทส.2 และรายงานระบาดวิทยา |
| **Auth** | JWT + bcrypt | session-based login |
| **Access** | Tailscale / Cloudflare Tunnel | เข้าจากโรงพยาบาลหรือมือถือได้ |

---

## โมดูลที่ต้องสร้าง (เรียงลำดับความสำคัญ)

### Phase 1 — Core (MVP) ⭐⭐⭐
- [ ] **Auth** — Login, Role (admin/user/viewer)
- [ ] **Water Quality** — บันทึกคุณภาพน้ำรายวัน (แทน module หลักของ ActivatedSludge)
- [ ] **Rabies PEP** — บันทึกผู้ถูกสัตว์กัด, ตารางวัคซีน 5 เข็ม
- [ ] **PDF Generator** — ส่งออก ทส.1/ทส.2, รายงานผู้ป่วย

### Phase 2 — Operations ⭐⭐
- [ ] **Fire Safety** — ตรวจสอบถังดับเพลิง + ไฟฉุกเฉิน
- [ ] **Water Supply** — ระบบน้ำประปา, coliform
- [ ] **Personnel** — ข้อมูลบุคลากร + รูปถ่าย
- [ ] **Equipment** — บันทึกซ่อมบำรุงเครื่องมือ

### Phase 3 — IoT Integration ⭐
- [ ] **ESP32 → MQTT → API** — sensor คุณภาพน้ำ real-time
- [ ] **Dashboard** — Grafana หรือ React charts
- [ ] **Alert** — LINE Notify / Telegram เมื่อค่าผิดปกติ
- [ ] **InfluxDB** — เก็บ time-series sensor data

---

## ข้อมูล Migration

### ข้อมูลเดิมที่ต้อง migrate
1. **Recovery Data** (JSON) → PostgreSQL (script Python)
2. **รูปถ่าย** (~2,900 ไฟล์) → เก็บใน `/data/uploads/` บน Pi5
3. **PDF templates** (DOCX → WeasyPrint template)
4. **Google Sheets** → PostgreSQL import

### การเข้าถึงจากโรงพยาบาล
```
Option A: Tailscale VPN (แนะนำ) — ง่าย, ปลอดภัย, ฟรีสำหรับ personal use
Option B: Cloudflare Tunnel — ไม่ต้อง public IP, ฟรี
Option C: Dynamic DNS + Router port forward — เสี่ยงกว่า
```

---

## เปรียบเทียบ: AppSheet vs Web App ใหม่

| หัวข้อ | AppSheet | Web App (Pi5) |
|--------|---------|---------------|
| ความเร็ว | ช้า | เร็ว (local) |
| ค่าใช้จ่าย | $50/เดือน (Business) | ~0 (Pi5 ซื้อครั้งเดียว) |
| IoT Integration | ไม่มี | MQTT + InfluxDB เลย |
| Custom PDF | จำกัด | เต็มที่ (WeasyPrint) |
| ออฟไลน์ | ไม่ได้ | ได้ (local server) |
| บำรุงรักษา | ไม่ต้องทำ | ต้องดูแลเอง |
| Backup | Google Drive อัตโนมัติ | ต้องตั้ง cron |

---

## สิ่งที่ Wiki รู้อยู่แล้วที่ใช้ได้เลย

- **[[entities/iot/esp32]]** → sensor node สำหรับ DO, pH, TDS
- **[[concepts/iot/mqtt-protocol]]** → ส่งข้อมูล sensor → Pi5
- **[[entities/iot/raspberry-pi-5]]** → server hardware
- **[[synthesis/pi4-lora-gateway-server]]** → สถาปัตยกรรม Pi server ที่เคยวางไว้
- **[[synthesis/temperature-monitor-project]]** → ตัวอย่าง sensor → dashboard
- **[[entities/ai-tools/claude-code]]** → ใช้ช่วย generate code

---

## สถานะปัจจุบัน

### Session 1 (2026-04-22) ✅ — Infrastructure เดิม (ถูกลบแล้ว)
- Infrastructure ผ่าน SSH บน Pi5: PostgreSQL 16, FastAPI :8000, Adminer :8181
- Schema 5 ตาราง: `users`, `water_quality_records`, `patients`, `rabies_cases`, `vaccination_schedule`
- Water Quality API: GET/POST/DELETE + auto-alert DO<2.0 / Cl<0.5
- ⚠️ **Umbrel OS update ล้าง custom Docker containers ทั้งหมด** → ต้อง redeploy ใหม่

### Session 2 (2026-05-04) — Storage cleanup + YAML analysis
- **Pi5 storage**: เดิม 91% (1.6T/1.8T) → ลบ Time Machine 690GB → เหลือ 51% (848GB free)
- **Bitcoin full node**: ยังอยู่ที่ 871GB — ปล่อยไว้ตามแผน
- **Portainer**: เข้าได้ปกติ (admin) — ใช้ deploy stack ใหม่แทน SSH
- **YAML analysis**: วิเคราะห์ AppSheet data dictionary ครบ 81 tables, 1,639 columns, 155 actions
- ⚠️ raw YAML file (`raw/manual-input-appsheet-env-2026-05-04.md`) บันทึกได้แค่ 2 chunks — ยังไม่ครบ

### 📋 ถัดไป (Session 3+)
- [ ] **Redeploy FastAPI + PostgreSQL ผ่าน Portainer** (สร้าง stack ถาวรที่รอดข้าม Umbrel update)
- [ ] ออกแบบ PostgreSQL schema ใหม่ครบทุก domain (เริ่ม wastewater)
- [ ] React frontend (เริ่มหลัง API พร้อม)
- [ ] Feature implementation: OCR, PDF, QR, Telegram

---

## โครงสร้าง AppSheet ENV — 6 Domain Groups (จาก YAML analysis 2026-05-04)

> App ID: ActivatedSludge-29279640 | 81 tables | 1,639 columns | 155 actions | 128 views

### Domain 1: ระบบบำบัดน้ำเสีย (Wastewater Treatment) ⭐ ซับซ้อนที่สุด
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| ข้อมูลคุณภาพน้ำ | บันทึกรายวัน: TDS, pH, DO-1/2/3, SV30, Free Chlorine, meter readings, energy calc | ข้อมูลน้ำประจำวัน |
| Filter_Water | สร้าง PDF report สรุปคุณภาพน้ำ | ข้อมูลน้ำประจำวัน |
| last meter | ค่ามิเตอร์ล่าสุด (คำนวณพลังงาน) | ข้อมูลน้ำประจำวัน |

### Domain 2: ระบบประปา (Water Supply)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| น้ำประปา | บันทึกคุณภาพน้ำประปา | ข้อมูลคุณภาพน้ำประปา |
| tap water_Filter | PDF report น้ำประปา | ข้อมูลคุณภาพน้ำประปา |
| Menu ประปา | เมนูนำทาง (virtual) | — |

### Domain 3: สุขาภิบาลอาหาร (Food Sanitation)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| coliform bac. | ผลตรวจโคลิฟอร์มน้ำ | สุขาภิบาลอาหารและน้ำ2 |
| coliform bac._Water | โคลิฟอร์มน้ำดื่ม | สุขาภิบาลอาหารและน้ำ2 |
| coliform bac. Food. | โคลิฟอร์มอาหาร | สุขาภิบาลอาหารและน้ำ2 |
| coliform bac. Employee | โคลิฟอร์มผู้สัมผัสอาหาร | สุขาภิบาลอาหารและน้ำ2 |

### Domain 4: ความปลอดภัย (Safety)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| Emergency light | รายการไฟฉุกเฉิน | Items |
| Check | ตรวจสอบไฟฉุกเฉิน (scan QR) | Items |
| ถังดับเพลิง | รายการถังดับเพลิง | fire_extinguisher |
| ตรวจสอบถัง | ตรวจสอบถังดับเพลิง (scan QR) | fire_extinguisher |
| Filter_Firer | PDF report ถังดับเพลิง | fire_extinguisher |
| Filter_Light | PDF report ไฟฉุกเฉิน | Items |

### Domain 5: ระบาดวิทยา (Epidemiology / Rabies PEP)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| patient information | ผู้ถูกสัตว์กัด: HN, ชื่อ-ที่อยู่-อายุ, วัคซีน 5 เข็ม | Patients / ข้อมูลหมากัด |
| แบบสอบสวนโรค | รายงานระบาดวิทยา | ข้อมูลหมากัด |
| sql_export 1–5 | lookup คนไข้จาก HN (OCR input) → ชื่อ/ที่อยู่/อายุ | (read-only mirror) |

### Domain 6: Admin / Shared
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| address | auto-complete ที่อยู่ (TambonID → อำเภอ/จังหวัด/รหัสไปรษณีย์) | — |
| ข้อมูลผู้ปฏิบัติงาน | บุคลากร + รูปถ่าย | ข้อมูลน้ำประจำวัน |
| location_area | จุดตรวจ QR สำหรับ job check-in | งานสวน |
| job | GPS geolocation check-in (คำนวณระยะห่างจากโรงพยาบาล) | งานสวน |

---

## Feature-to-Implementation Mapping

| AppSheet Feature | Implementation ใน Web App |
|-----------------|--------------------------|
| Virtual columns + สูตรคำนวณ (DO avg, energy, SV30%) | PostgreSQL computed columns + Python ใน FastAPI |
| Auto-complete ที่อยู่ (address table) | Import address table → PostgreSQL → API endpoint |
| OCR HN → ดึงข้อมูลคนไข้ (sql_export) | Claude API (vision) → extract HN → query patient table |
| PDF report (Filter_Water, Filter_Firer, Filter_Light) | WeasyPrint templates (HTML/CSS → PDF) |
| Telegram notification + PDF attach | python-telegram-bot → ส่งหลัง POST สำเร็จ |
| QR scan (ถังดับเพลิง, ไฟฉุกเฉิน, job) | React QR reader library → lookup location_area / equipment |
| GPS check-in (job) | Browser Geolocation API → FastAPI distance calc (Haversine) |
| Thai Buddhist date (พ.ศ.) | Python: `year + 543` conversion ใน API response |
| Enum dropdowns | PostgreSQL ENUM types หรือ lookup tables |

---

## ข้อมูล Infrastructure สำคัญ

```
Pi5 Home Server:
  OS: Umbrel (rugpi — system partition ไม่ persistent ข้าม update!)
  ⚠️ Deploy ผ่าน Portainer Stack เท่านั้น (ไม่ใช่ SSH manual) เพื่อให้รอดข้าม update

Target Ports:
  :8000  FastAPI backend
  :5432  PostgreSQL
  :8181  Adminer (DB UI)
  :9000  Portainer

Access:
  Local:     umbrel.local / 192.168.1.165
  Tailscale: 100.x.y.z

DB credentials (เดิม — ยังไม่ deploy ใหม่):
  user: webapp / pass: webapp1234 / db: webapp
```

## แผนการทำงาน (ปรับปรุง)

```
Session 1 (2026-04-22): Infrastructure SSH + DB schema + Water Quality API ✅ (ถูกลบแล้ว)
Session 2 (2026-05-04): Storage cleanup + AppSheet YAML analysis ✅
Session 3: Redeploy ผ่าน Portainer + ออกแบบ schema ครบทุก domain
Session 4: Water Quality + Rabies PEP API endpoints
Session 5: Auth (JWT login)
Session 6: React frontend (mobile-first)
Session 7: PDF generation (WeasyPrint)
Session 8: Feature: OCR, QR, GPS, Telegram
Session 9: Data migration จาก AppSheet JSON/Google Sheets
Session 10+: IoT sensor integration
```

## แหล่งข้อมูลที่ใช้

- [[entities/env/activated-sludge-system]] — schema ระบบบำบัดน้ำเสีย
- [[entities/env/rabies-pep-surveillance]] — schema ระบาดวิทยา
- AppSheet ActivatedSludge-29279640 — โครงสร้างข้อมูลเดิม
- AppSheet Epidem-29279640 — โครงสร้างข้อมูลเดิม


---

### `wiki/synthesis/dream-projects.md`

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


---

### `wiki/synthesis/local-llm-pc-vs-mac-2026.md`

---
type: synthesis
tags: [local-llm, pc-build, mac-mini, mac-studio, hardware-comparison, ryzen, apple-silicon, vram, unified-memory, strix-halo]
sources: [ai-iot-server-build-v3, local-llm-mac-mini-guide, strix-halo-research-2026-05-05]
created: 2026-05-05
updated: 2026-05-05
---

> 🔄 **อัปเดต 2026-05-05 (later)**: เพิ่ม section "Strix Halo verified data" หลัง verify ผ่าน Gemini CLI — **ตัวเลขเดิมที่ผมประเมินผิด** ดูใน [[sources/strix-halo-research-2026-05-05]]

# Local LLM Hardware: PC Build vs Mac (2026)

## คำถามที่ตอบ

ในงบ ~100,000฿ สำหรับงาน Local LLM 24/7 + IoT monitor + AI agent + web server ควรเลือก:

- **PC build** (Ryzen + RTX 4070 Ti Super 16GB + 128GB DDR5)
- **Mac mini M4 Pro 64GB** หรือ
- **Mac Studio M4 Max 64GB**

## TL;DR

| ปัจจัย | PC ชนะ | Mac ชนะ |
|---|---|---|
| Upgradeability | ✅ เปลี่ยน GPU/RAM/SSD ได้ตลอด | ❌ ทุกอย่างบัดกรี |
| ราคาต่อ spec ดิบ | ✅ 16GB VRAM + 128GB RAM ในงบเดียวกัน | ❌ unified memory แพงกว่า/GB |
| **70B+ model speed** | ❌ VRAM ไม่พอ ต้อง offload → ช้า | ✅ unified memory bandwidth สูง รันได้ลื่น |
| ประหยัดไฟ 24/7 | ❌ idle 50-80W, load 200-400W | ✅ idle 5-10W, load 30-80W |
| เสียงเงียบ | ⚠️ ขึ้นกับ build (TK-1 + Noctua = เงียบ) | ✅ เงียบสนิท |
| OS ecosystem | ✅ Linux/Windows native, CUDA | ⚠️ macOS ผูก ecosystem |
| รัน Docker/IoT broker | ✅ Linux native, Home Assistant, Mosquitto | ⚠️ ใช้ Docker Desktop ได้ แต่กิน resource |
| Resale value 5 ปี | ⚠️ depreciate เร็ว (GPU ใหม่ออก) | ✅ Mac คงราคาดี |

## เปรียบเทียบ Spec ที่งบใกล้กัน

### PC build (~98,500฿) — จาก [[sources/ai-iot-server-build-v3]]

```
CPU:    Ryzen 7 9700X (8C/16T, Eco 65W)
GPU:    RTX 4070 Ti Super 16GB GDDR6X
RAM:    128GB DDR5-5600 (4x 32GB)
SSD:    2TB NVMe Gen4
HDD:    8TB NAS-grade
PSU:    750W SFX Gold
Case:   Jonsbo TK-1 v2 (mini)
```

**Local LLM throughput:**
- 7B Q4: ~80-100 tok/s (in VRAM)
- 14B Q4: ~40-60 tok/s (in VRAM)
- 32B Q4: ~15-25 tok/s (partial offload)
- 70B Q4: ~3-6 tok/s (heavy CPU offload — ใช้ DDR5 bandwidth ~70 GB/s)

### Mac Studio M4 Max 64GB (~120,000-130,000฿)

```
CPU:    M4 Max (16C: 12P+4E)
GPU:    40-core integrated
RAM:    64GB unified (~410 GB/s bandwidth)
SSD:    512GB - 1TB
```

**Local LLM throughput** (จาก [[sources/local-llm-mac-mini-guide]]):
- 7B-8B Q4: ~25-35 tok/s
- 14B-32B Q4: ~12-18 tok/s
- 70B Q4: ~6-10 tok/s (อยู่ใน unified memory ได้ ไม่ต้อง offload)

### Mac mini M4 Pro 64GB (~80,000-90,000฿)

```
CPU:    M4 Pro (12-14C)
GPU:    16-20 core integrated
RAM:    64GB unified (~273 GB/s bandwidth)
SSD:    512GB - 1TB
```

**Local LLM throughput:**
- 14B-32B Q4: 12-18 tok/s
- 70B Q4: <10 tok/s (ใช้ 60% rule = ~38GB available ไม่พอ 70B Q4 ที่ ~40GB → ต้อง quant ลง)

## การวิเคราะห์เชิงลึก

### 1. VRAM vs Unified Memory — แตกต่างยังไงบน Local LLM

**PC (discrete GPU):**
- VRAM (16GB) เร็วมาก (~700 GB/s) แต่จำกัดขนาด model
- ถ้า model ใหญ่กว่า VRAM → ต้อง offload layer ไป system RAM (DDR5 = 70 GB/s) → ช้าลง 5-10 เท่า
- **Sweet spot**: model ที่ fit ใน VRAM (ปัจจุบัน Q4 ขนาด 7B-13B fit สบาย, 32B ต้อง Q3 หรือ partial offload)

**Mac (unified memory):**
- หน่วยความจำเดียว GPU+CPU แชร์กัน, bandwidth ปานกลาง (273-546 GB/s)
- model ใหญ่อยู่ในหน่วยความจำเดียว ไม่ต้อง offload
- **Sweet spot**: model ใหญ่กว่า VRAM ของ GPU consumer (เช่น 70B Q4 ใน 64GB Mac คุ้มกว่า 16GB VRAM)

### 2. งบเท่าไรจึงคุ้มแต่ละแบบ

```
< 50,000฿:  Mac mini M4 24GB หรือ Pi5+AI HAT (ดู [[sources/rpi-ai-hat-plus-2-official]])
50-90,000฿: Mac mini M4 Pro 48-64GB (ดี balance)
90-120,000฿: PC build 16GB VRAM + 128GB RAM ⚠️ หรือ Mac mini M4 Pro 64GB
120-180,000฿: Mac Studio M4 Max 64GB หรือ PC + RTX 5080 16GB
> 180,000฿: PC + RTX 5090 32GB ⭐ หรือ Mac Studio M4 Ultra 128GB+
```

### 3. การ Upgrade ในอนาคต

**PC เลือก path ได้:**
- เปลี่ยน GPU เป็น RTX 5090 (32GB) ภายหลัง — รัน 70B Q4 ใน VRAM เต็ม
- เพิ่ม GPU ใบที่ 2 (ถ้า PSU+case รับได้) — กระจาย model
- เพิ่ม HDD/SSD ได้ตลอด
- ✅ **PC build จะอายุยาว 5-7 ปี** ถ้า upgrade GPU ทุก 2-3 ปี

**Mac:**
- ❌ RAM/SSD บัดกรี เปลี่ยนไม่ได้
- ขายเครื่องเก่าซื้อรุ่นใหม่ (Mac คงราคาดี ~60-70% หลัง 2 ปี)
- ✅ รุ่นใหม่ทุก 1-2 ปี ดีขึ้นชัดเจน (M4→M5)

### 4. นอกเหนือจาก Local LLM

**PC ดีกว่าเรื่อง:**
- Linux native → Docker, Home Assistant, Mosquitto MQTT, Node-RED, Grafana ลื่น
- IoT broker 24/7 + Local LLM พร้อมกันได้สบาย
- 4K entertainment (HDMI 2.1 + GPU)
- Gaming (ถ้าอยาก)
- Bitcoin full node, file server, etc.

**Mac ดีกว่าเรื่อง:**
- ใช้เป็น workstation หลักได้ด้วย (PC + Mac = 2 เครื่อง)
- เสียงเงียบสนิท (เหมาะตั้งห้องนอน)
- ไฟน้อย (idle 5W vs PC idle 50-80W)
- macOS native apps + iCloud sync

## 🆕 Option ที่ 3: AMD Strix Halo (Ryzen AI Max+ 395) — verified 2026-05-05

ทางที่ Gemini Pro ใน PDF [[sources/ai-iot-server-build-v3]] ไม่ได้เสนอ — สเปกคล้าย Mac แต่ใช้ AMD + Linux ได้

### Spec
```
CPU:    Ryzen AI Max+ 395 (16C Zen 5)
GPU:    Radeon 8060S (40 RDNA 3.5 CUs) — iGPU
RAM:    128GB LPDDR5X-8000 unified, 256-bit bus
Bandwidth: ~215 GB/s (verified)
iGPU shared VRAM: max 96GB
TDP: 45-120W configurable
```

### ราคาในไทย (verified)

| เครื่อง | ราคา |
|---|---|
| **GMKtec EVO-X2 128GB** ⭐ | **78,900฿** (ศูนย์ไทย, Lazada/Shopee) |
| PELADN YO1 128GB | 78,900฿ (ศูนย์ไทย) |
| Framework Desktop 128GB | 125-135K฿ (นำเข้า) |
| HP ZBook Ultra G1a (laptop) | 199,900฿ |

### Benchmark Local LLM (verified)
- Llama 3.3 70B Q4_K_M: **5.0-5.5 tok/s** ⚠️ ช้ากว่า M4 Max
- Qwen 2.5 72B Q4: 4.5-5.5 tok/s
- Llama 3.1 8B Q4: 45-55 tok/s

### Power consumption
- Idle: 10-13W (เทียบ Mac M4 Max 6-10W — ใกล้เคียง)
- LLM load: ~82W (เทียบ Mac 80-120W — ดีกว่าเล็กน้อย)
- Peak: 220W (เทียบ Mac 145-170W)

### Strix Halo เหนือ M4 Max ตรงไหนบ้าง?

| ปัจจัย | Strix Halo 128GB | M4 Max 64GB |
|---|---|---|
| **70B Q4 speed** | ❌ 5 tok/s | ✅ 6-10 tok/s (bandwidth 2.5x) |
| **RAM size** | ✅ 128GB → รัน 100B+ ได้ | ❌ 64GB เพดาน |
| **ราคาในไทย** | ✅ **78,900฿** | ❌ 120-130K฿ |
| **Linux native** | ✅ | ⚠️ macOS only |
| **Idle power** | ใกล้เคียง 10-13W | 6-10W |
| **Resale 5 ปี** | ⚠️ AMD | ✅ Mac คงราคา |
| **Upgradeable** | ❌ บัดกรี | ❌ บัดกรี |

**Verdict**: เหนือ Mac เรื่อง "ขนาด RAM + ราคา + Linux" / **แพ้ Mac เรื่อง 70B speed**

ดูรายละเอียด → [[sources/strix-halo-research-2026-05-05]]

## เปรียบเทียบ 3 ทางเลือกหลัก (สำหรับเงื่อนไข "เหนือ M4 Max + ประหยัดไฟ + ราคาเหมาะสม + ระยะยาว")

| เกณฑ์ | A: Strix Halo 128GB | B: PC + RTX 5090 | C: PC + RTX 4090 มือสอง |
|---|---|---|---|
| **70B Q4 speed** | ⚠️ 5 tok/s (ช้ากว่า Mac) | ✅✅ 25-35 tok/s | ✅ 10-15 tok/s |
| **RAM/VRAM size** | ✅✅ 128GB unified | ⚠️ 32GB VRAM | ⚠️ 24GB VRAM |
| **ประหยัดไฟ 24/7** | ✅✅ idle 12W | ❌ ~80W idle (system+GPU) | ⚠️ ~70W idle |
| **ราคาในไทย** | ✅✅ **78,900฿** | ❌ ~140-150K฿ | ✅ ~95-105K฿ |
| **ระยะยาว** | ✅ 5+ ปี (แต่ไม่ upgrade) | ⚠️ GPU ใหม่ทุก 3-4 ปี | ⚠️ GPU เก่าแล้ว ใช้ 3-4 ปี |
| **Linux/IoT/Docker** | ✅ | ✅ | ✅ |

### Verdict ตามค่านิยมของผู้ใช้

ถ้า "**เหนือ M4 Max**" = เร็วกว่าที่ 70B → **Option B (RTX 5090)** เท่านั้น แต่ขัดประหยัดไฟ + ราคา
ถ้า "**เหนือ M4 Max**" = RAM ใหญ่กว่า + ถูกกว่า + Linux → **Option A (Strix Halo)** ✅ คุ้มที่สุด
ถ้าต้องการ balance → **Option C (RTX 4090 used)** เร็วกว่า A, ถูกกว่า B, แต่ idle power สูง

**คำเตือน**: PC build ใน PDF [[sources/ai-iot-server-build-v3]] (RTX 4070 Ti Super 16GB) **ไม่ตอบโจทย์ "เหนือ M4 Max"** ที่ 70B เลย → 70B Q4 จะรันที่ 3-6 tok/s (offload หนัก) ซึ่งช้ากว่าทั้ง M4 Max และ Strix Halo

## 🆕 Option ที่ 4: Mac Studio มือสอง — verified 2026-05-05

⭐ **Plot twist**: Mac Studio M1 Ultra 128GB มือสองในไทย **ถูกกว่า + เร็วกว่า** Strix Halo

### ราคามือสองไทย + 70B Q4 (verified)

| รุ่น | RAM | Bandwidth | ราคามือสอง | 70B Q4 |
|---|---|---|---|---|
| M1 Max | 64GB | 400 GB/s | **36-42K฿** | 6.3-7.0 |
| **M1 Ultra** | **128GB** | **800 GB/s** | **65-75K฿** ⭐ | **12.5-13.5** |
| M2 Max | 64GB | 400 GB/s | 55-62K฿ | 7.5-8.2 |
| M2 Ultra | 128GB | 800 GB/s | 105-120K฿ | 14.0-15.5 |
| M2 Ultra | 192GB | 800 GB/s | 115-135K฿ | 14.0-15.5 |
| M3 Ultra | 96GB | 819 GB/s | 115-125K฿ | 16.5-18.0 |
| M3 Ultra | 256GB | 819 GB/s | 165-195K฿ | 16.5-18.0 |

### M1 Ultra 128GB used vs Strix Halo (head-to-head)

| | Strix Halo 128GB | M1 Ultra 128GB used |
|---|---|---|
| ราคา | 78,900฿ | **65-75K฿** ⭐ |
| Bandwidth | 215 GB/s | **800 GB/s** (3.7x) |
| 70B Q4 | 5.0-5.5 tok/s | **12.5-13.5 tok/s** (2.3x) |
| RAM | 128GB | 128GB |
| ประกัน | ✅ ใหม่ | ❌ มือสอง 4 ปี |
| Linux/Docker | ✅ native | ⚠️ Docker Desktop |
| Resale 5 ปี | ⚠️ AMD | ✅ Mac คงราคาดี |
| macOS support | - | ถึง ~2030 |

→ **M1 Ultra 128GB used ชนะที่: ราคา + speed + bandwidth**
→ **Strix Halo ชนะที่: ใหม่+ประกัน, Linux native, อายุการใช้งานยาวกว่าแน่ๆ**

### ⚠️ Caveats ของ Mac มือสอง
1. ไม่มีประกัน — เช็ค AppleCare ที่เหลือ
2. M1 Ultra ปี 2022 → 4 ปีแล้ว, โอกาส SSD wear / fan / power supply เสื่อม
3. macOS support ลด (M1 อาจถูก deprecate ใน macOS 19-20)
4. ราคามือสองผันผวน — เช็ค Facebook Group "ซื้อขาย Mac"
5. Software lock / iCloud lock — verify ก่อนโอนเงิน

ดูรายละเอียด → `raw/mac-studio-used-thailand-2026-05-05.md`

## เปรียบเทียบ 4 ทางเลือกหลัก (Final)

| เกณฑ์ | Strix Halo new | M1 Ultra used | RTX 5090 PC | RTX 4090 used PC |
|---|---|---|---|---|
| ราคา | 78,900฿ | **65-75K** ⭐ | 140-150K | 95-105K |
| 70B Q4 tok/s | 5 | **12-13** | 25-35 | 10-15 |
| RAM/VRAM | 128GB | 128GB | 32GB | 24GB |
| ประหยัดไฟ idle | ✅ 12W | ⚠️ 6-10W | ❌ 80W | ❌ 70W |
| Linux/IoT | ✅ | ⚠️ Docker | ✅ | ✅ |
| ประกัน | ✅ ใหม่ | ❌ | ✅ ใหม่ | ❌ |
| ระยะยาว 5 ปี | ✅ | ⚠️ HW เสื่อม | ⚠️ GPU obsolete | ⚠️ |
| Resale | ⚠️ | ✅ | ⚠️ | ⚠️ |

### 🎯 Verdict ตามค่านิยมของผู้ใช้

**ถ้ารับ "มือสอง" ได้** → **M1 Ultra 128GB มือสอง 65-75K฿** ⭐ คุ้มที่สุด:
- ถูกกว่า Strix Halo ~5-15K
- เร็วกว่า Strix Halo ที่ 70B 2.3 เท่า
- "ใช้ระยะยาว" ได้ ~3-5 ปีก่อนเสี่ยง hardware fail (เพราะ 4 ปีแล้ว)

**ถ้าต้อง "ใหม่ + ประกัน + Linux native"** → **Strix Halo (GMKtec EVO-X2) 78,900฿**:
- ใหม่ทั้งเครื่อง, support เต็มที่
- Linux/Docker/IoT native
- 70B 5 tok/s ก็ยังพอใช้

**ถ้าต้อง "70B เร็วสุดในงบ"** → **M2 Ultra 128GB used 105-120K** (14-15 tok/s) หรือ **PC + RTX 5090** (25-35 tok/s)

## ข้อเสนอแนะ (Decision Logic)

> ผู้ใช้กำลังเปลี่ยนใจจาก Mac → PC เพราะ "spec แรงกว่า อัพเดทได้ ในราคาใกล้เคียงกัน"

**ถ้าจะเลือก PC:**
1. ✅ ถูกต้องที่จะเลือก PC ถ้าต้องการ:
   - Upgradeability (เปลี่ยน GPU ในอนาคต)
   - รัน IoT broker + Home Assistant 24/7 native บน Linux
   - Bitcoin full node + Umbrel-style apps (ดู [[memory:project-pi5-server]])
2. ⚠️ แต่ต้องรู้ว่า **16GB VRAM ไม่พอรัน 70B Q4 เต็มความเร็ว** — รันได้แต่ช้ากว่า Mac unified memory
3. ⚠️ **ตรวจสอบ mainboard อีกครั้ง** — PDF ระบุ B860M ซึ่งเป็น Intel chipset, ของจริง AMD ต้องเป็น **B850M**

**ทางเลือกอื่นในงบเดียวกัน:**
- **PC + RTX 5070 Ti 16GB** (รุ่นใหม่กว่า ราคาใกล้กัน) — efficiency ดีกว่า 4070 Ti Super
- **PC + RTX 4090 24GB ซื้อมือสอง** — VRAM เพิ่มเป็น 24GB, รัน 32B Q4 เต็ม + 70B Q3 ได้
- **PC ลด RAM เป็น 64GB** ประหยัด ~10,000฿ → upgrade GPU ดีกว่า

**Hybrid approach (น่าสนใจสุด):**
- ใช้ Pi5 ปัจจุบันเป็น IoT broker + Bitcoin node 24/7 (ใช้ไฟ ~10W)
- สร้าง PC สำหรับ Local LLM (เปิดเฉพาะตอนใช้)
- ลดปัญหา PC ใช้ไฟ 50-80W idle 24/7

## แหล่งข้อมูลที่ใช้

- [[sources/ai-iot-server-build-v3]] — สเปก PC build ที่ Gemini Pro เสนอ (พบ chipset typo + 16GB VRAM ไม่พอ 70B)
- [[sources/strix-halo-research-2026-05-05]] — verified ราคา/benchmark/power ของ Ryzen AI Max+ 395
- [[sources/local-llm-mac-mini-guide]] — ตัวเลข tok/s, 60% rule, Apple Silicon
- [[sources/rpi-ai-hat-plus-2-official]] — ทางเลือก low-end (Pi5 + AI HAT+)
- [[sources/ollama-pi5]] — บริบท Ollama บน ARM
- [[concepts/ai-tools/local-llm-routing]] — pattern routing local↔cloud

## ความสัมพันธ์

- ขยายแนวคิดจาก [[synthesis/dual-ai-workflow]] (ใช้ทั้ง local + cloud)
- เกี่ยวข้องกับ [[entities/ai-tools/telegram-ai-router]] (ใช้ local LLM เป็น tier 1)


---

### `wiki/synthesis/iot-lora-architecture.md`

---
type: synthesis
tags: [architecture, lora, esp32, esp32-s3, mqtt, telegram, grafana, project-decided]
sources: [iot-lora-gateway-architecture, hardware-inventory-2026-04-18, mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# สถาปัตยกรรมโปรเจ็ค: IoT Temperature Monitor (LoRa Gateway)

> **สถานะ**: Architecture ตัดสินใจแล้ว (จาก diagram 2026-04-18)

## Data Flow ทั้งหมด

```
[DHT11]
   │ single-wire
[ESP32 DevKit V1]  ← Sensor Node (ไม่ต้องมี WiFi)
   │ UART (TX/RX/M0/M1/AUX)
[DX-LR02 TX]
   │ LoRa 900MHz ~~ wireless (สูงสุด km)
[DX-LR02 RX]
   │ UART
[ESP32-S3-N16R8]   ← LoRa Gateway (มี WiFi)
   │ WiFi + MQTT (TCP port 1883)
[Mosquitto Broker] ← MQTT Broker
   │
   ├── [Python/Node.js bridge] → [Telegram Bot]  ← alert อุณหภูมิผิดปกติ
   └── [Telegraf] → [InfluxDB] → [Grafana]       ← dashboard กราฟย้อนหลัง
```

## Hardware Mapping (จาก inventory)

| บทบาท | Hardware | สถานะ |
|------|---------|-------|
| Sensor | [[entities/iot/esp32]] DevKit V1 | ✅ มีแล้ว |
| Sensor | [[entities/iot/dht11]] | ✅ มีแล้ว |
| LoRa TX | [[entities/iot/dx-lr02-lora]] #1 | ✅ มีแล้ว |
| LoRa RX | [[entities/iot/dx-lr02-lora]] #2 | ✅ มีแล้ว |
| Gateway | [[entities/iot/esp32-s3]] N16R8 | ✅ มีแล้ว |
| Power | [[entities/iot/18650-battery-shield]] + Vapcell M35 ×2 | ✅ มีแล้ว |

**ข้อสรุปสำคัญ: Hardware ครบทุกชิ้นแล้ว ไม่ต้องซื้อเพิ่ม**

## Software Stack (ต้องติดตั้ง)

| Layer | Software | ติดตั้งที่ | สถานะ |
|-------|---------|----------|-------|
| Firmware (Sensor) | Arduino/ESP-IDF + DHT lib | ESP32 flash | 🔲 |
| Firmware (Gateway) | Arduino/ESP-IDF + PubSubClient | ESP32-S3 flash | 🔲 |
| MQTT Broker | [[entities/iot/mosquitto]] | Server/Mac | 🔲 |
| Data bridge | **Telegraf** หรือ **[[entities/iot/node-red]]** | Server/Mac | 🔲 |
| DB | [[entities/iot/influxdb]] v2 หรือ [[entities/iot/mysql]] | Server/Mac | 🔲 |
| Dashboard | [[entities/iot/grafana]] | Server/Mac | 🔲 |
| Alert | [[entities/iot/telegram-bot]] | Python script | 🔲 |

### ⚡ เปรียบเทียบ Stack ทางเลือก

| หัวข้อ | Stack A (Telegraf) | Stack B (Node-RED) |
|--------|--------------------|--------------------|
| Middleware | Telegraf | [[entities/iot/node-red]] |
| Database | [[entities/iot/influxdb]] | [[entities/iot/mysql]] |
| Dashboard | [[entities/iot/grafana]] | Grafana หรือ Node-RED Dashboard |
| ความซับซ้อน | ปานกลาง | ต่ำ (low-code) |
| Control Panel | ❌ | ✅ (Button/Switch บน dashboard) |
| เหมาะกับ | production, analytics | lab, prototype, control |

## MQTT Topic Structure (แนะนำ)

```
home/
├── room/
│   ├── temperature      ← ESP32-S3 publish
│   └── humidity         ← ESP32-S3 publish
└── alerts/
    └── temperature      ← Python bridge publish (เมื่อเกิน threshold)
```

## ⚠️ ข้อควรระวัง / Open Questions

1. **Line Notify deprecated** — เปลี่ยนเป็น Telegram หรือ Line Messaging API
2. **Mosquitto รันที่ไหน?** — Mac local (dev) vs Raspberry Pi (production)
3. **LoRa channel config** — DX-LR02 ทั้ง 2 ตัวต้องตั้งค่า channel เดียวกัน
4. **Power budget** — ESP32 Sensor node ใช้ 18650 shield หรือ USB?
5. **Deep sleep** — ESP32 Sensor ควร deep sleep ระหว่าง reading เพื่อประหยัด battery

## ลำดับการ Implement (แนะนำ)

1. **Phase 1** — Flash ESP32 + DHT11 → Serial print ทดสอบ sensor
2. **Phase 2** — ต่อ DX-LR02 TX กับ ESP32, ทดสอบ LoRa send
3. **Phase 3** — ต่อ DX-LR02 RX กับ ESP32-S3, ทดสอบ LoRa receive
4. **Phase 4** — ESP32-S3 → WiFi → Mosquitto local → MQTT subscribe ยืนยันได้
5. **Phase 5** — Telegraf + InfluxDB + Grafana dashboard
6. **Phase 6** — Telegram Bot alert

## แหล่งข้อมูล

- [[sources/iot-lora-gateway-architecture]] — architecture diagram (ตัดสินใจ)
- [[sources/hardware-inventory-2026-04-18]] — hardware ที่มี
- [[sources/mqtt-introduction]] — MQTT foundation


---

### `wiki/synthesis/garbage-report-ocr.md`

---
type: synthesis
tags: [env, ai-tools, ocr, claude-api, waste-report, hospital, vision]
sources: [infectious-waste-th-law]
domains: [Env, AI Tools]
created: 2026-05-14
updated: 2026-05-14
---

# ระบบอ่านภาพใบรายงานขยะทั่วไปโรงพยาบาล (Garbage Report OCR)

## คำถามที่ตอบ

"จะสร้างระบบอ่านภาพใบรายงานขยะทั่วไปของโรงพยาบาล (internal form) โดยอัตโนมัติได้อย่างไร?"

## สรุป

ใช้ **Claude Vision API** อ่านภาพถ่ายใบรายงานขยะทั่วไป (รับจาก LINE หรือ upload) แล้ว extract ข้อมูลออกมาเป็น JSON structured data เพื่อบันทึกลงระบบหรือตรวจสอบต่อ — เป็น pattern เดียวกับ [[synthesis/pharmacy-order-checker]] แต่ปรับ domain สำหรับงานอนามัยสิ่งแวดล้อม

## Architecture

```
[ภาพใบรายงานขยะ (ถ่ายจากมือถือ / LINE / scan)]
      ↓ base64 encode
[Claude Vision API (claude-sonnet-4-6)]
      ↓ system prompt: extract waste report fields
[JSON structured data]
      ↓
[ตรวจสอบ / แก้ไข / บันทึกฐานข้อมูล]
      ↓ (อนาคต)
[FastAPI endpoint บน Raspberry Pi 5]
```

## Fields ที่ extract จากใบรายงานขยะทั่วไป

ฟิลด์มาตรฐานที่พบในแบบฟอร์มภายในโรงพยาบาล:

| Field (JSON key) | ความหมาย | ตัวอย่าง |
|-----------------|----------|---------|
| `date` | วันที่บันทึก | "2026-05-14" |
| `department` | ตึก / แผนก / ward | "ตึกอายุรกรรม" |
| `waste_type` | ประเภทขยะ | "มูลฝอยติดเชื้อ" / "ขยะทั่วไป" |
| `color_code` | สีถุง/ภาชนะ | "แดง" / "เหลือง" / "น้ำตาล" / "ดำ" |
| `weight_kg` | น้ำหนัก (กิโลกรัม) | 12.5 |
| `quantity` | จำนวนถุง/กล่อง/ภาชนะ | 4 |
| `unit` | หน่วย | "ถุง" / "กล่อง" |
| `recorder` | ชื่อผู้บันทึก | "นายสมชาย ใจดี" |
| `supervisor` | ผู้ตรวจสอบ / หัวหน้า | "นางสาวมาลี สุขใส" |
| `notes` | หมายเหตุ (ถ้ามี) | null |

> ระบบสีถุงอ้างอิงจาก [[concepts/env/infectious-waste-management]] — แดง = ติดเชื้อทั่วไป, เหลือง = sharps, น้ำตาล = เคมี, ดำ = ทั่วไป

## Claude API Prompt Design

```python
SYSTEM_PROMPT = """
You are a data extraction assistant for hospital waste reports (Thai hospital internal forms).
Extract all visible fields from the waste report image and return as JSON.

Required fields:
- date: recording date (YYYY-MM-DD format, convert Thai Buddhist Era to CE if needed)
- department: ward/department name in Thai
- waste_type: type of waste in Thai (มูลฝอยติดเชื้อ / ขยะทั่วไป / ขยะเคมี / ของมีคม)
- color_code: bag/container color in Thai (แดง / เหลือง / น้ำตาล / ดำ)
- weight_kg: weight as float, null if not recorded
- quantity: number of bags/boxes as integer, null if not recorded
- unit: unit in Thai (ถุง / กล่อง / กระป๋อง)
- recorder: name of person who recorded
- supervisor: name of supervisor/checker, null if not present
- notes: any additional notes, null if none

If a field is unclear, illegible, or missing from the form, set it to null.
Return ONLY valid JSON, no explanations, no markdown.
"""
```

## Python Code Sample

```python
import anthropic
import base64
import json
from pathlib import Path


def read_waste_report(image_path: str) -> dict:
    client = anthropic.Anthropic()

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    ext = Path(image_path).suffix.lower()
    media_type_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                      ".png": "image/png", ".webp": "image/webp"}
    media_type = media_type_map.get(ext, "image/jpeg")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract all fields from this hospital waste report form."
                    }
                ],
            }
        ],
        system=SYSTEM_PROMPT,
    )

    raw = message.content[0].text.strip()
    return json.loads(raw)


# ตัวอย่างใช้งาน
if __name__ == "__main__":
    result = read_waste_report("waste_report_2026_05_14.jpg")
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### ตัวอย่าง Output

```json
{
  "date": "2026-05-14",
  "department": "ตึกอายุรกรรมชาย",
  "waste_type": "มูลฝอยติดเชื้อ",
  "color_code": "แดง",
  "weight_kg": 8.5,
  "quantity": 3,
  "unit": "ถุง",
  "recorder": "นายสมชาย ใจดี",
  "supervisor": "นางสาวมาลี สุขใส",
  "notes": null
}
```

## Confidence Handling

กรณีที่ภาพไม่ชัด / ตัวเขียนยาก → เพิ่ม field `_confidence` ใน prompt:

```python
# เพิ่มใน SYSTEM_PROMPT
"""
Also include a "_confidence" field (0.0-1.0) indicating overall extraction confidence.
If confidence < 0.7, add "_unclear_fields" list with field names that were hard to read.
"""
```

## Integration Points

- **IoT cross-check**: นำค่า `weight_kg` ไปเปรียบเทียบกับ sensor data จาก [[synthesis/waste-weight-monitoring]] (load cell บนถังขยะ)
- **Database**: บันทึกลง PostgreSQL / PocketBase บน Raspberry Pi 5 ([[entities/ai-tools/pocketbase]])
- **FastAPI endpoint**: รับ multipart image upload → return JSON → frontend แสดงผลตรวจสอบ
- **LINE integration**: webhook รับรูปจาก LINE → ส่ง OCR → ตอบกลับตาราง (อนาคต)

## ข้อจำกัด

| ปัญหา | วิธีรับมือ |
|-------|-----------|
| ลายมือแย่มาก | Claude Vision รับมือได้ดี แต่เพิ่ม `_unclear_fields` ให้ user ตรวจ |
| แบบฟอร์มแต่ละตึกต่างกัน | Prompt แบบ flexible (ไม่ผูกกับ layout เฉพาะ) |
| ภาพมืด/เบลอ | แจ้ง user ถ่ายใหม่ถ้า confidence < 0.6 |
| วันที่ พ.ศ. / ค.ศ. | Prompt สั่งให้ convert เป็น CE เสมอ |

## ความสัมพันธ์

- [[concepts/env/infectious-waste-management]] — ประเภทขยะ ระบบสีถุง กฎการบันทึกปริมาณ (ประกาศกรมอนามัย 2565)
- [[synthesis/waste-weight-monitoring]] — IoT weight sensor cross-check
- [[synthesis/pharmacy-order-checker]] — OCR architecture pattern ต้นแบบ (Claude Vision + JSON output)
- [[synthesis/appsheet-to-webapp-pi5]] — Platform: FastAPI + Raspberry Pi 5 สำหรับ deployment

## แหล่งข้อมูล

- [[sources/infectious-waste-th-law]] — กฎกระทรวงว่าด้วยการกำจัดมูลฝอยติดเชื้อ พ.ศ. 2545, 2564
- [training] Anthropic Claude Vision API documentation


---

### `wiki/synthesis/temperature-monitor-project.md`

---
type: synthesis
tags: [project-plan, temperature, mqtt, dht11, esp32, dashboard, line, telegram]
sources: [hardware-inventory-2026-04-18, mqtt-introduction]
created: 2026-04-18
updated: 2026-04-18
---

# แผนโปรเจ็ค: Temperature Monitor → มือถือ

> **✅ อัปเดต 2026-04-18**: Architecture ตัดสินใจแล้ว — **เลือก Approach C (LoRa Gateway)**  
> ดูรายละเอียดเต็มที่ [[synthesis/iot-lora-architecture]]

## คำถามที่ตอบ

*"จะทำ temperature monitoring ในห้อง ส่งข้อมูลผ่านมือถือ (Line/Telegram/Dashboard กราฟย้อนหลัง) ได้ยังไง?"*

## สรุป

ด้วย hardware ที่มีอยู่ใน lab สามารถทำได้ **3 แนวทาง** (~~Approach C ถูกเลือกแล้ว~~):

---

## แนวทาง A — WiFi + MQTT + Grafana (แนะนำสำหรับเริ่มต้น)

```
[ESP32 + DHT11] --WiFi/MQTT--> [Mosquitto] --> [InfluxDB] --> [Grafana]
                                                           --> [Telegram Bot]
```

**Hardware ที่ใช้**: [[entities/iot/esp32]] + [[entities/iot/dht11]] + [[entities/iot/18650-battery-shield]]  
**Software**: [[entities/iot/mosquitto]] + InfluxDB + Grafana + Telegram Bot API

**ข้อดี**: กราฟย้อนหลัง, dashboard สวย, alert ได้  
**ข้อเสีย**: ต้องมี server (Raspberry Pi, VPS, หรือ PC เปิดตลอด)  
**เวลาทำ**: ~1-2 วัน

---

## แนวทาง B — WiFi + HTTP + Line Notify (ง่ายที่สุด)

```
[ESP32 + DHT11] --HTTP POST--> [Line Notify API]
```

**Hardware ที่ใช้**: [[entities/iot/esp32]] + [[entities/iot/dht11]]  
**Software**: Line Notify (ฟรี, หมดอายุ 2025 — อาจต้องใช้ Line Messaging API แทน)

**ข้อดี**: ง่ายสุด ไม่ต้องมี server  
**ข้อเสีย**: ไม่มีกราฟย้อนหลัง แค่ notification  
**เวลาทำ**: ~2-3 ชั่วโมง

---

## แนวทาง C — LoRa + WiFi Gateway + MQTT (advanced)

```
[ESP32 + DHT11 + DX-LR02] --LoRa--> [ESP32-S3 + DX-LR02 + WiFi] --MQTT--> [Dashboard]
    (ห้องอื่น/ไม่มี WiFi)                   (ใกล้ router)
```

**Hardware ที่ใช้**: [[entities/iot/esp32]] + [[entities/iot/dht11]] + [[entities/iot/dx-lr02-lora]] × 2 + [[entities/iot/esp32-s3]]  
**ข้อดี**: ไม่ต้องการ WiFi ที่ node — เหมาะถ้า sensor อยู่ไกล router  
**ข้อเสีย**: ซับซ้อนกว่า setup มากกว่า  
**เวลาทำ**: ~3-5 วัน

---

## แนะนำลำดับการทำ

1. **เริ่มด้วย A** — ใช้ ESP32 + DHT11, test MQTT กับ Mosquitto local ก่อน
2. ทำ **Telegram bot** แจ้งเตือนถ้าอุณหภูมิเกิน threshold
3. ถ้าต้องการ node ที่ไม่มี WiFi → upgrade เป็น **C**

## Stack ที่แนะนำ (Approach A)

| Layer | Technology | หมายเหตุ |
|-------|-----------|---------|
| Sensor | DHT11 → ESP32 | อ่านทุก 30s |
| Transport | MQTT QoS 1 | topic: `home/room/temperature` |
| Broker | Mosquitto (local) | รันบน Mac/PC หรือ RPi |
| Storage | InfluxDB | time-series DB ฟรี |
| Dashboard | Grafana | กราฟย้อนหลัง |
| Alert | Telegram Bot | แจ้งเตือนเมื่อเกิน threshold |

## แหล่งข้อมูล

- [[sources/hardware-inventory-2026-04-18]] — inventory hardware ที่มี
- [[sources/mqtt-introduction]] — MQTT protocol พื้นฐาน


---

### `wiki/synthesis/dual-ai-workflow.md`

---
type: synthesis
tags: [gemini, claude, workflow, ai-tools, cost-optimization]
sources: [telegram-ai-router-design]
created: 2026-04-19
updated: 2026-04-19
---

# Dual AI Workflow — Gemini CLI + Claude

## คำถามที่ตอบ
จะใช้ Gemini CLI และ Claude ร่วมกันอย่างไรให้ประหยัด credit สูงสุด โดยไม่สูญเสียความต่อเนื่องของ context?

> หมายเหตุ: หน้านี้เน้น workflow ระหว่าง Gemini CLI กับ Claude เท่านั้น สำหรับการใช้งาน OpenRouter และ fallback free-model ให้ดู [[wiki/synthesis/openrouter-agent-routing]] และ [[concepts/ai-tools/openrouter-api]].

---

## ตาราง: งานไหนถาม Gemini / งานไหนถาม Claude

### ✅ ถาม Gemini CLI ก่อนเสมอ

| งาน | คำสั่งที่ใช้ |
|-----|------------|
| อ่านและสรุปไฟล์ใน `raw/` | "สรุปไฟล์ raw/ชื่อไฟล์.md ให้หน่อย" |
| สร้าง source page ใหม่ | "ingest raw/ชื่อไฟล์.md สร้าง wiki/sources/ ตาม GEMINI.md" |
| สร้าง entity/concept page (template ชัดเจน) | "สร้าง entity page สำหรับ [ชื่อ] ใน wiki/entities/iot/" |
| อัปเดต index-iot.md / index-env.md / index-ai.md | "อัปเดต index-iot.md เพิ่ม [ชื่อหน้า]" |
| append log.md | "เพิ่ม log entry สำหรับ [action] วันนี้" |
| ดูรายการไฟล์ใน wiki/ | "list ไฟล์ทั้งหมดใน wiki/entities/iot/" |
| ถามข้อมูลง่ายจากหน้าที่มีอยู่แล้ว | "ESP32 มีกี่ core?" / "LoRa ใช้ความถี่อะไรในไทย?" |
| นับหน้า / ตรวจ stats | "นับไฟล์ .md ใน wiki/ ทั้งหมด" |
| แก้ไขข้อความง่ายๆ ในหน้าเดียว | "แก้วันที่ updated ในไฟล์ X เป็น 2026-04-19" |
| **ค้นหา source ใหม่จาก web** | "ค้นหาข้อมูล [หัวข้อ] บันทึกลง raw/ ตาม Web Search Protocol" |

### 🧠 ถาม Claude เท่านั้น

| งาน | เหตุผล |
|-----|--------|
| `/lint` — ตรวจ contradiction + orphan pages | ต้องอ่านหลายหน้าพร้อมกันและ reason |
| Synthesis ข้ามโดเมน (IoT × Env) | ต้องเชื่อมโยง context ซับซ้อน |
| ออกแบบ schema / แก้ CLAUDE.md | ต้องเข้าใจ intent ทั้งระบบ |
| วิเคราะห์ contradiction ที่พบ | ต้องตัดสินว่าอันไหนถูก |
| ออกแบบระบบใหม่ (architecture) | ต้องการ reasoning หลายขั้น |
| คำถามที่ต้องการ "ความเห็น" หรือ tradeoff | Gemini ตอบ fact ได้ แต่ judgment ไม่เท่า |
| แก้ไขหลายไฟล์พร้อมกัน (atomic update) | Gemini อาจทำบางไฟล์พลาด |

---

## Handoff Protocol: Gemini → Claude

### Gemini ต้องทำเมื่อเสร็จงาน
เขียน entry ลงใน `handoff.md` format นี้:

```markdown
## [YYYY-MM-DD HH:MM] Gemini session

**งานที่ทำ:**
- สร้าง: wiki/sources/xxx.md
- อัปเดต: index-iot.md (เพิ่ม yyy)
- append: log.md

**context ที่ Claude ควรรู้:**
- [สิ่งที่น่าสนใจ / ข้อสังเกต / งานที่ค้างไว้]

**งานที่ยังไม่ทำ (ส่งต่อ Claude):**
- [ ] [งานที่ต้องการ Claude]
```

### Claude อ่าน handoff.md ก่อนเสมอ
เมื่อเริ่ม session ใหม่ Claude จะอ่าน handoff.md เพื่อรู้ว่า Gemini ทำอะไรไปแล้ว → ไม่ทำซ้ำ ต่อได้เลย

---

## Prompt Templates สำหรับ Gemini CLI

คัดลอกใช้ได้เลย:

### Ingest ไฟล์ใหม่
```
อ่านไฟล์ /Users/aase7en/Desktop/My-IoT-Wiki/raw/[ชื่อไฟล์].md
สรุปประเด็นหลัก และสร้าง source page ใน wiki/sources/[slug].md
ตาม template ใน GEMINI.md
แล้วเพิ่ม log entry ใน log.md และ handoff.md
```

### อัปเดต entity page
```
อ่าน /Users/aase7en/Desktop/My-IoT-Wiki/wiki/entities/iot/[ชื่อ].md
เพิ่มข้อมูล [X] ในหัวข้อ [Y]
อัปเดต updated date เป็น 2026-XX-XX
```

### ถามข้อมูลจาก wiki
```
อ่าน /Users/aase7en/Desktop/My-IoT-Wiki/wiki/context/wiki-overview.md
แล้วตอบ: [คำถาม]
```

### บันทึก handoff หลังเสร็จงาน
```
เขียน entry ใหม่ใน /Users/aase7en/Desktop/My-IoT-Wiki/handoff.md
สรุปสิ่งที่ทำในวันนี้ และงานที่ค้างไว้สำหรับ Claude
```

---

## ข้อจำกัดที่ต้องรู้ของ Gemini CLI (free tier)

| ข้อจำกัด | ผลกระทบ |
|---------|---------|
| shell ไม่ persist `cd` | ต้องใช้ absolute path เสมอ (แก้ใน GEMINI.md แล้ว) |
| ถูก restrict เป็น flash model | ตอบ reasoning ซับซ้อนได้ไม่ดี |
| ไม่มี memory ข้าม session | ต้องอ่าน wiki-overview.md ทุกครั้ง |
| อาจหยุดกลางคัน (context limit) | แบ่งงานเป็นชิ้นเล็ก |

---

## ความสัมพันธ์
- ใช้ร่วมกับ: [[entities/ai-tools/telegram-ai-router]]
- ใช้แนวคิด: [[concepts/ai-tools/local-llm-routing]]
- เกี่ยวข้องกับ: [[entities/ai-tools/hermes-agent]]


---

### `wiki/synthesis/waste-weight-monitoring.md`

---
type: synthesis
tags: [weight, load-cell, hx711, esp32, lora, mqtt, waste-monitoring]
sources: [esp32-hx711-randomnerd, esp32-hx711-mqtt-github, iot-lora-gateway-architecture]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Waste/Weight Monitoring (Load Cell + HX711 + ESP32 + LoRa)

> **คำถามที่ตอบ**: จะออกแบบระบบชั่งน้ำหนักถังขยะ/สินค้า แบบ wireless อย่างไร?

## สรุป

ใช้ [[entities/iot/load-cell]] (strain gauge) + [[entities/iot/hx711]] (24-bit ADC) วัดน้ำหนัก ต่อกับ [[entities/iot/esp32]] → ส่งผ่าน LoRa P2P (DX-LR02) → Gateway → MQTT → Dashboard แจ้งเตือนเมื่อถังเต็ม

## Data Flow

```
[Load Cell] (ติดใต้ถังขยะ)
      ↓ analog differential
[HX711 ADC] (24-bit, gain 128)
      ↓ 2-wire (DOUT + SCK)
[ESP32 Sensor] ← deep sleep ระหว่าง reading (ประหยัด battery)
      ↓ LoRa (DX-LR02 P2P)
[ESP32-S3 Gateway]
      ↓ WiFi MQTT
[Mosquitto] → [InfluxDB] → [Grafana]
      ↓ alert (weight > threshold)
[Telegram Bot] → แจ้ง "ถังขยะใกล้เต็ม"
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/load-cell]] | ❌ ยังไม่มี | ต้องซื้อ, เลือก range ตาม load (5kg/50kg) |
| [[entities/iot/hx711]] | ❌ ยังไม่มี | ต้องซื้อ, 24-bit ADC |
| [[entities/iot/esp32]] | ✅ มีแล้ว | GPIO digital สำหรับ HX711 |
| [[entities/iot/dx-lr02-lora]] | ✅×2 มีแล้ว | LoRa P2P wireless |
| [[entities/iot/18650-battery-shield]] | ✅ มีแล้ว | battery-powered node |

## Calibration ขั้นตอน

```cpp
#include <HX711.h>
HX711 scale;
scale.begin(DOUT, SCK);
scale.set_scale(calibration_factor);  // หา factor จากน้ำหนักรู้ค่า
scale.tare();                          // reset 0
float weight_kg = scale.get_units(10); // average 10 readings
```

**Calibration**: วางน้ำหนักรู้ค่า (1kg) → ปรับ `calibration_factor` จนแสดงค่าถูกต้อง

## Deep Sleep Strategy (ประหยัด Battery)

```
อ่านค่า → publish MQTT → deep sleep 5 นาที → ตื่น → repeat
Active: ~250mA × 2 วินาที
Sleep:  ~10µA × 298 วินาที
Average: ~1.7mA → 18650 3500mAh → ~85 วัน
```

## MQTT JSON Format

```json
{
  "bin_id": "bin_A1",
  "weight_kg": 12.5,
  "fill_pct": 62.5,
  "battery_v": 3.81,
  "rssi": -68
}
```

**Topic**: `waste/bin/<bin_id>/weight`

## ⚠️ ข้อควรระวัง

1. Load Cell ต้องการ **mechanical mounting ที่ดี** — ถ้าถังเอียง ค่าผิดพลาด
2. Temperature drift — HX711 gain เปลี่ยนตามอุณหภูมิ → calibrate ใหม่ทุกฤดู
3. LoRa interference — ถ้าหลาย sensor node → ใช้ time-slotting เพื่อกัน collision
4. ลม/vibration → noise ใน load cell → average readings 10-20 ครั้ง

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[entities/iot/load-cell]], [[entities/iot/hx711]], [[concepts/iot/lora-p2p]]
- ใช้ร่วมกับ: [[concepts/iot/data-logger]], [[concepts/iot/dashboard-design]]
- TinyML ต่อยอด: [[concepts/iot/tinyml]] (predict fill rate, optimize pickup schedule)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/esp32-hx711-randomnerd]] — wiring, calibration, HX711 library
- [[sources/esp32-hx711-mqtt-github]] — MQTT integration + Node-RED + Thingsboard


---

### `wiki/synthesis/cold-chain-vaccine.md`

---
type: synthesis
tags: [cold-chain, vaccine, ds18b20, esp32, lora, tinyml, anomaly-detection]
sources: [vaccine-temp-monitoring-iot, vaccine-cae-anomaly-detection, ds18b20-esp32-randomnerd]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Cold Chain Vaccine Monitoring (DS18B20 + ESP32 + AI Anomaly)

> **คำถามที่ตอบ**: จะออกแบบระบบตรวจสอบอุณหภูมิวัคซีน (+2°C~+8°C) ที่แจ้งเตือนทันทีเมื่อผิดปกติอย่างไร?

## สรุป

ใช้ [[entities/iot/ds18b20]] (One-Wire, ±0.5°C, waterproof) วัดอุณหภูมิตู้เก็บวัคซีน ส่งข้อมูลผ่าน LoRa หรือ GSM → MQTT → alert ทันทีผ่าน Telegram ต่อยอดด้วย TinyML anomaly detection บน ESP32 เพื่อตรวจสอบ pattern ผิดปกติก่อนที่อุณหภูมิจะเกิน threshold

## ข้อกำหนด Cold Chain วัคซีน

| ประเภทวัคซีน | Range อุณหภูมิ | ความเสี่ยง |
|------------|--------------|---------|
| วัคซีนทั่วไป (OPV, Hep B) | +2°C ~ +8°C | เสียได้ถ้าเกิน 8°C >1 ชั่วโมง |
| วัคซีนที่แช่แข็ง (OPV บางชนิด) | -15°C ~ -25°C | เสียได้ถ้าละลาย |
| Alert threshold แนะนำ | เกิน +7°C หรือต่ำกว่า +3°C | แจ้งเตือนทันที |

## Data Flow

```
[DS18B20 One-Wire] (หลายตัวใน 1 สาย)
      ↓
[ESP32 Sensor]
  ├── TinyML Anomaly Detection (local inference)
  │   └── แจ้งเตือน pattern ผิดปกติ ก่อน threshold
  └── LoRa P2P / GSM → [Gateway/Cloud]
                              ↓ MQTT
                        [Mosquitto]
                              ↓
                        [InfluxDB] → [Grafana]
                              ↓ alert
                        [Telegram Bot] 🚨
```

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/ds18b20]] | ❌ ยังไม่มี | One-Wire, waterproof, ±0.5°C |
| [[entities/iot/esp32]] | ✅ มีแล้ว | One-Wire library, DallasTemperature |
| [[entities/iot/dx-lr02-lora]] | ✅×2 มีแล้ว | LoRa P2P (ถ้าไม่มี WiFi) |
| [[entities/iot/18650-battery-shield]] | ✅ มีแล้ว | backup power สำคัญมาก |

## Multi-Sensor One-Wire (DS18B20)

```cpp
// ต่อหลายตัวใน pin เดียว (4.7kΩ pull-up)
OneWire oneWire(2);           // GPIO2
DallasTemperature sensors(&oneWire);
sensors.getDeviceCount();     // นับจำนวน sensors
sensors.getTempCByIndex(0);   // อ่านตัวที่ 0
```

## TinyML Anomaly Detection (ต่อยอด)

จาก [[sources/vaccine-cae-anomaly-detection]]: ใช้ **Convolutional Autoencoder (CAE)** train ด้วย temperature time-series ปกติ → ตรวจจับ anomaly ด้วย reconstruction error

| วิธี | Accuracy | Hardware | Latency |
|-----|---------|---------|---------|
| Threshold rule | ~70% | ทุก MCU | real-time |
| CAE (TF Lite) | **92%** | ESP32-S3 (PSRAM ต้องการ) | ~50ms |

**แนะนำ**: เริ่มด้วย threshold → ต่อยอด CAE บน ESP32-S3

## MQTT JSON Format

```json
{
  "sensor_id": "fridge_01",
  "temp_c": 5.25,
  "anomaly_score": 0.02,
  "alert": false,
  "battery_v": 3.82,
  "ts": 1745001234
}
```

## ⚠️ ข้อควรระวัง

1. **Battery backup** — ถ้าไฟดับ ระบบต้องทำงานต่อ ≥4 ชั่วโมง
2. **One-Wire parasite power** — ระวัง cable ยาว → ใช้ external power mode
3. **GSM vs LoRa** — ถ้าอยู่ในห้องเย็นที่มีผนังหนา → GSM ดีกว่า LoRa
4. **Log ไม่ขาดหาย** — ใช้ local SD card buffer ก่อน sync cloud

## ความสัมพันธ์

- เกี่ยวข้องกับ: [[concepts/iot/cold-chain-monitoring]], [[concepts/iot/tinyml]]
- ใช้ร่วมกับ: [[entities/iot/ds18b20]], [[entities/iot/esp32-s3]] (CAE)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/vaccine-temp-monitoring-iot]] — ESP32 + GSM alert cold chain
- [[sources/vaccine-cae-anomaly-detection]] — Deep Learning anomaly 92% accuracy
- [[sources/ds18b20-esp32-randomnerd]] — One-Wire wiring + library guide


---

### `wiki/synthesis/sunday-estate-webapp.md`

---
title: Sunday Estate Webapp — Real-Estate Management Platform
type: synthesis
domain: cross-domain
related:
  - ai-tools
  - iot          # Pi5 self-hosted infrastructure
created: 2026-05-17
session: 2026-05-17 dev
sources:
  - claude.ai/design bundle (tvug1cB05oRqix3k0_2SEA)
  - /Users/aase7en/supabase-pi5/.env (Pi5 self-host config)
  - /Users/aase7en/Library/CloudStorage/GoogleDrive-aase7en@sunday-estate.com/My Drive/ปล่อยกู้
  - /Users/aase7en/Library/CloudStorage/GoogleDrive-aase7en@sunday-estate.com/My Drive/ขายที่ดิน
---

# Sunday Estate Webapp

ระบบจัดการธุรกิจอสังหาริมทรัพย์ของ **Sunday Estate Co., Ltd.** — แทนเอกสาร Google Drive + กระดาษเดิม. ออกแบบ UI hi-fi prototype ผ่าน claude.ai/design แล้วต่อ data layer เข้า Supabase self-host บน Pi5 พร้อม FastAPI backend สำหรับ AI/OCR

> **Code อยู่นอก wiki**: `/Users/aase7en/Desktop/sunday-estate-webapp/` (separate GitHub repo `aase7en/sunday-estate-webapp`)
> **Entry doc**: [`sunday-estate-webapp/GETTING_STARTED.md`](../../../sunday-estate-webapp/GETTING_STARTED.md)
> **Latest QA batch** (2026-05-18): [[sunday-estate-frontend-qa-2026-05-18]] — 4 bugs fixed + 21 ghost buttons wired (commit `1e8147c`)

---

## Modules ทั้งหมด

### Core business modules
1. **ปล่อยกู้ / รับซื้อฝาก / จำนอง** — ติดตามสัญญา, ดอกเบี้ย, ตารางผ่อน, แจ้งเตือนครบกำหนด + OCR เอกสาร (โฉนด, บัตร ปชช., สัญญา)
2. **ลงทุนพัฒนาที่ดิน** — บัญชีรายจ่าย, หุ้นส่วน + ปันผล, แบ่งแปลง (parcel), ROI calculator, Gantt timeline

### Cross-cutting features
3. **AI Assistant** — chat ผ่าน OpenRouter (เลือก model ฟรี/ถูกได้เอง), system prompt ใส่ context ตาม role
4. **OCR เอกสาร** — Vision model (Gemini Flash 2.0 free / Qwen2-VL) → JSON → pre-fill form
5. **Custom fields editor** — Admin เพิ่ม field ลง loan/land ได้จาก UI โดยไม่ต้อง migrate (เก็บใน `metadata` JSONB)
6. **Drag-and-drop dashboard** — 12 widget catalog, long-press แก้ลำดับ, บันทึก layout ต่อ user ที่ `profiles.dashboard_layout`
7. **Notification popover** — unread filter, mark-read = หายจาก popup
8. **3 themes** — Light (Stripe) / Dark (Linear) / Modern (Vercel violet→cyan glassy)
9. **3 languages** — ไทย / English / 中文 พร้อม tooltips
10. **Profile editor** — แก้ชื่อ/รูป/สี/เบอร์, อัปโหลด avatar ผ่าน Supabase Storage

---

## Role × Scope Matrix

| Role | Loans | Lands | Dashboard | Settings | Scope toggle |
|------|-------|-------|-----------|----------|--------------|
| **Admin** | all (CRUD + delete) | all (CRUD + delete) | full + custom widgets | ทุก section + custom fields + model picker | All / Company / Personal |
| **Super** | scope='company' only (CRUD) | scope='company' read-only | full (no personal-only widgets) | integrations + account | locked → company |
| **User** (borrower) | own contracts only | none | borrower widgets | own profile + notifs | locked → own |

**Scope filter** (Admin only): `all` / `company` (Sunday Estate Co.,Ltd. + partners) / `personal` (Admin's individual business)

---

## Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React 18 + Babel-in-browser (bundle as-is) | rapid iteration, no build step; ฟิวเจอร์ migrate Vite+TS |
| Styling | CSS custom properties (3-theme system) | one source of truth, swap via `data-theme` attr |
| Fonts | IBM Plex Sans Thai + IBM Plex Mono + Sarabun | Thai-first typography |
| Charts | Custom SVG (in dashboard.jsx) | no extra lib |
| Backend | FastAPI on Pi5 | proxy for AI/OCR + admin ops |
| Database | Supabase self-host (Pi5 stack `supabasepi5`) | Auth + RLS + Storage + Realtime + Studio |
| Auth | Supabase Auth — Google OAuth + Email/Password | first signup → auto admin |
| AI / OCR | OpenRouter (Admin-selectable model) | free tier (Gemini Flash 2.0, Llama 3.3, Qwen) |
| Deploy | Docker Compose + Cloudflare Tunnel | nginx only public; Supabase/Postgres/Portainer/Bitcoin LAN-only |

---

## Infrastructure on Pi5

- Pi5 รัน Umbrel + Bitcoin node — **ห้ามแตะ**
- Supabase self-host ผ่าน Portainer, stack `supabasepi5`
  - Supabase API/Studio: `http://umbrel.local:8000` (Kong gateway)
  - Pooler ports: `5433` (session), `6543` (transaction) — internal/LAN only
  - PostgreSQL เก่า `webapp_db` ยังอยู่ที่ `5432` — ห้าม overwrite
- Secrets: `/Users/aase7en/supabase-pi5/.env` (ห้าม commit, ห้าม expose `SERVICE_ROLE_KEY` ใน frontend)
- Webapp stack จะลง Portainer แยก: `nginx :8080` + `fastapi :8000` (internal) + `cloudflared` (public profile)

---

## Supabase schema (13 migrations)

ลำดับการรัน — ดู [`sunday-estate-webapp/supabase/README.md`](../../../sunday-estate-webapp/supabase/README.md)

| # | File | Creates |
|---|------|---------|
| 0001–0002 | extensions + enums | pgcrypto, citext, pg_trgm, 19 ENUM types |
| 0003 | profiles | + `handle_new_user` trigger (first user → admin) + role helpers (`is_admin()`, `is_admin_or_super()`, `current_role()`) |
| 0004 | loans | + `loan_payments` (PK `LN-YYYY-NNN`, generated `due` column) |
| 0005 | lands | + `land_costs` / `land_partners` / `land_parcels` |
| 0006 | documents | metadata table; files in Supabase Storage bucket `documents` |
| 0007 | notifications | + `notification_reads` (per-user popover unread) |
| 0008 | audit_log + activity_log | trigger ทุก INSERT/UPDATE/DELETE บน loans/lands/profiles |
| 0009 | custom_field_defs + app_settings + or_model_cache | seeded defaults |
| 0010 | **RLS policies** | DENY-by-default, scope-aware (admin → all, super → company, user → own) |
| 0011 | storage | `documents` bucket (20MB, private) + path-aware policies `<entity>/<id>/file` |
| 0012 | views | `loan_summary`, `loans_aging`, `kpi_snapshot` + RPC helpers |
| 0013 | seed_demo | optional — demo data mirroring bundle |

### Extensibility built-in
- ทุก main table มี `metadata JSONB` + `tags TEXT[]` → เพิ่ม field โดยไม่ต้อง migrate
- `custom_field_defs` table — Admin สร้าง field ใหม่จาก UI; ค่าจริงเก็บใน `loans.metadata->>field_key`
- AI query (Admin only) ใช้ `custom_field_defs` schema → AI รู้จัก fields ทันทีที่สร้าง

---

## Project structure

```
sunday-estate-webapp/
├── GETTING_STARTED.md             ← walkthrough + troubleshooting
├── docker-compose.yml             ← nginx + fastapi + cloudflared
├── .env.example
├── prototype/                     ← React webapp (Babel-in-browser)
│   ├── index.html  styles.css  config.js
│   └── src/  (12 .jsx files: sbclient, data, ui, shell, login,
│              dashboard, loans, lands, borrower, ai, misc, app)
├── backend/                       ← FastAPI
│   ├── main.py  Dockerfile  requirements.txt
│   ├── core/    (config, auth, supabase, openrouter)
│   └── routers/ (ai, ocr, ai_sql, openrouter, custom_fields)
├── supabase/
│   ├── migrations/0001…0013.sql  ← 13 files, 1130 lines
│   └── README.md
└── deploy/
    ├── nginx/nginx.conf           ← static + reverse proxy /api/ + /<auth|rest|storage|realtime>/v1/
    └── cloudflared/config.example.yml
```

---

## Decisions & rationale (session 2026-05-17)

- **Bundle prototype as-is แทน Vite+TS รอบแรก** — speed of iteration ก่อน, migrate ทีหลังถ้าจำเป็น
- **Supabase self-host (Pi5) แทน Cloud** — Pi5 setup ทำไปแล้ว, ไม่ต้องสมัคร, ฟรี, public ผ่าน Cloudflare Tunnel
- **OpenRouter แทน Claude API ตรง** — Admin pick model ฟรี/ถูก (Gemini Flash 2.0, Qwen, DeepSeek) ลด cost
- **Demo mode shim ใน `sbclient.jsx`** — UI ทำงานได้แม้ไม่ตั้ง Supabase (mock auth + queries) → user ทดสอบ flow ได้ก่อน
- **Cache-buster `?v=N` ใน index.html** — Babel-in-browser cache aggressive, ต้อง bump version เมื่อแก้ .jsx
- **AddWidgetModal portal to body** — fade-in parent animation มี `transform` ทำให้ `position: fixed` ตกอยู่ใน parent containing block → ต้อง portal ออกมา
- **First signup → auto admin** — trigger ใน `0003_profiles.sql` ทำให้ Setup ครั้งแรกง่าย
- **service_role = backend only** — FastAPI ใช้สำหรับ admin ops; browser ใช้ ANON_KEY + JWT พร้อม RLS
- **Cloudflare Tunnel เปิดแค่ nginx :80** — Supabase Studio (8000), Portainer (9000), Postgres (5432/5433/6543), Bitcoin ports ยังคงอยู่ใน LAN

---

## Verification status (end of session)

✅ Demo mode end-to-end:
- Login → 3 roles → dashboard, loans, lands, settings, AI, OCR pages render
- Create loan → appears in list (LN-2026-001 created via test)
- Create land → appears in list (LD-008 created via test)
- 3 themes สลับได้, 3 ภาษาเปลี่ยน label, drag-drop ทำงาน, popover unread filter ทำงาน
- Settings → AI & OCR Models / Custom Fields panels load ไม่ error

⚠️ ต้องตั้งเองก่อนใช้จริง (รายละเอียดใน `GETTING_STARTED.md`):
- รัน migrations 0001–0013 ใน Supabase Studio
- ใส่ `SUPABASE_URL` + `SUPABASE_ANON_KEY` ใน `prototype/config.js`
- สมัครคนแรก → auto admin
- (Optional) `docker compose up` backend + `OPENROUTER_API_KEY` สำหรับ AI/OCR
- (Optional) Cloudflare Tunnel สำหรับ public access

## Real Supabase wiring status (2026-05-17)

✅ Applied migrations `0001…0013` to the Pi5 Supabase database via Postgres pooler (`umbrel.local:5433`) after fixing `0004_loans.sql` generated-column syntax.

✅ Verification after migration:
- 15 business tables present
- RLS enabled on 15 public tables
- 33 public RLS policies
- `documents` Storage bucket present
- seed demo data present (`loans=7`, `lands=7`)

✅ Filled `prototype/config.js` with `SUPABASE_URL=http://umbrel.local:8000` + browser-safe `ANON_KEY` only. No `SERVICE_ROLE` key was put in frontend code.

✅ Real auth smoke test passed:
- temporary signup through the web UI succeeded
- first profile became `admin` via `0003_profiles.sql` trigger
- dashboard, loans list, lands list, and Settings → AI & OCR Models loaded in Supabase mode
- temporary test user was deleted afterward, leaving `auth.users=0`, `profiles=0`; the real first account can still become admin

✅ Demo smoke still passed from a temporary demo-mode copy:
- `[sb] DEMO mode` logged
- demo admin login worked
- create loan produced `LN-2026-001`
- create land produced `LD-008`

✅ Production backend deploy via Pi5 Portainer is now live:
- real owner/admin account exists and has role `admin`
- webapp stack `sunday-estate` deploys from private GitHub repo through Portainer repository mode using a read-only GitHub token
- FastAPI + nginx are reachable at `http://umbrel.local:8090`
- `http://umbrel.local:8090/api/health` returns `{"status":"ok","service":"sunday-estate-api"}`
- OpenRouter model cache was synced into `or_model_cache` (`356` models, `28` free, `7` free vision) and `app_settings` points to cache-valid free models

✅ Deployment fixes committed to webapp `main` after Portainer errors:
- `4ebe39d fix: register FastAPI rate limiter` — fixed `se-fastapi` unhealthy by setting `app.state.limiter`
- `07b5faf fix: avoid nginx port 8080 conflict` — changed nginx host port to `NGINX_PORT=8090`
- `93c3840 fix: bake nginx config into image` — removed fragile bind mount for `deploy/nginx/nginx.conf`

✅ Production UI fully verified (2026-05-17 session 2):
- Login page renders correctly (Google OAuth + Email, 3 themes, 3 ภาษา, security badge)
- Login as admin (`aase7en@sunday-estate.com`) → Dashboard loads with real data (KPI widgets, bar chart, portfolio donut, contract table)
- Settings → AI & OCR Models: model list loads from cache correctly
- **Bug found & fixed**: `ดึงรายการใหม่` (sync from OpenRouter) failed with `"Invalid token: The specified alg value is not allowed"` — Supabase Pi5 uses **ES256** (EC P-256 via JWKS), not HS256. Fixed in `backend/core/auth.py` (commit `501c6c7`): fetch JWKS from `<SUPABASE_URL>/auth/v1/.well-known/jwks.json`, decode with algorithm from JWK, fallback to HS256.
- After redeploy: sync succeeded, model list refreshed from OpenRouter (new `openai/gpt-oss-120b:free` appeared)
- AI Chat tested: question "มีสัญญากี่ฉบับในระบบ?" → correct answer "7 ฉบับ" (matches seed data) ✅
- OCR UI renders (page accessible); full OCR test requires a real document image

⚠️ Still pending:
- optional Cloudflare Tunnel public access

---

## Claude handoff prompt (2026-05-17 session 2 — production verified)

Paste this into Claude if continuing from here:

```text
อ่าน CLAUDE.md และ wiki/synthesis/sunday-estate-webapp.md ก่อนเริ่มเสมอ.

Sunday Estate webapp — fully verified production state (2026-05-17):
- Wiki: /Users/aase7en/Desktop/InW-Wiki
- Webapp repo: /Users/aase7en/Desktop/sunday-estate-webapp
- Solo workflow: main only, no branch, no PR.
- Pi5 Supabase: http://umbrel.local:8000, stack supabasepi5. Do not touch Umbrel/Bitcoin/Postgres 5432.
- Webapp Portainer stack: sunday-estate
- Production URL: http://umbrel.local:8090
- Admin login: aase7en@sunday-estate.com (email/password via Supabase)

Everything verified and working:
- Production UI: login page, dashboard (real data), all sidebar pages render
- JWT: Supabase Pi5 uses ES256 (JWKS). Fixed in backend/core/auth.py (commit 501c6c7).
  Backend now fetches JWKS from <SUPABASE_URL>/auth/v1/.well-known/jwks.json (lru_cache).
- Settings → AI & OCR Models: model cache loads, "ดึงรายการใหม่" sync works
- AI Chat: end-to-end via OpenRouter, tested and correct ("7 สัญญา" matched seed data)
- Current models: Chat=deepseek/deepseek-v4-flash:free, OCR=google/gemma-4-31b-it:free

Next tasks (choose one):
A) Cloudflare Tunnel: `cloudflared tunnel create sunday-estate` → bind domain → `docker compose --profile public up -d cloudflared`
B) Test OCR: go to OCR เอกสาร page, upload a real Thai document image, verify JSON extraction
C) Real data: replace seed data with actual Sunday Estate loan/land records
D) New feature on the webapp

No code changes needed unless user picks a specific task.
```

## Future fields to consider (`metadata` JSONB — ไม่ต้องคิดตอนนี้)

- **Loans**: `credit_score`, `legal_status`, `insurance_policy`, `co_signer`, `redemption_history[]`, `previous_loans[]`
- **Lands**: `zoning`, `soil_type`, `utilities {water,electric,sewer,internet}`, `construction_permits[]`, `environmental_assessment`, `tax_history[]`
- **Profiles**: `two_factor_enabled`, `login_history[]`, `api_tokens[]`, `kyc_status`
- **Documents**: `version_history[]`, `signing_status` (DocuSign), `legal_review_status`
- **Analytics tables** (future): `saved_reports`, `custom_kpis`, `scheduled_exports`

---

## Notification roadmap

- Phase 1 (done): in-app popover เท่านั้น
- Phase 6+: Telegram Bot + SMS (ThaiBulkSMS/Twilio) + Email (Resend free 3K/month) + per-user opt-in `notification_channels` table

---

## Open Issues (2026-05-18)

> Synced จาก `session-memory.md` — อัปเดตเมื่อ TODO เสร็จหรือเปลี่ยนสถานะ

| # | Task | Priority | Notes |
|---|------|----------|-------|
| 1 | **Cloudflare Tunnel** — `cloudflared tunnel create sunday-estate` + bind domain + `docker compose --profile public up -d cloudflared` | 🟡 Medium | ทำให้ public access ได้จากนอก LAN |
| 2 | **Pi5 redeploy commit `1e8147c`** (Portainer Re-pull + Redeploy) + hard refresh + verify 14 ปุ่มตาม [[sunday-estate-frontend-qa-2026-05-18]] + OCR PDF editable fields | 🔴 High | frontend batch fix ยังไม่ถูก deploy |
| 3 | **Pi5 git pull webapp** + Portainer "Pull and redeploy" stack `sunday-estate` (commit `73860a0`) → verify `curl http://umbrel.local:8090/api/health` | 🔴 High | email-validator fix ยังไม่ถูก deploy |
| 4 | **ตรวจ `SUPABASE_SECRET_KEY`** (service_role) ใน Portainer stack `sunday-estate` env — ให้ `/api/admin/invite` ทำงาน | 🟡 Medium | ต้องใส่ service_role key ใน Portainer env |

---

## Pi5 Deployment Checklist

### วิธี redeploy ผ่าน Portainer (ทุกครั้งที่ push commit ใหม่)

```bash
# 1. ตรวจก่อน
curl http://umbrel.local:8090/api/health
# → {"status":"ok","service":"sunday-estate-api"}

# 2. บน Pi5 Portainer (http://umbrel.local:9000)
#    Stacks → sunday-estate → "Pull and redeploy"
#    (Portainer ดึง commit ล่าสุดจาก GitHub repo อัตโนมัติ)

# 3. ตรวจหลัง deploy
curl http://umbrel.local:8090/api/health
# hard refresh browser: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Win)
```

### ตรวจ env ใน Portainer stack `sunday-estate`

| Variable | ต้องมี | หมายเหตุ |
|----------|--------|---------|
| `SUPABASE_URL` | `http://umbrel.local:8000` | Kong gateway |
| `SUPABASE_ANON_KEY` | ✅ | browser-safe |
| `SUPABASE_SECRET_KEY` | ✅ service_role key | backend only — ห้าม expose frontend |
| `OPENROUTER_API_KEY` | ✅ | AI/OCR routing |
| `NGINX_PORT` | `8090` | avoid conflict |

### Cloudflare Tunnel setup (ยังไม่ได้ทำ)

```bash
# บนเครื่อง local หรือ Pi5
cloudflared tunnel login
cloudflared tunnel create sunday-estate
# → จด Tunnel ID ที่ได้

# แก้ deploy/cloudflared/config.example.yml
# ใส่ tunnel: <TUNNEL_ID> + credentials-file path
# hostname: sunday-estate.<your-domain>.com → http://nginx:80

# รัน public profile
docker compose --profile public up -d cloudflared
```

---

## Related wiki pages

- [[ai-tools/openrouter-claude-code]] — OpenRouter free models, model selection patterns
- [[synthesis/appsheet-to-webapp-pi5]] — prior wiki note on Pi5 self-hosted webapp architecture
- [[sources/umbrel-pi5-setup]] — Pi5 Umbrel / Portainer setup
- [[concepts/ai-tools/session-setup]] — Pi5 git redirect (`.git` outside Drive) — prerequisite


---

### `wiki/synthesis/env-webapp-schema-wastewater.md`

---
type: synthesis
tags: [web-app, postgresql, schema, wastewater, env, fastapi, migration]
sources: [appsheet-env-datadict]
created: 2026-05-04
updated: 2026-05-04
---

# PostgreSQL Schema: ระบบบำบัดน้ำเสีย (Wastewater Domain)

## คำถามที่ตอบ

"ออกแบบ database schema สำหรับแทน AppSheet ข้อมูลคุณภาพน้ำ โดยให้รองรับ: บันทึกรายวัน, สูตรคำนวณ, PDF report, IoT sensor ในอนาคต"

## สรุป

AppSheet table `ข้อมูลคุณภาพน้ำ` เดิมมี virtual columns และ computed fields จำนวนมาก ใน PostgreSQL แยกออกเป็น:
- **ตารางหลัก** เก็บค่าที่วัดได้จริง (raw measurements)
- **Computed values** คำนวณใน FastAPI (ไม่เก็บซ้ำ เพื่อ single source of truth)
- **ตาราง reference** สำหรับ meter, บุคลากร, บ่อบำบัด

---

## Schema SQL

```sql
-- =============================================
-- DOMAIN: Wastewater Treatment
-- AppSheet source: ข้อมูลน้ำประจำวัน → ข้อมูลคุณภาพน้ำ
-- =============================================

-- บ่อบำบัด (Aeration Pond / Treatment Unit)
CREATE TABLE treatment_ponds (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,  -- เช่น 'POND-1', 'AERATOR-A'
    name        VARCHAR(100) NOT NULL,         -- ชื่อบ่อ/จุดวัด
    type        VARCHAR(50),                   -- 'aeration', 'settling', 'chlorination'
    is_active   BOOLEAN DEFAULT TRUE
);

-- บุคลากร (ใช้ร่วมกับทุก domain)
CREATE TABLE staff (
    id          SERIAL PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,   -- AppSheet: Employee_id
    full_name   VARCHAR(100) NOT NULL,
    nickname    VARCHAR(50),
    position    VARCHAR(50),                   -- Enum: นักวิชาการ/เจ้าหน้าที่/etc
    phone       VARCHAR(20),
    photo_url   VARCHAR(500),
    status      VARCHAR(20) DEFAULT 'active'   -- Enum: active/inactive
);

-- ค่ามิเตอร์ล่าสุด (AppSheet: last meter)
CREATE TABLE meter_readings (
    id              SERIAL PRIMARY KEY,
    reading_date    DATE NOT NULL,
    meter_kwh       NUMERIC(10,2),             -- ค่ามิเตอร์ไฟฟ้า (kWh)
    recorded_by     INTEGER REFERENCES staff(id),
    note            TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- บันทึกคุณภาพน้ำรายวัน (AppSheet: ข้อมูลคุณภาพน้ำ)
-- เก็บเฉพาะค่าที่วัดได้จริง — computed values คำนวณใน API
CREATE TABLE water_quality_records (
    id              SERIAL PRIMARY KEY,
    record_date     DATE NOT NULL,

    -- DO (Dissolved Oxygen) — 3 จุดวัด
    do_inlet        NUMERIC(5,2),              -- DO บ่อรับน้ำ (mg/L)
    do_aeration_1   NUMERIC(5,2),              -- DO บ่อเติมอากาศ 1
    do_aeration_2   NUMERIC(5,2),              -- DO บ่อเติมอากาศ 2

    -- ค่าเคมีน้ำ
    ph              NUMERIC(4,2),              -- pH (0-14)
    tds             NUMERIC(8,2),              -- Total Dissolved Solids (mg/L)
    free_chlorine   NUMERIC(5,2),              -- Free Chlorine (mg/L)

    -- Sludge Volume (SV30)
    sv30_ml         NUMERIC(6,1),              -- ปริมาณตะกอน 30 นาที (mL/L)

    -- การใช้พลังงาน
    meter_start_kwh NUMERIC(10,2),             -- ค่ามิเตอร์ต้นรอบ
    meter_end_kwh   NUMERIC(10,2),             -- ค่ามิเตอร์สิ้นรอบ
    -- energy_kwh ← COMPUTED: meter_end - meter_start (ใน API)

    -- ปริมาณน้ำ
    flow_rate_m3    NUMERIC(10,2),             -- ปริมาณน้ำเข้า (m3/วัน)

    -- Metadata
    recorded_by     INTEGER REFERENCES staff(id),
    pond_id         INTEGER REFERENCES treatment_ponds(id),
    note            TEXT,
    photo_url       VARCHAR(500),              -- รูปบ่อ/หน้างาน
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),

    -- Unique constraint: 1 record ต่อวัน ต่อบ่อ
    UNIQUE (record_date, pond_id)
);

-- Index สำหรับ query ช่วงวันที่
CREATE INDEX idx_wqr_date ON water_quality_records(record_date DESC);
CREATE INDEX idx_wqr_pond ON water_quality_records(pond_id);

-- PDF Report log (AppSheet: Filter_Water)
CREATE TABLE water_quality_reports (
    id              SERIAL PRIMARY KEY,
    report_month    DATE NOT NULL,             -- เดือน/ปี ของ report
    pdf_url         VARCHAR(500),              -- path ของ PDF ที่ generate แล้ว
    generated_by    INTEGER REFERENCES staff(id),
    generated_at    TIMESTAMP DEFAULT NOW(),
    sent_to_telegram BOOLEAN DEFAULT FALSE
);
```

---

## Computed Values (คำนวณใน FastAPI — ไม่เก็บใน DB)

| Computed Field | สูตร | หน่วย |
|---------------|------|-------|
| `do_average` | `(do_inlet + do_aeration_1 + do_aeration_2) / 3` | mg/L |
| `energy_kwh` | `meter_end_kwh - meter_start_kwh` | kWh |
| `sv30_percent` | `sv30_ml / 1000 * 100` | % |
| `energy_per_m3` | `energy_kwh / flow_rate_m3` | kWh/m3 |
| `date_thai_be` | `record_date.year + 543` | พ.ศ. |

```python
# FastAPI Pydantic Response Model
class WaterQualityResponse(BaseModel):
    # ... raw fields ...
    do_average: float | None = None
    energy_kwh: float | None = None
    sv30_percent: float | None = None
    energy_per_m3: float | None = None
    date_thai_be: int

    @model_validator(mode='after')
    def compute_fields(self):
        if all(v is not None for v in [self.do_inlet, self.do_aeration_1, self.do_aeration_2]):
            self.do_average = round((self.do_inlet + self.do_aeration_1 + self.do_aeration_2) / 3, 2)
        if self.meter_end_kwh and self.meter_start_kwh:
            self.energy_kwh = round(self.meter_end_kwh - self.meter_start_kwh, 2)
        if self.sv30_ml:
            self.sv30_percent = round(self.sv30_ml / 10, 1)
        if self.energy_kwh and self.flow_rate_m3:
            self.energy_per_m3 = round(self.energy_kwh / self.flow_rate_m3, 3)
        if self.record_date:
            self.date_thai_be = self.record_date.year + 543
        return self
```

---

## Alert Logic (AppSheet เดิม: เตือนค่าผิดปกติ)

```python
# ใน POST /water-quality/ endpoint
ALERT_THRESHOLDS = {
    "do_average": {"min": 2.0, "message": "⚠️ DO ต่ำกว่า 2.0 mg/L"},
    "free_chlorine": {"min": 0.5, "message": "⚠️ Chlorine ต่ำกว่า 0.5 mg/L"},
    "ph": {"min": 6.5, "max": 8.5, "message": "⚠️ pH ออกนอกช่วง 6.5-8.5"},
}

async def check_and_alert(record: WaterQualityResponse, telegram_bot):
    alerts = []
    for field, threshold in ALERT_THRESHOLDS.items():
        value = getattr(record, field)
        if value is None:
            continue
        if "min" in threshold and value < threshold["min"]:
            alerts.append(threshold["message"] + f" (ค่าที่วัด: {value})")
        if "max" in threshold and value > threshold["max"]:
            alerts.append(threshold["message"] + f" (ค่าที่วัด: {value})")
    if alerts:
        await telegram_bot.send_message("\n".join(alerts))
```

---

## API Endpoints Plan

```
GET    /api/water-quality/              list (filter: date range, pond)
GET    /api/water-quality/{id}          detail
POST   /api/water-quality/              create (trigger alerts)
PUT    /api/water-quality/{id}          update
DELETE /api/water-quality/{id}          delete (admin only)

GET    /api/water-quality/report/monthly?month=YYYY-MM    monthly summary + PDF
POST   /api/water-quality/report/generate                 generate PDF + Telegram

GET    /api/staff/                      list (shared across domains)
GET    /api/treatment-ponds/            list
```

---

## ลำดับการ Implement

1. **สร้าง Docker stack บน Portainer** (PostgreSQL + FastAPI + Adminer)
2. **Run migration SQL** ด้านบนสร้างตาราง
3. **FastAPI models.py** — SQLAlchemy models + Pydantic schemas
4. **CRUD endpoints** — water_quality_records
5. **Computed fields** — ใน Pydantic response model
6. **Alert logic** — Telegram bot integration
7. **PDF generation** — WeasyPrint monthly report
8. **Frontend** — React form + chart (Recharts)

---

## ความสัมพันธ์

- [[synthesis/appsheet-to-webapp-pi5]] — แผน migration ครบทุก domain
- [[sources/appsheet-env-datadict]] — โครงสร้าง AppSheet ต้นทาง
- [[entities/env/activated-sludge-system]] — ระบบบำบัดน้ำเสียโรงพยาบาล
- [[sources/umbrel-pi5-setup]] — infrastructure Pi5


---

### `wiki/synthesis/sunday-estate-frontend-qa-2026-05-18.md`

---
title: Sunday Estate Webapp — Frontend QA Batch (2026-05-18)
type: synthesis
domain: cross-domain
related:
  - ai-tools
  - iot
status: deployed-frontend / pending-backend-migrations
created: 2026-05-18
session: 2026-05-18 dev
sources:
  - User QA report 2026-05-18 (4 bugs from production UI testing)
  - Plan file ~/.claude/plans/webapp-snoopy-lobster.md (in-session, local-only)
  - Webapp commit aase7en/sunday-estate-webapp@1e8147c
  - Webapp repo: /Users/aase7en/Desktop/sunday-estate-webapp/
---

# Sunday Estate Frontend QA Batch — 2026-05-18

> **Purpose**: handoff doc สำหรับ AI agent ตัวถัดไปที่จะมาทำงานต่อกับ webapp นี้
> หลัง Claude Sonnet 4.6 ติด rate limit หรือ session หมด
> ดู synthesis หลัก: [[sunday-estate-webapp]]

> **Status**: Frontend commit `1e8147c` push สำเร็จขึ้น `origin/main` แล้ว
> รอ user redeploy Pi5 + verify + ส่งงาน backend migrations ให้ session ถัดไป

---

## 🎯 Context (ทำไมงานนี้ถึงเกิด)

User test production UI ที่ `http://umbrel.local:8090` หลัง deploy เสร็จ (commit b0d1d09) แล้วแจ้ง **4 ปัญหา** ใน 1 message:

1. OCR เอกสาร > ทะเบียนบ้าน > input box "ผู้อยู่อาศัย" อ่านออกมาเป็น raw JSON
2. ปุ่ม "บันทึกใหม่" บน Dashboard (admin) ไม่ทำงาน
3. ปุ่มผีทั่ว frontend (21 ปุ่ม) — user ต้องการให้ "ทุกปุ่มทำงานได้จริง ไม่ใช่ปุ่มผีว่างๆ"
4. ตาราง ปล่อยกู้/ขายฝาก ไม่มี select-all + bulk Edit/Delete

User decisions (จาก AskUserQuestion):
- Dashboard btn → **Quick-Create menu** (สัญญาใหม่ / ที่ดินใหม่)
- Bulk Edit → **Bulk patch field** (status/type หลาย row พร้อมกัน)
- Ghost btns → **Wire ทุกปุ่ม scope ขยาย** (ไม่ใช่ "Coming soon" toast)

---

## ✅ สิ่งที่ทำเสร็จแล้ว (commit `1e8147c`, 1,210 บรรทัด, 7 ไฟล์)

### T1 — OCR `_flattenOcrRows` fix
- **Root cause**: `prototype/src/misc.jsx:199` มี `&& !Array.isArray(v)` ทำให้ array-of-objects ตกลง `_ocrValueToText` แล้วโดน `JSON.stringify`
- **Fix**: เอา `&& !Array.isArray(v)` ออก → array recurse เป็น rows แยก
- **ผล**: `residents: [{name:"A"},{name:"B"}]` → flatten เป็น `residents.name` (section #1), `residents.name` (section #2)

### T4 — Bulk select + edit + delete (ปล่อยกู้/ขายฝาก)
- **Files**: `loans.jsx` (state + UI + `BulkEditLoansModal`) + `data.jsx` (`bulkUpdateLoans` + `bulkDeleteLoans`)
- **Features**:
  - Header checkbox indeterminate (`-`) เมื่อเลือกบางส่วน
  - Bulk action bar: "N รายการที่เลือก" + ปุ่ม Bulk edit / Delete / Clear
  - Bulk Delete: confirm + Supabase `.in()` filter (RLS admin-only)
  - Bulk Edit modal: pick field (status/type/scope) + new value (dropdown ตามชนิด)
- **Note**: ขายฝากไม่ใช่หน้าแยก — เป็น `type` filter ในตารางเดียวกัน → bulk ทำงานครอบคลุมทั้งสอง

### T2 — Dashboard Quick-Create menu
- **Files**: `dashboard.jsx` (dropdown UI) + `app.jsx` (pendingAction routing) + `loans.jsx`/`lands.jsx` (consume pendingAction)
- **Flow**: กด "บันทึกใหม่" → menu เด้ง → เลือก "สัญญาใหม่"/"ที่ดินใหม่" → setPage + setPendingAction("new") → list page useEffect เห็น pendingAction → setFormOpen(true)
- **Click-outside**: useEffect listener บน `document.mousedown`

### T3 — Ghost button audit (21 buttons wired)

| # | Location | Action |
|---|----------|--------|
| 3a | `dashboard.jsx:145` CashFlow 12M/6M/3M | Slice data array ตาม period state |
| 3b | `loans.jsx:127` ตัวกรอง | Dropdown panel: type checkboxes + due-within radio + counter badge |
| 3c | `loans.jsx:210` Pagination | Client-side 20/page + page selector buttons |
| 3d | `lands.jsx:40` รายงาน | Modal: Export CSV (BOM+UTF-8) / Print (Cmd+P → Save as PDF) |
| 3e | `borrower.jsx:36` ติดต่อเจ้าหน้าที่ | ContactOfficerModal: tel/LINE/mailto links |
| 3f | `borrower.jsx:37,130` แจ้งการชำระ | PaymentNotifyModal: slip upload + amount + date → insert `payment_notifications` |
| 3g | `borrower.jsx:106` เชื่อมต่อ/จัดการ | NotificationPrefsModal stub |
| 3h | `borrower.jsx:187` download icon | `window.open(doc.url, "_blank")` + fallback alert |
| 3i | `misc.jsx:42` Export iCal | Generate `.ics` blob from `LOANS.due` → download |
| 3j | `misc.jsx:43` เพิ่มนัดหมาย | NewEventModal: title + date + time + note → insert `events` |
| 3k | `misc.jsx:58-60` Month/Week/Agenda | View state → conditional render 3 layouts |
| 3l | `misc.jsx:528` ตั้งค่าแจ้งเตือน | AlertSettingsModal: per-type toggles + lead-days + quiet hours → upsert `app_settings.alert_preferences` |
| 3m | `misc.jsx:564` alert action btn | `handleAlertAction(a)` switch (dismiss/snooze/view) |
| 3n | `misc.jsx:730` เชิญผู้ใช้ | InviteUserModal: POST `/api/admin/invite` → fallback `pending_invitations` insert |
| 3o | `misc.jsx:758` edit pencil | EditUserModal: update `profiles.role` + `display_name` |
| 3p | `misc.jsx:783` Add integration | IntegrationManageModal: insert `integrations` |
| 3q | `misc.jsx:798` Manage/Connect | Same modal in edit mode |

---

## 🔴 ที่ค้างอยู่ — Backend migrations + FastAPI routes

### ตารางใหม่ที่ frontend modals คาดว่าจะมี (graceful fallback ตอนนี้ — alert "บันทึกแล้ว" แต่ data ไม่ persist)

#### 1. `payment_notifications` (สำหรับ PaymentNotifyModal)
```sql
create table public.payment_notifications (
  id           uuid primary key default gen_random_uuid(),
  loan_id      text references public.loans(id) on delete cascade,
  user_id      uuid references auth.users(id),
  amount       numeric not null,
  paid_at      date not null,
  slip_url     text,
  note         text,
  status       text not null default 'pending' check (status in ('pending','verified','rejected')),
  created_at   timestamptz not null default now(),
  verified_at  timestamptz,
  verified_by  uuid references auth.users(id)
);
alter table public.payment_notifications enable row level security;
-- RLS: borrower เห็นเฉพาะ row ของตัวเอง; admin/super เห็นทุก row
```
+ Storage bucket `payment-slips` (10MB, private, path `<loan_id>/<timestamp>-<name>`)

#### 2. `events` (สำหรับ NewEventModal + Calendar)
```sql
create table public.events (
  id            uuid primary key default gen_random_uuid(),
  title         text not null,
  scheduled_at  timestamptz not null,
  description   text,
  loan_id       text references public.loans(id) on delete set null,
  land_id       text references public.lands(id) on delete set null,
  created_by    uuid references auth.users(id),
  created_at    timestamptz not null default now()
);
alter table public.events enable row level security;
```

#### 3. `pending_invitations` + FastAPI `/api/admin/invite`
```sql
create table public.pending_invitations (
  id          uuid primary key default gen_random_uuid(),
  email       citext unique not null,
  role        text not null check (role in ('admin','super','user')),
  invited_by  uuid references auth.users(id),
  status      text not null default 'pending' check (status in ('pending','accepted','expired','revoked')),
  token       text unique,
  created_at  timestamptz not null default now(),
  expires_at  timestamptz default (now() + interval '7 days')
);
```
+ FastAPI route `backend/routers/admin.py`:
```python
@router.post("/invite")
async def invite(req: InviteReq, current = Depends(require_admin)):
    # 1) Use SERVICE_ROLE to call supabase.auth.admin.invite_user_by_email
    # 2) Insert pending_invitations row with token returned
    # 3) Return {ok: true, expires_at}
```

#### 4. `integrations` (สำหรับ IntegrationManageModal)
```sql
create table public.integrations (
  id          uuid primary key default gen_random_uuid(),
  name        text unique not null,           -- e.g. "LINE Notify", "Telegram Bot"
  kind        text not null,                  -- 'notify' | 'storage' | 'ai'
  config      jsonb not null default '{}',    -- token, webhook URL, etc.
  enabled     boolean not null default true,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
alter table public.integrations enable row level security;
-- RLS: admin-only
```

#### 5. `alert_preferences` (ใน app_settings)
ไม่ต้องสร้างตารางใหม่ — frontend upsert ลง `app_settings` ด้วย key `alert_preferences` (มี table อยู่แล้วใน migration 0009)

---

## 🧪 Verification (User ต้องทำ)

1. **Pi5 redeploy**: Portainer → stack `sunday-estate` → **Re-pull image and redeploy** (~2 min)
2. **Hard refresh**: Cmd+Shift+R ที่ `http://umbrel.local:8090`
3. **Test matrix**:

| Test | Expected |
|------|----------|
| Upload ทะเบียนบ้าน (มีหลายผู้อาศัย) → Review page | Field "residents.*" แสดงเป็น input ปกติ ไม่ใช่ JSON block |
| Dashboard admin → "บันทึกใหม่" | Menu เด้ง: "สัญญาใหม่" / "ที่ดินใหม่" → navigate + form เปิด |
| ปล่อยกู้ → ติ๊ก 3 row | Bar "3 รายการที่เลือก" + ปุ่ม Bulk edit/Delete |
| ปล่อยกู้ → header checkbox | Indeterminate (`-`) เมื่อบางส่วน, ✓ ครบเมื่อทั้งหมด |
| Bulk Delete | Confirm → row หาย หลัง reload |
| Bulk Edit → status=ไถ่ถอนแล้ว | Confirm → row ที่เลือกเปลี่ยนสถานะพร้อมกัน |
| Loans Filter dropdown | เลือก type "ขายฝาก" + due "ภายใน 7 วัน" → ตารางกรอง + badge "2" |
| Loans pagination | >20 rows → page 2 + ← → ทำงาน |
| Dashboard CashFlow chips | 6M → กราฟยุบเหลือ 6 bars |
| Calendar Export iCal | Download `.ics` → import Google Calendar เห็น events |
| Calendar Week toggle | Layout เปลี่ยนเป็น 7-day strip |
| Lands รายงาน → CSV | Download `lands-YYYY-MM-DD.csv` |
| Borrower contact officer | Modal มี tel/LINE/email links คลิกได้ |
| Settings เชิญผู้ใช้ | Modal: email + role → submit → alert (จะ persist เมื่อ backend ทำ) |

---

## 📝 Instructions for Next AI Agent

### ถ้าคุณมารับงานต่อจาก session นี้:

1. **Read first**:
   - ไฟล์นี้ (เห็นภาพรวมงานที่ทำไป)
   - [[sunday-estate-webapp]] (synthesis หลัก)
   - `git log --oneline -10` ใน `/Users/aase7en/Desktop/sunday-estate-webapp/` (เห็น commit history)

2. **Confirm with user first**:
   - User redeploy + verify หรือยัง? ถ้ายัง — ขอ feedback ก่อนทำ migration
   - มี bug ใหม่ที่เจอจาก QA หรือไม่?

3. **Next-priority work** (ตามลำดับ):
   1. รอ user feedback จาก verify → ถ้ามี bug ใหม่ใน 14 ปุ่มที่ wire → fix ก่อน
   2. **Migration 0014** (`payment_notifications` + storage bucket `payment-slips`)
   3. **Migration 0015** (`events`)
   4. **Migration 0016** (`pending_invitations` + `integrations`)
   5. FastAPI route `backend/routers/admin.py` (`/api/admin/invite` ใช้ service_role)
   6. (Optional) Cloudflare Tunnel public access — ยังค้างจาก session เก่า

4. **กฎเหล็ก**:
   - **ห้าม push ตรงๆ ไม่ขอผู้ใช้** — push main เท่านั้น ไม่มี branch/PR
   - **ห้ามแตะ** Umbrel/Bitcoin/supabasepi5 stack
   - **Pi5 deploy** ใช้ Portainer (`http://umbrel.local:9000`) stack `sunday-estate` → Re-pull + Redeploy
   - Frontend prototype ใช้ Babel-in-browser — แก้ .jsx แล้ว push commit ได้เลย (image rebuild ใน Docker)
   - Backend ARM64 wheels (`cryptography`, `httpx`) compile ช้า — ใช้ pre-built image จาก ghcr.io/aase7en/sunday-estate-api

5. **Files mental model**:
   ```
   prototype/src/
   ├── app.jsx          ← Top-level routing, App state (page, scope, lang)
   ├── shell.jsx        ← Sidebar + Topbar + nav structure
   ├── dashboard.jsx    ← Drag-drop widgets + Quick-Create menu (T2)
   ├── loans.jsx        ← Loans table + bulk select (T4) + filter/pagination (T3b,c)
   ├── lands.jsx        ← Lands grid/list + Report modal (T3d)
   ├── borrower.jsx     ← Borrower portal (T3e-h modals)
   ├── misc.jsx         ← Calendar + OCR + Alerts + Settings (T1, T3i-q)
   ├── data.jsx         ← window.SE_DATA exports + Supabase calls
   ├── sbclient.jsx     ← window.sb client init
   ├── ui.jsx           ← Reusable: Icon, Tag, Donut, BarsChart
   ├── ai.jsx           ← AIPanel + AIInlinePage
   └── login.jsx        ← LoginPage
   ```

6. **กลไก pendingAction** (T2 → list pages):
   - App.jsx มี `pendingAction` state + `triggerQuickCreate(entity)` ฟังก์ชัน
   - Dashboard accept `onQuickCreate(entity)` prop → call function
   - LoansList/LandsList accept `pendingAction` + `onPendingActionConsumed` props
   - List pages useEffect: ถ้า `pendingAction === "new"` && canWrite → `setFormOpen(true)` + consume
   - Pattern นี้ขยาย "edit:<id>", "scroll-to:<id>" ได้ในอนาคต

---

## 🔗 Related artifacts

- **Plan file (local-only)**: `~/.claude/plans/webapp-snoopy-lobster.md` (เครื่อง Claude นี้เท่านั้น)
- **Webapp commit**: `aase7en/sunday-estate-webapp@1e8147c` (GitHub: https://github.com/aase7en/sunday-estate-webapp)
- **Pi5 stack**: Portainer → `sunday-estate` (nginx :8090 + fastapi :8000 internal)
- **Last working production URL**: `http://umbrel.local:8090`
- **Previous session log**: [[../../log#2026-05-17 sunday-estate-production-verified]]
- **Main synthesis**: [[sunday-estate-webapp]]


---

### `wiki/synthesis/air-quality-monitoring.md`

---
type: synthesis
tags: [air-quality, pms5003, lora, esp32, grafana, aqi, pm25]
sources: [air-quality-iot-lora-network, air-quality-sensors-dronebot, iot-lora-gateway-architecture]
created: 2026-04-19
updated: 2026-04-19
---

# ระบบ Air Quality Monitoring (PMS5003 + LoRa + Grafana)

> **คำถามที่ตอบ**: จะออกแบบระบบวัด PM2.5/PM10 แบบ distributed (หลายจุด) อย่างไร?

## สรุป

ใช้ [[entities/iot/pms5003]] วัด PM2.5/PM10 ต่อกับ [[entities/iot/esp32]] ส่งผ่าน LoRa (DX-LR02) → Gateway → MQTT → [[entities/iot/influxdb]] → [[entities/iot/grafana]] แสดงบน map หรือ dashboard เปรียบเทียบหลายจุด

## Data Flow

```
[PMS5003 UART 5V]
      ↓
[ESP32 Sensor Node] ← battery (18650 shield)
      ↓ LoRa (DX-LR02 P2P)
[ESP32-S3 Gateway]
      ↓ WiFi MQTT
[Mosquitto Broker]
      ↓
[Node-RED] → [InfluxDB] → [Grafana Dashboard + Map]
      ↓ alert (PM2.5 > 37.5 µg/m³)
[Telegram Bot]
```

## Thai AQI Standard

| ระดับ | PM2.5 (µg/m³) | สี | ความหมาย |
|-------|--------------|-----|---------|
| ดีมาก | 0-25 | ฟ้า | ปลอดภัย |
| ดี | 25.1-37.5 | เขียว | ปลอดภัย |
| ปานกลาง | 37.6-75 | เหลือง | ผู้ป่วยระวัง |
| ไม่ดี | 75.1-150 | ส้ม | ทุกคนระวัง |
| แย่มาก | >150 | แดง | อันตราย |

**Alert threshold แนะนำ**: PM2.5 > 37.5 µg/m³ → Telegram

## Hardware Required

| Component | Status | หมายเหตุ |
|-----------|--------|---------|
| [[entities/iot/pms5003]] | ❌ ยังไม่มี | UART 5V, ~100mA, ต้องมี level shifter |
| [[entities/iot/esp32]] | ✅ มีแล้ว | UART1 (GPIO16/17) ต่อ PMS5003 |
| [[entities/iot/dx-lr02-lora]] | ✅×2 มีแล้ว | LoRa P2P sensor → gateway |
| [[entities/iot/esp32-s3]] | ✅ มีแล้ว | Gateway (WiFi) |
| [[entities/iot/18650-battery-shield]] | ✅ มีแล้ว | Sensor node power |

## ⚠️ ข้อควรระวัง

1. PMS5003 ใช้ไฟ 5V แต่ data line 3.3V → ต้องมี **level shifter** (หรือ voltage divider)
2. warm-up time ~30 วินาทีก่อนอ่านค่าได้เสถียร
3. ทำความสะอาด sensor ทุก 3-6 เดือน (ฝุ่นอุด laser)
4. Multi-sensor LoRa network → ต้องกำหนด device ID ในแต่ละ node

## MQTT JSON Format

```json
{
  "node_id": "sensor_01",
  "pm25": 35.2,
  "pm10": 48.7,
  "pm1": 22.1,
  "rssi": -72,
  "battery": 3.85
}
```

**Topic**: `air/sensor/<node_id>/data`

## ความสัมพันธ์

- ใช้ร่วมกับ: [[concepts/iot/air-quality-index]], [[concepts/iot/lora-p2p]]
- เกี่ยวข้องกับ: [[entities/iot/pms5003]], [[entities/iot/dx-lr02-lora]]
- TinyML ต่อยอด: [[concepts/iot/tinyml]] (anomaly detection บน sensor data)
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/air-quality-iot-lora-network]] — ESP32+PMS5003+LoRa+Grafana reference
- [[sources/air-quality-sensors-dronebot]] — sensor comparison (PMS5003, SGP30, BME280)


---

### `wiki/synthesis/pi4-lora-gateway-server.md`

---
type: synthesis
tags: [raspberry-pi, lora, gateway, server, esp32, mqtt, multi-node, architecture]
sources: [raspberry-pi-iot-guide, iot-lora-gateway-architecture, dx-lr02-datasheet]
created: 2026-04-19
updated: 2026-04-19
---

# Raspberry Pi 4 เป็น LoRa Gateway + Server เครื่องเดียว

> **คำถามที่ตอบ**: ใช้ Pi 4 4GB รับสัญญาณ LoRa จากหลาย IoT node พร้อมรัน dashboard server ได้ไหม?

## สรุป

**ได้ — และ Pi 4 4GB overkill สำหรับงานนี้** ทำหน้าที่ได้ทั้งรับ LoRa, รัน MQTT broker, ประมวลผล, เก็บข้อมูล และแสดง dashboard พร้อมกัน RAM ใช้ไปแค่ ~600MB จาก 4GB

---

## สถาปัตยกรรมแนะนำ (Option B — Pi เป็นศูนย์กลาง)

```
[ESP32 Node A] → DX-LR02 TX ~~LoRa~~
[ESP32 Node B] → DX-LR02 TX ~~LoRa~~  ──→  [DX-LR02 RX]
[ESP32 Node C] → DX-LR02 TX ~~LoRa~~         │ UART
                                         [DX-SMART TTL]
                                               │ USB
                                         [Raspberry Pi 4B 4GB]
                                          ├── Python/Node-RED  ← รับ UART → parse JSON
                                          ├── Mosquitto        ← MQTT broker (local)
                                          ├── Node-RED         ← flow + rules
                                          ├── InfluxDB         ← time-series storage
                                          └── Grafana :3000    ← dashboard
                                               │ alert
                                          [Telegram Bot]
```

---

## เปรียบเทียบ Option A vs B

| หัวข้อ | **Option A** (ESP32-S3 เป็น gateway) | **Option B** (Pi เป็น gateway) ✅ |
|--------|--------------------------------------|----------------------------------|
| Hardware เพิ่ม | ESP32-S3 (มีอยู่แล้ว) | DX-LR02 + DX-SMART TTL (มีอยู่แล้ว) |
| LoRa receiver | ESP32-S3 + DX-LR02 | Pi + DX-LR02 via USB |
| WiFi hop | ESP32-S3 → Pi (WiFi MQTT) | ไม่มี — ต่อตรง USB |
| Latency | เพิ่ม WiFi hop ~50ms | ต่ำกว่า (USB serial direct) |
| Reliability | ESP32-S3 อาจ crash/reset | Pi Linux stable กว่า |
| Code ที่ต้องเขียน | ESP32-S3 firmware | Python script บน Pi |
| ค่าไฟ | Pi + ESP32-S3 (เพิ่ม ~0.5W) | Pi อย่างเดียว |
| **แนะนำ** | ถ้าต้องการ LoRa อยู่ห่าง Pi | **ถ้า Pi อยู่ใกล้ DX-LR02** ✅ |

---

## Multi-Node Time-Slotting (หลาย ESP32 → Pi เดียว)

DX-LR02 รับได้ทีละ 1 packet — ต้องให้ node ส่งสลับกัน:

```
Timeline:
Node A ──[send 500ms]── sleep ──────────────────── sleep ────────
Node B ────── sleep ──────────[send 500ms]── sleep ─────────────
Node C ─────────── sleep ──────────────────────────[send 500ms]─

Pi DX-LR02 ──[recv A]────────[recv B]────────────[recv C]───────
```

**Interval แนะนำ**: ส่งทุก 30-60 วินาที, offset node ละ `node_id × 10 วินาที`

```cpp
// ESP32 Node firmware
int node_id = 1;  // Node A=0, B=1, C=2
delay(node_id * 10000);  // offset ก่อน loop แรก
// loop: อ่าน sensor → ส่ง LoRa → sleep 30s
```

---

## Python Script บน Pi (รับ LoRa UART → MQTT)

```python
import serial
import paho.mqtt.client as mqtt
import json

ser = serial.Serial('/dev/ttyUSB0', 9600)
client = mqtt.Client()
client.connect("localhost", 1883)

while True:
    line = ser.readline().decode().strip()
    try:
        data = json.loads(line)
        node = data.get("node", "unknown")
        topic = f"home/{node}/data"
        client.publish(topic, json.dumps(data))
    except json.JSONDecodeError:
        pass  # ignore AT command responses
```

**Device path**: `/dev/ttyUSB0` (DX-SMART TTL) — ตรวจด้วย `ls /dev/tty*`

---

## JSON Format จาก ESP32 Node

```json
{"node":"A","temp":28.5,"humidity":72,"rssi":-68,"batt":3.82}
```

**MQTT Topics ที่ได้**:
```
home/A/data  →  {"node":"A","temp":28.5,...}
home/B/data  →  {"node":"B","temp":31.2,...}
home/C/data  →  {"node":"C","temp":26.8,...}
```

---

## Services บน Pi 4 — Resource Usage

| Service | RAM | CPU idle | Port |
|---------|-----|---------|------|
| Mosquitto | ~10MB | <1% | 1883 |
| Python UART reader | ~20MB | <1% | — |
| Node-RED | ~80MB | <2% | 1880 |
| InfluxDB 2.x | ~200MB | 1-3% | 8086 |
| Grafana | ~100MB | <2% | 3000 |
| OS (RPi OS Lite) | ~200MB | — | — |
| **รวม** | **~610MB / 4GB** | **<10%** | |

**Pi 4 4GB รับงานนี้ได้ง่ายมาก** — เหลือ RAM 3.4GB สำหรับ expand ในอนาคต

---

## ลำดับ Setup แนะนำ

1. **ติดตั้ง OS** — Raspberry Pi OS Lite 64-bit (headless)
2. **ต่อ DX-LR02 + DX-SMART TTL** → USB → Pi, ทดสอบ `screen /dev/ttyUSB0 9600`
3. **ติดตั้ง Mosquitto** → ทดสอบ publish/subscribe local
4. **รัน Python UART reader** → ยืนยัน MQTT message ถูกต้อง
5. **ติดตั้ง InfluxDB 2.x** (ARM64 package)
6. **ติดตั้ง Node-RED** → สร้าง flow MQTT → InfluxDB
7. **ติดตั้ง Grafana** → สร้าง dashboard จาก InfluxDB
8. **เพิ่ม Telegram Bot** alert (Python หรือ Node-RED node)

---

## ⚠️ ข้อควรระวัง

1. **DX-LR02 ต้องตั้ง channel เดียวกันทุกตัว** — ใช้ AT+CH= ให้ตรงกัน
2. **InfluxDB 2.x บน ARM64** — ใช้ package จาก influxdata.com ไม่ใช่ apt default
3. **ttyUSB0 อาจเปลี่ยนเป็น ttyUSB1** ถ้าเสียบ USB อื่นก่อน → ใช้ udev rule ผูก port
4. **Packet collision** — ถ้า node ส่งพร้อมกันพอดี packet หาย → เพิ่ม jitter `random(0,500)ms`
5. **Pi ไม่มี RTC** → sync time ด้วย NTP ก่อนเสมอ (สำคัญสำหรับ InfluxDB timestamp)

---

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/raspberry-pi]], [[entities/iot/dx-lr02-lora]], [[entities/iot/dx-smart-ttl]]
- Services บน Pi: [[entities/iot/mosquitto]], [[entities/iot/node-red]], [[entities/iot/influxdb]], [[entities/iot/grafana]]
- Concept: [[concepts/iot/lora-p2p]], [[concepts/iot/data-logger]]
- อ้างอิง stack: [[synthesis/iot-lora-architecture]]

## แหล่งข้อมูล

- [[sources/raspberry-pi-iot-guide]] — RPi roles in IoT
- [[sources/iot-lora-gateway-architecture]] — original architecture decision
- [[sources/dx-lr02-datasheet]] — DX-LR02 AT commands, channel config


---

### `wiki/synthesis/wiki-to-video-pipeline.md`

---
type: synthesis
tags: [wiki, hyperframes, video-rendering, notebooklm, ai-tools, knowledge-management, media-pipeline]
sources: [hyperframes-official-docs]
created: 2026-05-17
updated: 2026-05-17
---

# Wiki-to-Video Pipeline

## คำถามที่ตอบ

จะใช้ [[entities/ai-tools/hyperframes]] ร่วมกับ InW-Wiki และ HyperFrames Catalog เพื่อเปลี่ยนหน้า wiki/synthesis ให้เป็นวิดีโอสั้นได้อย่างไร?

## สรุป

ใช้ wiki เป็น **knowledge source**, NotebookLM หรือ agent เป็น **script/storyboard layer**, และ HyperFrames เป็น **render layer**. ผลลัพธ์คือวิดีโอสั้นที่อธิบาย entity, concept, หรือ architecture จาก wiki โดยยังเก็บ source traceability ผ่าน wikilinks และ source pages.

เหมาะที่สุดกับงานที่ต้องสื่อสารซ้ำ เช่น IoT architecture, pharmacy order checker, environmental health report, AI tool explainer, หรือ onboarding ให้ตัวเอง/ทีม.

## Pipeline แนะนำ

```text
wiki page / synthesis
  -> extract key claims + sources
  -> write 30-90s script
  -> storyboard scenes
  -> choose HyperFrames catalog blocks
  -> render preview
  -> lint/inspect
  -> export video
  -> store artifact outside tracked wiki or under exports/ with care
```

## Mapping กับงานใน Wiki นี้

| Wiki content | HyperFrames block/pattern | วิดีโอที่ได้ |
|---|---|---|
| [[synthesis/iot-lora-architecture]] | `flowchart`, animated arrows, device cards | LoRa node -> gateway -> server walkthrough |
| [[synthesis/pharmacy-order-checker]] | process timeline, lower third, OCR before/after | Demo ขั้นตอนรับรายการยา -> validate -> export |
| [[synthesis/appsheet-to-webapp-pi5]] | dashboard mock + data chart | อธิบาย migration จาก AppSheet เป็น web app |
| [[synthesis/env-webapp-schema-wastewater]] | schema/table animation + charts | Data model briefing สำหรับระบบน้ำเสีย |
| [[concepts/ai-tools/openrouter-api]] | code card + routing diagram | Explainer เรื่อง model routing/cost-first |
| [[entities/ai-tools/hyperframes]] | catalog showcase + CLI terminal scene | Tool explainer ของ HyperFrames เอง |

## Catalog Strategy

| Catalog group | ใช้เมื่อ | ตัวอย่างใน wiki |
|---|---|---|
| Data | ต้องเล่า trend, KPI, quantity | น้ำเสีย, PM2.5, ขยะ, ยอดสั่งยา |
| Blocks / Flowchart | ต้องอธิบายระบบหรือ workflow | IoT pipeline, pharmacy validation |
| Social Overlays | ทำ short-form clip หรือ update สั้น | release note, tool tip, announcement |
| Shader/CSS Transitions | ทำ chapter break | เปลี่ยนจาก problem -> solution |
| Showcases / HTML-in-Canvas | โชว์ web app หรือ device UI | Supabase/PocketBase demo, dashboard mock |

## Workflow แบบประหยัด Token

1. ใช้ `wiki/context/wiki-overview.md` หา page ที่เกี่ยวข้องก่อน
2. ถ้าต้อง synthesize หลายหน้า ให้ export/ใช้ NotebookLM summary ก่อน
3. ให้ agent เขียน script ภาษาไทยสั้น ๆ พร้อม scene list
4. ให้ HyperFrames ทำ composition จาก scene list ไม่ใช่ให้โหลด wiki ทั้งก้อน
5. Render draft ด้วย low worker count ก่อน แล้วค่อยเพิ่ม quality/format

## Folder Policy

วิดีโอและ frame output มักใหญ่กว่า markdown มาก จึงไม่ควร commit ทุกไฟล์เข้า repo โดยตรง.

แนวทางที่ปลอดภัย:

- เก็บ source composition เป็น code/text ในโปรเจกต์ย่อย เช่น `experiments/hyperframes/<slug>/` ถ้าต้องการ version control
- เก็บ output video ไว้ใน `exports/hyperframes/` หรือ external storage แล้ว commit เฉพาะ manifest/link
- ถ้าเป็นไฟล์ใหญ่หรือ binary ให้ทำตาม policy `raw/` และ `wiki/context/local-sources.md` แทนการยัดไฟล์เข้า git

## Dependency Status

ตรวจเครื่อง local วันที่ 2026-05-17:

| Dependency | สถานะ | ผลต่อ pipeline |
|---|---|---|
| Node.js | `v24.15.0` | พร้อมใช้ HyperFrames CLI |
| npm | `11.12.1` | พร้อมเรียก `npx hyperframes` |
| FFmpeg | ยังไม่พบ | ยัง render video local ไม่ได้จนกว่าจะติดตั้ง |

## Next Experiment

ทดลองเล็กที่สุดที่คุ้ม:

```bash
brew install ffmpeg
npx hyperframes init wiki-hyperframes-demo --example blank --tailwind
cd wiki-hyperframes-demo
npx hyperframes add flowchart
npx hyperframes preview
npx hyperframes render --output wiki-hyperframes-demo.mp4
```

หัวข้อทดลองแรกที่เหมาะ: [[synthesis/iot-lora-architecture]] เพราะมี flow ของ sensor node -> gateway -> server ที่แปลงเป็น animated flowchart ได้ชัด.

## แหล่งข้อมูลที่ใช้

- [[sources/hyperframes-official-docs]]
- [[entities/ai-tools/hyperframes]]


---

### `wiki/synthesis/CLAUDE.md`

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

---
