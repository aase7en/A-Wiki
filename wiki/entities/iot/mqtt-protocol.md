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
