---
type: entity
category: device
tags: [sensor, power-meter, energy, modbus, uart, ac, pzem]
sources: [espem-energy-monitor]
created: 2026-04-18
updated: 2026-04-18
---

# PZEM-004T

**ผู้ผลิต**: PeaceFair  
**รุ่น**: v3.0 (ปัจจุบัน)  
**สถานะใน Lab**: ❌ ยังไม่มี (future expansion)  
**ราคาประมาณ**: ~$10-15 (AliExpress)

## ภาพรวม

PZEM-004T คือ AC power meter module วัดพารามิเตอร์ไฟฟ้าได้หลายค่าพร้อมกัน — Voltage, Current, Power, Energy, Power Factor, Frequency — และสื่อสารผ่าน UART TTL (Modbus RTU protocol) เหมาะสำหรับ energy monitoring ในบ้านหรือโรงงานเล็กๆ

## Specs หลัก

| พารามิเตอร์ | ย่าน | ความละเอียด |
|------------|------|------------|
| Voltage | 80–260V AC | 0.1V |
| Current | 0–100A | 0.001A |
| Power | 0–23kW | 0.1W |
| Energy | 0–9999kWh | 1Wh |
| Power Factor | 0.00–1.00 | 0.01 |
| Frequency | 45–65Hz | 0.1Hz |

**Interface**: UART TTL (Modbus RTU, 9600 baud)  
**Supply**: 5V DC

## การใช้งานใน IoT

```
[สายไฟ AC] ──CT clamp──> [PZEM-004T] ──UART──> [ESP32]
                                                    ↓
                                             [MQTT publish]
                                                    ↓
                                          [Broker → Grafana]
```

ใช้คู่กับ [[entities/iot/esp32]] หรือ [[entities/iot/raspberry-pi]] เพื่อ publish พลังงานไฟฟ้าแบบ real-time ไปยัง MQTT broker

## MQTT JSON Format (จาก espem project)

```json
[{"U":2180,"I":503,"P":778,"W":560,"Pf":71,"freq":505}]
```
(หน่วย: decivolts, mA, deciwatts, Wh, %, dHz)

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/iot/esp32]] — MCU อ่านค่าผ่าน UART
- Protocol: [[concepts/iot/modbus]] — Modbus RTU บน UART
- Pattern: [[concepts/iot/data-logger]] — บันทึก energy data ย้อนหลัง
- Source project: [[sources/espem-energy-monitor]]

## แหล่งข้อมูล

- [[sources/espem-energy-monitor]] — ESP32 + PZEM-004T energy monitor project พร้อม MQTT + WebUI
