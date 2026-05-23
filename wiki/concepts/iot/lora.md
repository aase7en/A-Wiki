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
