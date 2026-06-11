# Wiki Master Index

> **หน้านี้ Claude ดูแลอัตโนมัติ** — อย่าแก้ไขด้วยมือ  
> อัปเดตล่าสุด: 2026-05-11 | จำนวนหน้าทั้งหมด: ~100+
>
> ⚡ **Fast Load**: ใช้ [[wiki/context/wiki-overview]] แทนหน้านี้ เพื่อประหยัด API tokens

## Domain Indexes

| Domain | Index | สถานะ |
|--------|-------|-------|
| Internet of Things (IoT) | [[index-iot]] | ✅ 34 entities, 11 concepts |
| Environmental Health (อนามัยสิ่งแวดล้อม) | [[index-env]] | ✅ 2 entities, 4 concepts |
| AI Tools | [[index-ai-tools]] | ✅ 2 entities, 5 concepts |
| Pharmacy (ร้านขายยา ภูฟาร์มาซี) | [[index-pharmacy]] | ✅ 3,760 SKU จาก SP Drugstore 2020 |
| IT Support | [[index-it]] | 🆕 1 concept |

---

## สถิติ Wiki

| ประเภท | จำนวน |
|--------|-------|
| Entities (IoT) | 34 |
| Entities (Env) | 2 |
| Entities (AI Tools) | 2 |
| Entities (Pharmacy) | 2 |
| Concepts (IoT) | 11 |
| Concepts (Env) | 4 |
| Concepts (AI Tools) | 5 |
| Concepts (Pharmacy) | 6 |
| Concepts (IT Support) | 1 |
| Sources | ~40 |
| Synthesis | ~15 |
| Context files | 4 |

---

## Entities

### IoT — Microcontrollers & SBCs
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/iot/esp32]] | ESP32 DevKit V1 — Sensor Node ในโปรเจ็ค | esp32, wifi |
| [[wiki/entities/iot/esp32-s3]] | ESP32-S3-N16R8 — LoRa Gateway ในโปรเจ็ค, 16MB/8MB PSRAM | esp32-s3, usb-native |
| [[wiki/entities/iot/arduino-uno-r3]] | Arduino Uno R3 CH340 — AVR, เหมาะ beginner | arduino |
| [[wiki/entities/iot/raspberry-pi]] | Raspberry Pi — Linux SBC, production host สำหรับ MQTT+Grafana stack | raspberry-pi, server |

### IoT — Communication Modules
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/iot/mqtt-protocol]] | MQTT — pub/sub IoT standard, OASIS, broker roles, QoS levels | mqtt, protocol |
| [[wiki/entities/iot/dx-lr02-lora]] | DX-LR02 900MHz — LoRa UART module ✅ ×2 ใน Lab | lora, uart |
| [[wiki/entities/iot/rfm95-sx1276]] | RFM95W/SX1276 — LoRa transceiver chip (SPI), chip มาตรฐาน | lora, spi |
| [[wiki/entities/iot/nb-iot]] | NB-IoT — cellular LPWAN, ทั่วประเทศแต่มีค่าบริการ | nb-iot, cellular |
| [[wiki/entities/iot/dx-smart-ttl]] | DX-SMART DX-PJ15-V1.1 — USB-C to TTL, flash/debug serial ✅ ×2 | usb, ttl |

### IoT — Platforms & Brokers
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/iot/mosquitto]] | Eclipse Mosquitto — MQTT broker, FOSS, edge/home lab | mqtt, broker |
| [[wiki/entities/iot/emqx]] | EMQX — enterprise MQTT broker, 100M connections, Rule Engine | mqtt, broker |
| [[wiki/entities/iot/home-assistant]] | Home Assistant — home automation, MQTT-first | home-automation |
| [[wiki/entities/iot/telegram-bot]] | Telegram Bot API — alert อุณหภูมิ ✅ แนะนำ | telegram, notification |
| [[wiki/entities/iot/line-notify]] | Line Notify — ⚠️ **DEPRECATED มี.ค. 2025** ใช้ Telegram แทน | line |
| [[wiki/entities/iot/grafana]] | Grafana — dashboard กราฟ time-series, รองรับ InfluxDB+MySQL | grafana, visualization |
| [[wiki/entities/iot/influxdb]] | InfluxDB 2.x — time-series DB สำหรับ sensor data | influxdb, database |
| [[wiki/entities/iot/node-red]] | Node-RED — low-code flow platform, MQTT+Dashboard+DB | node-red, low-code |
| [[wiki/entities/iot/mysql]] | MySQL — relational DB, Data Logger ทางเลือกแทน InfluxDB | mysql, database |
| [[wiki/entities/iot/the-things-network]] | The Things Network (TTN) — cloud LoRaWAN Network Server ฟรี | lorawan, cloud |
| [[wiki/entities/iot/chirpstack]] | ChirpStack — self-hosted open-source LoRaWAN Network Server | lorawan, self-hosted |

