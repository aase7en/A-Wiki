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
