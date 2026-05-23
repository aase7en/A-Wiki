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
