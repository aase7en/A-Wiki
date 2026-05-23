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
