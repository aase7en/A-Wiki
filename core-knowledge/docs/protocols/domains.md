# Domains

> Wiki แยกเป็น 4 domains หลัก + cross-domain synthesis. ใช้สำหรับ classify source ตอน ingest และเลือก path/index ที่ถูกต้อง.
> Loaded on demand — Claude อ่านไฟล์นี้เมื่อ ingest source ใหม่หรือ user ถามข้ามโดเมน. ไม่ได้ auto-load ทุก session.

## Domain 1: Internet of Things (IoT)

- **Protocols**: MQTT, CoAP, HTTP, WebSocket, Zigbee, Z-Wave, BLE, LoRa, NB-IoT, LTE-M
- **Hardware**: ESP32, ESP8266, Raspberry Pi, Arduino, industrial PLCs
- **Platforms**: Home Assistant, AWS IoT, Azure IoT Hub, Google Cloud IoT, Tuya, Matter
- **Security**: device authentication, TLS/DTLS, firmware OTA, edge security
- **Architecture**: edge computing, fog computing, cloud-IoT, digital twins
- **Standards**: Matter, Thread, IEEE 802.15.4, ETSI, oneM2M
- **Path**: `wiki/entities/iot/`, `wiki/concepts/iot/`, `index-iot.md`

## Domain 2: Environmental Health (อนามัยสิ่งแวดล้อม)

- **กฎหมาย/มาตรฐาน**: พรบ.สิ่งแวดล้อม, มาตรฐานโรงพยาบาล กรมอนามัย, WHO guidelines
- **ของเสีย**: ขยะติดเชื้อ, ขยะเคมี, น้ำเสีย, อากาศเสีย
- **ระบบ**: บำบัดน้ำเสีย, กรองอากาศ HEPA, autoclave, เตาเผา
- **การตรวจวัด**: เครื่องมือวัดสิ่งแวดล้อม, มาตรฐานตรวจ
- **Path**: `wiki/entities/env/`, `wiki/concepts/env/`, `index-env.md`

## Domain 3: AI Tools

- **Agent frameworks**: Hermes Agent, Claude Code, OpenClaw
- **LLM providers**: OpenRouter, MiniMax, OpenAI, Anthropic
- **Automation**: cron, webhook, gateway, skills
- **Memory & context**: mem0, honcho, hindsight, MCP servers
- **Path**: `wiki/entities/ai-tools/`, `wiki/concepts/ai-tools/`, `index-ai.md`

## Domain 4: Pharmacy (ร้านขายยา ภูฟาร์มาซี)

- **ฐานข้อมูลยา**: catalog จากบริษัทขายส่ง (SP Drugstore 2020: 3,760 SKU), ชื่อสามัญ, ขนาดยา, หน่วยสั่งซื้อ
- **Drug validation**: fuzzy match ชื่อยาสะกดผิด → ชื่อมาตรฐาน, aliases, ATC code
- **Ordering workflow**: รับรายการจาก LINE (ข้อความ/รูปภาพ) → ตรวจสอบ → export order
- **Supplier**: เอสพีดรักสโตร์ 2020 และบริษัทอื่นๆ
- **Web App (อนาคต)**: FastAPI + React บน Pi5, Claude API สำหรับ OCR + drug validation
- **Runtime DB (primary)**: `wiki/entities/pharmacy/drugs.db` — SQLite FTS5 ที่ build จาก raw JSON (gitignored — รัน `python3 scripts/build_pharmacy_db.py` เพื่อ regenerate)
- **Raw data (source, immutable)**: `raw/pharmacy/sp_drugs_full_3760.json` 3,760 รายการ + `raw/pharmacy/sp_drugs_medications_2895.json` 2,895 รายการ (ยาเท่านั้น)
- **Path**: `wiki/entities/pharmacy/`, `wiki/concepts/pharmacy/`, `index-pharmacy.md`

## Cross-domain

- **IoT × Env**: ระบบ IoT ตรวจวัดสิ่งแวดล้อมโรงพยาบาล
- **AI × IoT**: ใช้ AI agent ควบคุม/วิเคราะห์ IoT data
- **AI × Pharmacy**: Claude API ตรวจสอบรายการยา + OCR รูปภาพ
- **Path**: `wiki/synthesis/` (เน้น synthesis เป็นหลัก)

## Ingest Rule

เมื่อ ingest source ใหม่ ให้ระบุ domain ก่อนเสมอ — ถ้าไม่ชัด ถามผู้ใช้ก่อนสร้างไฟล์.
