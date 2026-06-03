> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#-cost-first-decision-pyramid-บังคับคิดก่อนทุกงาน)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---


# Scoped Context — IoT Concepts

> **โดเมน**: Internet of Things (IoT) — Concepts
> **Last updated**: 2026-06-03
> **ไฟล์นี้เป็น nested context สำหรับ Claude/Cline — อ่านเมื่อทำงานใน concepts/iot/ เท่านั้น**

---

## Concepts ที่มีอยู่ (11 concepts)

| Slug | Abstract |
|------|----------|
| `air-quality-index` | AQI — มาตรฐานสากลแปลงค่ามลพิษเป็นสเกลเดียว |
| `cold-chain-monitoring` | IoT วัดอุณหภูมิสินค้าตลอดห่วงโซ่อุปทาน |
| `dashboard-design` | Dashboard design principles สำหรับ IoT |
| `data-logger` | บันทึก sensor data ต่อเนื่องลง database |
| `lora` | LoRa modulation — CSS, long-range, low-power |
| `lora-p2p` | LoRa point-to-point โดยไม่ผ่าน LoRaWAN server |
| `lorawan` | LoRaWAN network protocol — star topology, device classes |
| `modbus` | Industrial serial protocol (1979) — RTU/ASCII/TCP |
| `mqtt-qos` | QoS 0/1/2 tradeoffs |
| `publish-subscribe` | Pub/sub messaging pattern |
| `tinyml` | ML บน microcontroller (RAM < 1MB) |

---

## Rules สำหรับ concept pages

1. **frontmatter บังคับ**: `type`, `tags`, `sources`, `created`, `updated`, `last_verified`, `verify_tool`
2. **ทุก concept ต้องมี**: นิยาม, ทำไมถึงสำคัญใน IoT, วิธีการทำงาน, ตัวอย่างการใช้งาน, ข้อดี/ข้อเสีย
3. **Cross-reference**: ลิงก์ไป entities และ synthesis ที่เกี่ยวข้อง
4. **Confidence markers**: `[training]` / `[verified YYYY-MM-DD]` / `[wiki]`

---

## ความสัมพันธ์กับ entities

| Concept | Entity ที่เกี่ยวข้อง |
|---------|---------------------|
| lora, lora-p2p, lorawan | dx-lr02-lora, rfm95-sx1276, chirpstack, the-things-network |
| mqtt-qos, publish-subscribe | mosquitto, emqx, mqtt-protocol |
| tinyml | esp32, esp32-s3 |
| cold-chain-monitoring | ds18b20, esp32 |
| air-quality-index | pms5003, esp32 |
| dashboard-design, data-logger | grafana, influxdb, node-red, mysql |

---

## Workflow สำหรับสร้าง concept ใหม่

1. ตรวจสอบว่าไม่มี concept นี้แล้ว — ค้นหาจาก `wiki-overview.md` หรือ grep
2. ใช้ template จาก CLAUDE.md หลัก (section Concept Page Template)
3. เชื่อมโยงไปยัง entities ที่เกี่ยวข้อง
4. อัปเดต cross-domain ถ้าต้อง synthesis
5. อัปเดต `index-iot.md` + รัน `python3 scripts/gen-index.py`
6. บันทึกใน `log.md`