### IoT — Dev Tools
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/iot/arduino-ide]] | Arduino IDE 2.x — IDE หลักสำหรับ flash ESP32, Board Manager URL | dev-tool, arduino |
| [[wiki/entities/iot/platformio]] | PlatformIO — professional IDE plugin สำหรับ VS Code | dev-tool, professional |
| [[wiki/entities/iot/esp-idf]] | ESP-IDF — native Espressif framework (advanced, production) | dev-tool, c |

### IoT — Sensors
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/iot/dht11]] | DHT11 — temp/humidity ±2°C ✅ | sensor, temperature |
| [[wiki/entities/iot/hc-sr501]] | HC-SR501 PIR Motion — range 7m ✅ | sensor, pir |
| [[wiki/entities/iot/pzem-004t]] | PZEM-004T — AC power meter (V/A/W/Wh/PF), Modbus RTU | sensor, power-meter |
| [[wiki/entities/iot/load-cell]] | Load Cell (Strain Gauge) — แปลงน้ำหนักเป็นไฟฟ้า, ใช้กับ HX711 | sensor, weight |
| [[wiki/entities/iot/hx711]] | HX711 — 24-bit ADC amplifier สำหรับ load cell, 2-wire interface | adc, weight |
| [[wiki/entities/iot/ds18b20]] | DS18B20 — One-Wire temp sensor, ±0.5°C, waterproof, cold chain | sensor, temperature |
| [[wiki/entities/iot/pms5003]] | PMS5003 — Laser PM2.5/PM10 sensor, UART 5V, ~100mA | sensor, air-quality |
| [[wiki/entities/iot/hc-sr04]] | HC-SR04 — Ultrasonic distance 2–400cm, tank level monitoring ✅ | sensor, ultrasonic |

### IoT — Power
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/iot/18650-battery-shield]] | 18650 Battery Shield V3 — 5V/4A + 3.3V/1A ✅ | power, battery |
| [[wiki/entities/iot/vapcell-m35-18650]] | Vapcell INR18650 M35 — 3500mAh 3.7V, 10A continuous ✅ ×2 | power, battery |

### Environmental Health — Entities
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/env/activated-sludge-system]] | ระบบตะกอนกระตุ้น (SBR) — กระบวนการบำบัดน้ำเสียโรงพยาบาล | wastewater, env |
| [[wiki/entities/env/rabies-pep-surveillance]] | ระบบเฝ้าระวัง Rabies PEP — AppSheet + DDC/WHO protocol | rabies, public-health |

### AI Tools — Entities
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/ai-tools/hermes-agent]] | Hermes Agent CLI — AI agent รองรับ Telegram/Discord/Slack + skills + cron | agent, automation |
| [[wiki/entities/ai-tools/telegram-ai-router]] | Personal Telegram bot + auto router: Ollama → Gemini → Claude | telegram, llm-routing |

### Pharmacy — Entities
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/entities/pharmacy/drug-database]] | Drug Database — sp_drugs_full_3760.json (primary) + sp_drugs_medications_2895.json | pharmacy, database |
| [[wiki/entities/pharmacy/drug-matching-system]] | Drug Matching System — fuzzy match + aliases + validation | pharmacy, ai |

---

## Concepts

### IoT — Protocols
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/concepts/iot/publish-subscribe]] | Pub/Sub pattern — decoupled messaging via broker | architecture |
| [[wiki/concepts/iot/mqtt-qos]] | MQTT QoS 0/1/2 — reliability tradeoffs | mqtt |
| [[wiki/concepts/iot/lora]] | LoRa radio — km range, low power, CSS modulation | lora, lpwan |
| [[wiki/concepts/iot/lorawan]] | LoRaWAN — network protocol บน LoRa, 3-layer architecture, AES-128 | lorawan, network |
| [[wiki/concepts/iot/lora-p2p]] | LoRa P2P — direct LoRa communication (DX-LR02 UART), no network server | lora, p2p |
| [[wiki/concepts/iot/modbus]] | Modbus RTU/TCP — serial protocol มาตรฐานอุตสาหกรรม, PLC/sensor | industrial, protocol |

