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
