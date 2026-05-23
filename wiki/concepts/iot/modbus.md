---
type: concept
tags: [modbus, protocol, industrial, rs485, serial, plc]
sources: [iot-nodered-mqtt-sql-course]
created: 2026-04-18
updated: 2026-04-18
---

# Modbus

## นิยาม

Modbus เป็น serial communication protocol ที่เก่าแก่ที่สุดในอุตสาหกรรม (1979) ออกแบบมาสำหรับเชื่อมต่อ PLC กับ HMI ปัจจุบันยังใช้งานแพร่หลายมากในอุปกรณ์อุตสาหกรรม เช่น temperature controller, power meter, VFD, sensor transmitter

## ทำไมถึงสำคัญใน IoT

อุปกรณ์อุตสาหกรรมส่วนใหญ่ยังพูด Modbus เป็นภาษาหลัก ถ้าต้องการ integrate IoT กับเครื่องจักรในโรงงาน ต้องรู้ Modbus

## วิธีการทำงาน

**Modbus RTU** (serial RS-485):
```
[Master (Node-RED)]  ──RS485──  [Slave Device (e.g. Omron E5CC)]
     ↑ poll request                ↓ response (register value)
```

**Modbus TCP** (ethernet):
```
[Master] ──TCP/IP──  [Slave/Gateway]
```

**Register Types**:
| ประเภท | Address | ข้อมูล |
|--------|---------|--------|
| Coil | 0x | Digital output (R/W) |
| Discrete Input | 1x | Digital input (R) |
| Holding Register | 4x | Analog/config (R/W) |
| Input Register | 3x | Analog input (R) |

## ตัวอย่างการใช้งาน (Node-RED)

```
[Modbus Read node] ← ตั้งค่า: server, FC (function code), address, quantity
        ↓
[msg.payload = [28.5, 65.2]]   ← array ของ register values
        ↓
[Function node]               ← แปลง raw value เป็น temp/humidity
        ↓
[MQTT out node]               ← publish ต่อไปยัง Broker
```

## อุปกรณ์ที่รองรับ Modbus (ที่พบบ่อย)

- **Temp Controller**: Omron E5CC, Autonics TC
- **Power Meter**: PZEM-004T, Eastron SDM120
- **VFD (Inverter)**: Delta, Mitsubishi, Siemens
- **PLC**: Mitsubishi FX5U (Modbus TCP), Siemens (ผ่าน gateway)
- **Sensor Transmitter**: 4-20mA → Modbus converter

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|-------|---------|
| standard เก่า รองรับทุก device | ช้า (baud rate 9600-115200) |
| node-red-contrib-modbus ฟรี | poll-based ไม่ใช่ event-driven |
| debug ง่าย | max 247 slaves ต่อ bus |
| ไม่ต้องการ internet | ไม่มี encryption/auth |

## ความสัมพันธ์

- [[entities/iot/node-red]] — มี Modbus node สำหรับ read/write registers
- [[concepts/iot/publish-subscribe]] — ต่างจาก Modbus ตรงที่ Modbus เป็น request/response

## แหล่งข้อมูล

- [[sources/iot-nodered-mqtt-sql-course]] — Modbus TCP/RTU กับ Node-RED