### IoT — Data & Architecture
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/concepts/iot/data-logger]] | Data Logger pattern — บันทึก sensor ลง DB สำหรับ historical analysis | storage, iot |
| [[wiki/concepts/iot/dashboard-design]] | Dashboard Design — widget selection, IoT UI principles, Grafana panel guide | dashboard, ux |
| [[wiki/concepts/iot/tinyml]] | TinyML — Edge AI บน MCU, TensorFlow Lite, Edge Impulse, anomaly detection | tinyml, edge-ai |
| [[wiki/concepts/iot/cold-chain-monitoring]] | Cold Chain Monitoring — vaccine +2°C~+8°C, DS18B20, alert, AI anomaly | cold-chain, vaccine |
| [[wiki/concepts/iot/air-quality-index]] | Air Quality Index — PM2.5 Thai standard, sensor comparison, LoRa network | aqi, air-quality |

### Environmental Health — Concepts
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/concepts/env/infectious-waste-management]] | มูลฝอยติดเชื้อ: นิยาม ประเภท ภาชนะสี กฎหมาย กระบวนการ | waste, env-law |
| [[wiki/concepts/env/hospital-wastewater-treatment]] | ระบบบำบัดน้ำเสียโรงพยาบาล: BOD, SBR, กฎหมาย | wastewater, env |
| [[wiki/concepts/env/rabies-pep-protocol]] | Rabies PEP: wound care, IM/ID regimen, RIG, DDC vs WHO | rabies, public-health |
| [[wiki/concepts/env/water-quality-parameters]] | พารามิเตอร์คุณภาพน้ำ: BOD, COD, SS, pH, DO | water-quality, env |

### AI Tools — Concepts
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/concepts/ai-tools/local-llm-routing]] | Auto model switching: route query ง่ายไป local, ยากไป cloud | llm, routing |
| [[wiki/concepts/ai-tools/agent-framework-tradeoffs]] | Lean vs Autonomous vs Orchestrator agent frameworks | agent, architecture |
| [[wiki/concepts/ai-tools/openrouter-api]] | OpenRouter unified gateway, free-model routing, OpenAI-compatible | openrouter, api |
| [[wiki/concepts/ai-tools/openrouter-claude-code]] | OpenRouter + Claude Code: cost optimization, free models | openrouter, claude-code |
| [[wiki/concepts/ai-tools/session-setup]] | Session setup workflow: git pull, Drive sync, context auto-load | workflow, setup |

### Pharmacy — Concepts
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/concepts/pharmacy/drug-aliases]] | Drug Aliases — แมปชื่อยาสะกดผิด → ชื่อมาตรฐาน | pharmacy, nlp |
| [[wiki/concepts/pharmacy/ordering-workflow]] | Workflow สั่งซื้อยา: LINE input → fuzzy match → validate → export | pharmacy, workflow |
| [[wiki/concepts/pharmacy/drug-classification]] | หมวดหมู่ยา ATC Code และกลุ่มยาที่พบบ่อย | pharmacy, atc |
| [[wiki/concepts/pharmacy/fuzzy-match]] | Fuzzy match ชื่อยาสะกดผิด: Levenshtein, confidence score | pharmacy, nlp |
| [[wiki/concepts/pharmacy/drug-validation]] | Drug Validation — ตรวจสอบ category, unit, supplier | pharmacy |
| [[wiki/concepts/pharmacy/ui-design-pharmacy]] | UI Design Pharmacy App (v3) — interactive form, badges, export | pharmacy, ui |

### IT Support — Concepts
| หน้า | สรุป | Tags |
|------|------|------|
| [[wiki/concepts/it-support/brother-hl-l3270cdw-wsd-error]] | Brother HL-L3270CDW ปริ้นไม่ได้: WSD Port เสีย — แก้ด้วย TCP/IP port | printer, windows |

---

## Sources

> ดูรายละเอียดเต็มตาม domain index — [[index-iot]], [[index-env]], [[index-ai-tools]], [[index-pharmacy]]

| หน้า | ชื่อ | Domain | วันที่ |
|------|------|--------|--------|
| [[wiki/sources/mqtt-introduction]] | MQTT: Standard Messaging Protocol for IoT | IoT | 2026-04-18 |
| [[wiki/sources/hardware-inventory-2026-04-18]] | Hardware Inventory — My IoT Lab | IoT | 2026-04-18 |
| [[wiki/sources/iot-lora-gateway-architecture]] | IoT Architecture: LoRa Gateway | IoT | 2026-04-18 |
| [[wiki/sources/infectious-waste-th-law]] | กฎกระทรวงว่าด้วยการกำจัดมูลฝอยติดเชื้อ พ.ศ. 2545, 2564 | Env | 2026-04-20 |
| [[wiki/sources/hospital-wastewater-treatment]] | มาตรฐานน้ำทิ้ง กระทรวงทรัพยากรฯ พ.ศ. 2563 | Env | 2026-04-20 |
| [[wiki/sources/ddc-cpg-rabies-2564]] | CPG กรมควบคุมโรค Rabies 2564 | Env | 2026-05-02 |
| [[wiki/sources/agent-frameworks-local-debug-2026]] | Agent Frameworks Local Debug Insight | AI | 2026-04-26 |
| [[wiki/sources/openrouter-api-demo]] | OpenRouter API demo script | AI | 2026-04-26 |
| [[wiki/sources/sp-drugstore-2020-catalog]] | SP Drugstore 2020 — 3,760 SKU | Pharmacy | 2026-04-30 |
| [[wiki/sources/pharmacy-context]] | Pharmacy Business Context | Pharmacy | 2026-04-30 |

