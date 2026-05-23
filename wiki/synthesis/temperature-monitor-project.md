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
