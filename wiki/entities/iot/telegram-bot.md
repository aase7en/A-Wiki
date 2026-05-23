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