---

## Synthesis

| หน้า | สรุป | Domain |
|------|------|--------|
| [[wiki/synthesis/iot-lora-architecture]] | Architecture เต็มรูปแบบ (LoRa → MQTT → Telegram/Grafana) | IoT |
| [[wiki/synthesis/temperature-monitor-project]] | แผน 3 แนวทาง (เลือก C: LoRa architecture) | IoT |
| [[wiki/synthesis/energy-power-monitoring]] | PZEM-004T + ESP32 + MQTT → Grafana | IoT |
| [[wiki/synthesis/air-quality-monitoring]] | PMS5003 + LoRa + Grafana, PM2.5/PM10 distributed | IoT |
| [[wiki/synthesis/cold-chain-vaccine]] | DS18B20 + ESP32 + TinyML anomaly, vaccine +2~+8°C | IoT |
| [[wiki/synthesis/fuel-tank-level]] | HC-SR04 + MQTT + Captive Portal, tank level % | IoT |
| [[wiki/synthesis/waste-weight-monitoring]] | Load Cell + HX711 + LoRa + MQTT, waste bin full alert | IoT |
| [[wiki/synthesis/pi4-lora-gateway-server]] | Pi 4 4GB เป็น LoRa gateway + server เครื่องเดียว | IoT |
| [[wiki/synthesis/pharmacy-order-checker]] | ระบบตรวจสอบรายการสั่งยา — Logic + Architecture | Pharmacy |
| [[wiki/synthesis/pharmacy-project-specs]] | Project Specs — แผนการพัฒนาระบบ pharmacy | Pharmacy |
| [[wiki/synthesis/pharmacy-web-app-roadmap]] | Web App Roadmap — FastAPI + React on Pi5 | Pharmacy |
| [[wiki/synthesis/openrouter-agent-routing]] | OpenRouter ใน context ของ agent routing | AI |
| [[wiki/synthesis/dual-ai-workflow]] | Dual AI workflow | AI |
| [[wiki/synthesis/env-webapp-schema-wastewater]] | Web App Schema สำหรับ wastewater management | Env |
| [[wiki/synthesis/appsheet-to-webapp-pi5]] | Migration จาก AppSheet → Web App บน Pi5 | Cross |

---

## Templates (สำหรับ PDF Generation — Env Health Webapp)

> ไฟล์ใน `wiki/templates/` — แบบฟอร์มราชการและเอกสารปฏิบัติงาน  
> จะใช้เป็น reference ในการ generate PDF ผ่าน webapp งานอนามัยสิ่งแวดล้อม (Raspberry Pi 5)

| หน้า | ประเภท | สรุป |
|------|--------|------|
| [[wiki/templates/td-21-power-of-attorney]] | แบบฟอร์มราชการ | ท.ด.21 หนังสือมอบอำนาจ — กรมที่ดิน |

---

## Context Files (Fast Load)

| หน้า | ใช้เมื่อ |
|------|--------|
| [[wiki/context/wiki-overview]] | เริ่ม session — abstract ทุกหน้า รวดเดียว |
| [[wiki/context/knowledge-graph]] | ต้องการรู้ relationships + use case matrix |
| [[wiki/context/wiki-state]] | ดูสถานะ page count, stubs, hardware |
| [[wiki/context/wiki-guide]] | กฎการเขียน wiki สำหรับ Claude |

---

## ⚠️ Contradictions ที่พบ

| หน้า | ปัญหา | วันที่พบ |
|------|------|---------|
| [[wiki/entities/iot/line-notify]] | deprecated ม.ค. 2025 แต่ยังอยู่ใน architecture diagram | 2026-04-18 |
| [[wiki/entities/iot/dx-lr02-lora]] | chip คือ **LLCC68** ไม่ใช่ SX1276 — บาง tutorial อ้าง SX1276 ผิด | 2026-04-18 |

---

## Stubs รอ Source เพิ่ม

IoT: `telegraf`, `esp32-deep-sleep`, `dht22`, `coap`, `hmi-scada`, `radiolib`, `bme688`, `scd41`  
Env: indoor-air-quality, chemical-waste-management  
IT: scanner-setup, network-troubleshooting
