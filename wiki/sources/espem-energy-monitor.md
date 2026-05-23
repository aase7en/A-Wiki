---
type: source
title: "vortigont/espem: Energy Monitor with Dashboard (ESP32 + PZEM-004T)"
slug: espem-energy-monitor
date_ingested: 2026-04-18
original_file: raw/vortigontespem Energy monitor with dashboardmetrics collector based on ESP32 controller and PeaceFair PZEM-004TPZEM-004Tv30 Power Meter.md
tags: [esp32, pzem-004t, power-meter, energy-monitor, mqtt, websocket, dashboard, github]
---

# vortigont/espem: Energy Monitor (ESP32 + PZEM-004T)

**ประเภท**: GitHub project (open source)
**ผู้เขียน**: vortigont

## ประเด็นหลัก

1. **ESP32 + PZEM-004T** — วัด Voltage/Current/Power/Energy/Power Factor/Frequency แบบ real-time
2. **WebUI via HTTP/WebSocket** — self-hosted บน ESP32 เอง ไม่ต้องการ server ภายนอก
3. **MQTT publishing** — ส่ง metrics เป็น JSON ไปยัง broker ทุก update cycle
4. **Tiered TimeSeries** — เก็บ metrics ใน ESP32 memory 3 ระดับ ไม่ต้องการ external DB
5. **OTA update** — อัปเดต firmware ผ่าน network ได้

## MQTT Message Format

```json
[{"stale":false,"age":999,"U":2180,"I":503,"P":778,"W":560,"Pf":71,"freq":505}]
```

| Field | หน่วย | ความหมาย |
|-------|-------|---------|
| U | decivolts (÷10) | Voltage — 2180 = 218.0V |
| I | mA | Current — 503 = 503mA |
| P | deciwatts (÷10) | Power — 778 = 77.8W |
| W | Wh | Energy accumulated |
| Pf | % | Power Factor |
| freq | dHz (÷10) | Frequency — 505 = 50.5Hz |

## PZEM-004T v3.0 Specs

- วัด AC 80-260V, 0-100A
- Interface: UART TTL (Modbus RTU)
- ราคา ~$10-15 (AliExpress)
- สื่อสาร: RS485 หรือ TTL UART โดยตรง

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

**Future expansion** — โปรเจ็คปัจจุบันวัดอุณหภูมิ แต่ถ้าต้องการ monitor พลังงานไฟฟ้าในบ้าน/โรงงาน PZEM-004T + ESP32 + MQTT คือ stack ที่สมบูรณ์แบบ รูปแบบ MQTT topic เดียวกัน

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/pzem-004t]] — สร้างใหม่ (stub)
