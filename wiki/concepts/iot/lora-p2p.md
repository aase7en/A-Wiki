---
type: concept
tags: [lora, p2p, point-to-point, uart, arduino-lora, sensor-node, gateway]
sources: [esp32-lora-arduino-ide, esp32-lora-sensor-webserver, easyloranode-tracker, lora-thai-intro]
created: 2026-04-18
updated: 2026-04-18
---

# LoRa Point-to-Point (P2P)

## นิยาม

LoRa P2P คือการสื่อสาร LoRa โดยตรงระหว่าง 2 อุปกรณ์ โดยไม่ผ่าน LoRaWAN Network Server เหมาะสำหรับ lab, prototype, หรือระบบที่มี node จำนวนน้อย

## ทำไมถึงสำคัญใน IoT

LoRa P2P เป็นวิธีที่ง่ายและเร็วที่สุดในการเริ่มต้นใช้งาน LoRa ไม่ต้องการ cloud service, gateway hardware พิเศษ, หรือ network server — เพียง LoRa module 2 ตัวก็ทำ long-range link ได้ทันที

## วิธีการทำงาน

**Pattern หลักในโปรเจ็คนี้:**
```
[Sensor Node]                    [Gateway Node]
ESP32 + DHT11                    ESP32-S3
    ↓ UART                           ↓ UART
[DX-LR02 TX]  ~~LoRa 900MHz~~  [DX-LR02 RX]
                                     ↓ WiFi + MQTT
                               [Mosquitto Broker]
                                     ↓
                               [Dashboard / Alert]
```

## 2 วิธี Interface กับ LoRa Module

| วิธี | Module ตัวอย่าง | ใช้กับ library | ข้อดี |
|------|--------------|--------------|-------|
| **UART (AT commands)** | DX-LR02, E32, E220 | ไม่ต้องการ library พิเศษ | ง่าย, transparent mode |
| **SPI (register-level)** | RFM95, SX1276, TTGO LoRa32 | `sandeepmistry/arduino-LoRa` | control ได้มากกว่า |

**โปรเจ็คนี้ใช้ UART (DX-LR02)** — ส่ง serial data ผ่าน UART, module จัดการ LoRa เอง

### DX-LR02 UART Mode (Transparent)
```cpp
// โหมด Normal (M0=0, M1=0): ส่ง UART → ออก LoRa อัตโนมัติ
Serial2.begin(9600);        // baud rate ของ DX-LR02
Serial2.println("28.5");    // ส่ง LoRa ทันที (transparent mode)

// ฝั่ง receiver:
if (Serial2.available()) {
    String data = Serial2.readString();  // รับ LoRa data
}
```

### RFM95/SX1276 SPI Mode (arduino-LoRa library)
```cpp
#include <LoRa.h>
LoRa.begin(915E6);           // ตั้ง frequency
LoRa.beginPacket();
LoRa.print("28.5");
LoRa.endPacket();            // ส่ง LoRa packet
```

## Packet Format แนะนำสำหรับโปรเจ็คนี้

```
// ส่งเป็น JSON string ผ่าน UART → LoRa
{"device":"node01","temp":28.5,"hum":65.2,"rssi":-87}
```

หรือ CSV แบบเบา:
```
node01,28.5,65.2
```

## Power Optimization Tips

- **Deep sleep ระหว่าง reading**: ตั้ง ESP32 deep sleep, ตื่นทุก 30 วินาที → อ่าน sensor → ส่ง LoRa → กลับ sleep
- **ปิด LoRa module**: DX-LR02 ใส่ M1=1 → deep sleep mode ใช้ไฟน้อยลง
- Target: <15µA ขณะ deep sleep (เหมือน EasyLoRaNode Tracker)

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| ง่าย ไม่ต้องการ cloud | scale ได้ยาก (หลาย node) |
| ไม่มีค่าบริการรายเดือน | ไม่มี encryption built-in |
| เริ่มต้นได้ทันที | ไม่มี network management |
| hardware ราคาถูก | ต้อง handle collision เอง (ถ้าหลาย node) |

## ความสัมพันธ์

- Hardware: [[entities/iot/dx-lr02-lora]] (UART), [[entities/iot/rfm95-sx1276]] (SPI)
- เปรียบเทียบกับ: [[concepts/iot/lorawan]] — LoRaWAN เหมาะ scale ขึ้น
- Physical layer: [[concepts/iot/lora]]
- ใช้ร่วมกับ: [[entities/iot/esp32]], [[entities/iot/esp32-s3]]

## แหล่งข้อมูล

- [[sources/esp32-lora-arduino-ide]] — P2P code + library (SPI method)
- [[sources/esp32-lora-sensor-webserver]] — project pattern sender/receiver
- [[sources/easyloranode-tracker]] — deep sleep + power optimization
- [[sources/lora-thai-intro]] — Thailand frequency legal reference
